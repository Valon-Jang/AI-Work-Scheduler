import tempfile
import unittest
from pathlib import Path

from ai_work_scheduler import ActionStatus, Message, Store, build_extraction_payload, ingest_model_output
from ai_work_scheduler.preprocess import strip_reply_history


class SchedulerCoreTests(unittest.TestCase):
    def make_store(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Store(Path(tmp.name) / "scheduler.db")

    def test_one_message_can_create_multiple_actions(self):
        store = self.make_store()
        message = Message("m1", "Project update", "Please review the draft and join the review meeting Friday.")
        raw = {"actions": [
            {"type": "task", "title": "Review the draft", "date_text": None},
            {"type": "event", "title": "Join the review meeting", "date_text": "Friday"},
        ]}
        ids = ingest_model_output(store, message, raw)
        self.assertEqual(len(ids), 2)
        self.assertEqual(len(store.list_actions()), 2)

    def test_missing_date_stays_null(self):
        payload = build_extraction_payload(Message("m2", "Review", "Please review the document."))
        self.assertIn("Never invent one", payload["instructions"])
        store = self.make_store()
        ingest_model_output(store, Message("m2", "Review", "Please review the document."), {
            "actions": [{"type": "task", "title": "Review the document", "date_text": None}]
        })
        self.assertIsNone(store.list_actions()[0]["date_text"])

    def test_reingest_is_idempotent(self):
        store = self.make_store()
        message = Message("m3", "Review", "Please review the document.")
        raw = {"actions": [{"type": "task", "title": "Review the document", "date_text": None}]}
        first = ingest_model_output(store, message, raw)
        second = ingest_model_output(store, message, raw)
        self.assertEqual(first, second)
        self.assertEqual(len(store.list_actions()), 1)

    def test_execution_requires_approval(self):
        store = self.make_store()
        message = Message("m4", "Review", "Please review the document.")
        action_id = ingest_model_output(store, message, {
            "actions": [{"type": "task", "title": "Review the document"}]
        })[0]
        with self.assertRaises(ValueError):
            store.set_status(action_id, ActionStatus.EXECUTED)
        store.set_status(action_id, ActionStatus.APPROVED)
        store.set_status(action_id, ActionStatus.EXECUTED)
        self.assertEqual(store.list_actions()[0]["status"], "executed")

    def test_reply_history_split(self):
        current, history = strip_reply_history(
            "Please review this.\n\nFrom: Old Sender\nSent: Yesterday\nTo: Me\nSubject: Old\nOld body"
        )
        self.assertEqual(current, "Please review this.")
        self.assertIn("Old Sender", history)


if __name__ == "__main__":
    unittest.main()

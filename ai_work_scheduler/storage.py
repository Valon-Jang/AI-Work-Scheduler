from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import ActionStatus, CandidateAction, Message


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS messages (
    source_id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    sender TEXT,
    received_at TEXT,
    conversation_id TEXT,
    previous_body TEXT
);
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_key TEXT NOT NULL UNIQUE,
    source_id TEXT NOT NULL REFERENCES messages(source_id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,
    title TEXT NOT NULL,
    date_text TEXT,
    start_text TEXT,
    rationale TEXT,
    source_quote TEXT,
    confidence REAL,
    status TEXT NOT NULL DEFAULT 'candidate',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at TEXT,
    executed_at TEXT
);
"""


def action_key(source_id: str, action: CandidateAction) -> str:
    canonical = json.dumps(
        {
            "source_id": source_id,
            "type": action.action_type.value,
            "title": " ".join(action.title.lower().split()),
            "date_text": action.date_text,
            "start_text": action.start_text,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._connection() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def save_message(self, message: Message) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO messages(source_id, subject, body, sender, received_at, conversation_id, previous_body)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    subject=excluded.subject,
                    body=excluded.body,
                    sender=excluded.sender,
                    received_at=excluded.received_at,
                    conversation_id=excluded.conversation_id,
                    previous_body=excluded.previous_body
                """,
                (
                    message.source_id,
                    message.subject,
                    message.body,
                    message.sender,
                    message.received_at,
                    message.conversation_id,
                    message.previous_body,
                ),
            )

    def add_candidates(self, message: Message, actions: list[CandidateAction]) -> list[int]:
        self.save_message(message)
        ids: list[int] = []
        with self._connection() as conn:
            for action in actions:
                key = action_key(message.source_id, action)
                conn.execute(
                    """
                    INSERT OR IGNORE INTO actions(
                        action_key, source_id, action_type, title, date_text, start_text,
                        rationale, source_quote, confidence, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        key,
                        message.source_id,
                        action.action_type.value,
                        action.title,
                        action.date_text,
                        action.start_text,
                        action.rationale,
                        action.source_quote,
                        action.confidence,
                        ActionStatus.CANDIDATE.value,
                    ),
                )
                row = conn.execute("SELECT id FROM actions WHERE action_key = ?", (key,)).fetchone()
                ids.append(int(row["id"]))
        return ids

    def set_status(self, action_id: int, status: ActionStatus) -> None:
        with self._connection() as conn:
            if status is ActionStatus.EXECUTED:
                current = conn.execute("SELECT status FROM actions WHERE id = ?", (action_id,)).fetchone()
                if current is None:
                    raise KeyError(action_id)
                if current["status"] != ActionStatus.APPROVED.value:
                    raise ValueError("an action must be approved before it can be marked executed")
                conn.execute(
                    "UPDATE actions SET status=?, executed_at=CURRENT_TIMESTAMP WHERE id=?",
                    (status.value, action_id),
                )
            elif status is ActionStatus.APPROVED:
                changed = conn.execute(
                    "UPDATE actions SET status=?, approved_at=CURRENT_TIMESTAMP WHERE id=?",
                    (status.value, action_id),
                ).rowcount
                if changed == 0:
                    raise KeyError(action_id)
            else:
                changed = conn.execute(
                    "UPDATE actions SET status=? WHERE id=?", (status.value, action_id)
                ).rowcount
                if changed == 0:
                    raise KeyError(action_id)

    def list_actions(self, status: ActionStatus | None = None) -> list[dict]:
        query = "SELECT * FROM actions"
        params: tuple = ()
        if status is not None:
            query += " WHERE status = ?"
            params = (status.value,)
        query += " ORDER BY id"
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .extraction import build_extraction_payload
from .models import ActionStatus, Message
from .pipeline import ingest_model_output
from .storage import Store


def _load_message(path: Path) -> Message:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Message(
        source_id=str(data["source_id"]),
        subject=str(data.get("subject", "")),
        body=str(data.get("body", "")),
        sender=data.get("sender"),
        received_at=data.get("received_at"),
        conversation_id=data.get("conversation_id"),
        previous_body=data.get("previous_body"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-work-scheduler")
    parser.add_argument("--db", default="ai_work_scheduler.db", help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)

    prompt_cmd = sub.add_parser("prompt", help="Build an AI extraction payload for a message")
    prompt_cmd.add_argument("message", type=Path)

    ingest_cmd = sub.add_parser("ingest", help="Store candidate actions returned by an AI")
    ingest_cmd.add_argument("message", type=Path)
    ingest_cmd.add_argument("actions", type=Path)

    list_cmd = sub.add_parser("list", help="List stored actions")
    list_cmd.add_argument("--status", choices=[s.value for s in ActionStatus])

    for name in ("approve", "reject", "hold", "execute"):
        cmd = sub.add_parser(name)
        cmd.add_argument("action_id", type=int)

    args = parser.parse_args(argv)
    store = Store(args.db)

    if args.command == "prompt":
        print(json.dumps(build_extraction_payload(_load_message(args.message)), ensure_ascii=False, indent=2))
        return 0

    if args.command == "ingest":
        message = _load_message(args.message)
        raw = args.actions.read_text(encoding="utf-8")
        ids = ingest_model_output(store, message, raw)
        print(json.dumps({"candidate_action_ids": ids}, ensure_ascii=False))
        return 0

    if args.command == "list":
        status = None if args.status is None else ActionStatus(args.status)
        print(json.dumps(store.list_actions(status), ensure_ascii=False, indent=2))
        return 0

    status_map = {
        "approve": ActionStatus.APPROVED,
        "reject": ActionStatus.REJECTED,
        "hold": ActionStatus.HELD,
        "execute": ActionStatus.EXECUTED,
    }
    store.set_status(args.action_id, status_map[args.command])
    print(json.dumps({"action_id": args.action_id, "status": status_map[args.command].value}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

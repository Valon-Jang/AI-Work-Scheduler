from __future__ import annotations

import json
from typing import Iterable

from .models import CandidateAction, Message
from .preprocess import should_include_previous, strip_reply_history


SYSTEM_RULES = """You extract reviewable work actions from a message.
Return JSON only.
Rules:
- One message may produce multiple actions.
- type must be task, event, follow_up, or ignore.
- task: something the user should do now.
- follow_up: something to check again after waiting for another person/system.
- event: a time-bound meeting or calendar event.
- Preserve date/time/deadline wording exactly in date_text/start_text.
- If the source contains no date/time, use null. Never invent one.
- Merge sequential or conditional steps that serve one work objective.
- Do not claim an action is approved or executed; these are candidates only.
"""


def build_extraction_payload(message: Message) -> dict:
    newest, history = strip_reply_history(message.body)
    context = None
    if should_include_previous(newest, message.previous_body):
        context = message.previous_body
    elif should_include_previous(newest, history):
        context = history

    return {
        "instructions": SYSTEM_RULES,
        "message": {
            "source_id": message.source_id,
            "subject": message.subject,
            "body": newest,
            "previous_context": context,
        },
        "response_schema": {
            "actions": [
                {
                    "type": "task|event|follow_up|ignore",
                    "title": "string",
                    "date_text": "string|null",
                    "start_text": "string|null",
                    "rationale": "string|null",
                    "source_quote": "string|null",
                    "confidence": "0..1|null",
                }
            ]
        },
    }


def parse_model_output(raw: str | bytes | dict | list) -> list[CandidateAction]:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        raw = json.loads(raw)

    if isinstance(raw, dict):
        items = raw.get("actions")
    elif isinstance(raw, list):
        items = raw
    else:
        items = None

    if not isinstance(items, list):
        raise ValueError("model output must be a JSON list or an object with actions[]")

    actions = [CandidateAction.from_mapping(item) for item in items]
    return list(_deduplicate_semantic(actions))


def _deduplicate_semantic(actions: Iterable[CandidateAction]) -> Iterable[CandidateAction]:
    seen: set[tuple[str, str, str | None, str | None]] = set()
    for action in actions:
        key = (
            action.action_type.value,
            " ".join(action.title.lower().split()),
            action.date_text,
            action.start_text,
        )
        if key not in seen:
            seen.add(key)
            yield action

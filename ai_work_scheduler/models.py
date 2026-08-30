from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    TASK = "task"
    EVENT = "event"
    FOLLOW_UP = "follow_up"
    IGNORE = "ignore"


class ActionStatus(str, Enum):
    CANDIDATE = "candidate"
    APPROVED = "approved"
    REJECTED = "rejected"
    HELD = "held"
    EXECUTED = "executed"


@dataclass(frozen=True)
class Message:
    source_id: str
    subject: str
    body: str
    sender: str | None = None
    received_at: str | None = None
    conversation_id: str | None = None
    previous_body: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")


@dataclass(frozen=True)
class CandidateAction:
    action_type: ActionType
    title: str
    date_text: str | None = None
    start_text: str | None = None
    rationale: str | None = None
    source_quote: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if self.action_type is not ActionType.IGNORE and not self.title.strip():
            raise ValueError("non-ignore actions require a title")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

    @classmethod
    def from_mapping(cls, item: dict[str, Any]) -> "CandidateAction":
        try:
            action_type = ActionType(str(item["type"]))
        except (KeyError, ValueError) as exc:
            raise ValueError("action type must be one of task/event/follow_up/ignore") from exc

        def optional_text(key: str) -> str | None:
            value = item.get(key)
            if value is None:
                return None
            return str(value)

        confidence = item.get("confidence")
        return cls(
            action_type=action_type,
            title=str(item.get("title", "")),
            date_text=optional_text("date_text"),
            start_text=optional_text("start_text"),
            rationale=optional_text("rationale"),
            source_quote=optional_text("source_quote"),
            confidence=None if confidence is None else float(confidence),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.action_type.value,
            "title": self.title,
            "date_text": self.date_text,
            "start_text": self.start_text,
            "rationale": self.rationale,
            "source_quote": self.source_quote,
            "confidence": self.confidence,
        }

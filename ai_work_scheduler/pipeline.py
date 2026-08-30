from __future__ import annotations

from .extraction import parse_model_output
from .models import Message
from .storage import Store


def ingest_model_output(store: Store, message: Message, raw_model_output) -> list[int]:
    """Persist a message and candidate actions without auto-approving them."""

    actions = parse_model_output(raw_model_output)
    return store.add_candidates(message, actions)

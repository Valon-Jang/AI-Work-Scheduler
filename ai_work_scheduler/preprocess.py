from __future__ import annotations

import re


_REPLY_HEADER = re.compile(
    r"(?im)^(?:from|sent|to|subject|보낸\s*사람|보낸\s*날짜|받는\s*사람|제목)\s*:\s*"
)


def strip_reply_history(body: str) -> tuple[str, str | None]:
    """Split a message body into newest text and older quoted history.

    This intentionally uses a conservative header-block heuristic. It is not
    expected to cover every mail client or locale.
    """

    matches = list(_REPLY_HEADER.finditer(body))
    if not matches:
        return body.strip(), None

    split_at = matches[0].start()
    newest = body[:split_at].strip()
    history = body[split_at:].strip()
    return newest or body.strip(), history or None


def should_include_previous(current_body: str, previous_body: str | None, threshold: int = 80) -> bool:
    """Use one previous message only when the newest text is very short."""

    return bool(previous_body and len(current_body.strip()) < threshold)

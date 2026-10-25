"""Secret redaction helpers for venue / broker logging.

Never log raw API keys, secrets, or bearer tokens from requests, health,
companion payloads, or crash dumps.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, MutableMapping

_SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|api[_-]?secret|secret|password|token|authorization|authent|"
    r"private[_-]?key|bearer|passwd|credential)",
    re.IGNORECASE,
)
_BEARER_RE = re.compile(r"(Bearer\s+)([A-Za-z0-9._\-]+)", re.IGNORECASE)


def mask_secret(value: str, *, visible: int = 4) -> str:
    """Mask a secret string, keeping a short prefix for debugging."""
    if value is None:
        return ""
    text = str(value)
    if not text:
        return ""
    if len(text) <= visible:
        return "*" * len(text)
    return text[:visible] + "*" * (len(text) - visible)


def redact_text(text: str) -> str:
    """Redact bearer tokens and obvious key=value pairs in free text."""
    if not text:
        return text
    redacted = _BEARER_RE.sub(lambda m: m.group(1) + mask_secret(m.group(2)), text)

    def _kv(match: re.Match[str]) -> str:
        return f"{match.group(1)}{mask_secret(match.group(2))}"

    redacted = re.sub(
        r"(?i)(api[_-]?key|api[_-]?secret|secret|token)\s*[:=]\s*([^\s,;]+)",
        _kv,
        redacted,
    )
    return redacted


def redact_mapping(data: Mapping[str, Any]) -> dict:
    """Return a shallow-copied mapping with secret-looking keys masked."""
    out: dict = {}
    for key, value in data.items():
        if _SECRET_KEY_RE.search(str(key)):
            out[key] = mask_secret(str(value) if value is not None else "")
        elif isinstance(value, Mapping):
            out[key] = redact_mapping(value)
        elif isinstance(value, str):
            out[key] = redact_text(value)
        else:
            out[key] = value
    return out


def scrub_inplace(data: MutableMapping[str, Any]) -> None:
    """Mask secret keys in-place (for settings dumps before logging)."""
    for key in list(data.keys()):
        if _SECRET_KEY_RE.search(str(key)):
            data[key] = mask_secret(str(data[key]) if data[key] is not None else "")
        elif isinstance(data[key], dict):
            scrub_inplace(data[key])

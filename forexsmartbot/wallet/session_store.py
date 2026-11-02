"""Process-local wallet session store (no private keys, no disk by default)."""

from __future__ import annotations

from typing import Optional

from .models import WalletSession

# Module-level session — cleared on disconnect / process exit.
_SESSION: Optional[WalletSession] = None
# Ephemeral WC pairing material (symKey) — never written to settings/disk.
_PAIRING_SECRETS: dict = {}


def get_session() -> Optional[WalletSession]:
    return _SESSION


def set_session(session: Optional[WalletSession]) -> None:
    global _SESSION
    _SESSION = session


def clear_session() -> None:
    global _SESSION
    _SESSION = None
    _PAIRING_SECRETS.clear()


def stash_pairing(topic: str, sym_key: str) -> None:
    """Keep WC symKey in RAM only for the active pairing attempt."""
    _PAIRING_SECRETS["topic"] = topic
    _PAIRING_SECRETS["sym_key"] = sym_key


def pop_pairing() -> dict:
    data = dict(_PAIRING_SECRETS)
    _PAIRING_SECRETS.clear()
    return data

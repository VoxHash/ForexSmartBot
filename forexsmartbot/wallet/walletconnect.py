"""WalletConnect / Reown helpers for desktop PyQt (dApp side).

PyQt has no ``window.ethereum`` injection. Desktop connect uses a
WalletConnect v2 pairing URI the user scans with MetaMask mobile (or opens
via MetaMask deep link). Full relay settlement needs a Reown Cloud
``WALLETCONNECT_PROJECT_ID``; without it we still emit a well-formed URI
scaffold and require explicit ``complete_connect`` with the public address
after the user confirms in-wallet (session-only, no private keys).

URI shape follows WalletConnect v2 / EIP-1328 (``wc:<topic>@2?…``).
Relay: ``wss://relay.walletconnect.com`` (official).
MetaMask deep link: ``https://metamask.app.link/wc?uri=…``.
"""

from __future__ import annotations

import os
import secrets
import urllib.parse
from typing import Optional, Tuple

from .base import WalletConnectConfigError


RELAY_URL = "wss://relay.walletconnect.com"
METAMASK_WC_DEEPLINK_BASE = "https://metamask.app.link/wc"


def get_project_id() -> Optional[str]:
    """Return Reown/WalletConnect Cloud project id from env (public id)."""
    pid = os.getenv("WALLETCONNECT_PROJECT_ID", "").strip()
    return pid or None


def require_project_id() -> str:
    pid = get_project_id()
    if not pid:
        raise WalletConnectConfigError(
            "Set WALLETCONNECT_PROJECT_ID (Reown Cloud) for live WalletConnect "
            "pairing. Until then, use MetaMask session-only address attach or mocks."
        )
    return pid


def new_pairing_topic() -> str:
    """32-byte topic as hex (WC v2 pairing topic)."""
    return secrets.token_hex(32)


def new_sym_key() -> str:
    """32-byte symmetric key as hex (never persisted to disk by default)."""
    return secrets.token_hex(32)


def build_wc_uri(
    *,
    project_id: Optional[str] = None,
    topic: Optional[str] = None,
    sym_key: Optional[str] = None,
    relay_url: str = RELAY_URL,
) -> Tuple[str, str, str]:
    """Build a WalletConnect v2 pairing URI.

    Returns ``(uri, topic, sym_key)``. ``sym_key`` stays in process memory only.
    """
    pid = project_id if project_id is not None else get_project_id()
    if not pid:
        # Allow URI scaffold for UI/QR demos; relay auth will fail without project id.
        pid = "forexsmartbot-local-scaffold"
    topic = topic or new_pairing_topic()
    sym_key = sym_key or new_sym_key()
    # Methods / events kept minimal; wallets negotiate namespaces on approve.
    query = urllib.parse.urlencode(
        {
            "relay-protocol": "irn",
            "symKey": sym_key,
            "projectId": pid,
            "relay-url": relay_url,
        }
    )
    uri = f"wc:{topic}@2?{query}"
    return uri, topic, sym_key


def metamask_deeplink(wc_uri: str) -> str:
    """MetaMask mobile deep link that opens a WalletConnect URI."""
    return f"{METAMASK_WC_DEEPLINK_BASE}?uri={urllib.parse.quote(wc_uri, safe='')}"


def phishing_warning() -> str:
    return (
        "Only scan WalletConnect URIs generated inside ForexSmartBot. "
        "Verify the Reown/WalletConnect project id from official docs; "
        "fake wc: URIs are a common phishing vector."
    )

"""Bridge wallet sessions to OneInchDexBroker ``broadcast_fn``.

Default behaviour: **refuse** on-chain send. A connected session supplies the
public ``from`` address for quotes/swap builds; live broadcast still needs an
explicit injected signer (hardware / WC relay / test mock). Never reads
private keys from env or settings.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from ..venues.live_guard import dex_broadcast_enabled, live_trading_enabled
from . import session_store

logger = logging.getLogger(__name__)

BroadcastFn = Callable[[Dict[str, Any]], Optional[str]]


def wallet_address_for_dex() -> Optional[str]:
    """Public EVM address from the active session, if any."""
    session = session_store.get_session()
    if session is None:
        return None
    if session.family.value != "evm":
        return None
    return session.address


def make_broadcast_fn(
    *,
    signer_fn: Optional[BroadcastFn] = None,
) -> BroadcastFn:
    """Return a ``broadcast_fn`` aligned with DEX double opt-in.

    Without ``signer_fn``, always returns ``None`` and logs — dry-run safe.
    With ``signer_fn``, still requires ``FSB_LIVE_TRADING`` + ``FSB_DEX_BROADCAST``.
    """

    def _broadcast(tx: Dict[str, Any]) -> Optional[str]:
        if not (live_trading_enabled() and dex_broadcast_enabled()):
            logger.info(
                "DEX broadcast skipped (live/broadcast flags off); tx keys=%s",
                sorted(tx.keys()) if isinstance(tx, dict) else type(tx),
            )
            return None
        if signer_fn is None:
            logger.warning(
                "DEX broadcast armed but no signer_fn injected — refusing send "
                "(connect wallet for address only; signing stays external)"
            )
            return None
        session = session_store.get_session()
        if session is None:
            logger.warning("DEX broadcast refused: no wallet session")
            return None
        return signer_fn(tx)

    return _broadcast

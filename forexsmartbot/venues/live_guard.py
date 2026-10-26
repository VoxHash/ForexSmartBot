"""Opt-in guard for production (mainnet) venue trading.

Live trading is refused unless ``FSB_LIVE_TRADING`` is an explicit truthy
value (``1`` / ``true`` / ``yes`` / ``on``). Secrets stay in the environment;
this module never logs credential values.
"""

from __future__ import annotations

import os
from typing import Optional

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def live_trading_enabled(env: Optional[dict] = None) -> bool:
    """Return True only when the operator explicitly opted into mainnet live."""
    source = env if env is not None else os.environ
    raw = str(source.get("FSB_LIVE_TRADING", "")).strip().lower()
    return raw in _TRUTHY


def require_live_opt_in(*, context: str = "live trading") -> None:
    """Raise ``PermissionError`` unless ``FSB_LIVE_TRADING`` is explicitly set.

    Used by mainnet brokers so accidental Settings selection cannot place
    production orders without the env flag.
    """
    if not live_trading_enabled():
        raise PermissionError(
            f"{context} refused: set FSB_LIVE_TRADING=1 in the local environment "
            "(opt-in only; never enable in CI)."
        )


def kill_switch_forced(env: Optional[dict] = None) -> bool:
    """Return True when ``FSB_KILL_SWITCH`` forces an immediate trading halt."""
    source = env if env is not None else os.environ
    raw = str(source.get("FSB_KILL_SWITCH", "")).strip().lower()
    return raw in _TRUTHY


def dex_broadcast_enabled(env: Optional[dict] = None) -> bool:
    """Return True only when the operator opted into on-chain DEX broadcast.

    Requires an explicit ``FSB_DEX_BROADCAST`` truthy value. Pair with
    ``FSB_LIVE_TRADING`` — 1inch dry-run quotes/swaps work without this flag;
    broadcasting unsigned calldata does not.
    """
    source = env if env is not None else os.environ
    raw = str(source.get("FSB_DEX_BROADCAST", "")).strip().lower()
    return raw in _TRUTHY

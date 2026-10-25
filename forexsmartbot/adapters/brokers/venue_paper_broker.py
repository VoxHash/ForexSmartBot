"""Venue-backed paper broker: live public prices, local fills (no keys / no funds).

Orders fill immediately at the public venue mid/last price. Positions, balance,
and equity are tracked locally. ``reconnect()`` re-establishes the price feed.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Optional

from ...core.interfaces import IBroker, Position
from .binance_public_broker import BinancePublicBroker
from .kraken_public_broker import KrakenPublicBroker

logger = logging.getLogger(__name__)

_FEED_BINANCE = "binance"
_FEED_KRAKEN = "kraken"
_VALID_FEEDS = frozenset({_FEED_BINANCE, _FEED_KRAKEN})


class VenuePaperBroker(IBroker):
    """Paper ledger filled against a live CEX public price feed."""

    def __init__(
        self,
        initial_balance: float = 10_000.0,
        *,
        feed: Optional[str] = None,
        timeout: float = 20.0,
    ):
        env_feed = os.getenv("FSB_VENUE_PAPER_FEED", "").strip().lower()
        chosen = (feed or env_feed or _FEED_BINANCE).strip().lower()
        if chosen not in _VALID_FEEDS:
            raise ValueError(
                f"Unsupported venue paper feed: {chosen!r}; "
                f"expected one of {sorted(_VALID_FEEDS)}"
            )
        self._feed_name = chosen
        self._timeout = timeout
        self._balance = float(initial_balance)
        self._positions: Dict[str, Position] = {}
        self._order_counter = 0
        self._connected = False
        self._feed: IBroker = self._build_feed()

    def _build_feed(self) -> IBroker:
        if self._feed_name == _FEED_KRAKEN:
            return KrakenPublicBroker(timeout=self._timeout)
        return BinancePublicBroker(sandbox=True, timeout=self._timeout)

    @property
    def feed_name(self) -> str:
        return self._feed_name

    def connect(self) -> bool:
        ok = bool(self._feed.connect())
        self._connected = ok
        if not ok:
            logger.warning("VenuePaperBroker: %s price feed connect failed", self._feed_name)
        return ok

    def disconnect(self) -> None:
        self._connected = False
        try:
            self._feed.disconnect()
        except Exception as exc:
            logger.debug("VenuePaperBroker feed disconnect: %s", exc)

    def reconnect(self) -> bool:
        """Drop and re-open the public price feed (orders stay on local ledger)."""
        self.disconnect()
        self._feed = self._build_feed()
        return self.connect()

    def is_connected(self) -> bool:
        return self._connected and self._feed.is_connected()

    def get_price(self, symbol: str) -> Optional[float]:
        if not self.is_connected():
            return None
        return self._feed.get_price(symbol)

    def submit_order(
        self,
        symbol: str,
        side: int,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Optional[str]:
        if not self.is_connected():
            logger.warning("VenuePaperBroker: submit_order while disconnected")
            return None
        if quantity <= 0:
            return None
        if side not in (-1, 1):
            logger.warning("VenuePaperBroker: invalid side %s", side)
            return None

        price = self.get_price(symbol)
        if price is None or price <= 0:
            logger.warning("VenuePaperBroker: no live price for %s", symbol)
            return None

        # Flatten / reverse if an opposite position already exists.
        existing = self._positions.get(symbol)
        if existing is not None and existing.side != side:
            closed = self.close_all(symbol)
            if not closed:
                return None
            # After flatten, continue to open the new side at current price.
            price = self.get_price(symbol) or price

        notional = abs(quantity) * price
        # Soft paper risk: reject opens that exceed remaining cash budget.
        if symbol not in self._positions and notional > self._balance:
            logger.warning(
                "VenuePaperBroker: insufficient paper balance (need %.4f have %.4f)",
                notional,
                self._balance,
            )
            return None

        order_id = f"VPAPER_{self._feed_name}_{self._order_counter}"
        self._order_counter += 1

        if symbol in self._positions and self._positions[symbol].side == side:
            pos = self._positions[symbol]
            new_qty = pos.quantity + quantity
            pos.entry_price = (
                (pos.entry_price * pos.quantity) + (price * quantity)
            ) / new_qty
            pos.quantity = new_qty
            pos.current_price = price
            pos.unrealized_pnl = pos.side * pos.quantity * (price - pos.entry_price)
        else:
            self._positions[symbol] = Position(
                symbol=symbol,
                side=side,
                quantity=float(quantity),
                entry_price=float(price),
                current_price=float(price),
                unrealized_pnl=0.0,
            )

        _ = stop_loss, take_profit  # strategies own SL/TP; paper fill is market
        logger.info(
            "VenuePaperBroker filled %s side=%s qty=%s @ %s id=%s",
            symbol,
            side,
            quantity,
            price,
            order_id,
        )
        return order_id

    def close_all(self, symbol: str) -> bool:
        if symbol not in self._positions:
            return False
        pos = self._positions.pop(symbol)
        exit_price = self.get_price(symbol) or pos.current_price
        realized = pos.side * pos.quantity * (exit_price - pos.entry_price)
        self._balance += realized
        logger.info(
            "VenuePaperBroker closed %s pnl=%.6f balance=%.4f",
            symbol,
            realized,
            self._balance,
        )
        return True

    def get_positions(self) -> Dict[str, Position]:
        # Refresh mark prices when connected.
        if self.is_connected():
            for symbol, pos in list(self._positions.items()):
                px = self.get_price(symbol)
                if px is not None:
                    pos.current_price = px
                    pos.unrealized_pnl = pos.side * pos.quantity * (
                        pos.current_price - pos.entry_price
                    )
        return {k: v for k, v in self._positions.items()}

    def get_balance(self) -> float:
        return float(self._balance)

    def get_equity(self) -> float:
        positions = self.get_positions()
        unrealized = sum(p.unrealized_pnl for p in positions.values())
        return float(self._balance + unrealized)

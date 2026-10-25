"""Binance Spot public / testnet (read-only) broker adapter.

Defaults to the Spot Test Network base URL. No API keys for market data.
Order methods refuse until an authenticated sandbox adapter is added.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Optional

import requests

from ...core.interfaces import IBroker, Position
from ...venues.registry import get_venue

logger = logging.getLogger(__name__)


class BinancePublicBroker(IBroker):
    """Thin IBroker over Binance Spot public ticker endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        sandbox: bool = True,
        timeout: float = 20.0,
    ):
        venue = get_venue("binance_spot")
        if base_url:
            self._base_url = base_url.rstrip("/")
        elif sandbox and venue.endpoints.rest_sandbox:
            self._base_url = venue.endpoints.rest_sandbox.rstrip("/")
        else:
            self._base_url = venue.endpoints.rest_public.rstrip("/")
        env_url = os.getenv("BINANCE_REST_URL", "").strip()
        if env_url and not base_url:
            self._base_url = env_url.rstrip("/")
        self._timeout = timeout
        self._connected = False
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "ForexSmartBot/3.4.2",
                "Accept": "application/json",
            }
        )

    def reconnect(self) -> bool:
        """Re-open the public testnet session."""
        self.disconnect()
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "ForexSmartBot/3.4.2",
                "Accept": "application/json",
            }
        )
        return self.connect()

    def connect(self) -> bool:
        try:
            response = self._session.get(
                f"{self._base_url}/v3/ping", timeout=self._timeout
            )
            response.raise_for_status()
            self._connected = True
            return True
        except Exception as exc:
            logger.warning("Binance public connect failed: %s", exc)
            self._connected = False
            return False

    def disconnect(self) -> None:
        self._connected = False
        self._session.close()

    def is_connected(self) -> bool:
        return self._connected

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return symbol.replace("/", "").replace("-", "").upper()

    def get_price(self, symbol: str) -> Optional[float]:
        try:
            sym = self._normalize_symbol(symbol)
            response = self._session.get(
                f"{self._base_url}/v3/ticker/price",
                params={"symbol": sym},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            price = payload.get("price")
            if price is not None:
                return float(price)
        except Exception as exc:
            logger.info("Binance get_price failed for %s: %s", symbol, exc)
        return None

    def submit_order(
        self,
        symbol: str,
        side: int,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Optional[str]:
        logger.warning(
            "BinancePublicBroker is read-only; use testnet API keys in a future "
            "authenticated adapter before any orders (never commit secrets)."
        )
        return None

    def close_all(self, symbol: str) -> bool:
        return False

    def get_positions(self) -> Dict[str, Position]:
        return {}

    def get_balance(self) -> float:
        return 0.0

    def get_equity(self) -> float:
        return 0.0

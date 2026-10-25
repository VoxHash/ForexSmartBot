"""Kraken Spot public (read-only) broker adapter.

Uses documented public REST endpoints only — no API keys. Suitable for
research, connection tests, and price feeds. Order methods refuse until a
future private adapter is wired with local secrets.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

import requests

from ...core.interfaces import IBroker, Position
from ...venues.registry import get_venue

logger = logging.getLogger(__name__)


class KrakenPublicBroker(IBroker):
    """Thin IBroker over Kraken Spot public market data."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 20.0):
        venue = get_venue("kraken_spot")
        self._base_url = (base_url or venue.endpoints.rest_public).rstrip("/")
        self._timeout = timeout
        self._connected = False
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "ForexSmartBot/3.4.2",
                "Accept": "application/json",
            }
        )
        # Map common FX / crypto aliases → Kraken pair ids seen in AssetPairs.
        self._pair_aliases = {
            "EURUSD": "ZEURZUSD",
            "EUR/USD": "ZEURZUSD",
            "GBPUSD": "ZGBPZUSD",
            "GBP/USD": "ZGBPZUSD",
            "USDJPY": "ZUSDZJPY",
            "USD/JPY": "ZUSDZJPY",
            "AUDUSD": "ZAUDZUSD",
            "AUD/USD": "ZAUDZUSD",
            "XBTUSD": "XXBTZUSD",
            "BTCUSD": "XXBTZUSD",
            "BTC/USD": "XXBTZUSD",
            "ETHUSD": "XETHZUSD",
            "ETH/USD": "XETHZUSD",
        }

    def reconnect(self) -> bool:
        """Re-open the public REST session."""
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
                f"{self._base_url}/Time", timeout=self._timeout
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("error"):
                logger.warning("Kraken public Time error: %s", payload["error"])
                return False
            self._connected = True
            return True
        except Exception as exc:
            logger.warning("Kraken public connect failed: %s", exc)
            self._connected = False
            return False

    def disconnect(self) -> None:
        self._connected = False
        self._session.close()

    def is_connected(self) -> bool:
        return self._connected

    def _resolve_pair(self, symbol: str) -> str:
        key = symbol.strip()
        return self._pair_aliases.get(key) or self._pair_aliases.get(key.upper()) or key

    def get_price(self, symbol: str) -> Optional[float]:
        try:
            pair = self._resolve_pair(symbol)
            response = self._session.get(
                f"{self._base_url}/Ticker",
                params={"pair": pair},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("error"):
                logger.info("Kraken ticker error for %s: %s", symbol, payload["error"])
                return None
            result = payload.get("result") or {}
            if not result:
                return None
            # Response key may differ from request pair id.
            book = next(iter(result.values()))
            last = book.get("c") or book.get("a")
            if isinstance(last, list) and last:
                return float(last[0])
            if last is not None:
                return float(last)
        except Exception as exc:
            logger.info("Kraken get_price failed for %s: %s", symbol, exc)
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
            "KrakenPublicBroker is read-only; trading requires private API keys "
            "via a future authenticated adapter (local .env / UI secrets only)."
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

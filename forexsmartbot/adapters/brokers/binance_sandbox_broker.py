"""Binance Spot Test Network authenticated broker (sandbox only).

Uses HMAC-SHA256 signed REST against ``testnet.binance.vision``. Production
``api.binance.com`` is refused — live mainnet is a later opt-in milestone.

Credentials: ``BINANCE_API_KEY`` / ``BINANCE_API_SECRET`` from the environment
(or constructor). Never log raw secrets.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from typing import Dict, List, Optional
from urllib.parse import urlencode

import requests

from ...core.interfaces import IBroker, Position
from ...venues.registry import get_venue
from ...venues.secrets import mask_secret, redact_mapping

logger = logging.getLogger(__name__)

_TESTNET_HOST_MARKERS = ("testnet.binance.vision",)
_FORBIDDEN_MAINNET_MARKERS = ("api.binance.com", "api.binance.us")


def _hmac_sha256(secret: str, payload: str) -> str:
    return hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()


class BinanceSandboxBroker(IBroker):
    """Authenticated IBroker for Binance Spot Test Network only."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = 20.0,
        recv_window: int = 5000,
    ):
        venue = get_venue("binance_spot")
        sandbox = (venue.endpoints.rest_sandbox or "").rstrip("/")
        env_url = os.getenv("BINANCE_REST_URL", "").strip().rstrip("/")
        chosen = (base_url or env_url or sandbox).rstrip("/")
        self._assert_sandbox_url(chosen)
        self._base_url = chosen

        self._api_key = (api_key if api_key is not None else os.getenv("BINANCE_API_KEY", "")).strip()
        self._api_secret = (
            api_secret if api_secret is not None else os.getenv("BINANCE_API_SECRET", "")
        ).strip()
        self._timeout = timeout
        self._recv_window = recv_window
        self._connected = False
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "ForexSmartBot/3.4.2",
                "Accept": "application/json",
            }
        )
        if self._api_key:
            self._session.headers["X-MBX-APIKEY"] = self._api_key

        # Local spot "position" ledger keyed by symbol (base exposure from fills).
        self._positions: Dict[str, Position] = {}
        self._quote_balance = 0.0

    @staticmethod
    def _assert_sandbox_url(url: str) -> None:
        lower = url.lower()
        if any(m in lower for m in _FORBIDDEN_MAINNET_MARKERS):
            raise ValueError(
                "BinanceSandboxBroker refuses mainnet URLs; use "
                "https://testnet.binance.vision/api (live trading is a later milestone)."
            )
        if not any(m in lower for m in _TESTNET_HOST_MARKERS):
            raise ValueError(
                f"BinanceSandboxBroker only allows Spot Test Network hosts; got {url!r}"
            )

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return symbol.replace("/", "").replace("-", "").upper()

    def _signed_params(self, params: Optional[dict] = None) -> dict:
        payload = dict(params or {})
        payload["timestamp"] = int(time.time() * 1000)
        payload["recvWindow"] = self._recv_window
        query = urlencode(payload, True)
        payload["signature"] = _hmac_sha256(self._api_secret, query)
        return payload

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        signed: bool = False,
    ) -> Optional[dict]:
        url = f"{self._base_url}{path}"
        try:
            if signed:
                if not self._api_key or not self._api_secret:
                    logger.warning(
                        "BinanceSandboxBroker: missing BINANCE_API_KEY / BINANCE_API_SECRET"
                    )
                    return None
                params = self._signed_params(params)
            response = self._session.request(
                method, url, params=params, timeout=self._timeout
            )
            if response.status_code >= 400:
                # Never echo secrets; Binance error bodies are safe but redact anyway.
                body = redact_mapping(
                    response.json()
                    if response.headers.get("content-type", "").startswith("application/json")
                    else {"text": response.text[:200]}
                )
                logger.warning(
                    "Binance sandbox %s %s -> %s %s",
                    method,
                    path,
                    response.status_code,
                    body,
                )
                return None
            if not response.content:
                return {}
            return response.json()
        except Exception as exc:
            logger.warning("Binance sandbox request failed: %s", exc)
            return None

    def connect(self) -> bool:
        if not self._api_key or not self._api_secret:
            logger.warning(
                "BinanceSandboxBroker: set BINANCE_API_KEY and BINANCE_API_SECRET "
                "(testnet keys from https://testnet.binance.vision/ — never commit)."
            )
            self._connected = False
            return False
        # Public ping first (no keys).
        ping = self._request("GET", "/v3/ping", signed=False)
        if ping is None:
            self._connected = False
            return False
        account = self._request("GET", "/v3/account", signed=True)
        if account is None:
            self._connected = False
            return False
        self._refresh_balances(account)
        self._connected = True
        logger.info(
            "BinanceSandboxBroker connected (key=%s url=%s)",
            mask_secret(self._api_key),
            self._base_url,
        )
        return True

    def disconnect(self) -> None:
        self._connected = False
        try:
            self._session.close()
        except Exception:
            pass
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "ForexSmartBot/3.4.2",
                "Accept": "application/json",
            }
        )
        if self._api_key:
            self._session.headers["X-MBX-APIKEY"] = self._api_key

    def reconnect(self) -> bool:
        """Re-open session and re-auth account on the Spot Test Network."""
        self.disconnect()
        return self.connect()

    def is_connected(self) -> bool:
        return self._connected

    def _refresh_balances(self, account: Optional[dict] = None) -> None:
        if account is None:
            account = self._request("GET", "/v3/account", signed=True)
        if not account:
            return
        balances: List[dict] = account.get("balances") or []
        usdt = 0.0
        for row in balances:
            asset = str(row.get("asset", "")).upper()
            free = float(row.get("free") or 0.0)
            locked = float(row.get("locked") or 0.0)
            total = free + locked
            if asset in ("USDT", "BUSD", "USD"):
                usdt += total
        self._quote_balance = usdt

    def get_price(self, symbol: str) -> Optional[float]:
        sym = self._normalize_symbol(symbol)
        payload = self._request(
            "GET", "/v3/ticker/price", params={"symbol": sym}, signed=False
        )
        if not payload:
            return None
        try:
            return float(payload.get("price"))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _fmt_qty(quantity: float) -> str:
        text = f"{quantity:.8f}".rstrip("0").rstrip(".")
        return text or "0"

    def _place_market_order(
        self, symbol: str, side: int, quantity: float
    ) -> Optional[dict]:
        sym = self._normalize_symbol(symbol)
        params = {
            "symbol": sym,
            "side": "BUY" if side > 0 else "SELL",
            "type": "MARKET",
            "quantity": self._fmt_qty(quantity),
        }
        return self._request("POST", "/v3/order", params=params, signed=True)

    @staticmethod
    def _fill_from_result(result: dict, fallback_price: float, quantity: float):
        fill_price = fallback_price
        fill_qty = quantity
        fills = result.get("fills") or []
        if fills:
            try:
                notional = sum(float(f["price"]) * float(f["qty"]) for f in fills)
                qty_sum = sum(float(f["qty"]) for f in fills)
                if qty_sum > 0:
                    fill_price = notional / qty_sum
                    fill_qty = qty_sum
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                pass
        return fill_price, fill_qty

    def submit_order(
        self,
        symbol: str,
        side: int,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Optional[str]:
        _ = stop_loss, take_profit
        if not self._connected:
            return None
        if quantity <= 0 or side not in (-1, 1):
            return None

        existing = self._positions.get(symbol)
        if existing is not None and existing.side != side:
            if not self.close_all(symbol):
                return None

        result = self._place_market_order(symbol, side, quantity)
        if not result:
            return None
        order_id = str(result.get("orderId") or result.get("clientOrderId") or "")
        if not order_id:
            return None

        fill_price, fill_qty = self._fill_from_result(
            result, self.get_price(symbol) or 0.0, quantity
        )
        existing = self._positions.get(symbol)
        if existing and existing.side == side:
            new_qty = existing.quantity + fill_qty
            existing.entry_price = (
                (existing.entry_price * existing.quantity) + (fill_price * fill_qty)
            ) / new_qty
            existing.quantity = new_qty
            existing.current_price = fill_price
            existing.unrealized_pnl = 0.0
        else:
            self._positions[symbol] = Position(
                symbol=symbol,
                side=side,
                quantity=float(fill_qty),
                entry_price=float(fill_price),
                current_price=float(fill_price),
                unrealized_pnl=0.0,
            )
        self._refresh_balances()
        logger.info(
            "BinanceSandboxBroker order side=%s %s qty=%s id=%s",
            side,
            self._normalize_symbol(symbol),
            fill_qty,
            order_id,
        )
        return order_id

    def close_all(self, symbol: str) -> bool:
        if not self._connected:
            return False
        pos = self._positions.get(symbol)
        if pos is None:
            return False
        opposite = -pos.side
        result = self._place_market_order(symbol, opposite, pos.quantity)
        if not result:
            return False
        self._positions.pop(symbol, None)
        self._refresh_balances()
        return True

    def get_positions(self) -> Dict[str, Position]:
        if self._connected:
            for symbol, pos in list(self._positions.items()):
                px = self.get_price(symbol)
                if px is not None:
                    pos.current_price = px
                    pos.unrealized_pnl = pos.side * pos.quantity * (
                        pos.current_price - pos.entry_price
                    )
        return dict(self._positions)

    def get_balance(self) -> float:
        if self._connected:
            self._refresh_balances()
        return float(self._quote_balance)

    def get_equity(self) -> float:
        positions = self.get_positions()
        unrealized = sum(p.unrealized_pnl for p in positions.values())
        return float(self.get_balance() + unrealized)

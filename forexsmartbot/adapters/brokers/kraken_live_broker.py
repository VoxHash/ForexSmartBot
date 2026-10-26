"""Kraken Spot **mainnet** authenticated broker (opt-in only).

Requires all of:
- ``FSB_LIVE_TRADING=1`` (explicit operator opt-in; refused otherwise)
- ``KRAKEN_LIVE_API_KEY`` / ``KRAKEN_LIVE_API_SECRET`` (dedicated live keys;
  generic ``KRAKEN_API_*`` are never used here)
- Mainnet host ``api.kraken.com`` (demo / futures hosts refused)

Kill-switch: ``FSB_KILL_SWITCH=1`` or an attached ``RiskEngine`` trip blocks
new orders. Prefer trade-only API keys with withdraw disabled + IP allowlist.
Never log raw secrets. CI must not set ``FSB_LIVE_TRADING``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import time
import urllib.parse
from typing import Dict, Optional, TYPE_CHECKING

import requests

from ...core.interfaces import IBroker, Position
from ...venues.live_guard import kill_switch_forced, require_live_opt_in
from ...venues.registry import get_venue
from ...venues.secrets import mask_secret, redact_mapping

if TYPE_CHECKING:
    from ...core.risk_engine import RiskEngine

logger = logging.getLogger(__name__)

_MAINNET_HOST_MARKERS = ("api.kraken.com",)
_FORBIDDEN_HOST_MARKERS = (
    "demo-futures.kraken.com",
    "futures.kraken.com",
    "beta-api.kraken.com",
)

# Documented Kraken signature vector (docs.kraken.com authentication guide).
_KRAKEN_SIG_VECTOR_SECRET = (
    "kQH5HW/8p1uGOVjbgWA7FunAmGO8lsSUXNsu3eow76sz84Q18fWxnyRzBHCd3pd5nE9qa99HAZtuZuj6F1huXg=="
)
_KRAKEN_SIG_VECTOR_EXPECTED = (
    "4/dpxb3iT4tp/ZCVEwSnEsLxx0bqyhLpdfOpc6fn7OR8+UClSV5n9E6aSS8MPtnRfp32bAb0nmbRn6H8ndwLUQ=="
)


def kraken_api_sign(urlpath: str, data: dict, secret: str) -> str:
    """HMAC-SHA512 API-Sign for Kraken Spot private REST (form-encoded POST)."""
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data["nonce"]) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


def verify_kraken_signature_vector() -> bool:
    """Return True when the published Kraken AddOrder signature vector matches."""
    payload = {
        "nonce": "1616492376594",
        "ordertype": "limit",
        "pair": "XBTUSD",
        "price": 37500,
        "type": "buy",
        "volume": 1.25,
    }
    got = kraken_api_sign("/0/private/AddOrder", payload, _KRAKEN_SIG_VECTOR_SECRET)
    return got == _KRAKEN_SIG_VECTOR_EXPECTED


class KrakenLiveBroker(IBroker):
    """Authenticated IBroker for Kraken Spot production (opt-in mainnet)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        *,
        private_base_url: Optional[str] = None,
        public_base_url: Optional[str] = None,
        timeout: float = 20.0,
        risk_engine: Optional["RiskEngine"] = None,
    ):
        require_live_opt_in(context="KrakenLiveBroker")

        venue = get_venue("kraken_spot")
        mainnet_private = (venue.endpoints.rest_private or "").rstrip("/")
        mainnet_public = (venue.endpoints.rest_public or "").rstrip("/")
        env_url = os.getenv("KRAKEN_LIVE_REST_URL", "").strip().rstrip("/")
        chosen_private = (private_base_url or env_url or mainnet_private).rstrip("/")
        self._assert_mainnet_url(chosen_private)
        self._private_base = chosen_private
        # Signing path must start at /0/private/...
        self._private_path_prefix = self._uri_path_prefix(chosen_private)

        self._public_base = (public_base_url or mainnet_public).rstrip("/")
        self._assert_mainnet_url(self._public_base)

        self._api_key = (
            api_key
            if api_key is not None
            else os.getenv("KRAKEN_LIVE_API_KEY", "")
        ).strip()
        self._api_secret = (
            api_secret
            if api_secret is not None
            else os.getenv("KRAKEN_LIVE_API_SECRET", "")
        ).strip()
        self._timeout = timeout
        self._risk_engine = risk_engine
        self._connected = False
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "ForexSmartBot/3.4.4",
                "Accept": "application/json",
            }
        )

        self._positions: Dict[str, Position] = {}
        self._quote_balance = 0.0
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
            "BTCUSDT": "XXBTZUSD",
            "ETHUSD": "XETHZUSD",
            "ETH/USD": "XETHZUSD",
            "ETHUSDT": "XETHZUSD",
        }

    @staticmethod
    def _uri_path_prefix(private_base: str) -> str:
        """Extract ``/0/private`` path prefix used in API-Sign."""
        marker = "/0/private"
        lower = private_base.lower()
        idx = lower.find(marker)
        if idx < 0:
            raise ValueError(
                f"KrakenLiveBroker private URL must include /0/private; got {private_base!r}"
            )
        return private_base[idx:].rstrip("/") or marker

    @staticmethod
    def _assert_mainnet_url(url: str) -> None:
        lower = url.lower()
        if any(m in lower for m in _FORBIDDEN_HOST_MARKERS):
            raise ValueError(
                "KrakenLiveBroker refuses demo/futures hosts; use api.kraken.com "
                "Spot private REST for live, or KrakenPublicBroker for MD only."
            )
        if not any(m in lower for m in _MAINNET_HOST_MARKERS):
            raise ValueError(
                f"KrakenLiveBroker only allows api.kraken.com hosts; got {url!r}"
            )

    def _resolve_pair(self, symbol: str) -> str:
        key = symbol.strip()
        return self._pair_aliases.get(key) or self._pair_aliases.get(key.upper()) or key

    def attach_risk_engine(self, risk_engine: "RiskEngine") -> None:
        """Attach risk engine so order path honors kill-switch / limits."""
        self._risk_engine = risk_engine

    def _orders_blocked(self) -> bool:
        if kill_switch_forced():
            return True
        if self._risk_engine is not None and self._risk_engine.is_kill_switch_active():
            return True
        return False

    def _nonce(self) -> str:
        return str(int(time.time() * 1000))

    def _private_request(self, method: str, data: Optional[dict] = None) -> Optional[dict]:
        if not self._api_key or not self._api_secret:
            logger.warning(
                "KrakenLiveBroker: missing KRAKEN_LIVE_API_KEY / KRAKEN_LIVE_API_SECRET"
            )
            return None
        payload = dict(data or {})
        payload["nonce"] = self._nonce()
        urlpath = f"{self._private_path_prefix}/{method}"
        url = f"{self._private_base}/{method}"
        try:
            signature = kraken_api_sign(urlpath, payload, self._api_secret)
            headers = {
                "API-Key": self._api_key,
                "API-Sign": signature,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            response = self._session.post(
                url,
                data=urllib.parse.urlencode(payload),
                headers=headers,
                timeout=self._timeout,
            )
            if response.status_code >= 400:
                body = redact_mapping(
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else {"text": response.text[:200]}
                )
                logger.warning(
                    "Kraken live private %s -> %s %s",
                    method,
                    response.status_code,
                    body,
                )
                return None
            payload_json = response.json() if response.content else {}
            errors = payload_json.get("error") or []
            if errors:
                logger.warning(
                    "Kraken live private %s error: %s",
                    method,
                    redact_mapping({"error": errors}),
                )
                return None
            return payload_json.get("result")
        except Exception as exc:
            logger.warning("Kraken live private request failed: %s", exc)
            return None

    def _public_get(self, path: str, params: Optional[dict] = None) -> Optional[dict]:
        url = f"{self._public_base}/{path.lstrip('/')}"
        try:
            response = self._session.get(url, params=params, timeout=self._timeout)
            if response.status_code >= 400:
                return None
            payload = response.json() if response.content else {}
            if payload.get("error"):
                return None
            return payload.get("result")
        except Exception as exc:
            logger.warning("Kraken live public request failed: %s", exc)
            return None

    def connect(self) -> bool:
        require_live_opt_in(context="KrakenLiveBroker.connect")
        if not self._api_key or not self._api_secret:
            logger.warning(
                "KrakenLiveBroker: set KRAKEN_LIVE_API_KEY and "
                "KRAKEN_LIVE_API_SECRET (trade-only, no withdraw; never commit)."
            )
            self._connected = False
            return False
        if self._orders_blocked():
            reason = (
                self._risk_engine.get_kill_reason()
                if self._risk_engine is not None
                else "FSB_KILL_SWITCH"
            )
            logger.warning(
                "KrakenLiveBroker: kill-switch active (%s); connect refused",
                reason or "unknown",
            )
            self._connected = False
            return False

        # Public health + private Balance auth check.
        if self._public_get("Time") is None:
            self._connected = False
            return False
        balances = self._private_request("Balance")
        if balances is None:
            self._connected = False
            return False
        self._refresh_balances(balances)
        self._connected = True
        logger.info(
            "KrakenLiveBroker connected (LIVE mainnet key=%s url=%s)",
            mask_secret(self._api_key),
            self._private_base,
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
                "User-Agent": "ForexSmartBot/3.4.4",
                "Accept": "application/json",
            }
        )

    def reconnect(self) -> bool:
        """Re-open session and re-auth Balance on mainnet (still requires opt-in)."""
        self.disconnect()
        return self.connect()

    def is_connected(self) -> bool:
        return self._connected

    def _refresh_balances(self, balances: Optional[dict] = None) -> None:
        if balances is None:
            balances = self._private_request("Balance")
        if not balances:
            return
        usd = 0.0
        for asset, amount in balances.items():
            name = str(asset).upper()
            try:
                total = float(amount)
            except (TypeError, ValueError):
                continue
            if name in ("ZUSD", "USD", "USDT", "USDC", "ZUSDT"):
                usd += total
        self._quote_balance = usd

    def get_price(self, symbol: str) -> Optional[float]:
        pair = self._resolve_pair(symbol)
        result = self._public_get("Ticker", params={"pair": pair})
        if not result:
            return None
        try:
            book = next(iter(result.values()))
            last = book.get("c") or book.get("a")
            if isinstance(last, list) and last:
                return float(last[0])
            if last is not None:
                return float(last)
        except (StopIteration, TypeError, ValueError):
            return None
        return None

    @staticmethod
    def _fmt_qty(quantity: float) -> str:
        text = f"{quantity:.8f}".rstrip("0").rstrip(".")
        return text or "0"

    def _place_market_order(
        self, symbol: str, side: int, quantity: float
    ) -> Optional[dict]:
        pair = self._resolve_pair(symbol)
        data = {
            "pair": pair,
            "type": "buy" if side > 0 else "sell",
            "ordertype": "market",
            "volume": self._fmt_qty(quantity),
        }
        return self._private_request("AddOrder", data)

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
        if self._orders_blocked():
            reason = (
                self._risk_engine.get_kill_reason()
                if self._risk_engine is not None
                else "FSB_KILL_SWITCH"
            )
            logger.warning(
                "KrakenLiveBroker: order blocked by kill-switch (%s)",
                reason or "unknown",
            )
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
        txids = result.get("txid") or []
        order_id = str(txids[0]) if txids else str(result.get("txid") or "")
        if not order_id:
            return None

        fill_price = self.get_price(symbol) or 0.0
        fill_qty = float(quantity)
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
            "KrakenLiveBroker LIVE order side=%s %s qty=%s id=%s",
            side,
            self._resolve_pair(symbol),
            fill_qty,
            order_id,
        )
        return order_id

    def close_all(self, symbol: str) -> bool:
        """Flatten local ledger position (allowed even under kill-switch)."""
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

    def flatten_all(self) -> int:
        """Close every tracked position; returns number closed."""
        closed = 0
        for symbol in list(self._positions.keys()):
            if self.close_all(symbol):
                closed += 1
        return closed

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

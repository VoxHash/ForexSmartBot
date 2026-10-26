"""1inch DEX aggregator broker (quote + swap path; dry-run by default).

Execution model
---------------
- **Dry-run (default)**: call 1inch Classic Swap ``/quote`` + ``/swap`` to
  obtain pricing and unsigned calldata, then record a **local simulated fill**.
  No RPC broadcast — safe for CI and Settings smoke tests.
- **Broadcast (opt-in)**: requires ``FSB_LIVE_TRADING=1`` **and**
  ``FSB_DEX_BROADCAST=1``. On-chain send only via an injected
  ``broadcast_fn(tx)`` (tests / operator hook). This package never holds or
  invents a wallet private key for CI.

Auth: ``ONEINCH_API_KEY`` Bearer (Business portal). Wallet address for
``/swap`` ``from`` param: ``ONEINCH_WALLET_ADDRESS`` (public address only).

Kill-switch: ``FSB_KILL_SWITCH`` / attached ``RiskEngine`` blocks new orders.
Never log raw API keys. Never enable live/broadcast flags in CI.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Callable, Dict, Optional, Tuple, TYPE_CHECKING

import requests

from ...core.interfaces import IBroker, Position
from ...venues.live_guard import dex_broadcast_enabled, kill_switch_forced, live_trading_enabled
from ...venues.registry import get_venue
from ...venues.secrets import mask_secret, redact_mapping

if TYPE_CHECKING:
    from ...core.risk_engine import RiskEngine

logger = logging.getLogger(__name__)

# Native ETH sentinel used by 1inch Classic Swap.
NATIVE_ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

# Well-known Ethereum mainnet (chainId=1) token addresses + decimals.
_ETH_MAINNET_TOKENS: Dict[str, Tuple[str, int]] = {
    "ETH": (NATIVE_ETH, 18),
    "WETH": ("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", 18),
    "USDC": ("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6),
    "USDT": ("0xdAC17F958D2ee523a2206206994597C13D831ec7", 6),
    "DAI": ("0x6B175474E89094C44Da98b954EedeAC495271d0F", 18),
    "WBTC": ("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", 8),
    "BTC": ("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", 8),
    "1INCH": ("0x111111111117dC0aa78b770fA6A738034120C302", 18),
}

_ALLOWED_API_HOSTS = ("api.1inch.com", "api.1inch.dev")
_SWAP_API_VERSION = "v6.1"


def parse_pair_symbol(symbol: str) -> Tuple[str, str]:
    """Split ``ETHUSDC`` / ``ETH/USDC`` / ``WETH-USDC`` into (base, quote)."""
    raw = symbol.strip().upper().replace(" ", "")
    for sep in ("/", "-", "_"):
        if sep in raw:
            left, right = raw.split(sep, 1)
            if left and right:
                return left, right
    # Longest-prefix match against known tickers.
    known = sorted(_ETH_MAINNET_TOKENS.keys(), key=len, reverse=True)
    for base in known:
        if raw.startswith(base) and raw[len(base) :] in _ETH_MAINNET_TOKENS:
            return base, raw[len(base) :]
    if len(raw) >= 6:
        # Fallback: split mid (e.g. ETHUSD → ETH / USD — USD may fail resolve).
        mid = len(raw) // 2
        return raw[:mid], raw[mid:]
    raise ValueError(f"Cannot parse DEX pair symbol: {symbol!r}")


def resolve_token(ticker: str) -> Tuple[str, int]:
    """Return (checksum/lower address, decimals) for a known ticker."""
    key = ticker.strip().upper()
    if key == "USD":
        key = "USDC"
    if key not in _ETH_MAINNET_TOKENS:
        raise ValueError(
            f"Unknown token ticker {ticker!r}; known: {sorted(_ETH_MAINNET_TOKENS)}"
        )
    return _ETH_MAINNET_TOKENS[key]


def to_minor_units(amount: float, decimals: int) -> str:
    """Convert a human amount to an integer string in token minor units."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    scaled = int(round(amount * (10**decimals)))
    if scaled <= 0:
        raise ValueError("amount too small for token decimals")
    return str(scaled)


def from_minor_units(amount_str: str, decimals: int) -> float:
    """Convert minor-unit integer string to float human amount."""
    return int(amount_str) / float(10**decimals)


class OneInchDexBroker(IBroker):
    """IBroker over 1inch Classic Swap (dry-run fills; optional broadcast hook)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        chain_id: Optional[int] = None,
        base_url: Optional[str] = None,
        wallet_address: Optional[str] = None,
        slippage_pct: float = 1.0,
        timeout: float = 20.0,
        paper_balance: float = 10_000.0,
        risk_engine: Optional["RiskEngine"] = None,
        broadcast_fn: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
        force_dry_run: Optional[bool] = None,
    ):
        venue = get_venue("oneinch")
        env_url = os.getenv("ONEINCH_REST_URL", "").strip().rstrip("/")
        chosen = (base_url or env_url or venue.endpoints.rest_public or "").rstrip("/")
        self._assert_api_host(chosen)
        self._base_url = chosen

        self._api_key = (
            api_key if api_key is not None else os.getenv("ONEINCH_API_KEY", "")
        ).strip()
        self._chain_id = int(
            chain_id
            if chain_id is not None
            else os.getenv("ONEINCH_CHAIN_ID", "1")
        )
        self._wallet = (
            wallet_address
            if wallet_address is not None
            else os.getenv("ONEINCH_WALLET_ADDRESS", "")
        ).strip()
        # Placeholder public address for dry-run /swap builds when unset.
        if not self._wallet:
            self._wallet = "0x0000000000000000000000000000000000000001"

        self._slippage = float(slippage_pct)
        self._timeout = timeout
        self._risk_engine = risk_engine
        self._broadcast_fn = broadcast_fn
        self._connected = False
        self._quote_balance = float(paper_balance)
        self._positions: Dict[str, Position] = {}
        self._last_quote: Optional[dict] = None
        self._last_swap_tx: Optional[dict] = None
        self._order_seq = 0

        if force_dry_run is not None:
            self._dry_run = bool(force_dry_run)
        else:
            # Broadcast only when both live + dex-broadcast flags are set.
            self._dry_run = not (
                live_trading_enabled() and dex_broadcast_enabled()
            )

        self._session = requests.Session()
        headers = {
            "User-Agent": "ForexSmartBot/3.4.5",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        self._session.headers.update(headers)

    @staticmethod
    def _assert_api_host(url: str) -> None:
        lower = url.lower()
        if not any(h in lower for h in _ALLOWED_API_HOSTS):
            raise ValueError(
                f"OneInchDexBroker only allows api.1inch.com / api.1inch.dev; got {url!r}"
            )

    @property
    def dry_run(self) -> bool:
        return self._dry_run

    @property
    def last_swap_tx(self) -> Optional[dict]:
        """Last unsigned swap transaction payload from ``/swap`` (redact before log)."""
        return self._last_swap_tx

    def attach_risk_engine(self, risk_engine: "RiskEngine") -> None:
        self._risk_engine = risk_engine

    def _orders_blocked(self) -> bool:
        if kill_switch_forced():
            return True
        if self._risk_engine is not None and self._risk_engine.is_kill_switch_active():
            return True
        return False

    def _api_get(self, path: str, params: Optional[dict] = None) -> Optional[dict]:
        url = f"{self._base_url}/{path.lstrip('/')}"
        try:
            response = self._session.get(url, params=params, timeout=self._timeout)
            if response.status_code >= 400:
                body: Any
                try:
                    body = response.json()
                except Exception:
                    body = {"text": response.text[:200]}
                logger.warning(
                    "1inch GET %s -> %s %s",
                    path,
                    response.status_code,
                    redact_mapping(body) if isinstance(body, dict) else body,
                )
                return None
            return response.json() if response.content else {}
        except Exception as exc:
            logger.warning("1inch request failed: %s", exc)
            return None

    def _swap_path(self, suffix: str) -> str:
        return f"swap/{_SWAP_API_VERSION}/{self._chain_id}/{suffix.lstrip('/')}"

    def quote_swap(
        self, src: str, dst: str, amount_minor: str
    ) -> Optional[dict]:
        """Call Classic Swap ``/quote`` (amount in src token minor units)."""
        payload = self._api_get(
            self._swap_path("quote"),
            params={
                "src": src,
                "dst": dst,
                "amount": amount_minor,
                "includeTokensInfo": "true",
            },
        )
        if payload:
            self._last_quote = payload
        return payload

    def build_swap_tx(
        self,
        src: str,
        dst: str,
        amount_minor: str,
        *,
        from_address: Optional[str] = None,
        slippage: Optional[float] = None,
    ) -> Optional[dict]:
        """Call Classic Swap ``/swap`` and return the response (includes ``tx``)."""
        params = {
            "src": src,
            "dst": dst,
            "amount": amount_minor,
            "from": from_address or self._wallet,
            "slippage": slippage if slippage is not None else self._slippage,
            "disableEstimate": "true",
        }
        payload = self._api_get(self._swap_path("swap"), params=params)
        if not payload:
            return None
        tx = payload.get("tx")
        if isinstance(tx, dict):
            self._last_swap_tx = dict(tx)
        else:
            self._last_swap_tx = payload
        return payload

    def connect(self) -> bool:
        if not self._api_key:
            logger.warning(
                "OneInchDexBroker: set ONEINCH_API_KEY (Bearer from Business portal; "
                "never commit)."
            )
            self._connected = False
            return False
        if self._orders_blocked() and not self._dry_run:
            reason = (
                self._risk_engine.get_kill_reason()
                if self._risk_engine is not None
                else "FSB_KILL_SWITCH"
            )
            logger.warning(
                "OneInchDexBroker: kill-switch active (%s); connect refused",
                reason or "unknown",
            )
            self._connected = False
            return False

        # Prefer healthcheck; fall back to a tiny quote if health path differs.
        health = self._api_get(self._swap_path("healthcheck"))
        if health is None:
            # Some portal gateways omit healthcheck — probe with 0.001 ETH→USDC quote.
            try:
                eth, eth_dec = resolve_token("ETH")
                usdc, _ = resolve_token("USDC")
                probe = self.quote_swap(eth, usdc, to_minor_units(0.001, eth_dec))
            except Exception:
                probe = None
            if probe is None:
                self._connected = False
                return False

        self._connected = True
        mode = "dry-run" if self._dry_run else "BROADCAST-ARMED"
        logger.info(
            "OneInchDexBroker connected (%s chain=%s key=%s url=%s)",
            mode,
            self._chain_id,
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
        headers = {
            "User-Agent": "ForexSmartBot/3.4.5",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        self._session.headers.update(headers)

    def reconnect(self) -> bool:
        self.disconnect()
        return self.connect()

    def is_connected(self) -> bool:
        return self._connected

    def get_price(self, symbol: str) -> Optional[float]:
        try:
            base, quote = parse_pair_symbol(symbol)
            src, src_dec = resolve_token(base)
            dst, dst_dec = resolve_token(quote)
            # Quote 1.0 base unit → dst amount / 1.0
            amount = to_minor_units(1.0, src_dec)
        except ValueError as exc:
            logger.warning("OneInchDexBroker get_price: %s", exc)
            return None
        payload = self.quote_swap(src, dst, amount)
        if not payload:
            return None
        dst_amount = payload.get("dstAmount")
        if dst_amount is None:
            return None
        try:
            return from_minor_units(str(dst_amount), dst_dec)
        except (TypeError, ValueError):
            return None

    def _apply_local_fill(
        self, symbol: str, side: int, quantity: float, fill_price: float
    ) -> str:
        existing = self._positions.get(symbol)
        if existing is not None and existing.side != side:
            # Flatten then open
            self._positions.pop(symbol, None)
            existing = None
        if existing and existing.side == side:
            new_qty = existing.quantity + quantity
            existing.entry_price = (
                (existing.entry_price * existing.quantity) + (fill_price * quantity)
            ) / new_qty
            existing.quantity = new_qty
            existing.current_price = fill_price
            existing.unrealized_pnl = 0.0
        else:
            self._positions[symbol] = Position(
                symbol=symbol,
                side=side,
                quantity=float(quantity),
                entry_price=float(fill_price),
                current_price=float(fill_price),
                unrealized_pnl=0.0,
            )
        # Rough quote-balance accounting in quote units.
        notional = fill_price * quantity
        if side > 0:
            self._quote_balance -= notional
        else:
            self._quote_balance += notional
        self._order_seq += 1
        return f"1INCH-DRY-{self._order_seq}-{uuid.uuid4().hex[:8]}"

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
                "OneInchDexBroker: order blocked by kill-switch (%s)",
                reason or "unknown",
            )
            return None
        if quantity <= 0 or side not in (-1, 1):
            return None

        try:
            base, quote = parse_pair_symbol(symbol)
            # Buy base with quote → src=quote, dst=base; sell base → src=base, dst=quote.
            if side > 0:
                src_ticker, dst_ticker = quote, base
                # Approximate src spend from mid using get_price.
                px = self.get_price(symbol)
                if px is None or px <= 0:
                    return None
                src_human = quantity * px
            else:
                src_ticker, dst_ticker = base, quote
                src_human = quantity
            src, src_dec = resolve_token(src_ticker)
            dst, dst_dec = resolve_token(dst_ticker)
            amount_minor = to_minor_units(src_human, src_dec)
        except ValueError as exc:
            logger.warning("OneInchDexBroker submit_order resolve: %s", exc)
            return None

        quote_payload = self.quote_swap(src, dst, amount_minor)
        if not quote_payload:
            return None
        dst_amount = quote_payload.get("dstAmount")
        if dst_amount is None:
            return None

        swap_payload = self.build_swap_tx(src, dst, amount_minor)
        if not swap_payload:
            return None

        # Fill price in quote-per-base terms for local ledger.
        try:
            if side > 0:
                # Spent src_human quote, received dst base
                got_base = from_minor_units(str(dst_amount), dst_dec)
                fill_price = src_human / got_base if got_base else 0.0
                fill_qty = got_base
            else:
                # Sold quantity base, received quote
                got_quote = from_minor_units(str(dst_amount), dst_dec)
                fill_price = got_quote / quantity if quantity else 0.0
                fill_qty = float(quantity)
        except (TypeError, ValueError, ZeroDivisionError):
            return None
        if fill_price <= 0 or fill_qty <= 0:
            return None

        if self._dry_run:
            order_id = self._apply_local_fill(symbol, side, fill_qty, fill_price)
            logger.info(
                "OneInchDexBroker DRY-RUN order side=%s %s qty=%s px=%s id=%s",
                side,
                symbol,
                fill_qty,
                fill_price,
                order_id,
            )
            return order_id

        # Broadcast path — double opt-in already enforced via _dry_run construction.
        if not live_trading_enabled() or not dex_broadcast_enabled():
            logger.error(
                "OneInchDexBroker: broadcast refused mid-flight "
                "(FSB_LIVE_TRADING + FSB_DEX_BROADCAST required)"
            )
            return None
        if self._broadcast_fn is None:
            logger.error(
                "OneInchDexBroker: FSB_DEX_BROADCAST=1 but no broadcast_fn injected; "
                "refusing to send raw txs from the default path (opsec)."
            )
            return None
        tx = self._last_swap_tx or {}
        try:
            tx_hash = self._broadcast_fn(dict(tx))
        except Exception as exc:
            logger.warning("OneInchDexBroker broadcast failed: %s", exc)
            return None
        if not tx_hash:
            return None
        self._apply_local_fill(symbol, side, fill_qty, fill_price)
        logger.info(
            "OneInchDexBroker BROADCAST order side=%s %s qty=%s tx=%s",
            side,
            symbol,
            fill_qty,
            tx_hash,
        )
        return str(tx_hash)

    def close_all(self, symbol: str) -> bool:
        """Flatten local ledger position (allowed even under kill-switch)."""
        if not self._connected:
            return False
        pos = self._positions.get(symbol)
        if pos is None:
            return False
        # Kill-switch: unwind locally without new aggregator round-trips.
        if self._orders_blocked():
            px = pos.current_price
            self._positions.pop(symbol, None)
            notional = px * pos.quantity
            if pos.side > 0:
                self._quote_balance += notional
            else:
                self._quote_balance -= notional
            return True
        opposite = -pos.side
        order_id = self.submit_order(symbol, opposite, pos.quantity)
        return order_id is not None

    def flatten_all(self) -> int:
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
        return float(self._quote_balance)

    def get_equity(self) -> float:
        positions = self.get_positions()
        unrealized = sum(p.unrealized_pnl for p in positions.values())
        return float(self.get_balance() + unrealized)

"""Live public-catalog probes for researched venues (no API secrets)."""

from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List, Optional

import requests

from .models import AssetClass, ProbeSymbol, VenueProbeReport
from .registry import classify_pair, get_venue

DEFAULT_TIMEOUT = 45
_USER_AGENT = "ForexSmartBot/3.4.1 (+https://github.com/VoxHash/ForexSmartBot)"


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
        }
    )
    return session


def _summarize(
    venue_id: str,
    endpoint: str,
    symbols: List[ProbeSymbol],
    *,
    sample: int = 12,
    notes: str = "",
) -> VenueProbeReport:
    counts: Counter[str] = Counter(s.asset_class.value for s in symbols)
    return VenueProbeReport(
        venue_id=venue_id,
        endpoint=endpoint,
        ok=True,
        symbol_count=len(symbols),
        by_asset_class=dict(counts),
        sample_symbols=[s.symbol for s in symbols[:sample]],
        notes=notes,
    )


def probe_kraken_spot(session: Optional[requests.Session] = None) -> VenueProbeReport:
    """Fetch Kraken Spot ``AssetPairs`` (public)."""
    venue = get_venue("kraken_spot")
    endpoint = f"{venue.endpoints.rest_public}/AssetPairs"
    sess = session or _session()
    try:
        response = sess.get(endpoint, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            return VenueProbeReport(
                venue_id=venue.id,
                endpoint=endpoint,
                ok=False,
                error=str(payload["error"]),
            )
        symbols: List[ProbeSymbol] = []
        for pair_id, meta in (payload.get("result") or {}).items():
            if not isinstance(meta, dict):
                continue
            if meta.get("status") not in (None, "online"):
                continue
            base = str(meta.get("base") or "")
            quote = str(meta.get("quote") or "")
            display = str(meta.get("wsname") or meta.get("altname") or pair_id)
            symbols.append(
                ProbeSymbol(
                    venue_id=venue.id,
                    symbol=display,
                    base=base,
                    quote=quote,
                    asset_class=classify_pair(base, quote, display),
                    status=str(meta.get("status") or "online"),
                )
            )
        return _summarize(
            venue.id,
            endpoint,
            symbols,
            notes="Public catalog; spot UAT is account-manager only.",
        )
    except Exception as exc:  # network / parse
        return VenueProbeReport(
            venue_id=venue.id, endpoint=endpoint, ok=False, error=str(exc)
        )


def probe_kraken_futures(
    session: Optional[requests.Session] = None,
) -> VenueProbeReport:
    """Fetch Kraken Futures public instruments catalog."""
    venue = get_venue("kraken_futures")
    endpoint = f"{venue.endpoints.rest_public}/instruments"
    sess = session or _session()
    try:
        response = sess.get(endpoint, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        if "application/json" not in (response.headers.get("content-type") or ""):
            return VenueProbeReport(
                venue_id=venue.id,
                endpoint=endpoint,
                ok=False,
                error="Non-JSON response (demo UI may redirect; use futures.kraken.com)",
            )
        payload = response.json()
        instruments = payload.get("instruments") or []
        symbols: List[ProbeSymbol] = []
        for item in instruments:
            if not isinstance(item, dict) or not item.get("tradeable", True):
                continue
            sym = str(item.get("symbol") or "")
            base = str(item.get("base") or "")
            quote = str(item.get("quote") or "")
            asset = classify_pair(base, quote, sym)
            if asset == AssetClass.SPOT_CRYPTO and (
                sym.startswith("PF_") or sym.startswith("PI_")
            ):
                asset = AssetClass.PERP_FUTURES
            symbols.append(
                ProbeSymbol(
                    venue_id=venue.id,
                    symbol=sym,
                    base=base,
                    quote=quote,
                    asset_class=asset,
                    status="tradeable",
                )
            )
        return _summarize(
            venue.id,
            endpoint,
            symbols,
            notes="Public instruments; demo keys are separate from production.",
        )
    except Exception as exc:
        return VenueProbeReport(
            venue_id=venue.id, endpoint=endpoint, ok=False, error=str(exc)
        )


def probe_binance_spot(
    *,
    sandbox: bool = True,
    session: Optional[requests.Session] = None,
) -> VenueProbeReport:
    """Fetch Binance ``exchangeInfo`` (testnet by default)."""
    venue = get_venue("binance_spot")
    base = (
        venue.endpoints.rest_sandbox
        if sandbox and venue.endpoints.rest_sandbox
        else venue.endpoints.rest_public
    )
    endpoint = f"{base}/v3/exchangeInfo"
    sess = session or _session()
    try:
        response = sess.get(endpoint, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        symbols: List[ProbeSymbol] = []
        for item in payload.get("symbols") or []:
            if not isinstance(item, dict):
                continue
            if item.get("status") != "TRADING":
                continue
            sym = str(item.get("symbol") or "")
            base_a = str(item.get("baseAsset") or "")
            quote_a = str(item.get("quoteAsset") or "")
            symbols.append(
                ProbeSymbol(
                    venue_id=venue.id,
                    symbol=sym,
                    base=base_a,
                    quote=quote_a,
                    asset_class=classify_pair(base_a, quote_a, sym),
                    status="TRADING",
                )
            )
        label = "testnet" if sandbox else "production"
        return _summarize(
            venue.id,
            endpoint,
            symbols,
            notes=f"Binance Spot {label} exchangeInfo.",
        )
    except Exception as exc:
        return VenueProbeReport(
            venue_id=venue.id, endpoint=endpoint, ok=False, error=str(exc)
        )


def probe_all_public(
    *,
    include_binance_prod: bool = False,
    session: Optional[requests.Session] = None,
) -> List[VenueProbeReport]:
    """Run all secret-free catalog probes used for the research milestone."""
    sess = session or _session()
    reports = [
        probe_kraken_spot(sess),
        probe_kraken_futures(sess),
        probe_binance_spot(sandbox=True, session=sess),
    ]
    if include_binance_prod:
        reports.append(probe_binance_spot(sandbox=False, session=sess))
    return reports


def reports_as_dict(reports: Iterable[VenueProbeReport]) -> Dict[str, dict]:
    """Serialize probe reports for CLI / tests."""
    out: Dict[str, dict] = {}
    for report in reports:
        key = report.venue_id
        if report.endpoint.endswith("exchangeInfo") and "testnet" in report.endpoint:
            key = f"{report.venue_id}_testnet"
        elif report.endpoint.endswith("exchangeInfo"):
            key = f"{report.venue_id}_prod"
        out[key] = {
            "ok": report.ok,
            "endpoint": report.endpoint,
            "symbol_count": report.symbol_count,
            "by_asset_class": report.by_asset_class,
            "sample_symbols": report.sample_symbols,
            "error": report.error,
            "notes": report.notes,
        }
    return out

"""Static multi-venue research registry (CEX + DEX aggregator).

Profiles encode documented sandbox/public endpoints and asset coverage
from vendor docs plus live probes (see ``probes``). No API secrets here.
"""

from __future__ import annotations

from typing import Dict, List

from .models import AssetClass, VenueEndpoints, VenueKind, VenueProfile

# Fiat / commodity heuristics used when classifying public catalogs.
FIAT_CODES = frozenset(
    {
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "CHF",
        "AUD",
        "CAD",
        "NZD",
        "ZUSD",
        "ZEUR",
        "ZGBP",
        "ZJPY",
        "ZAUD",
        "ZCAD",
        "ZCHF",
    }
)
COMMODITY_MARKERS = frozenset(
    {
        "XAU",
        "XAG",
        "XAUT",
        "PAXG",
        "WTI",
        "BRENT",
        "OIL",
        "NATGAS",
        "COPPER",
    }
)


def _kraken_spot() -> VenueProfile:
    return VenueProfile(
        id="kraken_spot",
        name="Kraken Spot",
        kind=VenueKind.CEX,
        endpoints=VenueEndpoints(
            rest_public="https://api.kraken.com/0/public",
            rest_private="https://api.kraken.com/0/private",
            # Spot UAT is provisioned on request via Kraken Account Manager
            # (not a public self-serve URL). Prefer Futures demo for sandbox trade.
            rest_sandbox=None,
            websocket="wss://ws.kraken.com/v2",
            docs_url="https://docs.kraken.com/exchange/guides/rest/introduction",
        ),
        asset_classes=(
            AssetClass.SPOT_CRYPTO,
            AssetClass.FX,
            AssetClass.TOKENIZED,
        ),
        notes=(
            "Public AssetPairs + Ticker need no keys. Spot covers 1400+ pairs "
            "(crypto + a small set of fiat FX like EUR/USD). Spot UAT is "
            "account-manager only; do not invent sandbox URLs."
        ),
        auth="api_key_secret",
    )


def _kraken_futures() -> VenueProfile:
    return VenueProfile(
        id="kraken_futures",
        name="Kraken Futures",
        kind=VenueKind.CEX,
        endpoints=VenueEndpoints(
            rest_public="https://futures.kraken.com/derivatives/api/v3",
            rest_private="https://futures.kraken.com/derivatives/api/v3",
            rest_sandbox="https://demo-futures.kraken.com",
            websocket="wss://futures.kraken.com/ws/v1",
            docs_url="https://docs.kraken.com/exchange/guides/futures/introduction",
        ),
        asset_classes=(
            AssetClass.PERP_FUTURES,
            AssetClass.FX,
            AssetClass.COMMODITY,
            AssetClass.SPOT_CRYPTO,
        ),
        notes=(
            "Public instruments catalog on futures.kraken.com. Self-serve demo "
            "UI at demo-futures.kraken.com (separate demo API keys). Includes "
            "crypto perps plus FX (e.g. PF_EURUSD) and commodity underlyings "
            "(XAU/XAG/WTI/Brent/NatGas)."
        ),
    )


def _binance_spot() -> VenueProfile:
    return VenueProfile(
        id="binance_spot",
        name="Binance Spot",
        kind=VenueKind.CEX,
        endpoints=VenueEndpoints(
            rest_public="https://api.binance.com/api",
            rest_private="https://api.binance.com/api",
            rest_sandbox="https://testnet.binance.vision/api",
            websocket="wss://stream.binance.com:9443/ws",
            docs_url="https://developers.binance.com/docs/binance-spot-api-docs",
        ),
        asset_classes=(
            AssetClass.SPOT_CRYPTO,
            AssetClass.TOKENIZED,
            AssetClass.FX,
        ),
        notes=(
            "Self-serve Spot Test Network at testnet.binance.vision (/api only, "
            "no /sapi). Production lists tokenized gold (PAXG/XAUT) and some "
            "fiat quote markets; not a traditional FX/CFD venue."
        ),
    )


def _oneinch() -> VenueProfile:
    return VenueProfile(
        id="oneinch",
        name="1inch Swap / Fusion",
        kind=VenueKind.AGGREGATOR,
        endpoints=VenueEndpoints(
            rest_public="https://api.1inch.com",
            rest_private="https://api.1inch.com",
            rest_sandbox=None,
            websocket=None,
            docs_url="https://business.1inch.com/portal/documentation/overview/getting-started",
        ),
        asset_classes=(AssetClass.SPOT_CRYPTO, AssetClass.TOKENIZED),
        notes=(
            "DEX aggregator / intent (Fusion) APIs. Requires Business portal "
            "Bearer API key (KYC). Classic + intent + cross-chain modes; chain "
            "IDs include Ethereum 1, Base 8453, etc. Wallet signing stays on "
            "the desktop host — never in the mobile companion."
        ),
        auth="bearer_api_key",
        withdraw_separable=False,
    )


VENUE_PROFILES: Dict[str, VenueProfile] = {
    p.id: p
    for p in (_kraken_spot(), _kraken_futures(), _binance_spot(), _oneinch())
}


def list_venues() -> List[VenueProfile]:
    """Return researched venue profiles in stable id order."""
    return [VENUE_PROFILES[k] for k in sorted(VENUE_PROFILES)]


def get_venue(venue_id: str) -> VenueProfile:
    """Lookup a venue profile by id."""
    try:
        return VENUE_PROFILES[venue_id]
    except KeyError as exc:
        raise KeyError(f"Unknown venue id: {venue_id}") from exc


def classify_pair(base: str, quote: str, symbol: str = "") -> AssetClass:
    """Heuristic asset-class label for catalog rows."""
    b = (base or "").upper()
    q = (quote or "").upper()
    sym = (symbol or "").upper()
    joined = f"{b}/{q}/{sym}"
    if any(m in joined for m in COMMODITY_MARKERS):
        return AssetClass.COMMODITY
    if b in FIAT_CODES and q in FIAT_CODES:
        return AssetClass.FX
    if sym.startswith("PF_") or sym.startswith("PI_") or "PERP" in sym:
        # Futures symbols may still be FX/commodity — prefer markers above.
        if b in FIAT_CODES and q in FIAT_CODES:
            return AssetClass.FX
        return AssetClass.PERP_FUTURES
    return AssetClass.SPOT_CRYPTO

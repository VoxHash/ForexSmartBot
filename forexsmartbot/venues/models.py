"""Venue capability models for multi-venue CEX/DEX research."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class VenueKind(str, Enum):
    CEX = "cex"
    DEX = "dex"
    AGGREGATOR = "aggregator"


class AssetClass(str, Enum):
    SPOT_CRYPTO = "spot_crypto"
    FX = "fx"
    COMMODITY = "commodity"
    PERP_FUTURES = "perp_futures"
    TOKENIZED = "tokenized"


@dataclass(frozen=True)
class VenueEndpoints:
    """Documented REST/WebSocket bases (sandbox preferred for integration)."""

    rest_public: str
    rest_private: Optional[str] = None
    rest_sandbox: Optional[str] = None
    websocket: Optional[str] = None
    docs_url: Optional[str] = None


@dataclass
class VenueProfile:
    """Static research profile for a trading venue."""

    id: str
    name: str
    kind: VenueKind
    endpoints: VenueEndpoints
    asset_classes: Tuple[AssetClass, ...]
    notes: str = ""
    auth: str = "api_key_secret"
    withdraw_separable: bool = True
    ip_allowlist_recommended: bool = True


@dataclass
class ProbeSymbol:
    """One tradable symbol discovered from a live public catalog."""

    venue_id: str
    symbol: str
    base: str = ""
    quote: str = ""
    asset_class: AssetClass = AssetClass.SPOT_CRYPTO
    status: str = "online"
    raw: Optional[Dict] = None


@dataclass
class VenueProbeReport:
    """Live probe summary for one venue endpoint."""

    venue_id: str
    endpoint: str
    ok: bool
    symbol_count: int = 0
    by_asset_class: Dict[str, int] = field(default_factory=dict)
    sample_symbols: List[str] = field(default_factory=list)
    error: Optional[str] = None
    notes: str = ""

"""Wallet session models (public addresses only — never private keys)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ChainFamily(str, Enum):
    """Execution / signing family for a network."""

    EVM = "evm"
    SOLANA = "solana"


class WalletProvider(str, Enum):
    """Known wallet providers for this slice."""

    METAMASK = "metamask"
    PHANTOM = "phantom"
    WALLETCONNECT = "walletconnect"
    MOCK = "mock"


@dataclass(frozen=True)
class ChainInfo:
    """Canonical chain metadata used by the registry and UI."""

    id: str
    name: str
    family: ChainFamily
    # EVM: numeric chain id. Solana: None (use solana_cluster).
    chain_id: Optional[int] = None
    native_symbol: str = "ETH"
    rpc_public: Optional[str] = None
    explorer: Optional[str] = None
    solana_cluster: Optional[str] = None
    # GA / research notes — never invent status.
    status: str = "ga"
    notes: str = ""
    eip155: Optional[str] = None  # e.g. "eip155:1"


@dataclass
class WalletSession:
    """In-memory session: public address + selected chain. No secrets."""

    provider: WalletProvider
    address: str
    chain_key: str
    family: ChainFamily
    chain_id: Optional[int] = None
    solana_cluster: Optional[str] = None
    # WalletConnect display URI (if pairing started); never a private key.
    connect_uri: Optional[str] = None
    # Extra non-secret metadata (peer name, deeplink, etc.).
    meta: Dict[str, Any] = field(default_factory=dict)

    def short_address(self, n: int = 6) -> str:
        addr = self.address or ""
        if len(addr) <= (n * 2) + 2:
            return addr
        return f"{addr[: n + 2]}…{addr[-n:]}"


@dataclass
class ConnectOffer:
    """URI / deeplink the user must open or scan to approve a connection."""

    provider: WalletProvider
    uri: str
    instructions: str
    deep_link: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

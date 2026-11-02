"""WalletManager facade: MetaMask + Phantom + mock; session-only state."""

from __future__ import annotations

from typing import Any, List, Optional

from .chains import default_chain_key, get_chain, list_chains
from .metamask import MetaMaskConnector
from .models import (
    ChainFamily,
    ChainInfo,
    ConnectOffer,
    WalletProvider,
    WalletSession,
)
from .phantom import PhantomConnector
from . import session_store


class MockWalletConnector:
    """Deterministic connector for unit tests (no network)."""

    provider = WalletProvider.MOCK

    def begin_connect(self, *, chain_key: str = "ethereum", **kwargs: Any) -> ConnectOffer:
        return ConnectOffer(
            provider=self.provider,
            uri="wc:mock-topic@2?relay-protocol=irn&symKey=00&projectId=test",
            deep_link=None,
            instructions="Mock connector — call complete_connect with a test address.",
            meta={"chain_key": chain_key},
        )

    def complete_connect(
        self,
        *,
        address: str,
        chain_key: str = "ethereum",
        offer: Optional[ConnectOffer] = None,
        **kwargs: Any,
    ) -> WalletSession:
        chain = get_chain(chain_key)
        session = WalletSession(
            provider=self.provider,
            address=address,
            chain_key=chain.id,
            family=chain.family,
            chain_id=chain.chain_id,
            solana_cluster=chain.solana_cluster,
            connect_uri=offer.uri if offer else None,
            meta={"method": "mock"},
        )
        session_store.set_session(session)
        return session

    def disconnect(self) -> None:
        session_store.clear_session()

    def request(self, method: str, params: Optional[Any] = None) -> Any:
        session = session_store.get_session()
        if method == "eth_accounts" and session:
            return [session.address]
        return None


class WalletManager:
    """App-facing wallet API used by Settings UI and DEX wiring."""

    def __init__(self) -> None:
        self.metamask = MetaMaskConnector()
        self.phantom = PhantomConnector()
        self.mock = MockWalletConnector()

    def session(self) -> Optional[WalletSession]:
        return session_store.get_session()

    def is_connected(self) -> bool:
        return self.session() is not None

    def disconnect(self) -> None:
        session_store.clear_session()

    def chains(
        self,
        *,
        family: Optional[ChainFamily] = None,
        include_testnets: bool = True,
    ) -> List[ChainInfo]:
        return list_chains(family=family, include_testnets=include_testnets)

    def begin(
        self,
        provider: str,
        *,
        chain_key: Optional[str] = None,
        **kwargs: Any,
    ) -> ConnectOffer:
        connector = self._connector(provider)
        family = (
            ChainFamily.SOLANA
            if provider.lower() == WalletProvider.PHANTOM.value
            else ChainFamily.EVM
        )
        key = chain_key or default_chain_key(family)
        return connector.begin_connect(chain_key=key, **kwargs)

    def complete(
        self,
        provider: str,
        *,
        address: str,
        chain_key: Optional[str] = None,
        offer: Optional[ConnectOffer] = None,
        **kwargs: Any,
    ) -> WalletSession:
        connector = self._connector(provider)
        family = (
            ChainFamily.SOLANA
            if provider.lower() == WalletProvider.PHANTOM.value
            and (chain_key is None or get_chain(chain_key).family == ChainFamily.SOLANA)
            else ChainFamily.EVM
        )
        key = chain_key or default_chain_key(family)
        return connector.complete_connect(
            address=address, chain_key=key, offer=offer, **kwargs
        )

    def attach_address(
        self,
        provider: str,
        address: str,
        *,
        chain_key: Optional[str] = None,
    ) -> WalletSession:
        """Session-only public address (dry-run / quote from). No keys."""
        p = provider.lower().strip()
        if p == WalletProvider.PHANTOM.value:
            key = chain_key or "solana"
            return self.phantom.connect_address(address, chain_key=key)
        if p == WalletProvider.MOCK.value:
            return self.complete("mock", address=address, chain_key=chain_key or "ethereum")
        key = chain_key or "ethereum"
        return self.metamask.connect_address(address, chain_key=key)

    def select_chain(self, chain_key: str) -> WalletSession:
        """Update selected chain on the current session (address unchanged)."""
        session = self.session()
        if session is None:
            raise RuntimeError("No wallet session — connect first")
        chain = get_chain(chain_key)
        if chain.family != session.family:
            raise ValueError(
                f"Cannot switch from {session.family.value} to {chain.family.value} "
                "on the same session; disconnect and reconnect"
            )
        updated = WalletSession(
            provider=session.provider,
            address=session.address,
            chain_key=chain.id,
            family=chain.family,
            chain_id=chain.chain_id,
            solana_cluster=chain.solana_cluster,
            connect_uri=session.connect_uri,
            meta=dict(session.meta),
        )
        session_store.set_session(updated)
        return updated

    def status_dict(self) -> dict:
        s = self.session()
        if not s:
            return {"connected": False, "address": None, "chain": None, "provider": None}
        return {
            "connected": True,
            "address": s.address,
            "short_address": s.short_address(),
            "chain": s.chain_key,
            "chain_id": s.chain_id,
            "solana_cluster": s.solana_cluster,
            "family": s.family.value,
            "provider": s.provider.value,
        }

    def _connector(self, provider: str):
        p = provider.lower().strip()
        if p in (WalletProvider.METAMASK.value, WalletProvider.WALLETCONNECT.value):
            return self.metamask
        if p == WalletProvider.PHANTOM.value:
            return self.phantom
        if p == WalletProvider.MOCK.value:
            return self.mock
        raise ValueError(f"Unknown wallet provider {provider!r}")


# Process singleton for UI / broker wiring.
_MANAGER: Optional[WalletManager] = None


def get_wallet_manager() -> WalletManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = WalletManager()
    return _MANAGER

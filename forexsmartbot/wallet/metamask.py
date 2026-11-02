"""MetaMask connector for desktop PyQt (WalletConnect URI + session attach).

Browser extensions inject EIP-1193 ``window.ethereum`` — unavailable inside
native PyQt. Desktop path:

1. ``begin_connect`` → WalletConnect v2 URI + MetaMask deep link (QR / copy).
2. User approves in MetaMask mobile / desktop WC.
3. ``complete_connect(address=…)`` stores a **session-only** public address
   (relay auto-settlement is a follow-on; this slice never holds private keys).

``connect_address`` attaches a known public address for dry-run DEX quotes
without claiming a live WC session.
"""

from __future__ import annotations

from typing import Any, Optional

from .base import (
    UnsupportedMethodError,
    WalletConnector,
    assert_public_address,
    eip1193_unsupported,
)
from .chains import get_chain
from .models import (
    ChainFamily,
    ConnectOffer,
    WalletProvider,
    WalletSession,
)
from . import session_store
from .walletconnect import (
    build_wc_uri,
    metamask_deeplink,
    phishing_warning,
)


class MetaMaskConnector:
    """MetaMask via WalletConnect URI flow (desktop-friendly)."""

    provider = WalletProvider.METAMASK

    def begin_connect(self, *, chain_key: str = "ethereum", **kwargs: Any) -> ConnectOffer:
        chain = get_chain(chain_key)
        if chain.family != ChainFamily.EVM:
            raise ValueError("MetaMask connector is EVM-only; use Phantom for Solana")
        uri, topic, sym_key = build_wc_uri(project_id=kwargs.get("project_id"))
        session_store.stash_pairing(topic, sym_key)
        deep = metamask_deeplink(uri)
        return ConnectOffer(
            provider=self.provider,
            uri=uri,
            deep_link=deep,
            instructions=(
                "Scan the WalletConnect URI with MetaMask mobile, or open the "
                "MetaMask deep link on a device with MetaMask installed. "
                + phishing_warning()
            ),
            meta={
                "chain_key": chain_key,
                "chain_id": chain.chain_id,
                "topic": topic,
                # sym_key intentionally omitted from offer.meta (RAM stash only)
            },
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
        addr = assert_public_address(address, family="evm")
        pairing = session_store.pop_pairing()
        session = WalletSession(
            provider=self.provider,
            address=addr,
            chain_key=chain.id,
            family=ChainFamily.EVM,
            chain_id=chain.chain_id,
            connect_uri=offer.uri if offer else None,
            meta={
                "method": "walletconnect_uri",
                "topic": pairing.get("topic")
                or (offer.meta.get("topic") if offer else None),
                "note": "Session holds public address only; signing stays in MetaMask",
            },
        )
        session_store.set_session(session)
        return session

    def connect_address(
        self, address: str, *, chain_key: str = "ethereum"
    ) -> WalletSession:
        """Attach a public EVM address for dry-run / quote ``from`` (no WC)."""
        chain = get_chain(chain_key)
        if chain.family != ChainFamily.EVM:
            raise ValueError("EVM chain required")
        addr = assert_public_address(address, family="evm")
        session = WalletSession(
            provider=self.provider,
            address=addr,
            chain_key=chain.id,
            family=ChainFamily.EVM,
            chain_id=chain.chain_id,
            meta={"method": "address_attach", "signing": False},
        )
        session_store.set_session(session)
        return session

    def disconnect(self) -> None:
        session_store.clear_session()

    def request(self, method: str, params: Optional[Any] = None) -> Any:
        session = session_store.get_session()
        if method == "eth_accounts":
            return [session.address] if session and session.family == ChainFamily.EVM else []
        if method == "eth_chainId":
            if not session or session.chain_id is None:
                return "0x1"
            return hex(session.chain_id)
        if method == "eth_requestAccounts":
            if session and session.family == ChainFamily.EVM:
                return [session.address]
            raise UnsupportedMethodError(
                "No MetaMask session; call begin_connect / complete_connect first"
            )
        # eth_sendTransaction / personal_sign require live WC relay — not in this slice.
        raise UnsupportedMethodError(str(eip1193_unsupported(method)["message"]))


# Protocol structural check helper for tests / typing.
def as_connector(connector: MetaMaskConnector) -> WalletConnector:
    return connector

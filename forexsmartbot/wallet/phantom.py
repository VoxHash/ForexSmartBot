"""Phantom connector scaffolding (Solana deeplink + session attach).

Phantom deeplinks (``https://phantom.com/ul/v1/…``) currently support
**Solana only**. EVM networks (Ethereum, Base, Polygon, Robinhood Chain, Arc)
are available via the Phantom **browser extension** injected provider — not
via deeplink. Desktop PyQt therefore:

- Builds a real Solana ``/connect`` universal-link URL (encryption pubkey +
  redirect required by Phantom docs).
- Completes with a session-only base58 public key after the user returns
  (full NaCl shared-secret decrypt of the redirect payload is a follow-on).
- Documents EVM-via-Phantom as roadmap (extension / future embedded EVM).

Refs: https://docs.phantom.com/phantom-deeplinks/provider-methods/connect
"""

from __future__ import annotations

import base64
import secrets
import urllib.parse
from typing import Any, Optional, Tuple

from .base import (
    UnsupportedMethodError,
    assert_public_address,
)
from .chains import get_chain
from .models import (
    ChainFamily,
    ConnectOffer,
    WalletProvider,
    WalletSession,
)
from . import session_store

PHANTOM_CONNECT_BASE = "https://phantom.com/ul/v1/connect"
# Ephemeral X25519-ish placeholder: 32 raw bytes → base58-ish via urlsafe b64
# for scaffolding. Production should use a real Curve25519 keypair (nacl).


def _scaffold_encryption_pubkey() -> Tuple[str, bytes]:
    """Generate a disposable 32-byte key material for deeplink scaffolding.

    Returns (url-safe encoding for query param, raw secret kept in RAM only).
    """
    raw = secrets.token_bytes(32)
    # Phantom expects base58; without an extra dep we use urlsafe base64 and
    # label the scaffold clearly. Follow-on: PyNaCl + base58.
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return encoded, raw


def build_phantom_connect_url(
    *,
    app_url: str,
    redirect_link: str,
    dapp_encryption_public_key: str,
    cluster: str = "mainnet-beta",
) -> str:
    """Build the official Phantom connect universal link (Solana)."""
    params = {
        "app_url": app_url,
        "redirect_link": redirect_link,
        "dapp_encryption_public_key": dapp_encryption_public_key,
        "cluster": cluster,
    }
    return f"{PHANTOM_CONNECT_BASE}?{urllib.parse.urlencode(params)}"


class PhantomConnector:
    """Phantom Solana deeplink path + address attach; EVM noted as scaffold."""

    provider = WalletProvider.PHANTOM

    def __init__(self) -> None:
        self._enc_secret: Optional[bytes] = None

    def begin_connect(
        self,
        *,
        chain_key: str = "solana",
        app_url: str = "https://github.com/VoxHash/ForexSmartBot",
        redirect_link: str = "forexsmartbot://phantom/callback",
        **kwargs: Any,
    ) -> ConnectOffer:
        chain = get_chain(chain_key)
        if chain.family == ChainFamily.EVM:
            return ConnectOffer(
                provider=self.provider,
                uri="",
                deep_link=None,
                instructions=(
                    "Phantom EVM (Ethereum / Base / Polygon / Robinhood Chain / Arc) "
                    "requires the browser extension injected provider "
                    "(window.phantom.ethereum). Deeplinks are Solana-only. "
                    "Use MetaMask + WalletConnect for desktop EVM, or attach a "
                    "public address for dry-run quotes."
                ),
                meta={"chain_key": chain_key, "evm_deeplink": False, "scaffold": True},
            )
        cluster = chain.solana_cluster or "mainnet-beta"
        enc_pub, enc_secret = _scaffold_encryption_pubkey()
        self._enc_secret = enc_secret
        session_store.stash_pairing("phantom", enc_secret.hex())
        url = build_phantom_connect_url(
            app_url=kwargs.get("app_url", app_url),
            redirect_link=kwargs.get("redirect_link", redirect_link),
            dapp_encryption_public_key=enc_pub,
            cluster=cluster,
        )
        return ConnectOffer(
            provider=self.provider,
            uri=url,
            deep_link=url,
            instructions=(
                "Open the Phantom universal link on a device with Phantom installed. "
                "Approve the Solana connection, then paste your public key into "
                "ForexSmartBot to complete the session (encrypted redirect decrypt "
                "is scaffolded for a later slice). Encryption secret stays in RAM only."
            ),
            meta={
                "chain_key": chain_key,
                "cluster": cluster,
                "dapp_encryption_public_key": enc_pub,
                "scaffold_encoding": "urlsafe_b64_not_base58",
            },
        )

    def complete_connect(
        self,
        *,
        address: str,
        chain_key: str = "solana",
        offer: Optional[ConnectOffer] = None,
        **kwargs: Any,
    ) -> WalletSession:
        chain = get_chain(chain_key)
        if chain.family != ChainFamily.SOLANA:
            # Allow EVM public-address attach via Phantom label for dry-run only.
            addr = assert_public_address(address, family="evm")
            session = WalletSession(
                provider=self.provider,
                address=addr,
                chain_key=chain.id,
                family=ChainFamily.EVM,
                chain_id=chain.chain_id,
                connect_uri=offer.uri if offer else None,
                meta={"method": "address_attach_evm", "signing": False},
            )
            session_store.set_session(session)
            self._enc_secret = None
            return session
        addr = assert_public_address(address, family="solana")
        session_store.pop_pairing()
        session = WalletSession(
            provider=self.provider,
            address=addr,
            chain_key=chain.id,
            family=ChainFamily.SOLANA,
            solana_cluster=chain.solana_cluster,
            connect_uri=offer.uri if offer else None,
            meta={
                "method": "phantom_deeplink_scaffold",
                "note": "Public key session only; signTransaction via deeplink TBD",
            },
        )
        session_store.set_session(session)
        self._enc_secret = None
        return session

    def connect_address(
        self, address: str, *, chain_key: str = "solana"
    ) -> WalletSession:
        chain = get_chain(chain_key)
        family = "solana" if chain.family == ChainFamily.SOLANA else "evm"
        addr = assert_public_address(address, family=family)
        session = WalletSession(
            provider=self.provider,
            address=addr,
            chain_key=chain.id,
            family=chain.family,
            chain_id=chain.chain_id,
            solana_cluster=chain.solana_cluster,
            meta={"method": "address_attach", "signing": False},
        )
        session_store.set_session(session)
        return session

    def disconnect(self) -> None:
        self._enc_secret = None
        session_store.clear_session()

    def request(self, method: str, params: Optional[Any] = None) -> Any:
        session = session_store.get_session()
        if method in ("solana_requestAccounts", "connect"):
            if session and session.family == ChainFamily.SOLANA:
                return {"publicKey": session.address}
            raise UnsupportedMethodError("No Phantom Solana session")
        raise UnsupportedMethodError(
            f"Phantom method {method!r} not available in this desktop scaffold"
        )

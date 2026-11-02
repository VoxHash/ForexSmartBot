"""Crypto wallet connect (MetaMask / Phantom / WalletConnect) — session only.

Opsec: no private keys or seed phrases in app storage by default. Sessions are
process-local; disconnect clears RAM. DEX broadcast still requires injected
``broadcast_fn`` + live flags (see ``broadcast.make_broadcast_fn``).
"""

from .broadcast import make_broadcast_fn, wallet_address_for_dex
from .chains import (
    chain_display_rows,
    evm_chain_ids,
    get_chain,
    get_chain_by_evm_id,
    list_chains,
)
from .manager import WalletManager, get_wallet_manager
from .models import ChainFamily, ChainInfo, ConnectOffer, WalletProvider, WalletSession

__all__ = [
    "ChainFamily",
    "ChainInfo",
    "ConnectOffer",
    "WalletManager",
    "WalletProvider",
    "WalletSession",
    "chain_display_rows",
    "evm_chain_ids",
    "get_chain",
    "get_chain_by_evm_id",
    "get_wallet_manager",
    "list_chains",
    "make_broadcast_fn",
    "wallet_address_for_dex",
]

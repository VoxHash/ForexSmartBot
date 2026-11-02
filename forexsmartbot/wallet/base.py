"""Wallet connector protocol (EIP-1193-shaped for EVM; Solana parallel)."""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, runtime_checkable

from .models import ConnectOffer, WalletProvider, WalletSession


@runtime_checkable
class WalletConnector(Protocol):
    """Narrow interface: connect / disconnect / optional request hooks."""

    provider: WalletProvider

    def begin_connect(self, *, chain_key: str, **kwargs: Any) -> ConnectOffer:
        """Start a connection; return URI/deeplink for the user to approve."""

    def complete_connect(
        self,
        *,
        address: str,
        chain_key: str,
        offer: Optional[ConnectOffer] = None,
        **kwargs: Any,
    ) -> WalletSession:
        """Finalize after the user approves in the external wallet."""

    def disconnect(self) -> None:
        """Clear in-memory session material for this connector."""

    def request(self, method: str, params: Optional[Any] = None) -> Any:
        """Optional JSON-RPC / provider request (signing stays in wallet)."""


class WalletError(RuntimeError):
    """Base wallet error."""


class WalletConnectConfigError(WalletError):
    """Missing or invalid WalletConnect / Reown project configuration."""


class UnsupportedMethodError(WalletError):
    """Provider method not available in this slice."""


def assert_public_address(address: str, *, family: str) -> str:
    """Validate a public address shape; never accept seed phrases."""
    addr = (address or "").strip()
    if not addr:
        raise WalletError("Address is required")
    # Reject anything that looks like a mnemonic or hex private key dump.
    lowered = addr.lower()
    if " " in addr and len(addr.split()) >= 12:
        raise WalletError("Seed phrases are not accepted — use a public address only")
    if family == "evm":
        if not (addr.startswith("0x") and len(addr) == 42):
            raise WalletError("EVM address must be 0x-prefixed 20-byte hex (42 chars)")
        int(addr[2:], 16)  # validate hex
        return addr
    if family == "solana":
        # Base58 public keys are typically 32–44 chars; reject 0x / hex keys.
        if addr.startswith("0x"):
            raise WalletError("Solana address must be base58, not 0x-hex")
        if len(addr) < 32 or len(addr) > 48:
            raise WalletError("Solana address length looks invalid")
        return addr
    raise WalletError(f"Unknown address family {family!r}")


def eip1193_unsupported(method: str) -> Dict[str, Any]:
    """Standardish error payload for methods not wired yet."""
    return {
        "code": 4200,
        "message": f"Method {method} not supported in this ForexSmartBot wallet slice",
    }

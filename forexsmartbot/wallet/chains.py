"""Chain registry: major EVM networks + Solana (+ Robinhood Chain facts).

Sources (do not invent):
- Ethereum / Base / OP / Arbitrum / Polygon: ChainList / vendor docs
- Robinhood Chain: docs.robinhood.com/chain/connecting/ — official name
  **Robinhood Chain** (EVM L2 on Arbitrum tech); mainnet chain ID **4663**,
  testnet **46630**; public mainnet announced 2026-07-01. Refer only as
  "Robinhood Chain" (not informal shorthands) in user-facing copy.
- Solana: mainnet-beta / devnet / testnet clusters (no EVM chain id)
- Phantom injected EVM support includes Ethereum, Polygon, Base, Robinhood
  Chain, Arc (Phantom Connect SDK docs); Arbitrum unsupported for Phantom txs.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .models import ChainFamily, ChainInfo

# Immutable registry keyed by stable slug.
_CHAINS: Dict[str, ChainInfo] = {
    "ethereum": ChainInfo(
        id="ethereum",
        name="Ethereum Mainnet",
        family=ChainFamily.EVM,
        chain_id=1,
        native_symbol="ETH",
        rpc_public="https://ethereum.publicnode.com",
        explorer="https://etherscan.io",
        eip155="eip155:1",
        status="ga",
    ),
    "base": ChainInfo(
        id="base",
        name="Base",
        family=ChainFamily.EVM,
        chain_id=8453,
        native_symbol="ETH",
        rpc_public="https://mainnet.base.org",
        explorer="https://basescan.org",
        eip155="eip155:8453",
        status="ga",
    ),
    "optimism": ChainInfo(
        id="optimism",
        name="OP Mainnet",
        family=ChainFamily.EVM,
        chain_id=10,
        native_symbol="ETH",
        rpc_public="https://mainnet.optimism.io",
        explorer="https://optimistic.etherscan.io",
        eip155="eip155:10",
        status="ga",
    ),
    "arbitrum": ChainInfo(
        id="arbitrum",
        name="Arbitrum One",
        family=ChainFamily.EVM,
        chain_id=42161,
        native_symbol="ETH",
        rpc_public="https://arb1.arbitrum.io/rpc",
        explorer="https://arbiscan.io",
        eip155="eip155:42161",
        status="ga",
        notes="Supported for MetaMask / WalletConnect EVM; Phantom marks Arbitrum unsupported for txs.",
    ),
    "polygon": ChainInfo(
        id="polygon",
        name="Polygon Mainnet",
        family=ChainFamily.EVM,
        chain_id=137,
        native_symbol="POL",
        rpc_public="https://polygon-rpc.com",
        explorer="https://polygonscan.com",
        eip155="eip155:137",
        status="ga",
    ),
    "bnb": ChainInfo(
        id="bnb",
        name="BNB Smart Chain",
        family=ChainFamily.EVM,
        chain_id=56,
        native_symbol="BNB",
        rpc_public="https://bsc-dataseed.binance.org",
        explorer="https://bscscan.com",
        eip155="eip155:56",
        status="ga",
    ),
    "avalanche": ChainInfo(
        id="avalanche",
        name="Avalanche C-Chain",
        family=ChainFamily.EVM,
        chain_id=43114,
        native_symbol="AVAX",
        rpc_public="https://api.avax.network/ext/bc/C/rpc",
        explorer="https://snowtrace.io",
        eip155="eip155:43114",
        status="ga",
    ),
    "robinhood_chain": ChainInfo(
        id="robinhood_chain",
        name="Robinhood Chain",
        family=ChainFamily.EVM,
        chain_id=4663,
        native_symbol="ETH",
        rpc_public="https://rpc.mainnet.chain.robinhood.com",
        explorer="https://robinhoodchain.blockscout.com",
        eip155="eip155:4663",
        status="ga",
        notes=(
            "Official name: Robinhood Chain (permissionless Ethereum-compatible "
            "L2 built on Arbitrum technology). Public mainnet launched 2026-07-01 "
            "(Robinhood newsroom). Chain ID 4663; testnet 46630. Docs: "
            "https://docs.robinhood.com/chain/connecting/"
        ),
    ),
    "robinhood_chain_testnet": ChainInfo(
        id="robinhood_chain_testnet",
        name="Robinhood Chain Testnet",
        family=ChainFamily.EVM,
        chain_id=46630,
        native_symbol="ETH",
        rpc_public="https://rpc.testnet.chain.robinhood.com",
        explorer="https://explorer.testnet.chain.robinhood.com",
        eip155="eip155:46630",
        status="testnet",
        notes="Testnet tokens have no monetary value (Robinhood Chain docs).",
    ),
    "arc": ChainInfo(
        id="arc",
        name="Arc",
        family=ChainFamily.EVM,
        chain_id=5042,
        native_symbol="USDC",
        explorer=None,
        eip155="eip155:5042",
        status="ga",
        notes="Listed in Phantom Connect injected EVM support (chain ID 5042).",
    ),
    "sepolia": ChainInfo(
        id="sepolia",
        name="Ethereum Sepolia",
        family=ChainFamily.EVM,
        chain_id=11155111,
        native_symbol="ETH",
        explorer="https://sepolia.etherscan.io",
        eip155="eip155:11155111",
        status="testnet",
    ),
    "base_sepolia": ChainInfo(
        id="base_sepolia",
        name="Base Sepolia",
        family=ChainFamily.EVM,
        chain_id=84532,
        native_symbol="ETH",
        explorer="https://sepolia.basescan.org",
        eip155="eip155:84532",
        status="testnet",
    ),
    "solana": ChainInfo(
        id="solana",
        name="Solana Mainnet",
        family=ChainFamily.SOLANA,
        chain_id=None,
        native_symbol="SOL",
        rpc_public="https://api.mainnet-beta.solana.com",
        explorer="https://explorer.solana.com",
        solana_cluster="mainnet-beta",
        status="ga",
    ),
    "solana_devnet": ChainInfo(
        id="solana_devnet",
        name="Solana Devnet",
        family=ChainFamily.SOLANA,
        chain_id=None,
        native_symbol="SOL",
        rpc_public="https://api.devnet.solana.com",
        explorer="https://explorer.solana.com/?cluster=devnet",
        solana_cluster="devnet",
        status="testnet",
    ),
    "solana_testnet": ChainInfo(
        id="solana_testnet",
        name="Solana Testnet",
        family=ChainFamily.SOLANA,
        chain_id=None,
        native_symbol="SOL",
        rpc_public="https://api.testnet.solana.com",
        explorer="https://explorer.solana.com/?cluster=testnet",
        solana_cluster="testnet",
        status="testnet",
    ),
}


def list_chains(
    *,
    family: Optional[ChainFamily] = None,
    include_testnets: bool = True,
) -> List[ChainInfo]:
    """Return registered chains, optionally filtered."""
    out: List[ChainInfo] = []
    for chain in _CHAINS.values():
        if family is not None and chain.family != family:
            continue
        if not include_testnets and chain.status == "testnet":
            continue
        out.append(chain)
    return out


def get_chain(key: str) -> ChainInfo:
    """Lookup by slug; raises KeyError if unknown."""
    if key not in _CHAINS:
        raise KeyError(f"Unknown chain {key!r}; known: {sorted(_CHAINS)}")
    return _CHAINS[key]


def get_chain_by_evm_id(chain_id: int) -> Optional[ChainInfo]:
    for chain in _CHAINS.values():
        if chain.family == ChainFamily.EVM and chain.chain_id == chain_id:
            return chain
    return None


def evm_chain_ids() -> Tuple[int, ...]:
    return tuple(
        c.chain_id
        for c in _CHAINS.values()
        if c.family == ChainFamily.EVM and c.chain_id is not None
    )


def default_chain_key(family: ChainFamily) -> str:
    return "ethereum" if family == ChainFamily.EVM else "solana"


def chain_display_rows() -> List[Dict[str, str]]:
    """UI-friendly rows (id, name, family, chain_id/cluster, status)."""
    rows: List[Dict[str, str]] = []
    for c in list_chains():
        ident = (
            str(c.chain_id)
            if c.family == ChainFamily.EVM
            else (c.solana_cluster or "")
        )
        rows.append(
            {
                "id": c.id,
                "name": c.name,
                "family": c.family.value,
                "identifier": ident,
                "status": c.status,
            }
        )
    return rows

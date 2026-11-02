"""Wallet connect slice: chains, MetaMask WC URI, Phantom scaffold, broadcast guard."""

from __future__ import annotations

import pytest

from forexsmartbot.wallet import (
    ChainFamily,
    get_chain,
    get_wallet_manager,
    list_chains,
    make_broadcast_fn,
    wallet_address_for_dex,
)
from forexsmartbot.wallet.base import WalletError, assert_public_address
from forexsmartbot.wallet.phantom import build_phantom_connect_url
from forexsmartbot.wallet.session_store import clear_session
from forexsmartbot.wallet.walletconnect import build_wc_uri, metamask_deeplink


@pytest.fixture(autouse=True)
def _clear_wallet_session():
    clear_session()
    yield
    clear_session()


def test_chain_registry_ethereum_base_solana_robinhood():
    eth = get_chain("ethereum")
    assert eth.chain_id == 1
    assert eth.family == ChainFamily.EVM
    base = get_chain("base")
    assert base.chain_id == 8453
    sol = get_chain("solana")
    assert sol.family == ChainFamily.SOLANA
    assert sol.solana_cluster == "mainnet-beta"
    rh = get_chain("robinhood_chain")
    assert rh.name == "Robinhood Chain"
    assert rh.chain_id == 4663
    assert rh.status == "ga"
    assert "Robinhood Chain" in rh.notes
    ids = {c.id for c in list_chains()}
    assert {"ethereum", "base", "solana", "robinhood_chain", "arbitrum", "polygon"} <= ids


def test_assert_rejects_seed_phrase_and_bad_evm():
    with pytest.raises(WalletError, match="Seed phrases"):
        assert_public_address(
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon about",
            family="evm",
        )
    with pytest.raises(WalletError):
        assert_public_address("not-an-address", family="evm")


def test_walletconnect_uri_and_metamask_deeplink():
    uri, topic, sym = build_wc_uri(project_id="test-project-id")
    assert uri.startswith("wc:")
    assert "@2?" in uri
    assert "symKey=" in uri
    assert topic
    assert len(sym) == 64
    deep = metamask_deeplink(uri)
    assert deep.startswith("https://metamask.app.link/wc?uri=")


def test_metamask_begin_complete_and_status():
    wm = get_wallet_manager()
    offer = wm.begin("metamask", chain_key="base")
    assert offer.uri.startswith("wc:")
    assert offer.deep_link and "metamask.app.link" in offer.deep_link
    addr = "0x1111111111111111111111111111111111111111"
    session = wm.complete("metamask", address=addr, chain_key="base", offer=offer)
    assert session.address == addr
    assert session.chain_id == 8453
    assert session.provider.value == "metamask"
    st = wm.status_dict()
    assert st["connected"] is True
    assert st["chain"] == "base"
    assert wallet_address_for_dex() == addr
    wm.disconnect()
    assert wm.is_connected() is False
    assert wallet_address_for_dex() is None


def test_metamask_attach_address_session_only():
    wm = get_wallet_manager()
    addr = "0x2222222222222222222222222222222222222222"
    session = wm.attach_address("metamask", addr, chain_key="ethereum")
    assert session.meta.get("method") == "address_attach"
    assert session.chain_id == 1


def test_phantom_deeplink_scaffold_and_solana_session():
    url = build_phantom_connect_url(
        app_url="https://example.com",
        redirect_link="forexsmartbot://phantom/callback",
        dapp_encryption_public_key="dGVzdGtleQ",
        cluster="mainnet-beta",
    )
    assert url.startswith("https://phantom.com/ul/v1/connect?")
    assert "cluster=mainnet-beta" in url
    wm = get_wallet_manager()
    offer = wm.begin("phantom", chain_key="solana")
    assert "phantom.com/ul/v1/connect" in (offer.uri or offer.instructions)
    # Valid-looking base58 length (32–48); synthetic test key.
    pk = "11111111111111111111111111111111"
    session = wm.complete("phantom", address=pk, chain_key="solana", offer=offer)
    assert session.family == ChainFamily.SOLANA
    assert wallet_address_for_dex() is None  # Solana not used as EVM from


def test_phantom_evm_begin_documents_extension_only():
    wm = get_wallet_manager()
    offer = wm.begin("phantom", chain_key="ethereum")
    assert offer.meta.get("evm_deeplink") is False
    assert "extension" in offer.instructions.lower() or "injected" in offer.instructions.lower()


def test_select_chain_same_family_only():
    wm = get_wallet_manager()
    wm.attach_address(
        "metamask",
        "0x3333333333333333333333333333333333333333",
        chain_key="ethereum",
    )
    updated = wm.select_chain("base")
    assert updated.chain_id == 8453
    with pytest.raises(ValueError, match="Cannot switch"):
        wm.select_chain("solana")


def test_broadcast_fn_refuses_without_flags_and_signer(monkeypatch):
    monkeypatch.delenv("FSB_LIVE_TRADING", raising=False)
    monkeypatch.delenv("FSB_DEX_BROADCAST", raising=False)
    fn = make_broadcast_fn()
    assert fn({"to": "0xabc", "data": "0x"}) is None

    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    monkeypatch.setenv("FSB_DEX_BROADCAST", "1")
    # Armed but no signer and no session → None
    assert make_broadcast_fn()({"to": "0xabc"}) is None

    wm = get_wallet_manager()
    wm.attach_address(
        "metamask",
        "0x4444444444444444444444444444444444444444",
        chain_key="ethereum",
    )
    calls = []

    def signer(tx):
        calls.append(tx)
        return "0xdeadbeef"

    out = make_broadcast_fn(signer_fn=signer)({"to": "0xabc"})
    assert out == "0xdeadbeef"
    assert calls


def test_mock_connector():
    wm = get_wallet_manager()
    offer = wm.begin("mock", chain_key="ethereum")
    assert "mock" in offer.uri
    s = wm.complete(
        "mock",
        address="0x5555555555555555555555555555555555555555",
        chain_key="ethereum",
        offer=offer,
    )
    assert s.provider.value == "mock"

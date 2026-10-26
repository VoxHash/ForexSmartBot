"""1inch DEX aggregator path: dry-run, guards, mocked quote/swap (no mainnet spends)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from forexsmartbot.adapters.brokers.oneinch_dex_broker import (
    OneInchDexBroker,
    parse_pair_symbol,
    resolve_token,
    to_minor_units,
)
from forexsmartbot.core.risk_engine import RiskConfig, RiskEngine
from forexsmartbot.venues.live_guard import dex_broadcast_enabled


def test_parse_pair_and_tokens():
    assert parse_pair_symbol("ETH/USDC") == ("ETH", "USDC")
    assert parse_pair_symbol("WETH-DAI") == ("WETH", "DAI")
    assert parse_pair_symbol("ETHUSDC") == ("ETH", "USDC")
    addr, dec = resolve_token("USDC")
    assert addr.startswith("0x")
    assert dec == 6
    assert to_minor_units(1.5, 6) == "1500000"


def test_dex_broadcast_flag(monkeypatch):
    monkeypatch.delenv("FSB_DEX_BROADCAST", raising=False)
    assert dex_broadcast_enabled() is False
    monkeypatch.setenv("FSB_DEX_BROADCAST", "1")
    assert dex_broadcast_enabled() is True


def test_oneinch_refuses_non_1inch_host(monkeypatch):
    monkeypatch.delenv("FSB_LIVE_TRADING", raising=False)
    monkeypatch.delenv("FSB_DEX_BROADCAST", raising=False)
    with pytest.raises(ValueError, match="api.1inch"):
        OneInchDexBroker(
            api_key="k",
            base_url="https://example.com",
            force_dry_run=True,
        )


def test_oneinch_connect_requires_api_key(monkeypatch):
    monkeypatch.delenv("ONEINCH_API_KEY", raising=False)
    broker = OneInchDexBroker(
        api_key="",
        base_url="https://api.1inch.com",
        force_dry_run=True,
    )
    assert broker.connect() is False


def test_oneinch_dry_run_quote_swap_and_kill_switch(monkeypatch):
    monkeypatch.delenv("FSB_LIVE_TRADING", raising=False)
    monkeypatch.delenv("FSB_DEX_BROADCAST", raising=False)
    monkeypatch.delenv("FSB_KILL_SWITCH", raising=False)
    engine = RiskEngine(RiskConfig())
    broker = OneInchDexBroker(
        api_key="test-key",
        base_url="https://api.1inch.com",
        force_dry_run=True,
        risk_engine=engine,
        paper_balance=10_000.0,
    )
    assert broker.dry_run is True

    def fake_api(path, params=None):
        if path.endswith("healthcheck"):
            return {"status": "OK"}
        if path.endswith("quote"):
            # Sell 0.01 ETH → ~30 USDC (6 decimals) for price probes / sells.
            # Buy path uses USDC src → return ETH wei.
            src = (params or {}).get("src", "")
            if src.lower().startswith("0xa0b86991"):  # USDC → ETH
                return {"dstAmount": str(10**15)}  # 0.001 ETH
            return {"dstAmount": "30000000"}  # 30 USDC
        if path.endswith("swap"):
            return {
                "dstAmount": "30000000",
                "tx": {
                    "to": "0x1111111254EEB25477B68fb85Ed929f73A960582",
                    "data": "0xdead",
                    "value": "0",
                    "gas": 250000,
                },
            }
        return None

    with patch.object(broker, "_api_get", side_effect=fake_api):
        assert broker.connect()
        px = broker.get_price("ETH/USDC")
        assert px == pytest.approx(30.0)
        order_id = broker.submit_order("ETH/USDC", -1, 0.01)
        assert order_id is not None
        assert order_id.startswith("1INCH-DRY-")
        assert broker.last_swap_tx is not None
        assert "ETH/USDC" in broker.get_positions()

        engine.trip_kill_switch("test_halt")
        assert broker.submit_order("ETH/USDC", -1, 0.01) is None
        assert broker.close_all("ETH/USDC") is True
        assert broker.get_positions() == {}


def test_oneinch_broadcast_requires_double_opt_in_and_fn(monkeypatch):
    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    monkeypatch.setenv("FSB_DEX_BROADCAST", "1")
    monkeypatch.delenv("FSB_KILL_SWITCH", raising=False)

    seen = {}

    def capture_broadcast(tx):
        seen["tx"] = tx
        return "0xabc123"

    broker = OneInchDexBroker(
        api_key="test-key",
        base_url="https://api.1inch.com",
        broadcast_fn=capture_broadcast,
        paper_balance=10_000.0,
    )
    assert broker.dry_run is False

    def fake_api(path, params=None):
        if path.endswith("healthcheck"):
            return {"status": "OK"}
        if path.endswith("quote"):
            return {"dstAmount": "30000000"}
        if path.endswith("swap"):
            return {
                "dstAmount": "30000000",
                "tx": {"to": "0xrouter", "data": "0xbeef", "value": "0"},
            }
        return None

    with patch.object(broker, "_api_get", side_effect=fake_api):
        assert broker.connect()
        order_id = broker.submit_order("ETH/USDC", -1, 0.01)
        assert order_id == "0xabc123"
        assert seen["tx"]["data"] == "0xbeef"


def test_oneinch_broadcast_armed_without_fn_refuses(monkeypatch):
    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    monkeypatch.setenv("FSB_DEX_BROADCAST", "1")
    broker = OneInchDexBroker(
        api_key="test-key",
        base_url="https://api.1inch.com",
        broadcast_fn=None,
    )
    assert broker.dry_run is False

    def fake_api(path, params=None):
        if path.endswith("healthcheck"):
            return {"status": "OK"}
        if path.endswith("quote"):
            return {"dstAmount": "30000000"}
        if path.endswith("swap"):
            return {
                "dstAmount": "30000000",
                "tx": {"to": "0xrouter", "data": "0xbeef", "value": "0"},
            }
        return None

    with patch.object(broker, "_api_get", side_effect=fake_api):
        assert broker.connect()
        assert broker.submit_order("ETH/USDC", -1, 0.01) is None

"""Binance Live opt-in path: guards, kill-switch, mocked mainnet (no real orders)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from forexsmartbot.adapters.brokers.binance_live_broker import BinanceLiveBroker
from forexsmartbot.core.risk_engine import RiskConfig, RiskEngine
from forexsmartbot.venues.live_guard import (
    kill_switch_forced,
    live_trading_enabled,
    require_live_opt_in,
)


def test_live_trading_enabled_truthy(monkeypatch):
    monkeypatch.delenv("FSB_LIVE_TRADING", raising=False)
    assert live_trading_enabled() is False
    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    assert live_trading_enabled() is True
    monkeypatch.setenv("FSB_LIVE_TRADING", "yes")
    assert live_trading_enabled() is True
    monkeypatch.setenv("FSB_LIVE_TRADING", "0")
    assert live_trading_enabled() is False


def test_require_live_opt_in_refuses_without_flag(monkeypatch):
    monkeypatch.delenv("FSB_LIVE_TRADING", raising=False)
    with pytest.raises(PermissionError, match="FSB_LIVE_TRADING"):
        require_live_opt_in()


def test_binance_live_refuses_without_opt_in(monkeypatch):
    monkeypatch.delenv("FSB_LIVE_TRADING", raising=False)
    with pytest.raises(PermissionError, match="FSB_LIVE_TRADING"):
        BinanceLiveBroker(api_key="k", api_secret="s")


def test_binance_live_refuses_testnet_url(monkeypatch):
    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    with pytest.raises(ValueError, match="testnet|refuses"):
        BinanceLiveBroker(
            api_key="k",
            api_secret="s",
            base_url="https://testnet.binance.vision/api",
        )


def test_binance_live_refuses_non_mainnet_host(monkeypatch):
    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    with pytest.raises(ValueError, match="api.binance.com"):
        BinanceLiveBroker(
            api_key="k",
            api_secret="s",
            base_url="https://example.com/api",
        )


def test_kill_switch_env_and_risk_engine(monkeypatch):
    monkeypatch.delenv("FSB_KILL_SWITCH", raising=False)
    engine = RiskEngine(RiskConfig())
    assert engine.is_kill_switch_active() is False
    engine.trip_kill_switch("unit_test")
    assert engine.is_kill_switch_active() is True
    assert engine.get_kill_reason() == "unit_test"
    assert engine.clear_kill_switch() is True
    assert engine.is_kill_switch_active() is False

    monkeypatch.setenv("FSB_KILL_SWITCH", "1")
    assert kill_switch_forced() is True
    assert engine.is_kill_switch_active() is True
    assert engine.clear_kill_switch() is False


def test_evaluate_kill_switch_from_drawdown(monkeypatch):
    monkeypatch.delenv("FSB_KILL_SWITCH", raising=False)
    engine = RiskEngine(RiskConfig(max_drawdown_pct=0.10))
    assert engine.evaluate_kill_switch(80.0, 100.0, 0.0, 100.0) is True
    assert engine.get_kill_reason() == "max_drawdown"


def test_binance_live_mocked_connect_order_and_kill_switch(monkeypatch):
    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    monkeypatch.delenv("FSB_KILL_SWITCH", raising=False)
    engine = RiskEngine(RiskConfig())
    broker = BinanceLiveBroker(
        api_key="live-key",
        api_secret="live-secret",
        base_url="https://api.binance.com/api",
        risk_engine=engine,
    )

    account_payload = {
        "balances": [
            {"asset": "USDT", "free": "1000.0", "locked": "0.0"},
        ]
    }
    order_payload = {
        "orderId": 99,
        "fills": [{"price": "50000.0", "qty": "0.001"}],
    }

    def fake_request(method, path, *, params=None, signed=False):
        if path == "/v3/ping":
            return {}
        if path == "/v3/account":
            assert signed is True
            return account_payload
        if path == "/v3/ticker/price":
            return {"price": "50000.0"}
        if path == "/v3/order" and method == "POST":
            assert signed is True
            return order_payload
        return None

    with patch.object(broker, "_request", side_effect=fake_request):
        assert broker.connect()
        assert broker.get_balance() == 1000.0
        order_id = broker.submit_order("BTCUSDT", 1, 0.001)
        assert order_id == "99"
        assert "BTCUSDT" in broker.get_positions()

        engine.trip_kill_switch("test_halt")
        assert broker.submit_order("BTCUSDT", 1, 0.001) is None

        assert broker.close_all("BTCUSDT") is True
        assert broker.get_positions() == {}

    with patch.object(broker, "_request", side_effect=fake_request):
        # Kill-switch still active — connect refused
        assert broker.reconnect() is False
        engine.clear_kill_switch()
        assert broker.reconnect() is True


def test_binance_live_does_not_use_sandbox_env_keys(monkeypatch):
    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    monkeypatch.setenv("BINANCE_API_KEY", "sandbox-only")
    monkeypatch.setenv("BINANCE_API_SECRET", "sandbox-secret")
    monkeypatch.delenv("BINANCE_LIVE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_LIVE_API_SECRET", raising=False)
    broker = BinanceLiveBroker(base_url="https://api.binance.com/api")
    assert broker.connect() is False

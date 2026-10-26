"""Kraken Live opt-in path: guards, kill-switch, mocked mainnet (no real orders)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from forexsmartbot.adapters.brokers.kraken_live_broker import (
    KrakenLiveBroker,
    verify_kraken_signature_vector,
)
from forexsmartbot.core.risk_engine import RiskConfig, RiskEngine


def test_kraken_signature_matches_published_vector():
    assert verify_kraken_signature_vector() is True


def test_kraken_live_refuses_without_opt_in(monkeypatch):
    monkeypatch.delenv("FSB_LIVE_TRADING", raising=False)
    with pytest.raises(PermissionError, match="FSB_LIVE_TRADING"):
        KrakenLiveBroker(api_key="k", api_secret="s")


def test_kraken_live_refuses_demo_futures_url(monkeypatch):
    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    with pytest.raises(ValueError, match="demo/futures|refuses"):
        KrakenLiveBroker(
            api_key="k",
            api_secret="s",
            private_base_url="https://demo-futures.kraken.com/derivatives/api/v3",
        )


def test_kraken_live_refuses_non_mainnet_host(monkeypatch):
    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    with pytest.raises(ValueError, match="api.kraken.com"):
        KrakenLiveBroker(
            api_key="k",
            api_secret="s",
            private_base_url="https://example.com/0/private",
        )


def test_kraken_live_mocked_connect_order_and_kill_switch(monkeypatch):
    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    monkeypatch.delenv("FSB_KILL_SWITCH", raising=False)
    engine = RiskEngine(RiskConfig())
    broker = KrakenLiveBroker(
        api_key="live-key",
        api_secret="live-secret",
        private_base_url="https://api.kraken.com/0/private",
        public_base_url="https://api.kraken.com/0/public",
        risk_engine=engine,
    )

    def fake_public(path, params=None):
        if path == "Time":
            return {"unixtime": 1}
        if path == "Ticker":
            return {"XXBTZUSD": {"c": ["50000.0", "0.001"]}}
        return None

    def fake_private(method, data=None):
        if method == "Balance":
            return {"ZUSD": "1000.0", "XXBT": "0.0"}
        if method == "AddOrder":
            assert data is not None
            assert data.get("ordertype") == "market"
            return {"txid": ["OID-KRAKEN-1"]}
        return None

    with (
        patch.object(broker, "_public_get", side_effect=fake_public),
        patch.object(broker, "_private_request", side_effect=fake_private),
    ):
        assert broker.connect()
        assert broker.get_balance() == 1000.0
        order_id = broker.submit_order("BTCUSD", 1, 0.001)
        assert order_id == "OID-KRAKEN-1"
        assert "BTCUSD" in broker.get_positions()

        engine.trip_kill_switch("test_halt")
        assert broker.submit_order("BTCUSD", 1, 0.001) is None

        assert broker.close_all("BTCUSD") is True
        assert broker.get_positions() == {}

    with (
        patch.object(broker, "_public_get", side_effect=fake_public),
        patch.object(broker, "_private_request", side_effect=fake_private),
    ):
        assert broker.reconnect() is False
        engine.clear_kill_switch()
        assert broker.reconnect() is True


def test_kraken_live_does_not_use_generic_env_keys(monkeypatch):
    monkeypatch.setenv("FSB_LIVE_TRADING", "1")
    monkeypatch.setenv("KRAKEN_API_KEY", "generic-only")
    monkeypatch.setenv("KRAKEN_API_SECRET", "generic-secret")
    monkeypatch.delenv("KRAKEN_LIVE_API_KEY", raising=False)
    monkeypatch.delenv("KRAKEN_LIVE_API_SECRET", raising=False)
    broker = KrakenLiveBroker(
        private_base_url="https://api.kraken.com/0/private",
        public_base_url="https://api.kraken.com/0/public",
    )
    assert broker.connect() is False

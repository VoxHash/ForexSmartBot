"""Tests for AppConfig defaults and environment loading."""

from __future__ import annotations

import pytest

from forexsmartbot.core.config import AppConfig


def test_app_config_defaults():
    cfg = AppConfig()
    assert cfg.broker == "PAPER"
    assert cfg.account_balance == 10_000
    assert cfg.trade_amount_min == 10
    assert cfg.trade_amount_max == 100
    assert cfg.risk_pct == 0.02
    assert cfg.max_drawdown_pct == 0.25
    assert cfg.mt4_host == "127.0.0.1"
    assert cfg.mt4_port == 5555
    assert cfg.symbols == ["EURUSD", "USDJPY", "GBPUSD"]


def test_app_config_from_env_reads_explicit_values(monkeypatch):
    monkeypatch.setenv("BROKER", "paper")
    monkeypatch.setenv("ACCOUNT_BALANCE", "25000")
    monkeypatch.setenv("TRADE_AMOUNT_MIN", "15")
    monkeypatch.setenv("TRADE_AMOUNT_MAX", "250")
    monkeypatch.setenv("RISK_PCT", "0.015")
    monkeypatch.setenv("MAX_DRAWDOWN_PCT", "0.2")
    monkeypatch.setenv("MT4_ZMQ_HOST", "10.0.0.2")
    monkeypatch.setenv("MT4_ZMQ_PORT", "6000")
    monkeypatch.setenv("SYMBOLS", "EURUSD, GBPUSD , AUDUSD")

    cfg = AppConfig.from_env()
    assert cfg.broker == "PAPER"
    assert cfg.account_balance == 25_000.0
    assert cfg.trade_amount_min == 15.0
    assert cfg.trade_amount_max == 250.0
    assert cfg.risk_pct == pytest.approx(0.015)
    assert cfg.max_drawdown_pct == pytest.approx(0.2)
    assert cfg.mt4_host == "10.0.0.2"
    assert cfg.mt4_port == 6000
    assert cfg.symbols == ["EURUSD", "GBPUSD", "AUDUSD"]


def test_app_config_rejects_invalid_broker():
    with pytest.raises(Exception):
        AppConfig(broker="LIVE")

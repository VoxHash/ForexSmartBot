"""Paper / sandbox venue paths: orders, positions, reconnect (no live funds)."""

from __future__ import annotations

import hashlib
import hmac
from unittest.mock import MagicMock, patch

import pytest

from forexsmartbot.adapters.brokers import (
    BinanceSandboxBroker,
    PaperBroker,
    VenuePaperBroker,
)
from forexsmartbot.adapters.brokers.binance_sandbox_broker import _hmac_sha256


def test_paper_broker_reconnect_preserves_ledger():
    broker = PaperBroker(5_000.0)
    assert broker.connect()
    broker.update_position("EURUSD", 1, 1.0, 1.10, 1.11)
    assert "EURUSD" in broker.get_positions()
    assert broker.reconnect()
    assert broker.is_connected()
    assert "EURUSD" in broker.get_positions()
    assert broker.get_balance() == 5_000.0


def test_hmac_sha256_matches_binance_doc_example():
    # Documented illustrative keys from Binance Spot API signing examples.
    secret = "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j"
    payload = (
        "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&"
        "price=0.1&recvWindow=5000&timestamp=1499827319559"
    )
    expected = hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    assert _hmac_sha256(secret, payload) == expected


def test_binance_sandbox_refuses_mainnet_url():
    with pytest.raises(ValueError, match="mainnet|refuses"):
        BinanceSandboxBroker(
            api_key="k",
            api_secret="s",
            base_url="https://api.binance.com/api",
        )


def test_binance_sandbox_connect_requires_keys(monkeypatch):
    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_API_SECRET", raising=False)
    broker = BinanceSandboxBroker(api_key="", api_secret="")
    assert broker.connect() is False


def test_binance_sandbox_signed_order_and_reconnect():
    broker = BinanceSandboxBroker(
        api_key="test-key",
        api_secret="test-secret",
        base_url="https://testnet.binance.vision/api",
    )

    account_payload = {
        "balances": [
            {"asset": "USDT", "free": "10000.0", "locked": "0.0"},
            {"asset": "BTC", "free": "0.0", "locked": "0.0"},
        ]
    }
    order_payload = {
        "orderId": 42,
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
            assert (params or {}).get("side") in ("BUY", "SELL")
            return order_payload
        return None

    with patch.object(broker, "_request", side_effect=fake_request):
        assert broker.connect()
        assert broker.get_balance() == 10000.0
        order_id = broker.submit_order("BTCUSDT", 1, 0.001)
        assert order_id == "42"
        positions = broker.get_positions()
        assert "BTCUSDT" in positions
        assert positions["BTCUSDT"].quantity == pytest.approx(0.001)
        assert broker.close_all("BTCUSDT")
        assert broker.get_positions() == {}

    with patch.object(broker, "_request", side_effect=fake_request):
        assert broker.reconnect()
        assert broker.is_connected()


def test_venue_paper_order_position_reconnect():
    feed = MagicMock()
    feed.connect.return_value = True
    feed.is_connected.return_value = True
    feed.get_price.return_value = 1.0850
    feed.disconnect.return_value = None

    with patch.object(VenuePaperBroker, "_build_feed", return_value=feed):
        broker = VenuePaperBroker(10_000.0, feed="binance")
        assert broker.connect()
        order_id = broker.submit_order("EURUSD", 1, 1_000.0)
        assert order_id and order_id.startswith("VPAPER_binance_")
        positions = broker.get_positions()
        assert "EURUSD" in positions
        assert positions["EURUSD"].entry_price == pytest.approx(1.0850)
        equity_before = broker.get_equity()
        feed.get_price.return_value = 1.0900
        equity_after = broker.get_equity()
        assert equity_after > equity_before
        assert broker.reconnect()
        assert "EURUSD" in broker.get_positions()
        assert broker.close_all("EURUSD")
        assert broker.get_positions() == {}


@pytest.mark.network
def test_venue_paper_live_binance_feed():
    broker = VenuePaperBroker(10_000.0, feed="binance")
    if not broker.connect():
        pytest.skip("Binance testnet unreachable")
    price = broker.get_price("BTCUSDT")
    if price is None:
        pytest.skip("BTCUSDT ticker unavailable on testnet")
    assert price > 0
    order_id = broker.submit_order("BTCUSDT", 1, 0.001)
    assert order_id is not None
    assert "BTCUSDT" in broker.get_positions()
    assert broker.reconnect()
    assert broker.close_all("BTCUSDT")
    broker.disconnect()

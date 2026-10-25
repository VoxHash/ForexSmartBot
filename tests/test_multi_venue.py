"""Multi-venue research registry, secret redaction, and public adapters."""

from __future__ import annotations

import pytest

from forexsmartbot.adapters.brokers import BinancePublicBroker, KrakenPublicBroker
from forexsmartbot.venues import (
    get_venue,
    list_venues,
    mask_secret,
    probe_all_public,
    probe_binance_spot,
    probe_kraken_futures,
    probe_kraken_spot,
    redact_mapping,
)
from forexsmartbot.venues.registry import classify_pair
from forexsmartbot.venues.models import AssetClass


def test_venue_registry_covers_cex_and_dex():
    venues = list_venues()
    ids = {v.id for v in venues}
    assert {"kraken_spot", "kraken_futures", "binance_spot", "oneinch"} <= ids
    kraken = get_venue("kraken_spot")
    assert "api.kraken.com" in kraken.endpoints.rest_public
    binance = get_venue("binance_spot")
    assert binance.endpoints.rest_sandbox and "testnet.binance.vision" in binance.endpoints.rest_sandbox


def test_classify_pair_heuristics():
    assert classify_pair("ZEUR", "ZUSD") == AssetClass.FX
    assert classify_pair("XAU", "USD", "PF_XAUUSD") == AssetClass.COMMODITY
    assert classify_pair("XBT", "USD", "PF_XBTUSD") == AssetClass.PERP_FUTURES


def test_secret_redaction():
    assert mask_secret("abcdefghijklmnop").startswith("abcd")
    assert "*" in mask_secret("abcdefghijklmnop")
    redacted = redact_mapping(
        {"api_key": "super-secret-key-value", "symbol": "EURUSD", "note": "Bearer tokensecret123"}
    )
    assert redacted["symbol"] == "EURUSD"
    assert "super-secret" not in str(redacted["api_key"])
    assert "tokensecret123" not in redacted["note"]


@pytest.mark.network
def test_live_kraken_spot_probe():
    report = probe_kraken_spot()
    if not report.ok:
        pytest.skip(f"Kraken spot unreachable: {report.error}")
    assert report.symbol_count > 100
    assert report.by_asset_class.get("spot_crypto", 0) > 0


@pytest.mark.network
def test_live_kraken_futures_probe():
    report = probe_kraken_futures()
    if not report.ok:
        pytest.skip(f"Kraken futures unreachable: {report.error}")
    assert report.symbol_count > 10
    # Live catalog includes FX / commodity underlyings among perps.
    assert sum(report.by_asset_class.values()) == report.symbol_count


@pytest.mark.network
def test_live_binance_testnet_probe():
    report = probe_binance_spot(sandbox=True)
    if not report.ok:
        pytest.skip(f"Binance testnet unreachable: {report.error}")
    assert report.symbol_count > 10


@pytest.mark.network
def test_probe_all_public_bundle():
    reports = probe_all_public()
    assert len(reports) == 3
    assert any(r.ok for r in reports)


@pytest.mark.network
def test_kraken_public_broker_price():
    broker = KrakenPublicBroker()
    if not broker.connect():
        pytest.skip("Kraken public Time unreachable")
    price = broker.get_price("EURUSD")
    assert price is not None and price > 0
    assert broker.submit_order("EURUSD", 1, 1.0) is None
    broker.disconnect()


@pytest.mark.network
def test_binance_public_broker_price():
    broker = BinancePublicBroker(sandbox=True)
    if not broker.connect():
        pytest.skip("Binance testnet ping unreachable")
    price = broker.get_price("BTCUSDT")
    assert price is not None and price > 0
    assert broker.submit_order("BTCUSDT", 1, 0.001) is None
    broker.disconnect()

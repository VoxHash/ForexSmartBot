"""Q2 2027: companion API + strategy health web dashboard."""

from __future__ import annotations

from forexsmartbot.cloud.companion_api import CompanionAPI, WebhookNotifier
from forexsmartbot.cloud.remote_monitor import RemoteMonitorServer
from forexsmartbot.monitoring.strategy_monitor import StrategyMonitor


class TestWebhookNotifier:
    def test_rejects_plain_http_non_loopback(self):
        n = WebhookNotifier()
        assert not n.register("http://example.com/hook")
        assert n.register("https://example.com/hook")
        assert n.register("http://127.0.0.1:9999/hook")
        assert "https://example.com/hook" in n.list_endpoints()

    def test_unregister(self):
        n = WebhookNotifier()
        n.register("https://hooks.example/a")
        assert n.unregister("https://hooks.example/a")
        assert n.list_endpoints() == []


class TestCompanionAPI:
    def test_health_public_and_portfolio_auth(self):
        api = CompanionAPI(
            api_key="companion-test-key16",
            require_api_key=True,
            portfolio_provider=lambda: {
                "balance": 10000.0,
                "equity": 10150.5,
                "positions": [{"symbol": "EURUSD", "side": "Long", "entry_price": 1.1, "current_price": 1.105, "pnl": 50}],
                "trades": [{"id": 1}],
                "status": "connected",
                "last_update": "2026-10-24T12:00:00",
            },
            alerts_provider=lambda: [{"level": "info", "message": "hi"}],
            strategies_provider=lambda: {
                "strategies": {"SMA_Crossover": {"status": "healthy", "signal_count": 3}}
            },
        )
        client = api.app.test_client()
        health = client.get("/api/v1/companion/health").get_json()
        assert health["service"] == "companion"
        assert health["read_only"] is True
        assert health["features"]["control"] is False

        assert client.get("/api/v1/companion/portfolio").status_code == 401
        ok = client.get(
            "/api/v1/companion/portfolio",
            headers={"Authorization": "Bearer companion-test-key16"},
        )
        assert ok.status_code == 200
        body = ok.get_json()
        assert body["balance"] == 10000.0
        assert body["positions_count"] == 1
        assert body["read_only"] is True

        alerts = client.get(
            "/api/v1/companion/alerts",
            headers={"X-API-Key": "companion-test-key16"},
        ).get_json()
        assert alerts["count"] == 1

        strategies = client.get(
            "/api/v1/companion/strategies",
            headers={"X-API-Key": "companion-test-key16"},
        ).get_json()
        assert "SMA_Crossover" in strategies["strategies"]

    def test_webhook_register_https(self):
        api = CompanionAPI(api_key="companion-test-key16", require_api_key=True)
        client = api.app.test_client()
        bad = client.post(
            "/api/v1/companion/devices/webhook",
            headers={"X-API-Key": "companion-test-key16"},
            json={"url": "http://evil.example/x"},
        )
        assert bad.status_code == 400
        good = client.post(
            "/api/v1/companion/devices/webhook",
            headers={"X-API-Key": "companion-test-key16"},
            json={"url": "https://notify.example/fsb"},
        )
        assert good.status_code == 201
        assert "https://notify.example/fsb" in good.get_json()["endpoints"]

    def test_control_disabled_by_default(self):
        api = CompanionAPI(api_key="companion-test-key16", require_api_key=True)
        client = api.app.test_client()
        assert (
            client.post(
                "/api/v1/companion/control/start",
                headers={"X-API-Key": "companion-test-key16"},
            ).status_code
            == 404
        )


class TestStrategyHealthDashboard:
    def test_strategies_endpoint_with_monitor(self):
        sm = StrategyMonitor()
        sm.register_strategy("SMA_Crossover")
        sm.record_signal("SMA_Crossover", execution_time=1.5)
        sm.record_signal("RSI_Reversion", execution_time=2.0)

        monitor = RemoteMonitorServer(
            host="127.0.0.1",
            port=18081,
            api_key="monitor-test-key-16",
            require_api_key=True,
            strategy_monitor=sm,
        )
        client = monitor.app.test_client()

        resp = client.get(
            "/api/v1/strategies",
            headers={"Authorization": "Bearer monitor-test-key-16"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["summary"]["total"] == 2
        assert data["strategies"]["SMA_Crossover"]["status"] in {
            "healthy",
            "unknown",
            "warning",
            "critical",
        }
        assert data["strategies"]["SMA_Crossover"]["signal_count"] == 1

        one = client.get(
            "/api/v1/strategies/SMA_Crossover",
            headers={"X-API-Key": "monitor-test-key-16"},
        )
        assert one.status_code == 200
        assert one.get_json()["strategy"]["strategy_name"] == "SMA_Crossover"

        missing = client.get(
            "/api/v1/strategies/NoSuch",
            headers={"X-API-Key": "monitor-test-key-16"},
        )
        assert missing.status_code == 404

    def test_companion_mounted_on_remote_monitor(self):
        sm = StrategyMonitor()
        sm.record_signal("Breakout", execution_time=0.5)
        monitor = RemoteMonitorServer(
            host="127.0.0.1",
            port=18082,
            api_key="monitor-test-key-16",
            require_api_key=True,
            strategy_monitor=sm,
        )
        monitor.update_trading_data(
            {
                "balance": 5000.0,
                "equity": 5100.0,
                "positions": [{"symbol": "GBPUSD", "side": "Short", "entry_price": 1.25, "current_price": 1.24, "pnl": 10}],
                "status": "connected",
            }
        )
        client = monitor.app.test_client()
        health = client.get("/api/v1/companion/health").get_json()
        assert health["service"] == "companion"

        portfolio = client.get(
            "/api/v1/companion/portfolio",
            headers={"Authorization": "Bearer monitor-test-key-16"},
        ).get_json()
        assert portfolio["equity"] == 5100.0
        assert portfolio["positions_count"] == 1

        strategies = client.get(
            "/api/v1/companion/strategies",
            headers={"Authorization": "Bearer monitor-test-key-16"},
        ).get_json()
        assert "Breakout" in strategies["strategies"]

    def test_dashboard_html_mentions_strategy_health(self):
        monitor = RemoteMonitorServer(
            host="127.0.0.1",
            port=18083,
            api_key="monitor-test-key-16",
            require_api_key=True,
        )
        html = monitor.app.test_client().get("/").data.decode("utf-8")
        assert "Strategy Health" in html
        assert "/api/v1/strategies" in html
        assert "/api/v1/companion" in html

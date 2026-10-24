"""Tests for remote monitoring / cloud sync hardening (3.2.5)."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from forexsmartbot.cloud.auth_utils import (
    constant_time_equals,
    extract_bearer_or_api_key,
    generate_api_token,
    is_insecure_secret,
    package_version,
)
from forexsmartbot.cloud.cloud_sync import CloudSyncManager
from forexsmartbot.cloud.error_handler import compute_backoff_delay, retry_call
from forexsmartbot.cloud.remote_monitor import RemoteMonitorServer
from forexsmartbot.cloud.security import RateLimiter, SecurityManager


class TestAuthUtils:
    def test_package_version_nonzero(self):
        assert package_version()

    def test_insecure_secrets(self):
        assert is_insecure_secret("")
        assert is_insecure_secret("default-secret-key-change-in-production")
        assert is_insecure_secret("short")
        assert not is_insecure_secret(generate_api_token())

    def test_extract_bearer_and_api_key(self):
        assert extract_bearer_or_api_key("Bearer abc", "") == "abc"
        assert extract_bearer_or_api_key("", "xyz") == "xyz"
        assert extract_bearer_or_api_key("", "") is None

    def test_constant_time_equals(self):
        assert constant_time_equals("same", "same")
        assert not constant_time_equals("a", "b")
        assert not constant_time_equals(None, "x")


class TestSecurityManager:
    def test_jwt_roundtrip(self):
        mgr = SecurityManager(secret_key="unit-test-secret-key-32chars-ok!!")
        token = mgr.generate_token("user-1", permissions=["read"])
        payload = mgr.verify_token(token)
        assert payload is not None
        assert payload["user_id"] == "user-1"
        assert "read" in payload["permissions"]
        assert "jti" in payload

    def test_invalid_token(self):
        mgr = SecurityManager(secret_key="unit-test-secret-key-32chars-ok!!")
        assert mgr.verify_token("not-a-token") is None

    def test_password_pbkdf2_roundtrip(self):
        mgr = SecurityManager(secret_key="unit-test-secret-key-32chars-ok!!")
        hashed = mgr.hash_password("s3cret!")
        assert mgr.verify_password("s3cret!", hashed)
        assert not mgr.verify_password("wrong", hashed)

    def test_api_key_verify(self):
        mgr = SecurityManager(secret_key="unit-test-secret-key-32chars-ok!!")
        key = mgr.generate_api_key("alice")
        assert mgr.verify_api_key(key, key)
        assert not mgr.verify_api_key(key, key + "x")


class TestRateLimiter:
    def test_limit_exceeded(self):
        limiter = RateLimiter()
        assert limiter.check_rate_limit("ip", max_requests=2, time_window=60)
        assert limiter.check_rate_limit("ip", max_requests=2, time_window=60)
        assert not limiter.check_rate_limit("ip", max_requests=2, time_window=60)
        assert limiter.get_remaining_requests("ip", 2, 60) == 0


class TestRetryBackoff:
    def test_backoff_grows(self):
        d0 = compute_backoff_delay(0, base_delay=1.0, jitter=False)
        d2 = compute_backoff_delay(2, base_delay=1.0, jitter=False)
        assert d0 == 1.0
        assert d2 == 4.0

    def test_retry_call_succeeds_after_failures(self):
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise requests.exceptions.ConnectionError("boom")
            return "ok"

        assert retry_call(flaky, max_retries=3, base_delay=0.01) == "ok"
        assert calls["n"] == 3


class TestCloudSync:
    def test_status_without_key(self):
        sync = CloudSyncManager(api_key="", api_endpoint="http://127.0.0.1:9")
        status = sync.get_sync_status()
        assert status["api_key_configured"] is False
        assert status["sync_enabled"] is False
        assert sync.sync_settings({"a": 1}) is False

    def test_sync_settings_success_with_retry(self):
        sync = CloudSyncManager(
            api_key="test-api-key-16chars",
            api_endpoint="http://example.test",
            max_retries=2,
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"

        with patch.object(sync, "_request", return_value=mock_resp) as req:
            assert sync.sync_settings({"risk_pct": 1.0}) is True
            req.assert_called_once()
            assert sync.last_sync_time is not None
            assert sync.consecutive_failures == 0

    def test_pending_queue_on_failure(self):
        sync = CloudSyncManager(
            api_key="test-api-key-16chars",
            api_endpoint="http://example.test",
            max_retries=1,
        )

        def boom(*_a, **_k):
            raise requests.exceptions.ConnectionError("down")

        with patch.object(sync, "_request", side_effect=boom):
            assert sync.sync_portfolio({"equity": 1000}) is False
        assert sync.consecutive_failures >= 1
        assert sync.get_sync_status()["pending_count"] >= 1

    def test_auto_sync_start_stop(self):
        sync = CloudSyncManager(api_key="test-api-key-16chars")
        sync.enable_auto_sync(interval_seconds=30)
        assert sync.get_sync_status()["auto_sync_enabled"] is True
        sync.disable_auto_sync()
        time.sleep(0.05)
        # Thread may finish join; flag cleared
        assert sync._auto_sync_thread is None


class TestRemoteMonitor:
    @pytest.fixture
    def monitor(self):
        return RemoteMonitorServer(
            host="127.0.0.1",
            port=18080,
            api_key="monitor-test-key-16",
            require_api_key=True,
        )

    def test_health_public(self, monitor):
        client = monitor.app.test_client()
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["service"] == "remote_monitor"
        assert body["auth_required"] is True
        assert "version" in body

    def test_status_requires_auth(self, monitor):
        client = monitor.app.test_client()
        assert client.get("/api/v1/status").status_code == 401
        ok = client.get(
            "/api/v1/status",
            headers={"Authorization": "Bearer monitor-test-key-16"},
        )
        assert ok.status_code == 200

    def test_x_api_key_header(self, monitor):
        client = monitor.app.test_client()
        ok = client.get(
            "/api/v1/positions",
            headers={"X-API-Key": "monitor-test-key-16"},
        )
        assert ok.status_code == 200

    def test_alerts_ring_buffer(self, monitor):
        monitor.push_alert("info", "hello", {"n": 1})
        client = monitor.app.test_client()
        resp = client.get(
            "/api/v1/alerts",
            headers={"Authorization": "Bearer monitor-test-key-16"},
        )
        assert resp.status_code == 200
        alerts = resp.get_json()["alerts"]
        assert alerts[0]["message"] == "hello"

    def test_control_callbacks(self, monitor):
        called = {"start": False}

        def start():
            called["start"] = True
            return True

        monitor.register_control_callback("start_trading", start)
        client = monitor.app.test_client()
        resp = client.post(
            "/api/v1/control/start",
            headers={"X-API-Key": "monitor-test-key-16"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
        assert called["start"] is True

    def test_update_trading_data(self, monitor):
        monitor.update_trading_data(
            {"balance": 1234.5, "equity": 1200.0, "status": "connected"}
        )
        client = monitor.app.test_client()
        resp = client.get(
            "/api/v1/status",
            headers={"Authorization": "Bearer monitor-test-key-16"},
        )
        data = resp.get_json()
        assert data["balance"] == 1234.5
        assert data["status"] == "connected"
        assert data["last_update"] is not None

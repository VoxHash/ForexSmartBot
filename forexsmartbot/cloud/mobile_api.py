"""
Mobile companion helpers.

Prefer :class:`forexsmartbot.cloud.companion_api.CompanionAPI` for new code.
This module keeps a thin compatibility layer and optional FCM push support.
"""

from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
from flask import Flask

from .companion_api import CompanionAPI, WebhookNotifier

load_dotenv(override=False)

logger = logging.getLogger(__name__)


class MobileAppAPI(CompanionAPI):
    """
    Backward-compatible mobile API wrapper.

    Defaults to **read-only** companion endpoints. Pass ``allow_control=True``
    only when high-level start/stop from a trusted device is intentional.
    Legacy ``/api/v1/mobile/*`` routes are not registered; use
    ``/api/v1/companion/*`` (also mounted by RemoteMonitorServer).
    """

    def __init__(self, app: Flask = None, **kwargs):
        kwargs.setdefault("allow_control", False)
        kwargs.setdefault("url_prefix", "/api/v1/companion")
        super().__init__(app=app, **kwargs)
        self.push_notification_service: Optional[PushNotificationService] = None
        self.trading_controller = None
        self.broker = None

    def set_trading_controller(self, controller):
        """Set trading controller reference (optional control path)."""
        self.trading_controller = controller

        def start():
            if hasattr(controller, "start"):
                controller.start()
                return True
            return False

        def stop():
            if hasattr(controller, "stop"):
                controller.stop()
                return True
            return False

        self.register_control_callback("start_trading", start)
        self.register_control_callback("stop_trading", stop)

    def set_broker(self, broker):
        """Bind a live broker as the portfolio provider."""
        self.broker = broker

        def portfolio():
            if not broker:
                return {}
            positions = []
            try:
                raw = broker.get_positions() or {}
                for symbol, pos in raw.items():
                    positions.append(
                        {
                            "symbol": getattr(pos, "symbol", symbol),
                            "side": "Long" if getattr(pos, "side", 0) > 0 else "Short",
                            "quantity": getattr(pos, "quantity", 0),
                            "entry_price": getattr(pos, "entry_price", 0),
                            "current_price": getattr(pos, "current_price", 0),
                            "pnl": getattr(pos, "pnl", 0),
                            "stop_loss": getattr(pos, "stop_loss", None),
                            "take_profit": getattr(pos, "take_profit", None),
                        }
                    )
            except Exception as exc:
                logger.warning("Broker positions failed: %s", exc)
            balance = 0.0
            equity = 0.0
            try:
                balance = float(broker.get_balance())
                equity = (
                    float(broker.get_equity())
                    if hasattr(broker, "get_equity")
                    else balance
                )
            except Exception as exc:
                logger.warning("Broker balance failed: %s", exc)
            status = "disconnected"
            try:
                status = "connected" if broker.is_connected() else "disconnected"
            except Exception:
                pass
            return {
                "balance": balance,
                "equity": equity,
                "positions": positions,
                "trades": [],
                "status": status,
            }

        self.set_portfolio_provider(portfolio)


class PushNotificationService:
    """
    Optional FCM push (requires Google infrastructure).

    For GrapheneOS / de-Googled devices prefer :class:`WebhookNotifier`.
    """

    def __init__(self, fcm_server_key: Optional[str] = None):
        self.fcm_server_key = fcm_server_key or os.getenv("FCM_SERVER_KEY", "")
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.device_tokens: List[str] = []
        self.webhook_notifier = WebhookNotifier()

    def register_device(self, token: str):
        if token and token not in self.device_tokens:
            self.device_tokens.append(token)

    def unregister_device(self, token: str):
        if token in self.device_tokens:
            self.device_tokens.remove(token)

    def register_webhook(self, url: str) -> bool:
        """GrapheneOS-friendly alert delivery (no FCM)."""
        return self.webhook_notifier.register(url)

    def send_notification(self, title: str, body: str, data: Optional[Dict] = None):
        webhook_ok = self.webhook_notifier.notify(title, body, data)
        if not self.fcm_server_key or not self.device_tokens:
            return webhook_ok > 0

        try:
            for token in self.device_tokens:
                payload = {
                    "to": token,
                    "notification": {
                        "title": title,
                        "body": body,
                        "sound": "default",
                    },
                    "data": data or {},
                }
                headers = {
                    "Authorization": f"key={self.fcm_server_key}",
                    "Content-Type": "application/json",
                }
                response = requests.post(
                    self.fcm_url, json=payload, headers=headers, timeout=5
                )
                if response.status_code != 200:
                    logger.warning("FCM failed: %s", response.status_code)
            return True
        except Exception as exc:
            logger.warning("FCM error: %s", exc)
            return webhook_ok > 0

    def send_trade_alert(
        self, trade_type: str, symbol: str, price: float, pnl: Optional[float] = None
    ):
        title = f"Trade {trade_type}: {symbol}"
        body = f"Price: {price:.4f}"
        if pnl is not None:
            body += f", PnL: ${pnl:.2f}"
        data = {"type": "trade", "symbol": symbol, "price": price, "pnl": pnl}
        return self.send_notification(title, body, data)

    def send_alert(self, alert_type: str, message: str):
        return self.send_notification(
            f"Alert: {alert_type}",
            message,
            {"type": "alert", "alert_type": alert_type, "message": message},
        )

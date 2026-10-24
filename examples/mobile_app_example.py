"""
Example: Mobile companion (read-only) + optional webhook alerts.

Prefer CompanionAPI / RemoteMonitorServer companion routes for GrapheneOS.
FCM remains optional and Google-dependent.
"""

from __future__ import annotations

import os

from flask import Flask

from forexsmartbot.cloud.auth_utils import generate_api_token
from forexsmartbot.cloud.mobile_api import MobileAppAPI, PushNotificationService


def main() -> None:
    app = Flask(__name__)
    api_key = os.getenv("API_KEY") or generate_api_token()

    mobile = MobileAppAPI(
        app=app,
        api_key=api_key,
        require_api_key=True,
        allow_control=False,
        portfolio_provider=lambda: {
            "balance": 10000.0,
            "equity": 10000.0,
            "positions": [],
            "trades": [],
            "status": "connected",
        },
    )

    push = PushNotificationService(fcm_server_key=os.getenv("FCM_SERVER_KEY", ""))
    mobile.push_notification_service = push

    # GrapheneOS path: HTTPS webhook instead of FCM device tokens
    webhook = os.getenv("COMPANION_WEBHOOK_URL", "")
    if webhook:
        push.register_webhook(webhook)

    print("Companion health: GET /api/v1/companion/health")
    print("Companion portfolio (auth): GET /api/v1/companion/portfolio")
    print(f"API key: {api_key}")
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()

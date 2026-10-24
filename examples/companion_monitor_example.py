"""
Q2 companion + strategy health dashboard example.

Starts RemoteMonitorServer with a live StrategyMonitor, feeds portfolio
snapshots, and prints companion endpoints for phone / webhook clients.
"""

from __future__ import annotations

import os
import time

from forexsmartbot.cloud.auth_utils import generate_api_token
from forexsmartbot.cloud.remote_monitor import RemoteMonitorServer
from forexsmartbot.monitoring.strategy_monitor import StrategyMonitor


def main() -> None:
    api_key = os.getenv("API_KEY") or generate_api_token()
    strategies = StrategyMonitor()
    strategies.register_strategy("SMA_Crossover")
    strategies.register_strategy("RSI_Reversion")
    strategies.record_signal("SMA_Crossover", execution_time=1.2)

    monitor = RemoteMonitorServer(
        host="127.0.0.1",
        port=int(os.getenv("REMOTE_MONITOR_PORT", "8080")),
        api_key=api_key,
        strategy_monitor=strategies,
        enable_companion=True,
    )
    monitor.register_control_callback("start_trading", lambda: True)
    monitor.register_control_callback("stop_trading", lambda: True)
    monitor.start()

    print(f"Dashboard:  http://127.0.0.1:{monitor.port}/")
    print(f"Health:     http://127.0.0.1:{monitor.port}/api/v1/health")
    print(f"Strategies: curl -H 'Authorization: Bearer {api_key}' http://127.0.0.1:{monitor.port}/api/v1/strategies")
    print(f"History:    curl -H 'Authorization: Bearer {api_key}' http://127.0.0.1:{monitor.port}/api/v1/strategies/history")
    print(f"Companion:  curl -H 'X-API-Key: {api_key}' http://127.0.0.1:{monitor.port}/api/v1/companion/portfolio")
    print(f"Pairing:    curl -X POST -H 'X-API-Key: {api_key}' http://127.0.0.1:{monitor.port}/api/v1/companion/pairing/session")
    print("Android: mobile/android-companion 0.3.0 — live CameraX QR / gallery / paste; encrypted cache")
    if os.getenv("FSB_COMPANION_CERT_PIN"):
        print("Cert pin:  FSB_COMPANION_CERT_PIN is set (included in pairing QR)")

    try:
        n = 0
        while True:
            n += 1
            if n % 5 == 0:
                strategies.record_signal("RSI_Reversion", execution_time=0.8)
            monitor.update_trading_data(
                {
                    "balance": 10000.0 + n,
                    "equity": 10050.0 + n,
                    "positions": [
                        {
                            "symbol": "EURUSD",
                            "side": "Long",
                            "entry_price": 1.1000,
                            "current_price": 1.1000 + (n * 0.0001),
                            "pnl": n * 0.5,
                        }
                    ],
                    "trades": [],
                    "status": "connected",
                }
            )
            time.sleep(2)
    except KeyboardInterrupt:
        monitor.stop()


if __name__ == "__main__":
    main()

"""Twelve Data provider implementation for forex market data."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests

from ...core.interfaces import IDataProvider


class TwelveDataProvider(IDataProvider):
    """Twelve Data provider for historical candles and latest price."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self._available = bool(api_key)

    def _to_twelve_symbol(self, symbol: str) -> str:
        raw = symbol.replace("=X", "").replace("/", "").upper()
        if len(raw) != 6:
            raise ValueError(f"Unsupported forex symbol format: {symbol}")
        return f"{raw[:3]}/{raw[3:]}"

    def _map_interval(self, interval: str) -> str:
        mapping = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1h": "1h",
            "4h": "4h",
            "1d": "1day",
        }
        return mapping.get(interval, "1h")

    def get_data(self, symbol: str, start: str, end: str, interval: str = "1h") -> pd.DataFrame:
        if not self._available:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

        try:
            td_symbol = self._to_twelve_symbol(symbol)
            params = {
                "symbol": td_symbol,
                "interval": self._map_interval(interval),
                "start_date": pd.to_datetime(start).strftime("%Y-%m-%d %H:%M:%S"),
                "end_date": pd.to_datetime(end).strftime("%Y-%m-%d %H:%M:%S"),
                "apikey": self.api_key,
                "outputsize": 5000,
            }
            response = requests.get(f"{self.base_url}/time_series", params=params, timeout=20)
            data = response.json()

            if "values" not in data:
                return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

            rows = data["values"]
            if not rows:
                return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

            df = pd.DataFrame(rows)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime").sort_index()
            df = df.rename(
                columns={
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume",
                }
            )
            for col in ["Open", "High", "Low", "Close", "Volume"]:
                if col not in df.columns:
                    df[col] = 0.0 if col == "Volume" else pd.NA
            df[["Open", "High", "Low", "Close", "Volume"]] = df[
                ["Open", "High", "Low", "Close", "Volume"]
            ].apply(pd.to_numeric, errors="coerce")
            df = df.dropna(subset=["Open", "High", "Low", "Close"])
            return df[["Open", "High", "Low", "Close", "Volume"]]
        except Exception:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    def get_latest_price(self, symbol: str) -> Optional[float]:
        if not self._available:
            return None
        try:
            td_symbol = self._to_twelve_symbol(symbol)
            params = {"symbol": td_symbol, "apikey": self.api_key}
            response = requests.get(f"{self.base_url}/price", params=params, timeout=10)
            data = response.json()
            if "price" in data:
                return float(data["price"])
            return None
        except Exception:
            return None

    def get_historical_data(self, symbol: str, period: str = "1d", interval: str = "1h") -> pd.DataFrame:
        now = datetime.now()
        period_map = {
            "1d": timedelta(days=1),
            "5d": timedelta(days=5),
            "1mo": timedelta(days=30),
            "3mo": timedelta(days=90),
            "6mo": timedelta(days=180),
            "1y": timedelta(days=365),
        }
        delta = period_map.get(period, timedelta(days=1))
        start = (now - delta).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
        return self.get_data(symbol, start, end, interval)

    def is_available(self) -> bool:
        return self._available

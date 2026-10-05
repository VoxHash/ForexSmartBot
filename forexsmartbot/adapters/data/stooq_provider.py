"""Stooq provider implementation (public CSV market data endpoint)."""

from __future__ import annotations

from datetime import datetime, timedelta
from io import StringIO
from typing import Optional

import pandas as pd
import requests

from ...core.interfaces import IDataProvider


class StooqProvider(IDataProvider):
    """Stooq provider for free forex data."""

    def __init__(self):
        self._available = True

    def _to_stooq_symbol(self, symbol: str) -> str:
        raw = symbol.replace("=X", "").replace("/", "").upper()
        if len(raw) != 6:
            raise ValueError(f"Unsupported forex symbol format: {symbol}")
        return raw.lower()

    def _map_interval(self, interval: str) -> str:
        mapping = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "30m": "30",
            "1h": "60",
            "4h": "240",
            "1d": "d",
        }
        return mapping.get(interval, "d")

    def get_data(self, symbol: str, start: str, end: str, interval: str = "1h") -> pd.DataFrame:
        try:
            s = self._to_stooq_symbol(symbol)
            i = self._map_interval(interval)
            # Stooq CSV endpoint
            url = f"https://stooq.com/q/d/l/?s={s}&i={i}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            csv_txt = response.text
            df = pd.read_csv(StringIO(csv_txt))
            if df.empty or "Date" not in df.columns:
                return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

            if "Time" in df.columns:
                df["datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"], errors="coerce")
            else:
                df["datetime"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.set_index("datetime").sort_index()
            df = df.rename(
                columns={
                    "Open": "Open",
                    "High": "High",
                    "Low": "Low",
                    "Close": "Close",
                    "Volume": "Volume",
                }
            )
            for col in ["Open", "High", "Low", "Close"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            if "Volume" not in df.columns:
                df["Volume"] = 0.0
            else:
                df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0.0)
            df = df.dropna(subset=["Open", "High", "Low", "Close"])

            start_dt = pd.to_datetime(start)
            end_dt = pd.to_datetime(end)
            df = df[(df.index >= start_dt) & (df.index <= end_dt)]
            return df[["Open", "High", "Low", "Close", "Volume"]]
        except Exception:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    def get_latest_price(self, symbol: str) -> Optional[float]:
        try:
            s = self._to_stooq_symbol(symbol)
            # Current quote endpoint
            url = f"https://stooq.com/q/l/?s={s}&f=sd2t2ohlcv&h&e=csv"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            df = pd.read_csv(StringIO(response.text))
            if df.empty or "Close" not in df.columns:
                return None
            price = pd.to_numeric(df["Close"].iloc[0], errors="coerce")
            if pd.isna(price):
                return None
            return float(price)
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

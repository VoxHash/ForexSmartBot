"""Fear Index strategy.

Composite macro-risk strategy that builds a normalized fear score from
volatility, momentum, and optional macro/news feature columns.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..core.interfaces import IStrategy


class FearIndexStrategy(IStrategy):
    """Regime-aware strategy using a composite fear score."""

    def __init__(
        self,
        lookback: int = 30,
        signal_smooth: int = 5,
        risk_on_threshold: float = -0.5,
        risk_off_threshold: float = 0.5,
        atr_period: int = 14,
        stop_atr_mult: float = 1.5,
        take_atr_mult: float = 2.5,
    ):
        self._lookback = int(lookback)
        self._signal_smooth = int(signal_smooth)
        self._risk_on_threshold = float(risk_on_threshold)
        self._risk_off_threshold = float(risk_off_threshold)
        self._atr_period = int(atr_period)
        self._stop_atr_mult = float(stop_atr_mult)
        self._take_atr_mult = float(take_atr_mult)
        self._name = "Fear Index"

    @property
    def name(self) -> str:
        return self._name

    @property
    def params(self) -> Dict[str, Any]:
        return {
            "lookback": self._lookback,
            "signal_smooth": self._signal_smooth,
            "risk_on_threshold": self._risk_on_threshold,
            "risk_off_threshold": self._risk_off_threshold,
            "atr_period": self._atr_period,
            "stop_atr_mult": self._stop_atr_mult,
            "take_atr_mult": self._take_atr_mult,
        }

    def set_params(self, **kwargs) -> None:
        if "lookback" in kwargs:
            self._lookback = max(5, int(kwargs["lookback"]))
        if "signal_smooth" in kwargs:
            self._signal_smooth = max(1, int(kwargs["signal_smooth"]))
        if "risk_on_threshold" in kwargs:
            self._risk_on_threshold = float(kwargs["risk_on_threshold"])
        if "risk_off_threshold" in kwargs:
            self._risk_off_threshold = float(kwargs["risk_off_threshold"])
        if "atr_period" in kwargs:
            self._atr_period = max(2, int(kwargs["atr_period"]))
        if "stop_atr_mult" in kwargs:
            self._stop_atr_mult = max(0.1, float(kwargs["stop_atr_mult"]))
        if "take_atr_mult" in kwargs:
            self._take_atr_mult = max(0.1, float(kwargs["take_atr_mult"]))

    def _zscore(self, series: pd.Series, window: int) -> pd.Series:
        mean = series.rolling(window).mean()
        std = series.rolling(window).std(ddof=0).replace(0, np.nan)
        return (series - mean) / std

    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if len(out) < max(self._lookback, self._atr_period) + 2:
            return out

        # Required price features
        out["ret_1"] = out["Close"].pct_change()
        out["ret_5"] = out["Close"].pct_change(5)
        out["vol_rolling"] = out["ret_1"].rolling(self._lookback).std(ddof=0)
        out["mom_abs"] = out["ret_5"].abs()

        # ATR
        tr = np.maximum(
            out["High"] - out["Low"],
            np.maximum(
                (out["High"] - out["Close"].shift(1)).abs(),
                (out["Low"] - out["Close"].shift(1)).abs(),
            ),
        )
        out["ATR"] = tr.rolling(self._atr_period).mean()

        # Optional macro/news columns if present
        # If not present, fallback to NaN then filled with price-derived proxies.
        out["feature_vix"] = out["VIX"] if "VIX" in out.columns else np.nan
        out["feature_fx_vol"] = out["FX_VOL"] if "FX_VOL" in out.columns else out["vol_rolling"]
        out["feature_dxy"] = out["DXY"] if "DXY" in out.columns else np.nan
        out["feature_news"] = out["NEWS_SENTIMENT"] if "NEWS_SENTIMENT" in out.columns else np.nan
        out["feature_policy"] = out["POLICY_RISK"] if "POLICY_RISK" in out.columns else np.nan

        # Fill missing optional features from local proxies
        out["feature_vix"] = out["feature_vix"].fillna(out["vol_rolling"] * 100.0)
        out["feature_dxy"] = out["feature_dxy"].fillna(out["ret_5"] * -100.0)
        out["feature_news"] = out["feature_news"].fillna(-out["ret_1"] * 50.0)
        out["feature_policy"] = out["feature_policy"].fillna(out["mom_abs"] * 100.0)

        # Z-normalized components
        z_vix = self._zscore(out["feature_vix"], self._lookback)
        z_fx_vol = self._zscore(out["feature_fx_vol"], self._lookback)
        z_dxy = self._zscore(out["feature_dxy"], self._lookback)
        z_news = self._zscore(out["feature_news"], self._lookback)
        z_policy = self._zscore(out["feature_policy"], self._lookback)

        # Weighted fear score (higher = more risk-off)
        out["FearScore_raw"] = (
            0.30 * z_vix
            + 0.25 * z_fx_vol
            + 0.15 * z_dxy
            + 0.20 * z_news
            + 0.10 * z_policy
        )
        out["FearScore"] = out["FearScore_raw"].rolling(self._signal_smooth).mean()

        return out

    def signal(self, df: pd.DataFrame) -> int:
        if len(df) < max(self._lookback, self._signal_smooth) + 2:
            return 0
        if "FearScore" not in df.columns:
            return 0

        score = df["FearScore"].iloc[-1]
        prev = df["FearScore"].iloc[-2]
        if pd.isna(score) or pd.isna(prev):
            return 0

        # Cross-based regime transitions
        if prev >= self._risk_on_threshold and score < self._risk_on_threshold:
            return 1
        if prev <= self._risk_off_threshold and score > self._risk_off_threshold:
            return -1
        return 0

    def volatility(self, df: pd.DataFrame) -> Optional[float]:
        if len(df) < self._lookback + 1:
            return None
        ret = df["Close"].pct_change().rolling(self._lookback).std(ddof=0).iloc[-1]
        if pd.isna(ret):
            return None
        return float(ret)

    def stop_loss(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        if "ATR" not in df.columns or len(df) == 0:
            return None
        atr = float(df["ATR"].iloc[-1])
        if pd.isna(atr) or atr <= 0:
            return None
        if side > 0:
            return entry_price - self._stop_atr_mult * atr
        return entry_price + self._stop_atr_mult * atr

    def take_profit(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        if "ATR" not in df.columns or len(df) == 0:
            return None
        atr = float(df["ATR"].iloc[-1])
        if pd.isna(atr) or atr <= 0:
            return None
        if side > 0:
            return entry_price + self._take_atr_mult * atr
        return entry_price - self._take_atr_mult * atr

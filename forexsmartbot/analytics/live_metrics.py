"""
Live portfolio and risk metrics for the analytics dashboard.

Pure computation (no Qt) so the snapshot can be unit-tested and reused by
dialogs, widgets, and remote monitors.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from ..core.interfaces import Trade
from .portfolio_analytics import PortfolioAnalytics
from .risk_analytics import RiskAnalytics


@dataclass
class LiveMetricsSnapshot:
    """Point-in-time analytics snapshot for UI and monitoring."""

    timestamp: datetime
    equity: float
    balance: float
    realized_pnl: float
    unrealized_pnl: float
    daily_pnl: float
    open_positions: int
    total_trades: int
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    current_drawdown: float
    var_95: float
    cvar_95: float
    volatility: float
    average_win: float
    average_loss: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for tables / JSON."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    def card_metrics(self) -> List[tuple]:
        """Primary KPI cards: (label, formatted value, tone)."""
        tone_pnl = "positive" if self.daily_pnl >= 0 else "negative"
        tone_eq = "positive" if self.unrealized_pnl + self.realized_pnl >= 0 else "negative"
        return [
            ("Equity", f"${self.equity:,.2f}", tone_eq),
            ("Daily P&L", f"${self.daily_pnl:,.2f}", tone_pnl),
            ("Win Rate", f"{self.win_rate:.1f}%", "neutral"),
            ("Sharpe", f"{self.sharpe_ratio:.3f}", "neutral"),
            ("Max DD", f"{self.max_drawdown_pct:.2f}%", "negative" if self.max_drawdown_pct else "neutral"),
            ("VaR 95%", f"{self.var_95:.4f}", "neutral"),
        ]


def _portfolio_trades(portfolio) -> List[Trade]:
    """Extract Trade list from Portfolio or trade sequence."""
    if portfolio is None:
        return []
    if hasattr(portfolio, "trades"):
        return list(portfolio.trades)
    if isinstance(portfolio, Sequence):
        return list(portfolio)
    return []


def _sync_portfolio_analytics(analytics: PortfolioAnalytics, portfolio) -> None:
    """Load trades and equity curve from a live Portfolio."""
    analytics.trades = _portfolio_trades(portfolio)
    analytics.equity_curve = []
    if portfolio is None:
        return
    timestamps = getattr(portfolio, "timestamps", None)
    equity_history = getattr(portfolio, "equity_history", None)
    if timestamps is not None and equity_history is not None:
        ts = list(timestamps)
        eq = list(equity_history)
        n = min(len(ts), len(eq))
        analytics.equity_curve = list(zip(ts[:n], eq[:n]))


def _sync_risk_analytics(risk: RiskAnalytics, portfolio) -> None:
    """Load trades into RiskAnalytics from a live Portfolio."""
    risk.trades = _portfolio_trades(portfolio)


def build_live_metrics(portfolio, *, now: Optional[datetime] = None) -> LiveMetricsSnapshot:
    """
    Build a live metrics snapshot from a Portfolio (or trade container).

    Uses Portfolio balance/equity when available; otherwise derives from trades.
    """
    now = now or datetime.now()
    portfolio_analytics = PortfolioAnalytics()
    risk_analytics = RiskAnalytics()
    _sync_portfolio_analytics(portfolio_analytics, portfolio)
    _sync_risk_analytics(risk_analytics, portfolio)

    summary = portfolio_analytics.get_performance_summary()
    max_dd = portfolio_analytics.calculate_max_drawdown()
    var_result = risk_analytics.calculate_var(confidence_level=0.95)
    cvar_result = risk_analytics.calculate_cvar(confidence_level=0.95)

    returns = risk_analytics._get_returns()
    volatility = float(returns.std()) if len(returns) >= 2 else 0.0

    if portfolio is not None and hasattr(portfolio, "get_total_equity"):
        equity = float(portfolio.get_total_equity())
        balance = float(portfolio.get_total_balance())
        realized = float(portfolio.get_realized_pnl())
        unrealized = float(portfolio.get_unrealized_pnl())
        daily = float(portfolio.get_daily_pnl())
        open_positions = len(getattr(portfolio, "positions", {}) or {})
        current_dd = float(portfolio.get_current_drawdown()) * 100.0
    else:
        equity = 10000.0 + float(summary.get("total_pnl", 0.0))
        balance = equity
        realized = float(summary.get("total_pnl", 0.0))
        unrealized = 0.0
        daily = realized
        open_positions = 0
        current_dd = float(max_dd.get("max_drawdown_pct", 0.0))

    profit_factor = summary.get("profit_factor", 0.0)
    if profit_factor == float("inf"):
        profit_factor = 0.0

    sortino = summary.get("sortino_ratio", 0.0)
    if sortino == float("inf"):
        sortino = 0.0

    return LiveMetricsSnapshot(
        timestamp=now,
        equity=equity,
        balance=balance,
        realized_pnl=realized,
        unrealized_pnl=unrealized,
        daily_pnl=daily,
        open_positions=open_positions,
        total_trades=int(summary.get("total_trades", 0)),
        win_rate=float(summary.get("win_rate", 0.0)),
        profit_factor=float(profit_factor),
        sharpe_ratio=float(summary.get("sharpe_ratio", 0.0)),
        sortino_ratio=float(sortino),
        max_drawdown=float(max_dd.get("max_drawdown", 0.0)),
        max_drawdown_pct=float(max_dd.get("max_drawdown_pct", 0.0)),
        current_drawdown=current_dd,
        var_95=float(var_result.get("var", 0.0)),
        cvar_95=float(cvar_result.get("cvar", 0.0)),
        volatility=volatility,
        average_win=float(summary.get("average_win", 0.0)),
        average_loss=float(summary.get("average_loss", 0.0)),
    )

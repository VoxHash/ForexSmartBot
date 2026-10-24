"""Tests for live analytics metrics snapshot."""

from datetime import datetime, timedelta

from forexsmartbot.analytics.live_metrics import LiveMetricsSnapshot, build_live_metrics
from forexsmartbot.analytics.portfolio_analytics import PortfolioAnalytics
from forexsmartbot.core.interfaces import Trade
from forexsmartbot.core.portfolio import Portfolio


def _make_trade(pnl: float, day_offset: int = 0, qty: float = 1.0, entry: float = 1.10) -> Trade:
    entry_time = datetime.now() - timedelta(days=2 + day_offset)
    exit_time = datetime.now() - timedelta(days=day_offset)
    return Trade(
        symbol="EURUSD",
        side=1,
        quantity=qty,
        entry_price=entry,
        exit_price=entry + (pnl / qty if qty else 0),
        pnl=pnl,
        strategy="SMA_Crossover",
        entry_time=entry_time,
        exit_time=exit_time,
    )


class TestLiveMetrics:
    def test_empty_portfolio_snapshot(self):
        portfolio = Portfolio(initial_balance=10000.0)
        snap = build_live_metrics(portfolio)
        assert isinstance(snap, LiveMetricsSnapshot)
        assert snap.equity == 10000.0
        assert snap.total_trades == 0
        assert snap.var_95 == 0.0
        assert len(snap.card_metrics()) == 6

    def test_snapshot_with_winning_and_losing_trades(self):
        portfolio = Portfolio(initial_balance=10000.0)
        portfolio.add_trade(_make_trade(50.0, day_offset=1))
        portfolio.add_trade(_make_trade(-20.0, day_offset=0))
        portfolio.update_equity(10030.0)

        snap = build_live_metrics(portfolio)
        assert snap.total_trades == 2
        assert snap.realized_pnl == 30.0
        assert snap.win_rate == 50.0
        assert snap.average_win == 50.0
        assert snap.average_loss == 20.0
        assert snap.equity == portfolio.get_total_equity()
        data = snap.to_dict()
        assert "timestamp" in data
        assert data["total_trades"] == 2

    def test_portfolio_analytics_loads_equity_from_portfolio(self):
        portfolio = Portfolio(initial_balance=10000.0)
        portfolio.add_trade(_make_trade(100.0))
        portfolio.update_equity(10100.0)
        analytics = PortfolioAnalytics()
        metrics = analytics.calculate_metrics(portfolio)
        assert metrics["total_trades"] == 1
        assert metrics["total_pnl"] == 100.0
        # Internal state restored after calculate_metrics
        assert analytics.trades == []

    def test_card_metrics_tone_for_negative_daily_pnl(self):
        portfolio = Portfolio(initial_balance=10000.0)
        portfolio.add_trade(_make_trade(-40.0, day_offset=0))
        snap = build_live_metrics(portfolio)
        cards = dict((label, (value, tone)) for label, value, tone in snap.card_metrics())
        assert cards["Daily P&L"][1] == "negative"

"""
Analytics module for ForexSmartBot v3.2.0
Provides portfolio analytics, risk analytics, and advanced charting features.
"""

from .portfolio_analytics import PortfolioAnalytics
from .risk_analytics import RiskAnalytics
from .chart_patterns import ChartPatternRecognizer
from .performance_attribution import PerformanceAttribution
from .live_metrics import LiveMetricsSnapshot, build_live_metrics

# Qt-backed widgets are optional (headless / test environments may lack PyQt6)
try:
    from .market_depth import MarketDepthWidget, MarketDepthProvider
    from .correlation_matrix import CorrelationMatrixWidget, CorrelationAnalyzer
    from .economic_calendar import EconomicCalendarWidget, EconomicCalendarProvider
    from .trade_journal import TradeJournalWidget, TradeJournalManager
except ImportError:  # pragma: no cover - UI optional
    MarketDepthWidget = None  # type: ignore[misc, assignment]
    MarketDepthProvider = None  # type: ignore[misc, assignment]
    CorrelationMatrixWidget = None  # type: ignore[misc, assignment]
    CorrelationAnalyzer = None  # type: ignore[misc, assignment]
    EconomicCalendarWidget = None  # type: ignore[misc, assignment]
    EconomicCalendarProvider = None  # type: ignore[misc, assignment]
    TradeJournalWidget = None  # type: ignore[misc, assignment]
    TradeJournalManager = None  # type: ignore[misc, assignment]

__all__ = [
    'PortfolioAnalytics',
    'RiskAnalytics',
    'ChartPatternRecognizer',
    'PerformanceAttribution',
    'MarketDepthWidget',
    'MarketDepthProvider',
    'CorrelationMatrixWidget',
    'CorrelationAnalyzer',
    'EconomicCalendarWidget',
    'EconomicCalendarProvider',
    'TradeJournalWidget',
    'TradeJournalManager',
    'LiveMetricsSnapshot',
    'build_live_metrics',
]

"""
Analytics module for ForexSmartBot v3.2.0
Provides portfolio analytics, risk analytics, and advanced charting features.
"""

from .portfolio_analytics import PortfolioAnalytics
from .risk_analytics import RiskAnalytics
from .chart_patterns import ChartPatternRecognizer
from .performance_attribution import PerformanceAttribution
from .market_depth import MarketDepthWidget, MarketDepthProvider
from .correlation_matrix import CorrelationMatrixWidget, CorrelationAnalyzer
from .economic_calendar import EconomicCalendarWidget, EconomicCalendarProvider
from .trade_journal import TradeJournalWidget, TradeJournalManager

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
]

"""Strategy plugins for ForexSmartBot."""

from .sma_crossover import SMACrossover
from .breakout_atr import BreakoutATR
from .rsi_reversion import RSIRevertion
from .ml_adaptive_supertrend import MLAdaptiveSuperTrend
from .adaptive_trend_flow import AdaptiveTrendFlow
from .mean_reversion import MeanReversion
from .momentum_breakout import MomentumBreakout
from .scalping_ma import ScalpingMA
from .news_trading import NewsTrading

# Strategy registry organized by risk level
STRATEGIES = {
    # Low Risk Strategies
    'Mean_Reversion': MeanReversion,
    'SMA_Crossover': SMACrossover,
    
    # Medium Risk Strategies
    'Scalping_MA': ScalpingMA,
    'RSI_Reversion': RSIRevertion,
    'BreakoutATR': BreakoutATR,
    
    # High Risk Strategies
    'Momentum_Breakout': MomentumBreakout,
    'News_Trading': NewsTrading,
    'ML_Adaptive_SuperTrend': MLAdaptiveSuperTrend,
    'Adaptive_Trend_Flow': AdaptiveTrendFlow,
}

# Risk level categorization
RISK_LEVELS = {
    'Low_Risk': ['Mean_Reversion', 'SMA_Crossover'],
    'Medium_Risk': ['Scalping_MA', 'RSI_Reversion', 'BreakoutATR'],
    'High_Risk': ['Momentum_Breakout', 'News_Trading', 'ML_Adaptive_SuperTrend', 'Adaptive_Trend_Flow']
}

def get_strategy(name: str, **params):
    """Get strategy instance by name."""
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}")
    return STRATEGIES[name](**params)

def list_strategies():
    """List available strategies."""
    return list(STRATEGIES.keys())

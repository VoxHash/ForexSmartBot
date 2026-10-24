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
from .fear_index import FearIndexStrategy

# New ML Strategies
# Use broad exception handling to catch DLL loading errors on Windows.
# FSB_SKIP_HEAVY_ML skips TensorFlow/torch-backed strategies (CI/CPU runners).
import os as _os

_SKIP_HEAVY_ML = _os.environ.get("FSB_SKIP_HEAVY_ML", "").strip().lower() in (
    "1",
    "true",
    "yes",
)

LSTM_AVAILABLE = False
LSTMStrategy = None
if not _SKIP_HEAVY_ML:
    try:
        from .lstm_strategy import LSTMStrategy
        LSTM_AVAILABLE = True
    except (ImportError, OSError, RuntimeError) as e:
        LSTMStrategy = None
        import warnings
        warnings.warn(f"LSTM strategy not available: {e}")

try:
    from .svm_strategy import SVMStrategy
    SVM_AVAILABLE = True
except (ImportError, OSError, RuntimeError) as e:
    SVM_AVAILABLE = False
    SVMStrategy = None
    import warnings
    warnings.warn(f"SVM strategy not available: {e}")

try:
    from .ensemble_ml_strategy import EnsembleMLStrategy
    ENSEMBLE_AVAILABLE = True
except (ImportError, OSError, RuntimeError) as e:
    ENSEMBLE_AVAILABLE = False
    EnsembleMLStrategy = None
    import warnings
    warnings.warn(f"Ensemble ML strategy not available: {e}")

TRANSFORMER_AVAILABLE = False
TransformerStrategy = None
if not _SKIP_HEAVY_ML:
    try:
        from .transformer_strategy import TransformerStrategy
        TRANSFORMER_AVAILABLE = True
    except (ImportError, OSError, RuntimeError) as e:
        TransformerStrategy = None
        import warnings
        warnings.warn(f"Transformer strategy not available: {e}")

try:
    from .rl_strategy import RLStrategy
    RL_AVAILABLE = True
except (ImportError, OSError, RuntimeError) as e:
    RL_AVAILABLE = False
    RLStrategy = None
    import warnings
    warnings.warn(f"RL strategy not available: {e}")

try:
    from .multi_timeframe_strategy import MultiTimeframeStrategy
    MULTI_TIMEFRAME_AVAILABLE = True
except (ImportError, OSError, RuntimeError) as e:
    MULTI_TIMEFRAME_AVAILABLE = False
    MultiTimeframeStrategy = None
    import warnings
    warnings.warn(f"Multi-timeframe strategy not available: {e}")

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
    'Fear_Index': FearIndexStrategy,
    'ML_Adaptive_SuperTrend': MLAdaptiveSuperTrend,
    'Adaptive_Trend_Flow': AdaptiveTrendFlow,
}

# Add ML strategies if available
if LSTM_AVAILABLE:
    STRATEGIES['LSTM_Strategy'] = LSTMStrategy
if SVM_AVAILABLE:
    STRATEGIES['SVM_Strategy'] = SVMStrategy
if ENSEMBLE_AVAILABLE:
    STRATEGIES['Ensemble_ML_Strategy'] = EnsembleMLStrategy
if TRANSFORMER_AVAILABLE:
    STRATEGIES['Transformer_Strategy'] = TransformerStrategy
if RL_AVAILABLE:
    STRATEGIES['RL_Strategy'] = RLStrategy
if MULTI_TIMEFRAME_AVAILABLE:
    STRATEGIES['Multi_Timeframe'] = MultiTimeframeStrategy

# Risk level categorization
RISK_LEVELS = {
    'Low_Risk': ['Mean_Reversion', 'SMA_Crossover'],
    'Medium_Risk': ['Scalping_MA', 'RSI_Reversion', 'BreakoutATR'],
    'High_Risk': ['Momentum_Breakout', 'News_Trading', 'Fear_Index', 'ML_Adaptive_SuperTrend', 'Adaptive_Trend_Flow',
                  'LSTM_Strategy', 'SVM_Strategy', 'Ensemble_ML_Strategy', 'Transformer_Strategy', 
                  'RL_Strategy', 'Multi_Timeframe']
}

def get_strategy(name: str, **params):
    """Get strategy instance by name.

    ``Multi_Timeframe`` accepts an optional ``base_strategy`` (instance or registry
    name). When omitted, it defaults to ``SMA_Crossover`` so UI / backtest call
    sites can use ``get_strategy('Multi_Timeframe')`` with no extra kwargs.
    """
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}")
    cls = STRATEGIES[name]
    if name == 'Multi_Timeframe':
        base = params.pop('base_strategy', None)
        if isinstance(base, str):
            if base == 'Multi_Timeframe':
                raise ValueError("Multi_Timeframe cannot wrap itself as base_strategy")
            base = get_strategy(base)
        return cls(base_strategy=base, **params)
    return cls(**params)

def list_strategies():
    """List available strategies."""
    return list(STRATEGIES.keys())

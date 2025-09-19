"""Enhanced risk management engine."""

import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass
from .interfaces import IRiskManager


@dataclass
class RiskConfig:
    """Risk management configuration."""
    base_risk_pct: float = 0.02
    max_risk_pct: float = 0.05
    daily_risk_cap: float = 0.05
    max_drawdown_pct: float = 0.25
    drawdown_recovery_pct: float = 0.10
    kelly_fraction: float = 0.25
    volatility_target: float = 0.01
    min_trade_amount: float = 10.0
    max_trade_amount: float = 100.0
    symbol_risk_multipliers: Dict[str, float] = None
    strategy_risk_multipliers: Dict[str, float] = None
    
    def __post_init__(self):
        if self.symbol_risk_multipliers is None:
            self.symbol_risk_multipliers = {}
        if self.strategy_risk_multipliers is None:
            self.strategy_risk_multipliers = {}


class RiskEngine(IRiskManager):
    """Enhanced risk management engine with multiple safety mechanisms."""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        self._daily_pnl = 0.0
        self._peak_equity = 0.0
        self._current_equity = 0.0
        self._drawdown_throttle = False
        self._recent_trades: List[Dict] = []
        self._max_recent_trades = 20
        
    def calculate_position_size(self, symbol: str, strategy: str, 
                              balance: float, volatility: Optional[float],
                              win_rate: Optional[float] = None) -> float:
        """Calculate position size using multiple risk management techniques."""
        
        # Base risk amount
        base_risk = balance * self.config.base_risk_pct
        
        # Apply symbol risk multiplier
        symbol_multiplier = self.config.symbol_risk_multipliers.get(symbol, 1.0)
        base_risk *= symbol_multiplier
        
        # Apply strategy risk multiplier
        strategy_multiplier = self.config.strategy_risk_multipliers.get(strategy, 1.0)
        base_risk *= strategy_multiplier
        
        # Kelly Criterion adjustment
        if win_rate is not None:
            kelly_fraction = self._calculate_kelly_fraction(win_rate)
            kelly_risk = balance * kelly_fraction * self.config.kelly_fraction
            base_risk = min(base_risk, kelly_risk)
        
        # Volatility targeting
        if volatility is not None and volatility > 0:
            vol_target_risk = balance * self.config.volatility_target / volatility
            base_risk = min(base_risk, vol_target_risk)
        
        # Drawdown throttle
        if self._drawdown_throttle:
            base_risk *= 0.5  # Reduce size by 50%
        
        # Apply limits - use max_risk_pct as the upper limit
        max_risk = balance * self.config.max_risk_pct
        base_risk = min(base_risk, max_risk)
        
        position_size = np.clip(
            base_risk, 
            self.config.min_trade_amount, 
            self.config.max_trade_amount
        )
        
        return float(position_size)
    
    def _calculate_kelly_fraction(self, win_rate: float) -> float:
        """Calculate Kelly Criterion fraction."""
        if win_rate <= 0 or win_rate >= 1:
            return 0.0
            
        # Simplified Kelly: (bp - q) / b
        # where b = 1 (1:1 risk/reward), p = win_rate, q = 1 - win_rate
        kelly = (2 * win_rate - 1)
        return max(0.0, kelly)
    
    def check_daily_risk_limit(self, current_pnl: float, balance: float) -> bool:
        """Check if daily risk limit is exceeded."""
        self._daily_pnl = current_pnl
        daily_limit = balance * self.config.daily_risk_cap
        
        if current_pnl < -daily_limit:
            return True  # Daily limit exceeded
            
        return False
    
    def check_drawdown_limit(self, current_equity: float, peak_equity: float) -> bool:
        """Check if drawdown limit is exceeded."""
        self._current_equity = current_equity
        
        if current_equity > peak_equity:
            self._peak_equity = current_equity
            self._drawdown_throttle = False
            return False
        
        current_drawdown = (peak_equity - current_equity) / peak_equity
        
        if current_drawdown > self.config.max_drawdown_pct:
            self._drawdown_throttle = True
            return True  # Drawdown limit exceeded
        
        # Check for recovery
        if self._drawdown_throttle:
            recovery_threshold = self.config.max_drawdown_pct - self.config.drawdown_recovery_pct
            if current_drawdown < recovery_threshold:
                self._drawdown_throttle = False
        
        return False
    
    def get_risk_multiplier(self, symbol: str, strategy: str) -> float:
        """Get risk multiplier for symbol/strategy combination."""
        symbol_mult = self.config.symbol_risk_multipliers.get(symbol, 1.0)
        strategy_mult = self.config.strategy_risk_multipliers.get(strategy, 1.0)
        return symbol_mult * strategy_mult
    
    def add_trade_result(self, pnl: float, symbol: str, strategy: str) -> None:
        """Add trade result for analysis."""
        trade_record = {
            'pnl': pnl,
            'symbol': symbol,
            'strategy': strategy,
            'timestamp': np.datetime64('now')
        }
        
        self._recent_trades.append(trade_record)
        
        # Keep only recent trades
        if len(self._recent_trades) > self._max_recent_trades:
            self._recent_trades = self._recent_trades[-self._max_recent_trades:]
    
    def get_recent_win_rate(self, symbol: str = None, strategy: str = None) -> Optional[float]:
        """Get recent win rate for analysis."""
        if not self._recent_trades:
            return None
        
        filtered_trades = self._recent_trades
        
        if symbol:
            filtered_trades = [t for t in filtered_trades if t['symbol'] == symbol]
        
        if strategy:
            filtered_trades = [t for t in filtered_trades if t['strategy'] == strategy]
        
        if not filtered_trades:
            return None
        
        wins = sum(1 for t in filtered_trades if t['pnl'] > 0)
        total = len(filtered_trades)
        
        return wins / total if total > 0 else None
    
    def get_recent_volatility(self, symbol: str = None) -> Optional[float]:
        """Get recent PnL volatility for analysis."""
        if not self._recent_trades:
            return None
        
        filtered_trades = self._recent_trades
        if symbol:
            filtered_trades = [t for t in filtered_trades if t['symbol'] == symbol]
        
        if len(filtered_trades) < 2:
            return None
        
        pnl_values = [t['pnl'] for t in filtered_trades]
        if len(pnl_values) < 2:
            return None
            
        return float(np.std(pnl_values))
    
    def reset_daily_metrics(self) -> None:
        """Reset daily metrics (call at start of new day)."""
        self._daily_pnl = 0.0
    
    def get_risk_summary(self) -> Dict:
        """Get current risk status summary."""
        return {
            'daily_pnl': self._daily_pnl,
            'current_equity': self._current_equity,
            'peak_equity': self._peak_equity,
            'current_drawdown': (self._peak_equity - self._current_equity) / self._peak_equity if self._peak_equity > 0 else 0.0,
            'drawdown_throttle': self._drawdown_throttle,
            'recent_trades_count': len(self._recent_trades),
            'recent_win_rate': self.get_recent_win_rate()
        }

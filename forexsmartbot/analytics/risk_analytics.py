"""
Risk Analytics Module
Calculates VaR, CVaR, stress testing, and risk-adjusted return metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats
from ..core.interfaces import Trade, Position


class RiskAnalytics:
    """Risk analytics and risk metrics calculation."""
    
    def __init__(self):
        self.trades: List[Trade] = []
        self.positions: List[Position] = []
        self.returns: List[float] = []
        
    def add_trade(self, trade: Trade):
        """Add a trade to the analytics."""
        self.trades.append(trade)
        
    def add_position(self, position: Position):
        """Add a position to the analytics."""
        self.positions.append(position)
        
    def calculate_var(self, confidence_level: float = 0.95, 
                     method: str = 'historical',
                     lookback_period: int = 252) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            method: Method to use ('historical', 'parametric', 'monte_carlo')
            lookback_period: Number of periods to look back
            
        Returns:
            Dictionary with VaR values
        """
        if not self.trades:
            return {
                'var': 0.0,
                'var_pct': 0.0,
                'confidence_level': confidence_level,
                'method': method
            }
            
        # Get returns
        returns = self._get_returns()
        if len(returns) < 2:
            return {
                'var': 0.0,
                'var_pct': 0.0,
                'confidence_level': confidence_level,
                'method': method
            }
            
        # Use recent returns if available
        if len(returns) > lookback_period:
            returns = returns[-lookback_period:]
            
        if method == 'historical':
            var = self._calculate_historical_var(returns, confidence_level)
        elif method == 'parametric':
            var = self._calculate_parametric_var(returns, confidence_level)
        elif method == 'monte_carlo':
            var = self._calculate_monte_carlo_var(returns, confidence_level)
        else:
            var = self._calculate_historical_var(returns, confidence_level)
            
        # Calculate VaR as percentage
        mean_return = np.mean(returns)
        var_pct = abs(var - mean_return) if mean_return != 0 else abs(var)
        
        return {
            'var': float(var),
            'var_pct': float(var_pct),
            'confidence_level': confidence_level,
            'method': method
        }
        
    def calculate_cvar(self, confidence_level: float = 0.95,
                      method: str = 'historical',
                      lookback_period: int = 252) -> Dict[str, float]:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.
        
        Args:
            confidence_level: Confidence level
            method: Method to use
            lookback_period: Number of periods to look back
            
        Returns:
            Dictionary with CVaR values
        """
        if not self.trades:
            return {
                'cvar': 0.0,
                'cvar_pct': 0.0,
                'confidence_level': confidence_level,
                'method': method
            }
            
        returns = self._get_returns()
        if len(returns) < 2:
            return {
                'cvar': 0.0,
                'cvar_pct': 0.0,
                'confidence_level': confidence_level,
                'method': method
            }
            
        if len(returns) > lookback_period:
            returns = returns[-lookback_period:]
            
        # Calculate VaR first
        var_result = self.calculate_var(confidence_level, method, lookback_period)
        var = var_result['var']
        
        # CVaR is the mean of returns below VaR
        tail_returns = returns[returns <= var]
        if len(tail_returns) == 0:
            cvar = var
        else:
            cvar = float(np.mean(tail_returns))
            
        mean_return = np.mean(returns)
        cvar_pct = abs(cvar - mean_return) if mean_return != 0 else abs(cvar)
        
        return {
            'cvar': cvar,
            'cvar_pct': cvar_pct,
            'var': var,
            'confidence_level': confidence_level,
            'method': method
        }
        
    def stress_test(self, scenarios: List[Dict[str, float]]) -> Dict[str, Dict]:
        """
        Perform stress testing with different scenarios.
        
        Args:
            scenarios: List of scenario dictionaries with 'name' and 'shock_pct'
            
        Returns:
            Dictionary with stress test results for each scenario
        """
        if not self.trades:
            return {}
            
        results = {}
        base_pnl = sum(t.pnl for t in self.trades)
        
        for scenario in scenarios:
            name = scenario.get('name', 'Unknown')
            shock_pct = scenario.get('shock_pct', 0.0)
            
            # Apply shock to all trades
            shocked_pnl = base_pnl * (1 + shock_pct / 100)
            loss = base_pnl - shocked_pnl
            
            results[name] = {
                'shock_pct': shock_pct,
                'base_pnl': base_pnl,
                'shocked_pnl': shocked_pnl,
                'loss': loss,
                'loss_pct': (loss / abs(base_pnl)) * 100 if base_pnl != 0 else 0.0
            }
            
        return results
        
    def calculate_risk_adjusted_returns(self) -> Dict[str, float]:
        """
        Calculate risk-adjusted return metrics.
        
        Returns:
            Dictionary with various risk-adjusted metrics
        """
        if not self.trades:
            return {
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'calmar_ratio': 0.0,
                'information_ratio': 0.0,
                'treynor_ratio': 0.0
            }
            
        returns = self._get_returns()
        if len(returns) < 2:
            return {
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'calmar_ratio': 0.0,
                'information_ratio': 0.0,
                'treynor_ratio': 0.0
            }
            
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02 / 252  # Daily risk-free rate
        sharpe = (mean_return - risk_free_rate) / std_return if std_return > 0 else 0.0
        sharpe *= np.sqrt(252)  # Annualize
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0.0
        sortino = (mean_return - risk_free_rate) / downside_std if downside_std > 0 else 0.0
        sortino *= np.sqrt(252)  # Annualize
        
        # Calmar ratio (return / max drawdown)
        max_dd = self._calculate_max_drawdown()
        calmar = (mean_return * 252) / abs(max_dd) if max_dd != 0 else 0.0
        
        # Information ratio (excess return / tracking error)
        # Using zero as benchmark for simplicity
        information_ratio = mean_return / std_return if std_return > 0 else 0.0
        information_ratio *= np.sqrt(252)  # Annualize
        
        # Treynor ratio (return / beta)
        # Beta calculation would require market data, using 1.0 as default
        beta = 1.0
        treynor = (mean_return - risk_free_rate) / beta if beta > 0 else 0.0
        treynor *= 252  # Annualize
        
        return {
            'sharpe_ratio': float(sharpe),
            'sortino_ratio': float(sortino),
            'calmar_ratio': float(calmar),
            'information_ratio': float(information_ratio),
            'treynor_ratio': float(treynor)
        }
        
    def _calculate_historical_var(self, returns: np.ndarray, 
                                 confidence_level: float) -> float:
        """Calculate VaR using historical method."""
        percentile = (1 - confidence_level) * 100
        return float(np.percentile(returns, percentile))
        
    def _calculate_parametric_var(self, returns: np.ndarray,
                                 confidence_level: float) -> float:
        """Calculate VaR using parametric (variance-covariance) method."""
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)
        
        var = mean_return + (z_score * std_return)
        return float(var)
        
    def _calculate_monte_carlo_var(self, returns: np.ndarray,
                                  confidence_level: float,
                                  n_simulations: int = 10000) -> float:
        """Calculate VaR using Monte Carlo simulation."""
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Generate random returns based on distribution
        simulated_returns = np.random.normal(mean_return, std_return, n_simulations)
        
        percentile = (1 - confidence_level) * 100
        return float(np.percentile(simulated_returns, percentile))
        
    def _get_returns(self) -> np.ndarray:
        """Get returns array from trades."""
        if not self.trades:
            return np.array([])
            
        returns = []
        for trade in self.trades:
            if trade.entry_price > 0:
                return_pct = (trade.pnl / (trade.entry_price * trade.quantity)) * 100
                returns.append(return_pct)
                
        return np.array(returns)
        
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage."""
        if not self.trades:
            return 0.0
            
        sorted_trades = sorted(self.trades, key=lambda t: t.exit_time if t.exit_time else t.entry_time)
        cumulative_pnl = 0.0
        equity_curve = []
        
        for trade in sorted_trades:
            cumulative_pnl += trade.pnl
            equity_curve.append(cumulative_pnl)
            
        if not equity_curve:
            return 0.0
            
        equity_array = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = running_max - equity_array
        
        if len(drawdown) == 0 or np.max(running_max) == 0:
            return 0.0
            
        max_dd_pct = (np.max(drawdown) / np.max(running_max)) * 100
        return float(max_dd_pct)


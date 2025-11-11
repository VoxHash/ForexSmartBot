"""Walk-forward analysis with rolling windows."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Callable
from datetime import datetime, timedelta


class WalkForwardAnalyzer:
    """Walk-forward analysis for strategy validation."""
    
    def __init__(self, train_period: int = 252, test_period: int = 63, 
                 step_size: int = 21):
        """
        Initialize walk-forward analyzer.
        
        Args:
            train_period: Training period in days
            test_period: Testing period in days
            step_size: Step size for rolling window in days
        """
        self.train_period = train_period
        self.test_period = test_period
        self.step_size = step_size
        
    def analyze(self, data: pd.DataFrame, 
                strategy_factory: Callable[[Dict[str, Any]], Any],
                optimize_function: Callable[[pd.DataFrame, Dict[str, Any]], float],
                initial_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run walk-forward analysis.
        
        Args:
            data: Historical price data
            strategy_factory: Function that creates strategy instance from params
            optimize_function: Function that optimizes parameters on training data
            initial_params: Initial parameter values
            
        Returns:
            Dictionary with analysis results
        """
        results = []
        current_date = data.index[0]
        end_date = data.index[-1]
        
        while current_date < end_date:
            # Define training and test periods
            train_start = current_date
            train_end = current_date + timedelta(days=self.train_period)
            test_start = train_end
            test_end = test_start + timedelta(days=self.test_period)
            
            # Check if we have enough data
            if test_end > end_date:
                break
                
            # Get training data
            train_data = data[(data.index >= train_start) & (data.index < train_end)]
            test_data = data[(data.index >= test_start) & (data.index < test_end)]
            
            if len(train_data) < self.train_period * 0.8 or len(test_data) < self.test_period * 0.8:
                current_date += timedelta(days=self.step_size)
                continue
                
            # Optimize on training data
            try:
                optimized_params = optimize_function(train_data, initial_params)
                
                # Test on out-of-sample data
                strategy = strategy_factory(optimized_params)
                test_results = self._test_strategy(strategy, test_data)
                
                results.append({
                    'train_start': train_start,
                    'train_end': train_end,
                    'test_start': test_start,
                    'test_end': test_end,
                    'params': optimized_params,
                    'test_results': test_results
                })
                
            except Exception as e:
                print(f"Error in walk-forward step: {e}")
                
            # Move to next window
            current_date += timedelta(days=self.step_size)
            
        # Aggregate results
        return self._aggregate_results(results)
        
    def _test_strategy(self, strategy, test_data: pd.DataFrame) -> Dict[str, float]:
        """Test strategy on test data."""
        # This is a simplified version - actual implementation would run full backtest
        returns = test_data['Close'].pct_change().dropna()
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        total_return = (test_data['Close'].iloc[-1] / test_data['Close'].iloc[0]) - 1
        
        return {
            'sharpe_ratio': sharpe,
            'total_return': total_return,
            'max_drawdown': self._calculate_max_drawdown(test_data['Close'])
        }
        
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown."""
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min())
        
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate walk-forward results."""
        if not results:
            return {}
            
        sharpe_ratios = [r['test_results']['sharpe_ratio'] for r in results]
        returns = [r['test_results']['total_return'] for r in results]
        drawdowns = [r['test_results']['max_drawdown'] for r in results]
        
        return {
            'num_periods': len(results),
            'avg_sharpe': np.mean(sharpe_ratios),
            'std_sharpe': np.std(sharpe_ratios),
            'avg_return': np.mean(returns),
            'std_return': np.std(returns),
            'avg_drawdown': np.mean(drawdowns),
            'max_drawdown': max(drawdowns),
            'win_rate': sum(1 for r in returns if r > 0) / len(returns) if returns else 0,
            'periods': results
        }


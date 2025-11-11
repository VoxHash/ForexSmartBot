"""Monte Carlo simulation for backtesting."""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Callable, Optional
from scipy import stats


class MonteCarloSimulator:
    """Monte Carlo simulator for strategy backtesting."""
    
    def __init__(self, n_simulations: int = 1000, confidence_level: float = 0.95):
        """
        Initialize Monte Carlo simulator.
        
        Args:
            n_simulations: Number of Monte Carlo simulations
            confidence_level: Confidence level for VaR/CVaR (e.g., 0.95 for 95%)
        """
        self.n_simulations = n_simulations
        self.confidence_level = confidence_level
        
    def simulate(self, returns: pd.Series, initial_balance: float = 10000.0,
                 n_periods: Optional[int] = None) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation.
        
        Args:
            returns: Historical returns series
            initial_balance: Initial account balance
            n_periods: Number of periods to simulate (default: length of returns)
            
        Returns:
            Dictionary with simulation results
        """
        if n_periods is None:
            n_periods = len(returns)
            
        # Fit distribution to returns
        mu, sigma = returns.mean(), returns.std()
        
        # Run simulations
        simulation_results = []
        for _ in range(self.n_simulations):
            # Generate random returns
            simulated_returns = np.random.normal(mu, sigma, n_periods)
            
            # Calculate equity curve
            equity = initial_balance * np.cumprod(1 + simulated_returns)
            final_balance = equity[-1]
            total_return = (final_balance / initial_balance) - 1
            
            # Calculate drawdown
            running_max = np.maximum.accumulate(equity)
            drawdown = (equity - running_max) / running_max
            max_drawdown = abs(np.min(drawdown))
            
            simulation_results.append({
                'final_balance': final_balance,
                'total_return': total_return,
                'max_drawdown': max_drawdown,
                'equity_curve': equity
            })
            
        # Aggregate results
        final_balances = [r['final_balance'] for r in simulation_results]
        total_returns = [r['total_return'] for r in simulation_results]
        max_drawdowns = [r['max_drawdown'] for r in simulation_results]
        
        # Calculate VaR and CVaR
        var = np.percentile(total_returns, (1 - self.confidence_level) * 100)
        cvar = np.mean([r for r in total_returns if r <= var])
        
        return {
            'n_simulations': self.n_simulations,
            'mean_final_balance': np.mean(final_balances),
            'std_final_balance': np.std(final_balances),
            'mean_return': np.mean(total_returns),
            'std_return': np.std(total_returns),
            'mean_drawdown': np.mean(max_drawdowns),
            'max_drawdown': np.max(max_drawdowns),
            'var': var,
            'cvar': cvar,
            'percentile_5': np.percentile(total_returns, 5),
            'percentile_95': np.percentile(total_returns, 95),
            'probability_of_profit': sum(1 for r in total_returns if r > 0) / len(total_returns),
            'simulations': simulation_results
        }
        
    def stress_test(self, returns: pd.Series, stress_scenarios: List[float],
                   initial_balance: float = 10000.0) -> Dict[str, Any]:
        """
        Run stress test with different market scenarios.
        
        Args:
            returns: Historical returns
            stress_scenarios: List of stress multipliers (e.g., [0.5, 1.5, 2.0])
            initial_balance: Initial account balance
            
        Returns:
            Dictionary with stress test results
        """
        results = {}
        
        for scenario in stress_scenarios:
            # Adjust returns by scenario multiplier
            stressed_returns = returns * scenario
            
            # Run simulation
            sim_results = self.simulate(stressed_returns, initial_balance)
            results[f'scenario_{scenario}x'] = sim_results
            
        return results


"""Integration example: Complete workflow from optimization to production monitoring."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.strategies import get_strategy
from forexsmartbot.optimization import (
    GeneticOptimizer,
    ParameterSensitivityAnalyzer,
    WalkForwardAnalyzer,
    MonteCarloSimulator
)
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.services.enhanced_backtest import EnhancedBacktestService
from forexsmartbot.monitoring import StrategyMonitor, PerformanceTracker, HealthChecker
from forexsmartbot.core.risk_engine import RiskConfig
from datetime import datetime
import pandas as pd


def main():
    """Complete workflow example."""
    print("=" * 70)
    print("Complete Integration Workflow Example")
    print("=" * 70)
    
    data_provider = YFinanceProvider()
    symbol = 'EURUSD=X'
    start_date = '2023-01-01'
    end_date = '2023-12-31'
    initial_balance = 10000.0
    
    # ========================================================================
    # STEP 1: Parameter Optimization
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 1: Parameter Optimization")
    print("=" * 70)
    
    def fitness_function(params):
        """Fitness function for optimization."""
        try:
            strategy = get_strategy('SMA_Crossover', **params)
            service = BacktestService(data_provider)
            results = service.run_backtest(
                strategy=strategy,
                symbol=symbol,
                start_date=start_date,
                end_date='2023-06-30',  # Use first half for optimization
                initial_balance=initial_balance
            )
            if 'error' in results:
                return -100.0
            metrics = results.get('metrics', {})
            return metrics.get('sharpe_ratio', 0.0)
        except Exception as e:
            print(f"  Error in fitness: {e}")
            return -100.0
    
    param_bounds = {
        'fast_period': (10, 30),
        'slow_period': (40, 80)
    }
    
    print("Running genetic algorithm optimization...")
    optimizer = GeneticOptimizer(param_bounds, population_size=20, generations=10)
    best_params, best_fitness = optimizer.optimize(fitness_function, verbose=False)
    
    print(f"✓ Optimization complete")
    print(f"  Best parameters: {best_params}")
    print(f"  Best fitness (Sharpe): {best_fitness:.4f}")
    
    # ========================================================================
    # STEP 2: Parameter Sensitivity Analysis
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 2: Parameter Sensitivity Analysis")
    print("=" * 70)
    
    def strategy_factory(params):
        return get_strategy('SMA_Crossover', **params)
    
    def performance_function(strategy):
        service = BacktestService(data_provider)
        results = service.run_backtest(
            strategy=strategy,
            symbol=symbol,
            start_date=start_date,
            end_date='2023-06-30',
            initial_balance=initial_balance
        )
        if 'error' in results:
            return 0.0
        metrics = results.get('metrics', {})
        return metrics.get('total_return', 0.0)
    
    sensitivity_analyzer = ParameterSensitivityAnalyzer(n_points=5)
    param_ranges = {
        'fast_period': (best_params['fast_period'] - 5, best_params['fast_period'] + 5),
        'slow_period': (best_params['slow_period'] - 10, best_params['slow_period'] + 10)
    }
    
    print("Analyzing parameter sensitivity...")
    sensitivity_results = sensitivity_analyzer.analyze(
        strategy_factory, best_params, param_ranges, performance_function
    )
    
    print(f"✓ Sensitivity analysis complete")
    for param_name, result in sensitivity_results.items():
        print(f"  {param_name}: Sensitivity = {result.sensitivity_score:.4f}")
    
    # ========================================================================
    # STEP 3: Walk-Forward Validation
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 3: Walk-Forward Validation")
    print("=" * 70)
    
    df = data_provider.get_data(symbol, start_date, end_date, '1h')
    
    if not df.empty:
        print("Running walk-forward analysis...")
        walk_forward = WalkForwardAnalyzer(train_period=60, test_period=20, step_size=10)
        
        def optimize_function(train_data, initial_params):
            return best_params  # Use optimized params
        
        wf_results = walk_forward.analyze(
            df, strategy_factory, optimize_function, best_params
        )
        
        if wf_results:
            print(f"✓ Walk-forward analysis complete")
            print(f"  Periods analyzed: {wf_results.get('num_periods', 0)}")
            print(f"  Average Sharpe: {wf_results.get('avg_sharpe', 0):.4f}")
            print(f"  Win Rate: {wf_results.get('win_rate', 0):.2%}")
    
    # ========================================================================
    # STEP 4: Risk Assessment (Monte Carlo)
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 4: Risk Assessment (Monte Carlo)")
    print("=" * 70)
    
    if not df.empty:
        print("Running Monte Carlo simulation...")
        returns = df['Close'].pct_change().dropna()
        mc_simulator = MonteCarloSimulator(n_simulations=100, confidence_level=0.95)
        mc_results = mc_simulator.simulate(returns, initial_balance=initial_balance, n_periods=252)
        
        print(f"✓ Monte Carlo simulation complete")
        print(f"  VaR (95%): {mc_results['var']:.4f}")
        print(f"  CVaR (95%): {mc_results['cvar']:.4f}")
        print(f"  Probability of Profit: {mc_results['probability_of_profit']:.2%}")
    
    # ========================================================================
    # STEP 5: Final Backtest with Optimized Parameters
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 5: Final Backtest with Optimized Parameters")
    print("=" * 70)
    
    optimized_strategy = get_strategy('SMA_Crossover', **best_params)
    enhanced_service = EnhancedBacktestService(data_provider, use_parallel=False)
    
    print("Running enhanced backtest...")
    final_results = enhanced_service.run_backtest(
        strategy=optimized_strategy,
        symbol=symbol,
        start_date='2023-07-01',  # Use second half for validation
        end_date=end_date,
        initial_balance=initial_balance,
        enable_logging=False
    )
    
    if 'error' not in final_results:
        print(f"✓ Final backtest complete")
        print(f"  Total Return: {final_results.get('total_return', 0):.2%}")
        print(f"  Total Trades: {final_results.get('total_trades', 0)}")
        print(f"  Winning Trades: {final_results.get('winning_trades', 0)}")
        print(f"  Losing Trades: {final_results.get('losing_trades', 0)}")
        metrics = final_results.get('metrics', {})
        if metrics:
            print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.4f}")
            print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
    else:
        print(f"✗ Backtest error: {final_results.get('error')}")
        return
    
    # ========================================================================
    # STEP 6: Production Monitoring Setup
    # ========================================================================
    print("\n" + "=" * 70)
    print("STEP 6: Production Monitoring Setup")
    print("=" * 70)
    
    monitor = StrategyMonitor()
    tracker = PerformanceTracker()
    health_checker = HealthChecker(monitor)
    
    strategy_name = "Optimized_SMA_Crossover"
    monitor.register_strategy(strategy_name)
    
    print(f"✓ Monitoring setup complete for '{strategy_name}'")
    
    # Simulate production monitoring
    print("\nSimulating production monitoring...")
    for i in range(10):
        # Simulate signal generation
        monitor.record_signal(strategy_name, execution_time=0.05 + i * 0.01)
        
        # Simulate trade
        if i % 3 == 0:  # Every 3rd signal results in trade
            profit = (i % 2 - 0.5) * 50.0
            tracker.record_trade(strategy_name, {
                'profit': profit,
                'entry_price': 1.1000,
                'exit_price': 1.1000 + profit / 10000,
                'entry_time': datetime.now(),
                'exit_time': datetime.now()
            })
            tracker.record_equity(strategy_name, initial_balance + i * 10.0)
    
    # Check health
    health = health_checker.check(strategy_name)
    print(f"✓ Health check: {health['status']}")
    
    # Get performance metrics
    metrics = tracker.calculate_metrics(strategy_name)
    if metrics:
        print(f"✓ Performance metrics calculated")
        print(f"  Total Return: {metrics.total_return:.2%}")
        print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.4f}")
        print(f"  Win Rate: {metrics.win_rate:.2%}")
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETE")
    print("=" * 70)
    print("\nCompleted steps:")
    print("  1. ✓ Parameter optimization")
    print("  2. ✓ Sensitivity analysis")
    print("  3. ✓ Walk-forward validation")
    print("  4. ✓ Risk assessment (Monte Carlo)")
    print("  5. ✓ Final backtest validation")
    print("  6. ✓ Production monitoring setup")
    print("\nStrategy is ready for production use!")
    print("=" * 70)


if __name__ == "__main__":
    main()


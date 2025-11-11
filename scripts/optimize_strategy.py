#!/usr/bin/env python3
"""Command-line tool for optimizing strategy parameters."""

import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.strategies import get_strategy
from forexsmartbot.optimization import GeneticOptimizer, HyperparameterOptimizer
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.core.risk_engine import RiskConfig


def create_fitness_function(strategy_name, symbol, start_date, end_date, initial_balance):
    """Create fitness function for optimization."""
    data_provider = YFinanceProvider()
    backtest_service = BacktestService(data_provider)
    
    def fitness(params):
        try:
            strategy = get_strategy(strategy_name, **params)
            results = backtest_service.run_backtest(
                strategy=strategy,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_balance=initial_balance,
                risk_config=RiskConfig()
            )
            
            if 'error' in results:
                return -100.0
                
            metrics = results.get('metrics', {})
            sharpe = metrics.get('sharpe_ratio', 0.0)
            return sharpe if sharpe > -100 else -100.0
            
        except Exception as e:
            print(f"Error in fitness function: {e}", file=sys.stderr)
            return -100.0
            
    return fitness


def main():
    parser = argparse.ArgumentParser(description='Optimize strategy parameters')
    parser.add_argument('--strategy', required=True, help='Strategy name')
    parser.add_argument('--symbol', default='EURUSD=X', help='Trading symbol')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--method', choices=['ga', 'optuna'], default='ga', 
                       help='Optimization method')
    parser.add_argument('--params', required=True, 
                       help='Parameter bounds as JSON string or file path')
    parser.add_argument('--population-size', type=int, default=50, 
                       help='Population size for GA')
    parser.add_argument('--generations', type=int, default=30, 
                       help='Number of generations for GA')
    parser.add_argument('--trials', type=int, default=100, 
                       help='Number of trials for Optuna')
    parser.add_argument('--balance', type=float, default=10000.0, 
                       help='Initial balance')
    
    args = parser.parse_args()
    
    # Parse parameter bounds
    import json
    if os.path.exists(args.params):
        with open(args.params, 'r') as f:
            param_config = json.load(f)
    else:
        param_config = json.loads(args.params)
    
    # Create fitness function
    fitness = create_fitness_function(
        args.strategy, args.symbol, args.start, args.end, args.balance
    )
    
    print(f"Optimizing {args.strategy} on {args.symbol}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Method: {args.method}")
    print()
    
    if args.method == 'ga':
        # Extract bounds
        param_bounds = {}
        for param, config in param_config.items():
            if isinstance(config, dict) and 'min' in config and 'max' in config:
                param_bounds[param] = (config['min'], config['max'])
            elif isinstance(config, list) and len(config) == 2:
                param_bounds[param] = tuple(config)
            else:
                print(f"Warning: Invalid bounds for {param}, skipping", file=sys.stderr)
                continue
        
        optimizer = GeneticOptimizer(
            param_bounds=param_bounds,
            population_size=args.population_size,
            generations=args.generations
        )
        
        best_params, best_fitness = optimizer.optimize(fitness, verbose=True)
        
    else:  # optuna
        param_space = {}
        for param, config in param_config.items():
            if isinstance(config, dict):
                param_space[param] = config
            else:
                print(f"Warning: Invalid config for {param}, skipping", file=sys.stderr)
                continue
        
        optimizer = HyperparameterOptimizer(
            param_space=param_space,
            n_trials=args.trials,
            direction='maximize'
        )
        
        def objective(params):
            return fitness(params)
        
        best_params, best_fitness = optimizer.optimize(objective, verbose=True)
    
    print()
    print("=" * 60)
    print("Optimization Results")
    print("=" * 60)
    print(f"Best Parameters:")
    for param, value in best_params.items():
        print(f"  {param}: {value}")
    print(f"Best Fitness (Sharpe Ratio): {best_fitness:.4f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


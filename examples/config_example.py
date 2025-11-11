"""Example: Using configuration files for strategies and optimization."""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forexsmartbot.strategies import get_strategy
from forexsmartbot.optimization import GeneticOptimizer, HyperparameterOptimizer
from forexsmartbot.adapters.data import YFinanceProvider
from forexsmartbot.services.backtest import BacktestService


def load_config(config_path):
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    """Example: Using configuration files."""
    print("Configuration Example")
    print("=" * 60)
    
    # Load strategy configurations
    try:
        strategy_configs = load_config('config/strategy_configs.json')
        print("✓ Loaded strategy configurations")
    except FileNotFoundError:
        print("⚠ Strategy config file not found, using defaults")
        strategy_configs = {}
    
    # Load optimization configurations
    try:
        opt_configs = load_config('config/optimization_config.json')
        print("✓ Loaded optimization configurations")
    except FileNotFoundError:
        print("⚠ Optimization config file not found, using defaults")
        opt_configs = {}
    
    # Example 1: Create strategy from config
    print("\n1. Creating Strategy from Config")
    print("-" * 60)
    
    if 'Ensemble_ML_Strategy' in strategy_configs:
        config = strategy_configs['Ensemble_ML_Strategy']
        strategy = get_strategy('Ensemble_ML_Strategy', **config)
        print(f"✓ Created {strategy.name} with config:")
        for key, value in config.items():
            print(f"  {key}: {value}")
    else:
        print("⚠ Ensemble_ML_Strategy config not found")
    
    # Example 2: Use optimization config
    print("\n2. Using Optimization Config")
    print("-" * 60)
    
    if 'genetic_algorithm' in opt_configs:
        ga_config = opt_configs['genetic_algorithm']
        print("Genetic Algorithm Configuration:")
        for key, value in ga_config.items():
            print(f"  {key}: {value}")
        
        # Example: Create optimizer with config
        param_bounds = {
            'fast_period': (10, 30),
            'slow_period': (40, 80)
        }
        
        optimizer = GeneticOptimizer(
            param_bounds=param_bounds,
            population_size=ga_config.get('population_size', 50),
            generations=ga_config.get('generations', 30),
            mutation_rate=ga_config.get('mutation_rate', 0.2),
            crossover_rate=ga_config.get('crossover_rate', 0.7)
        )
        print("✓ Created optimizer with configuration")
    else:
        print("⚠ Genetic algorithm config not found")
    
    # Example 3: Hyperparameter optimization config
    print("\n3. Hyperparameter Optimization Config")
    print("-" * 60)
    
    if 'hyperparameter_optimization' in opt_configs:
        hp_config = opt_configs['hyperparameter_optimization']
        print("Hyperparameter Optimization Configuration:")
        for key, value in hp_config.items():
            print(f"  {key}: {value}")
    else:
        print("⚠ Hyperparameter optimization config not found")
    
    # Example 4: Walk-forward config
    print("\n4. Walk-Forward Analysis Config")
    print("-" * 60)
    
    if 'walk_forward' in opt_configs:
        wf_config = opt_configs['walk_forward']
        print("Walk-Forward Configuration:")
        for key, value in wf_config.items():
            print(f"  {key}: {value}")
    else:
        print("⚠ Walk-forward config not found")
    
    # Example 5: Monte Carlo config
    print("\n5. Monte Carlo Simulation Config")
    print("-" * 60)
    
    if 'monte_carlo' in opt_configs:
        mc_config = opt_configs['monte_carlo']
        print("Monte Carlo Configuration:")
        for key, value in mc_config.items():
            print(f"  {key}: {value}")
    else:
        print("⚠ Monte Carlo config not found")
    
    print("\n" + "=" * 60)
    print("Configuration example complete!")
    print("\nTip: Modify config files to customize behavior without changing code.")


if __name__ == "__main__":
    main()


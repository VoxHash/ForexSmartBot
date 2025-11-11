#!/usr/bin/env python3
"""Validate v3.1.0 installation and features."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_import(module_name, package_name=None):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)


def check_strategy(strategy_name):
    """Check if a strategy is available."""
    try:
        from forexsmartbot.strategies import get_strategy, STRATEGIES
        if strategy_name in STRATEGIES:
            strategy = get_strategy(strategy_name)
            return True, f"Available: {strategy.name}"
        else:
            return False, "Not in strategy registry"
    except Exception as e:
        return False, str(e)


def main():
    """Validate installation."""
    print("=" * 70)
    print("ForexSmartBot v3.1.0 Installation Validation")
    print("=" * 70)
    
    all_passed = True
    results = []
    
    # Check core imports
    print("\n1. Core Modules")
    print("-" * 70)
    
    core_modules = [
        ('forexsmartbot.strategies', 'Core strategies'),
        ('forexsmartbot.optimization', 'Optimization tools'),
        ('forexsmartbot.monitoring', 'Monitoring tools'),
        ('forexsmartbot.builder', 'Strategy builder'),
        ('forexsmartbot.marketplace', 'Marketplace'),
    ]
    
    for module, name in core_modules:
        success, error = check_import(module)
        status = "✓" if success else "✗"
        print(f"{status} {name}: {module}")
        if not success:
            print(f"  Error: {error}")
            all_passed = False
        results.append((name, success))
    
    # Check ML dependencies
    print("\n2. ML Dependencies (Optional)")
    print("-" * 70)
    
    ml_dependencies = [
        ('tensorflow', 'TensorFlow (LSTM)'),
        ('torch', 'PyTorch (Deep Learning)'),
        ('transformers', 'Transformers (Transformer models)'),
        ('gymnasium', 'Gymnasium (RL)'),
        ('stable_baselines3', 'Stable-Baselines3 (RL)'),
        ('optuna', 'Optuna (Hyperparameter optimization)'),
        ('deap', 'DEAP (Genetic algorithms)'),
    ]
    
    ml_available = []
    for module, name in ml_dependencies:
        success, error = check_import(module)
        status = "✓" if success else "○"
        print(f"{status} {name}: {module}")
        if success:
            ml_available.append(name)
        results.append((name, success))
    
    # Check strategies
    print("\n3. Strategy Availability")
    print("-" * 70)
    
    strategies_to_check = [
        ('SMA_Crossover', 'Core strategy'),
        ('RSI_Reversion', 'Core strategy'),
        ('ML_Adaptive_SuperTrend', 'ML strategy'),
        ('LSTM_Strategy', 'ML strategy (requires TensorFlow)'),
        ('SVM_Strategy', 'ML strategy'),
        ('Ensemble_ML_Strategy', 'ML strategy'),
        ('Transformer_Strategy', 'ML strategy (requires Transformers)'),
        ('RL_Strategy', 'RL strategy (requires Gymnasium)'),
        ('Multi_Timeframe', 'Multi-timeframe strategy'),
    ]
    
    for strategy_name, description in strategies_to_check:
        success, message = check_strategy(strategy_name)
        status = "✓" if success else "○"
        print(f"{status} {strategy_name}: {description}")
        if not success and 'requires' not in description.lower():
            print(f"  Warning: {message}")
            all_passed = False
        elif not success:
            print(f"  Note: {message} (optional dependency)")
        results.append((strategy_name, success))
    
    # Check optimization tools
    print("\n4. Optimization Tools")
    print("-" * 70)
    
    opt_tools = [
        ('GeneticOptimizer', 'forexsmartbot.optimization'),
        ('HyperparameterOptimizer', 'forexsmartbot.optimization'),
        ('WalkForwardAnalyzer', 'forexsmartbot.optimization'),
        ('MonteCarloSimulator', 'forexsmartbot.optimization'),
        ('ParameterSensitivityAnalyzer', 'forexsmartbot.optimization'),
    ]
    
    for tool_name, module in opt_tools:
        try:
            module_obj = __import__(module, fromlist=[tool_name])
            tool = getattr(module_obj, tool_name)
            print(f"✓ {tool_name}")
            results.append((tool_name, True))
        except Exception as e:
            print(f"✗ {tool_name}: {str(e)}")
            all_passed = False
            results.append((tool_name, False))
    
    # Check monitoring tools
    print("\n5. Monitoring Tools")
    print("-" * 70)
    
    monitor_tools = [
        ('StrategyMonitor', 'forexsmartbot.monitoring'),
        ('PerformanceTracker', 'forexsmartbot.monitoring'),
        ('HealthChecker', 'forexsmartbot.monitoring'),
    ]
    
    for tool_name, module in monitor_tools:
        try:
            module_obj = __import__(module, fromlist=[tool_name])
            tool = getattr(module_obj, tool_name)
            print(f"✓ {tool_name}")
            results.append((tool_name, True))
        except Exception as e:
            print(f"✗ {tool_name}: {str(e)}")
            all_passed = False
            results.append((tool_name, False))
    
    # Check builder tools
    print("\n6. Strategy Builder")
    print("-" * 70)
    
    builder_tools = [
        ('StrategyBuilder', 'forexsmartbot.builder'),
        ('StrategyTemplate', 'forexsmartbot.builder'),
        ('CodeGenerator', 'forexsmartbot.builder'),
    ]
    
    for tool_name, module in builder_tools:
        try:
            module_obj = __import__(module, fromlist=[tool_name])
            tool = getattr(module_obj, tool_name)
            print(f"✓ {tool_name}")
            results.append((tool_name, True))
        except Exception as e:
            print(f"✗ {tool_name}: {str(e)}")
            all_passed = False
            results.append((tool_name, False))
    
    # Check marketplace
    print("\n7. Marketplace")
    print("-" * 70)
    
    marketplace_tools = [
        ('StrategyMarketplace', 'forexsmartbot.marketplace'),
        ('StrategyRating', 'forexsmartbot.marketplace'),
    ]
    
    for tool_name, module in marketplace_tools:
        try:
            module_obj = __import__(module, fromlist=[tool_name])
            tool = getattr(module_obj, tool_name)
            print(f"✓ {tool_name}")
            results.append((tool_name, True))
        except Exception as e:
            print(f"✗ {tool_name}: {str(e)}")
            all_passed = False
            results.append((tool_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Validation Summary")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed
    
    print(f"Total Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if ml_available:
        print(f"\nML Features Available: {len(ml_available)}/{len(ml_dependencies)}")
        print("Available ML dependencies:")
        for dep in ml_available:
            print(f"  - {dep}")
    
    if all_passed:
        print("\n✓ All core features validated successfully!")
        print("✓ Installation is correct")
        if ml_available:
            print(f"✓ {len(ml_available)} ML dependencies available")
        return 0
    else:
        print("\n⚠ Some checks failed")
        print("⚠ Core features may not work correctly")
        print("\nTo install missing dependencies:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())


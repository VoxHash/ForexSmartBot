# Quick Start Guide - v3.1.0 Enhanced Strategies

This guide will help you quickly get started with the new v3.1.0 features.

## 🚀 Installation

First, install the new dependencies:

```bash
pip install -r requirements.txt
```

This will install:
- TensorFlow (for LSTM)
- PyTorch (for deep learning)
- Transformers (for transformer models)
- Gymnasium & Stable-Baselines3 (for RL)
- Optuna (for hyperparameter optimization)
- DEAP (for genetic algorithms)

## 📚 Quick Examples

### 1. Using ML Strategies

```python
from forexsmartbot.strategies import get_strategy

# LSTM Strategy
strategy = get_strategy('LSTM_Strategy', 
    lookback_period=60,
    sequence_length=20,
    lstm_units=50
)

# SVM Strategy
strategy = get_strategy('SVM_Strategy',
    kernel='rbf',
    C=1.0
)

# Ensemble ML Strategy
strategy = get_strategy('Ensemble_ML_Strategy',
    n_estimators=100,
    max_depth=10
)
```

### 2. Optimizing Strategy Parameters

```python
from forexsmartbot.optimization import GeneticOptimizer
from forexsmartbot.strategies import get_strategy
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.adapters.data import YFinanceProvider

# Define parameter bounds
param_bounds = {
    'fast_period': (10, 30),
    'slow_period': (40, 80)
}

# Create optimizer
optimizer = GeneticOptimizer(param_bounds, population_size=50, generations=30)

# Define fitness function
def fitness(params):
    strategy = get_strategy('SMA_Crossover', **params)
    service = BacktestService(YFinanceProvider())
    results = service.run_backtest(strategy, 'EURUSD=X', '2023-01-01', '2023-12-31')
    return results.get('metrics', {}).get('sharpe_ratio', 0.0)

# Optimize
best_params, best_fitness = optimizer.optimize(fitness)
print(f"Best parameters: {best_params}")
```

### 3. Parameter Sensitivity Analysis

```python
from forexsmartbot.optimization import ParameterSensitivityAnalyzer
from forexsmartbot.strategies import get_strategy

# Create analyzer
analyzer = ParameterSensitivityAnalyzer(n_points=10)

# Define strategy factory
def strategy_factory(params):
    return get_strategy('SMA_Crossover', **params)

# Define performance function
def performance(strategy):
    # Your backtest logic here
    return sharpe_ratio

# Analyze
base_params = {'fast_period': 20, 'slow_period': 50}
param_ranges = {
    'fast_period': (15, 25),
    'slow_period': (45, 55)
}

results = analyzer.analyze(strategy_factory, base_params, param_ranges, performance)

# Generate report
report = analyzer.generate_report(results)
print(report)
```

### 4. Walk-Forward Analysis

```python
from forexsmartbot.optimization import WalkForwardAnalyzer
from forexsmartbot.adapters.data import YFinanceProvider

# Get data
data_provider = YFinanceProvider()
df = data_provider.get_data('EURUSD=X', '2023-01-01', '2023-12-31', '1h')

# Create analyzer
analyzer = WalkForwardAnalyzer(train_period=252, test_period=63, step_size=21)

# Run analysis
results = analyzer.analyze(df, strategy_factory, optimize_function, initial_params)
print(f"Average Sharpe: {results['avg_sharpe']:.4f}")
```

### 5. Monte Carlo Simulation

```python
from forexsmartbot.optimization import MonteCarloSimulator
import pandas as pd

# Get returns data
returns = df['Close'].pct_change().dropna()

# Create simulator
simulator = MonteCarloSimulator(n_simulations=1000, confidence_level=0.95)

# Run simulation
results = simulator.simulate(returns, initial_balance=10000.0)

print(f"VaR (95%): {results['var']:.4f}")
print(f"CVaR (95%): {results['cvar']:.4f}")
print(f"Probability of Profit: {results['probability_of_profit']:.2%}")
```

### 6. Strategy Monitoring

```python
from forexsmartbot.monitoring import StrategyMonitor, HealthChecker

# Create monitor
monitor = StrategyMonitor()
monitor.register_strategy("MyStrategy")

# Record events
monitor.record_signal("MyStrategy", execution_time=0.1)
monitor.record_error("MyStrategy", "Connection timeout")

# Check health
health_checker = HealthChecker(monitor)
health = health_checker.check("MyStrategy")
print(f"Status: {health['status']}")
```

### 7. Performance Tracking

```python
from forexsmartbot.monitoring import PerformanceTracker

# Create tracker
tracker = PerformanceTracker()

# Record trades
tracker.record_trade("MyStrategy", {
    'profit': 100.0,
    'entry_price': 1.1000,
    'exit_price': 1.1100,
    'entry_time': datetime.now(),
    'exit_time': datetime.now()
})

# Calculate metrics
metrics = tracker.calculate_metrics("MyStrategy")
print(f"Sharpe Ratio: {metrics.sharpe_ratio:.4f}")
print(f"Win Rate: {metrics.win_rate:.2%}")
```

### 8. Strategy Builder

```python
from forexsmartbot.builder import StrategyBuilder, StrategyTemplate, CodeGenerator
from forexsmartbot.builder.strategy_builder import ComponentType

# Use template
builder = StrategyTemplate.get_template("SMA Crossover")

# Or build custom
builder = StrategyBuilder()
sma_id = builder.add_component(ComponentType.INDICATOR, "SMA", {"period": 20})
signal_id = builder.add_component(ComponentType.SIGNAL, "Signal", {})
builder.connect_components(sma_id, signal_id)

# Generate code
generator = CodeGenerator(builder)
code = generator.generate_code()
print(code)
```

### 9. Strategy Marketplace

```python
from forexsmartbot.marketplace import StrategyMarketplace, StrategyListing
from datetime import datetime

# Create marketplace
marketplace = StrategyMarketplace()

# Add listing
listing = StrategyListing(
    strategy_id="my_strategy_001",
    name="My Awesome Strategy",
    description="A great trading strategy",
    author="Your Name",
    version="1.0.0",
    category="Trend Following",
    tags=["SMA", "Trend"],
    created_at=datetime.now(),
    updated_at=datetime.now()
)
marketplace.add_listing(listing)

# Search
results = marketplace.search_listings(query="SMA", min_rating=4.0)
```

### 10. Multi-Timeframe Strategy

```python
from forexsmartbot.strategies import get_strategy, MultiTimeframeStrategy
from forexsmartbot.adapters.data import YFinanceProvider

# Create base strategy
base_strategy = get_strategy('SMA_Crossover', fast_period=20, slow_period=50)

# Create multi-timeframe wrapper
mtf_strategy = MultiTimeframeStrategy(
    base_strategy=base_strategy,
    timeframes=['1h', '4h', '1d'],
    timeframe_weights={'1h': 0.3, '4h': 0.3, '1d': 0.4}
)

# Set data provider
data_provider = YFinanceProvider()
mtf_strategy.set_data_provider(data_provider)
```

## 🎯 Common Workflows

### Workflow 1: Optimize and Deploy

```python
# 1. Optimize parameters
optimizer = GeneticOptimizer(param_bounds)
best_params, _ = optimizer.optimize(fitness_function)

# 2. Analyze sensitivity
analyzer = ParameterSensitivityAnalyzer()
sensitivity = analyzer.analyze(strategy_factory, best_params, param_ranges, performance)

# 3. Run walk-forward validation
wf_analyzer = WalkForwardAnalyzer()
wf_results = wf_analyzer.analyze(data, strategy_factory, optimize, best_params)

# 4. Monitor in production
monitor = StrategyMonitor()
monitor.register_strategy("OptimizedStrategy")
```

### Workflow 2: Build Custom Strategy

```python
# 1. Build strategy visually
builder = StrategyBuilder()
# ... add components ...

# 2. Validate
is_valid, errors = builder.validate_strategy()

# 3. Generate code
generator = CodeGenerator(builder)
code = generator.generate_code()

# 4. Save and test
# ... save code to file ...
# ... import and test ...

# 5. Share on marketplace
marketplace.add_listing(listing)
```

## ⚠️ Important Notes

1. **ML Strategies**: Require sufficient data (200+ samples) for training
2. **RL Strategies**: Need significant training time (1000+ steps)
3. **Optimization**: Can be resource-intensive for large parameter spaces
4. **Multi-timeframe**: Requires data provider to fetch multiple timeframes
5. **Marketplace**: Uses local JSON storage (can be extended to database)

## 📖 Next Steps

- Read `docs/V3.1.0_FEATURES.md` for detailed feature documentation
- Run `examples/comprehensive_example.py` to see all features in action
- Check individual strategy files for specific parameters
- Review optimization module docstrings for advanced usage

## 🆘 Troubleshooting

### Import Errors
If you get import errors for ML libraries:
```bash
pip install tensorflow torch transformers gymnasium stable-baselines3 optuna deap
```

### Strategy Not Available
Some strategies require optional dependencies. Check `forexsmartbot/strategies/__init__.py` for availability flags.

### Performance Issues
- Reduce `n_simulations` for Monte Carlo
- Use smaller `population_size` for genetic algorithms
- Limit `n_trials` for Optuna optimization

## 📚 Additional Resources

- `examples/strategy_optimization_example.py` - Optimization examples
- `examples/strategy_builder_example.py` - Builder examples
- `examples/comprehensive_example.py` - Full feature demo
- `docs/V3.1.0_FEATURES.md` - Complete feature list
- `docs/V3.1.0_IMPLEMENTATION_COMPLETE.md` - Implementation status


# Quick Reference - v3.1.0 Features

## 🎯 Strategy Selection Guide

### When to Use Each Strategy Type

| Strategy Type | Best For | Requirements |
|--------------|----------|--------------|
| **SMA_Crossover** | Trend following, beginners | None |
| **RSI_Reversion** | Range-bound markets | None |
| **BreakoutATR** | Volatile markets, breakouts | None |
| **LSTM_Strategy** | Time series prediction | TensorFlow, 200+ samples |
| **SVM_Strategy** | Classification-based trading | scikit-learn, 100+ samples |
| **Ensemble_ML** | Robust predictions | scikit-learn, 100+ samples |
| **Transformer** | Pattern recognition | Transformers, 200+ samples |
| **RL_Strategy** | Autonomous learning | Gymnasium, Stable-Baselines3, 500+ samples |
| **Multi_Timeframe** | Multi-timeframe analysis | Data provider for multiple timeframes |

## 🔧 Optimization Tools Quick Reference

### Genetic Algorithm
```python
from forexsmartbot.optimization import GeneticOptimizer

optimizer = GeneticOptimizer(
    param_bounds={'param': (min, max)},
    population_size=50,
    generations=30
)
best_params, fitness = optimizer.optimize(fitness_function)
```

### Hyperparameter Optimization
```python
from forexsmartbot.optimization import HyperparameterOptimizer

optimizer = HyperparameterOptimizer(
    param_space={'param': {'type': 'float', 'low': 0, 'high': 1}},
    n_trials=100
)
best_params, value = optimizer.optimize(objective_function)
```

### Walk-Forward Analysis
```python
from forexsmartbot.optimization import WalkForwardAnalyzer

analyzer = WalkForwardAnalyzer(
    train_period=252,
    test_period=63,
    step_size=21
)
results = analyzer.analyze(data, strategy_factory, optimize, params)
```

### Monte Carlo Simulation
```python
from forexsmartbot.optimization import MonteCarloSimulator

simulator = MonteCarloSimulator(n_simulations=1000, confidence_level=0.95)
results = simulator.simulate(returns, initial_balance=10000.0)
```

### Parameter Sensitivity
```python
from forexsmartbot.optimization import ParameterSensitivityAnalyzer

analyzer = ParameterSensitivityAnalyzer(n_points=10)
results = analyzer.analyze(strategy_factory, base_params, ranges, performance)
```

## 📊 Monitoring Quick Reference

### Strategy Monitor
```python
from forexsmartbot.monitoring import StrategyMonitor

monitor = StrategyMonitor()
monitor.register_strategy("MyStrategy")
monitor.record_signal("MyStrategy", execution_time=0.1)
health = monitor.get_health("MyStrategy")
```

### Performance Tracker
```python
from forexsmartbot.monitoring import PerformanceTracker

tracker = PerformanceTracker()
tracker.record_trade("MyStrategy", trade_data)
metrics = tracker.calculate_metrics("MyStrategy")
```

### Health Checker
```python
from forexsmartbot.monitoring import HealthChecker

checker = HealthChecker(monitor)
health = checker.check("MyStrategy")
```

## 🏗️ Strategy Builder Quick Reference

### Create from Template
```python
from forexsmartbot.builder import StrategyTemplate

builder = StrategyTemplate.get_template("SMA Crossover")
```

### Build Custom
```python
from forexsmartbot.builder import StrategyBuilder, CodeGenerator
from forexsmartbot.builder.strategy_builder import ComponentType

builder = StrategyBuilder()
indicator_id = builder.add_component(ComponentType.INDICATOR, "SMA", {"period": 20})
signal_id = builder.add_component(ComponentType.SIGNAL, "Signal", {})
builder.connect_components(indicator_id, signal_id)

generator = CodeGenerator(builder)
code = generator.generate_code()
```

## 🛒 Marketplace Quick Reference

### Add Listing
```python
from forexsmartbot.marketplace import StrategyMarketplace, StrategyListing

marketplace = StrategyMarketplace()
listing = StrategyListing(...)
marketplace.add_listing(listing)
```

### Search
```python
results = marketplace.search_listings(query="SMA", min_rating=4.0)
```

## 🚀 Common Patterns

### Pattern 1: Optimize and Deploy
```python
# 1. Optimize
optimizer = GeneticOptimizer(param_bounds)
best_params, _ = optimizer.optimize(fitness)

# 2. Create strategy
strategy = get_strategy('SMA_Crossover', **best_params)

# 3. Monitor
monitor = StrategyMonitor()
monitor.register_strategy("OptimizedStrategy")
```

### Pattern 2: Multi-Strategy Ensemble
```python
strategies = [
    get_strategy('SMA_Crossover'),
    get_strategy('RSI_Reversion'),
    get_strategy('Ensemble_ML_Strategy')
]

# Run all and combine signals
```

### Pattern 3: Risk Assessment
```python
# 1. Run backtest
results = backtest_service.run_backtest(...)

# 2. Monte Carlo simulation
returns = calculate_returns(results)
mc_results = monte_carlo.simulate(returns)

# 3. Check VaR/CVaR
print(f"VaR: {mc_results['var']:.4f}")
```

## 📝 Parameter Ranges (Common Strategies)

### SMA_Crossover
- `fast_period`: 10-30
- `slow_period`: 40-80
- `atr_period`: 10-20

### RSI_Reversion
- `rsi_period`: 10-20
- `oversold_level`: 20-40
- `overbought_level`: 60-80

### BreakoutATR
- `lookback_period`: 15-30
- `atr_period`: 10-20
- `atr_multiplier`: 1.0-3.0

## ⚡ Performance Tips

1. **ML Strategies**: Use during development, simpler strategies for production
2. **Optimization**: Run overnight or on separate machines
3. **Monitoring**: Enable only for production strategies
4. **Multi-Timeframe**: Cache data to avoid repeated fetches
5. **Parallel Processing**: Use for multiple backtests

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| Import error for ML strategy | Install dependencies: `pip install tensorflow torch` |
| Strategy not found | Check `list_strategies()` for available strategies |
| Optimization too slow | Reduce population_size or n_trials |
| Memory issues | Use smaller datasets or simpler strategies |
| Training fails | Ensure 200+ samples for ML strategies |

## 📚 File Locations

- **Strategies**: `forexsmartbot/strategies/`
- **Optimization**: `forexsmartbot/optimization/`
- **Monitoring**: `forexsmartbot/monitoring/`
- **Builder**: `forexsmartbot/builder/`
- **Marketplace**: `forexsmartbot/marketplace/`
- **Examples**: `examples/`
- **Configs**: `config/`
- **Scripts**: `scripts/`

## 🎓 Learning Path

1. **Start**: Use existing strategies (`SMA_Crossover`, `RSI_Reversion`)
2. **Optimize**: Learn parameter optimization (`GeneticOptimizer`)
3. **Analyze**: Understand sensitivity (`ParameterSensitivityAnalyzer`)
4. **Validate**: Use walk-forward (`WalkForwardAnalyzer`)
5. **Assess**: Run Monte Carlo (`MonteCarloSimulator`)
6. **Advanced**: Try ML strategies (`LSTM_Strategy`, `Ensemble_ML_Strategy`)
7. **Build**: Create custom strategies (`StrategyBuilder`)
8. **Monitor**: Track performance (`StrategyMonitor`, `PerformanceTracker`)

---

**Quick Links:**
- [Quick Start Guide](QUICK_START_V3.1.0.md)
- [Feature Documentation](V3.1.0_FEATURES.md)
- [Migration Guide](MIGRATION_V3.0_TO_V3.1.md)


# Migration Guide: v3.0.0 to v3.1.0

This guide will help you migrate from ForexSmartBot v3.0.0 to v3.1.0.

## 🔄 Overview

v3.1.0 is **backward compatible** with v3.0.0. Your existing code will continue to work without changes. New features are opt-in.

## 📦 Installation

### Step 1: Update Dependencies

```bash
pip install -r requirements.txt
```

This will install new optional dependencies:
- TensorFlow (for LSTM)
- PyTorch (for deep learning)
- Transformers (for transformer models)
- Gymnasium & Stable-Baselines3 (for RL)
- Optuna (for hyperparameter optimization)
- DEAP (for genetic algorithms)

### Step 2: Verify Installation

```python
from forexsmartbot.strategies import list_strategies
print(list_strategies())
```

You should see new strategies like:
- `LSTM_Strategy`
- `SVM_Strategy`
- `Ensemble_ML_Strategy`
- `Transformer_Strategy`
- `RL_Strategy`
- `Multi_Timeframe`

## 🔧 Code Changes

### No Breaking Changes Required

Your existing code will work as-is:

```python
# This still works exactly as before
from forexsmartbot.strategies import get_strategy
strategy = get_strategy('SMA_Crossover', fast_period=20, slow_period=50)
```

### Optional: Use New Features

#### 1. Try ML Strategies

```python
# Old way (still works)
strategy = get_strategy('ML_Adaptive_SuperTrend')

# New way (optional)
strategy = get_strategy('LSTM_Strategy', lookback_period=60)
strategy = get_strategy('Ensemble_ML_Strategy', n_estimators=100)
```

#### 2. Optimize Parameters

```python
# New feature - optimize your existing strategies
from forexsmartbot.optimization import GeneticOptimizer

param_bounds = {
    'fast_period': (10, 30),
    'slow_period': (40, 80)
}

optimizer = GeneticOptimizer(param_bounds)
best_params, fitness = optimizer.optimize(fitness_function)
```

#### 3. Monitor Strategies

```python
# New feature - monitor strategy health
from forexsmartbot.monitoring import StrategyMonitor

monitor = StrategyMonitor()
monitor.register_strategy("MyStrategy")
monitor.record_signal("MyStrategy", execution_time=0.1)
```

## 📋 Migration Checklist

### Required (No Action Needed)
- ✅ Existing strategies work without changes
- ✅ Existing backtests work without changes
- ✅ Existing UI code works without changes
- ✅ Configuration files remain compatible

### Optional (New Features)
- [ ] Install new dependencies (if using ML strategies)
- [ ] Update strategy selection to include ML strategies
- [ ] Add optimization workflow
- [ ] Integrate monitoring system
- [ ] Use strategy builder for custom strategies

## 🎯 Common Migration Scenarios

### Scenario 1: Using Existing Strategies

**No changes required.** Your code continues to work:

```python
# v3.0.0 code - still works in v3.1.0
from forexsmartbot.strategies import get_strategy
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.adapters.data import YFinanceProvider

strategy = get_strategy('SMA_Crossover', fast_period=20, slow_period=50)
service = BacktestService(YFinanceProvider())
results = service.run_backtest(strategy, 'EURUSD=X', '2023-01-01', '2023-12-31')
```

### Scenario 2: Adding ML Strategies

**Optional enhancement:**

```python
# New in v3.1.0
strategy = get_strategy('Ensemble_ML_Strategy', 
    lookback_period=50,
    n_estimators=100
)
```

### Scenario 3: Optimizing Parameters

**New feature:**

```python
# v3.0.0: Manual parameter tuning
strategy = get_strategy('SMA_Crossover', fast_period=20, slow_period=50)

# v3.1.0: Automated optimization
from forexsmartbot.optimization import GeneticOptimizer

def fitness(params):
    strategy = get_strategy('SMA_Crossover', **params)
    # ... run backtest and return Sharpe ratio ...
    return sharpe_ratio

optimizer = GeneticOptimizer({'fast_period': (10, 30), 'slow_period': (40, 80)})
best_params, _ = optimizer.optimize(fitness)
strategy = get_strategy('SMA_Crossover', **best_params)
```

### Scenario 4: Monitoring Strategies

**New feature:**

```python
# v3.0.0: No monitoring
# Just run strategies

# v3.1.0: Add monitoring
from forexsmartbot.monitoring import StrategyMonitor, HealthChecker

monitor = StrategyMonitor()
monitor.register_strategy("MyStrategy")

# In your trading loop
monitor.record_signal("MyStrategy", execution_time=0.1)

# Check health
health_checker = HealthChecker(monitor)
health = health_checker.check("MyStrategy")
```

## ⚠️ Potential Issues

### Issue 1: Missing Dependencies

**Symptom:** Import errors for ML strategies

**Solution:**
```bash
pip install tensorflow torch transformers gymnasium stable-baselines3 optuna deap
```

### Issue 2: ML Strategy Not Available

**Symptom:** `ValueError: Unknown strategy: LSTM_Strategy`

**Solution:** Check if dependencies are installed. Strategies are conditionally loaded:
```python
from forexsmartbot.strategies import STRATEGIES
print('LSTM_Strategy' in STRATEGIES)  # Should be True if TensorFlow installed
```

### Issue 3: Performance Degradation

**Symptom:** Slower execution with ML strategies

**Solution:** ML strategies require more computation. Consider:
- Using simpler strategies for real-time trading
- Running ML strategies on separate threads
- Using optimization tools during development, not production

## 🔍 Verification

### Test 1: Existing Code Works

```python
# Run your existing code
# Should work without any changes
```

### Test 2: New Features Available

```python
from forexsmartbot.strategies import list_strategies
from forexsmartbot.optimization import GeneticOptimizer
from forexsmartbot.monitoring import StrategyMonitor

# Should not raise errors
strategies = list_strategies()
print(f"Available strategies: {len(strategies)}")
```

### Test 3: ML Strategies Load

```python
try:
    from forexsmartbot.strategies import get_strategy
    strategy = get_strategy('LSTM_Strategy')
    print("✓ ML strategies available")
except (ImportError, ValueError):
    print("⚠ ML strategies require additional dependencies")
```

## 📚 Next Steps

1. **Read Quick Start**: `docs/QUICK_START_V3.1.0.md`
2. **Try Examples**: `examples/comprehensive_example.py`
3. **Explore Features**: Review `docs/V3.1.0_FEATURES.md`
4. **Optimize Strategies**: Use `scripts/optimize_strategy.py`

## 🆘 Support

If you encounter issues:

1. Check dependencies: `pip list | grep -E "tensorflow|torch|optuna|deap"`
2. Review error messages
3. Check documentation: `docs/QUICK_START_V3.1.0.md`
4. Review examples: `examples/`

## ✅ Migration Complete

Once you've:
- ✅ Installed new dependencies (optional)
- ✅ Verified existing code works
- ✅ Tried new features (optional)

You're ready to use v3.1.0!

---

**Remember**: v3.1.0 is backward compatible. You can migrate gradually, using new features as needed.


# Troubleshooting Guide - v3.1.0

## Quick Diagnosis

### Step 1: Validate Installation
```bash
python scripts/validate_installation.py
```

This will check:
- All modules are importable
- Dependencies are installed
- Strategies are available
- Tools are functional

### Step 2: Check Common Issues

## Common Issues and Solutions

### Issue: Import Errors

#### Error: `ModuleNotFoundError: No module named 'tensorflow'`
**Cause**: TensorFlow not installed  
**Solution**:
```bash
pip install tensorflow
```
**Note**: Only needed for LSTM strategies

#### Error: `ModuleNotFoundError: No module named 'optuna'`
**Cause**: Optuna not installed  
**Solution**:
```bash
pip install optuna
```
**Note**: Only needed for hyperparameter optimization

#### Error: `ModuleNotFoundError: No module named 'deap'`
**Cause**: DEAP not installed  
**Solution**:
```bash
pip install deap
```
**Note**: Only needed for genetic algorithm optimization

#### Error: `ModuleNotFoundError: No module named 'forexsmartbot.optimization'`
**Cause**: Module not found  
**Solution**: Check Python path and ensure you're in the project directory

### Issue: Strategy Not Available

#### Error: `ValueError: Unknown strategy: LSTM_Strategy`
**Possible Causes**:
1. Dependencies not installed (TensorFlow)
2. Strategy not in registry
3. Import error in strategy file

**Solutions**:
```python
# Check if strategy is available
from forexsmartbot.strategies import STRATEGIES
print('LSTM_Strategy' in STRATEGIES)  # Should be True

# Check dependencies
try:
    import tensorflow
    print("TensorFlow installed")
except ImportError:
    print("Install TensorFlow: pip install tensorflow")
```

### Issue: ML Strategy Not Training

#### Problem: Strategy always returns 0 (hold)
**Possible Causes**:
1. Insufficient data (< 200 samples)
2. Training failed silently
3. Prediction threshold too high

**Solutions**:
```python
# Check data length
print(f"Data length: {len(df)}")

# Check if trained
print(f"Is trained: {strategy._is_trained}")

# Check prediction threshold
print(f"Threshold: {strategy._prediction_threshold}")

# Ensure enough data
if len(df) < strategy._min_samples:
    print(f"Need at least {strategy._min_samples} samples")
```

### Issue: Optimization Problems

#### Problem: Optimization returns same parameters
**Possible Causes**:
1. Parameter bounds too narrow
2. Fitness function not sensitive
3. Not enough generations/trials
4. Stuck in local optimum

**Solutions**:
```python
# Widen parameter bounds
param_bounds = {
    'fast_period': (5, 50),  # Wider range
    'slow_period': (20, 100)
}

# Increase generations
optimizer = GeneticOptimizer(
    param_bounds, 
    population_size=100,  # Larger population
    generations=50        # More generations
)

# Check fitness function
def fitness(params):
    # Ensure function is sensitive to parameters
    result = run_backtest(params)
    return result  # Should vary with params
```

#### Problem: Optimization too slow
**Solutions**:
```python
# Reduce population size
optimizer = GeneticOptimizer(
    param_bounds,
    population_size=20,  # Smaller
    generations=10        # Fewer
)

# Use smaller dataset for optimization
results = backtest_service.run_backtest(
    strategy, symbol, '2023-01-01', '2023-06-30'  # Shorter period
)
```

### Issue: Backtest Errors

#### Error: `No data available`
**Cause**: Data provider can't fetch data  
**Solutions**:
```python
# Check data provider
data_provider = YFinanceProvider()
df = data_provider.get_data('EURUSD=X', '2023-01-01', '2023-12-31', '1h')
print(f"Data fetched: {len(df)} rows")

# Try different symbol format
# Some providers need 'EURUSD=X', others need 'EURUSD'

# Check date format
# Use 'YYYY-MM-DD' format
```

#### Error: `KeyError: 'Close'`
**Cause**: Data format issue  
**Solutions**:
```python
# Check column names
print(df.columns)

# Ensure proper case
df.columns = df.columns.str.title()

# Check for required columns
required = ['Open', 'High', 'Low', 'Close']
missing = [col for col in required if col not in df.columns]
if missing:
    print(f"Missing columns: {missing}")
```

### Issue: Performance Problems

#### Problem: Backtest very slow
**Possible Causes**:
1. Large dataset
2. ML strategies training
3. Complex calculations

**Solutions**:
```python
# Use smaller dataset
df = df.tail(1000)  # Last 1000 rows

# Disable ML training for quick tests
# Use simpler strategies

# Use parallel processing
service = EnhancedBacktestService(
    data_provider,
    use_parallel=True,
    max_workers=4
)
```

#### Problem: High memory usage
**Solutions**:
```python
# Process data in chunks
for chunk in pd.read_csv('data.csv', chunksize=1000):
    process(chunk)

# Clear cache
import gc
gc.collect()

# Use simpler strategies
# ML strategies use more memory
```

### Issue: Monitoring Problems

#### Problem: Health check always shows "unknown"
**Cause**: No signals recorded  
**Solutions**:
```python
# Ensure signals are being recorded
monitor.record_signal("MyStrategy", execution_time=0.1)

# Check registration
monitor.register_strategy("MyStrategy")

# Check health after recording
health = monitor.get_health("MyStrategy")
print(health.status)
```

#### Problem: Performance metrics are None
**Cause**: No trades recorded  
**Solutions**:
```python
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
```

### Issue: Strategy Builder Problems

#### Problem: Generated code has errors
**Cause**: Invalid component connections  
**Solutions**:
```python
# Validate strategy before generating
is_valid, errors = builder.validate_strategy()
if not is_valid:
    print(f"Errors: {errors}")
    # Fix errors before generating code

# Check component connections
structure = builder.get_strategy_structure()
for comp_id, comp_data in structure['components'].items():
    print(f"{comp_id}: {comp_data['connections']}")
```

### Issue: Marketplace Problems

#### Problem: Can't save listing
**Cause**: Permission or path issue  
**Solutions**:
```python
# Check storage path
marketplace = StrategyMarketplace(storage_path="marketplace")
print(f"Storage path: {marketplace.storage_path}")

# Check permissions
import os
print(f"Writable: {os.access(marketplace.storage_path, os.W_OK)}")

# Use absolute path
marketplace = StrategyMarketplace(storage_path="/absolute/path/marketplace")
```

## Debugging Tips

### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific module
logger = logging.getLogger('forexsmartbot')
logger.setLevel(logging.DEBUG)
```

### Check Strategy State
```python
# Check strategy parameters
print(strategy.params)

# Check if trained (for ML)
if hasattr(strategy, '_is_trained'):
    print(f"Trained: {strategy._is_trained}")

# Check model (for ML)
if hasattr(strategy, '_model'):
    print(f"Model: {strategy._model is not None}")
```

### Validate Data
```python
# Check data quality
print(f"Rows: {len(df)}")
print(f"NaN values: {df.isna().sum().sum()}")
print(f"Columns: {df.columns.tolist()}")
print(f"Date range: {df.index.min()} to {df.index.max()}")
```

### Test Individual Components
```python
# Test strategy indicators
df_with_indicators = strategy.indicators(df)
print(df_with_indicators.columns)

# Test signal generation
signal = strategy.signal(df_with_indicators)
print(f"Signal: {signal}")

# Test volatility
volatility = strategy.volatility(df_with_indicators)
print(f"Volatility: {volatility}")
```

## Getting Help

### 1. Run Validation
```bash
python scripts/validate_installation.py
```

### 2. Check Documentation
- Quick Start: `docs/QUICK_START_V3.1.0.md`
- FAQ: `docs/FAQ.md`
- Quick Reference: `docs/QUICK_REFERENCE.md`

### 3. Review Examples
- Comprehensive: `examples/comprehensive_example.py`
- Integration: `examples/integration_example.py`

### 4. Check Logs
- Look for error messages
- Check execution traces
- Review performance metrics

### 5. Isolate the Problem
```python
# Test minimal case
strategy = get_strategy('SMA_Crossover', fast_period=20, slow_period=50)
print(f"Strategy created: {strategy.name}")

# Test with minimal data
import pandas as pd
df = pd.DataFrame({
    'Open': [1.0, 1.1, 1.2],
    'High': [1.1, 1.2, 1.3],
    'Low': [0.9, 1.0, 1.1],
    'Close': [1.05, 1.15, 1.25]
})
df = strategy.indicators(df)
signal = strategy.signal(df)
print(f"Signal: {signal}")
```

## Error Codes Reference

| Error | Meaning | Solution |
|-------|---------|----------|
| `ModuleNotFoundError` | Dependency missing | Install with pip |
| `ValueError: Unknown strategy` | Strategy not in registry | Check dependencies or strategy name |
| `KeyError: 'Close'` | Data format issue | Check column names |
| `No data available` | Data fetch failed | Check symbol, dates, data provider |
| `Training error` | ML training failed | Check data quality and quantity |
| `Optimization timeout` | Too slow | Reduce parameters or dataset |

## Performance Optimization

### For Slow Backtests
1. Reduce dataset size
2. Use simpler strategies
3. Disable ML training
4. Use parallel processing
5. Cache indicator calculations

### For High Memory Usage
1. Process in chunks
2. Use simpler strategies
3. Clear cache regularly
4. Reduce dataset size
5. Close unused resources

### For Slow Optimization
1. Reduce population size
2. Fewer generations/trials
3. Smaller parameter space
4. Shorter backtest period
5. Use faster fitness function

---

**Still having issues?** Check the FAQ (`docs/FAQ.md`) or review the examples.

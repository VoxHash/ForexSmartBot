# Frequently Asked Questions - v3.1.0

## General Questions

### Q: Is v3.1.0 backward compatible with v3.0.0?
**A:** Yes! v3.1.0 is fully backward compatible. Your existing code will work without any changes. New features are opt-in.

### Q: Do I need to install all the new dependencies?
**A:** No. Core features work without ML dependencies. Install them only if you want to use ML strategies:
- TensorFlow: For LSTM strategies
- PyTorch: For deep learning
- Transformers: For transformer models
- Gymnasium + Stable-Baselines3: For RL strategies
- Optuna: For hyperparameter optimization
- DEAP: For genetic algorithms

### Q: Which strategies require additional dependencies?
**A:** 
- `LSTM_Strategy` - Requires TensorFlow
- `Transformer_Strategy` - Requires Transformers
- `RL_Strategy` - Requires Gymnasium and Stable-Baselines3
- `SVM_Strategy`, `Ensemble_ML_Strategy` - Only require scikit-learn (already in requirements)

### Q: How do I know if a strategy is available?
**A:** 
```python
from forexsmartbot.strategies import list_strategies, STRATEGIES

# List all available strategies
print(list_strategies())

# Check specific strategy
if 'LSTM_Strategy' in STRATEGIES:
    print("LSTM Strategy is available")
```

## Strategy Questions

### Q: How much data do ML strategies need?
**A:** 
- LSTM/Transformer: 200+ samples minimum
- SVM/Ensemble: 100+ samples minimum
- RL: 500+ samples minimum
- Traditional strategies: 20-50 samples

### Q: Why is my ML strategy not generating signals?
**A:** ML strategies need training data. They will return 0 (hold) until they have enough historical data to train. Check:
1. Sufficient data: `len(df) >= min_samples`
2. Training completed: Check strategy's `_is_trained` flag
3. Data quality: Ensure no NaN values

### Q: Can I use ML strategies in production?
**A:** Yes, but consider:
- ML strategies are computationally intensive
- They require sufficient data for training
- Consider using simpler strategies for real-time trading
- Use ML strategies for analysis and optimization

### Q: What's the difference between Ensemble_ML_Strategy and other ML strategies?
**A:** Ensemble combines multiple models (Random Forest + Gradient Boosting) for more robust predictions. It's generally more stable but slower than individual models.

## Optimization Questions

### Q: How long does optimization take?
**A:** Depends on:
- **Genetic Algorithm**: 5-30 minutes (population_size × generations)
- **Optuna**: 10-60 minutes (n_trials)
- **Walk-Forward**: 15-60 minutes (number of periods)
- **Monte Carlo**: 1-5 minutes (n_simulations)

### Q: Can I optimize multiple parameters at once?
**A:** Yes! Both Genetic Optimizer and Hyperparameter Optimizer support multiple parameters:
```python
param_bounds = {
    'fast_period': (10, 30),
    'slow_period': (40, 80),
    'atr_period': (10, 20)
}
```

### Q: What's the difference between Genetic Algorithm and Optuna?
**A:**
- **Genetic Algorithm**: Population-based, good for continuous parameters
- **Optuna**: Tree-structured Parzen Estimator, better for mixed parameter types (int, float, categorical)

### Q: How do I interpret sensitivity analysis results?
**A:**
- **High sensitivity score**: Parameter has large impact on performance
- **Low sensitivity score**: Parameter has minimal impact
- **Optimal value**: Best parameter value found
- **Impact range**: Min/max performance variation

## Monitoring Questions

### Q: Do I need to use monitoring in production?
**A:** Recommended but not required. Monitoring helps:
- Detect strategy failures early
- Track performance metrics
- Identify execution issues
- Monitor strategy health

### Q: How much overhead does monitoring add?
**A:** Minimal (<1ms per signal). Monitoring is lightweight and designed for production use.

### Q: What health statuses are there?
**A:**
- **Healthy**: Strategy working normally
- **Warning**: Some issues detected (moderate errors, slow execution)
- **Critical**: Serious issues (high error count)
- **Unknown**: No recent activity

## Builder Questions

### Q: Can I save strategies built with the builder?
**A:** Yes! The code generator creates Python code that you can save to a file and import:
```python
generator = CodeGenerator(builder)
code = generator.generate_code()
# Save to file
with open('my_strategy.py', 'w') as f:
    f.write(code)
```

### Q: Are builder templates customizable?
**A:** Yes! You can modify templates or create new ones by extending `StrategyTemplate`.

### Q: Can I use the builder without the UI?
**A:** Yes! The builder is a Python API. The UI is a future enhancement.

## Marketplace Questions

### Q: Where is marketplace data stored?
**A:** By default, in a local `marketplace/` directory as JSON files. You can extend this to use a database.

### Q: Can I share strategies privately?
**A:** Currently, marketplace uses local storage. For private sharing, you'd need to implement authentication/authorization.

### Q: How are strategy ratings calculated?
**A:** Simple average of all ratings. Future versions may include weighted averages or Bayesian ratings.

## Performance Questions

### Q: Why is my backtest slow?
**A:** Possible reasons:
- ML strategies require training
- Large datasets
- Complex optimization
- Multiple timeframes

**Solutions:**
- Use simpler strategies for quick tests
- Reduce dataset size
- Use parallel processing (`EnhancedBacktestService`)
- Cache indicator calculations

### Q: Can I run optimizations in parallel?
**A:** Yes! Use `EnhancedBacktestService` with `use_parallel=True`:
```python
service = EnhancedBacktestService(data_provider, use_parallel=True, max_workers=4)
```

### Q: How much memory do ML strategies use?
**A:**
- LSTM: ~100-500 MB (depends on model size)
- Transformer: ~200-1000 MB (depends on model)
- RL: ~50-200 MB
- SVM/Ensemble: ~10-50 MB

## Troubleshooting

### Q: ImportError: No module named 'tensorflow'
**A:** Install TensorFlow: `pip install tensorflow`. This is optional unless using LSTM strategies.

### Q: Strategy not found error
**A:** Check:
1. Strategy name is correct (case-sensitive)
2. Strategy is in registry: `'StrategyName' in STRATEGIES`
3. Dependencies are installed (for ML strategies)

### Q: Optimization returns same parameters
**A:** Possible causes:
- Parameter bounds too narrow
- Fitness function not sensitive to parameters
- Not enough generations/trials
- Local optimum

**Solutions:**
- Widen parameter bounds
- Check fitness function
- Increase generations/trials
- Try different optimization method

### Q: ML strategy always returns 0 (hold)
**A:** Check:
1. Sufficient training data
2. Strategy is trained: `strategy._is_trained == True`
3. Data quality (no NaN, sufficient history)
4. Prediction threshold not too high

### Q: Walk-forward analysis shows poor results
**A:** This might indicate:
- Strategy overfitting to training data
- Market regime changes
- Insufficient training data
- Strategy not robust

**Solutions:**
- Use simpler strategies
- Increase training period
- Add regularization
- Try different time periods

## Best Practices

### Q: What's the recommended workflow?
**A:**
1. Start with simple strategies
2. Optimize parameters
3. Run sensitivity analysis
4. Validate with walk-forward
5. Assess risk with Monte Carlo
6. Monitor in production

### Q: How often should I optimize?
**A:**
- **Development**: Optimize frequently
- **Production**: Re-optimize monthly/quarterly or when market conditions change
- **Real-time**: Use fixed parameters, optimize separately

### Q: Should I use ML strategies for live trading?
**A:** Consider:
- ML strategies need retraining periodically
- They're computationally intensive
- Simpler strategies may be more reliable
- Use ML for analysis, simpler strategies for execution

## Advanced Questions

### Q: Can I combine multiple strategies?
**A:** Yes! Create a custom strategy that combines signals:
```python
class CombinedStrategy(IStrategy):
    def signal(self, df):
        signal1 = strategy1.signal(df)
        signal2 = strategy2.signal(df)
        # Combine logic
        return combined_signal
```

### Q: How do I add custom indicators?
**A:** Extend the strategy's `indicators()` method:
```python
def indicators(self, df):
    df = super().indicators(df)
    df['MyIndicator'] = calculate_my_indicator(df)
    return df
```

### Q: Can I use custom data sources?
**A:** Yes! Implement `IDataProvider` interface:
```python
class MyDataProvider(IDataProvider):
    def get_data(self, symbol, start, end, interval):
        # Your implementation
        return df
```

## Support

### Q: Where can I get help?
**A:**
1. Check documentation: `docs/`
2. Review examples: `examples/`
3. Run validation: `python scripts/validate_installation.py`
4. Check GitHub issues
5. Review code docstrings

### Q: How do I report bugs?
**A:** 
1. Run validation script to verify installation
2. Check if it's a known issue
3. Create GitHub issue with:
   - Error message
   - Steps to reproduce
   - Environment details
   - Validation script output

---

**Last Updated**: January 2026  
**Version**: 3.1.0

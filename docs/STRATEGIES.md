# Trading Strategies

ForexSmartBot includes several built-in trading strategies that can be used for automated trading. Each strategy implements the `IStrategy` interface and can be easily extended or replaced.

## Available Strategies

### 1. SMA Crossover (SMA_Crossover)

A simple moving average crossover strategy that generates buy/sell signals when a fast moving average crosses above/below a slow moving average.

**Parameters:**
- `fast_period` (int): Period for fast SMA (default: 20)
- `slow_period` (int): Period for slow SMA (default: 50)
- `atr_period` (int): Period for ATR calculation (default: 14)

**Signal Logic:**
- Buy signal: Fast SMA crosses above slow SMA
- Sell signal: Fast SMA crosses below slow SMA

**Risk Management:**
- Stop Loss: 2x ATR below/above entry price
- Take Profit: 3x ATR above/below entry price (1.5:1 risk/reward)

### 2. Breakout ATR (BreakoutATR)

A Donchian channel breakout strategy with ATR volatility filter. Generates signals when price breaks above/below the highest/lowest price over a lookback period.

**Parameters:**
- `lookback_period` (int): Period for Donchian channels (default: 20)
- `atr_period` (int): Period for ATR calculation (default: 14)
- `atr_multiplier` (float): ATR filter multiplier (default: 1.5)
- `min_breakout_pct` (float): Minimum breakout percentage (default: 0.001)

**Signal Logic:**
- Buy signal: Price breaks above Donchian high
- Sell signal: Price breaks below Donchian low
- Only trades if volatility is above minimum threshold

**Risk Management:**
- Stop Loss: Donchian low/high
- Take Profit: 2x ATR from entry (2:1 risk/reward)

### 3. RSI Reversion (RSI_Reversion)

A mean reversion strategy using RSI with trend filter. Generates signals when RSI reaches oversold/overbought levels in the direction of the trend.

**Parameters:**
- `rsi_period` (int): Period for RSI calculation (default: 14)
- `oversold_level` (float): RSI oversold threshold (default: 30)
- `overbought_level` (float): RSI overbought threshold (default: 70)
- `trend_period` (int): Period for trend filter SMA (default: 50)
- `atr_period` (int): Period for ATR calculation (default: 14)

**Signal Logic:**
- Buy signal: RSI crosses above oversold level in uptrend
- Sell signal: RSI crosses below overbought level in downtrend
- Trend filter: Only trade in direction of longer-term trend

**Risk Management:**
- Stop Loss: 1.5x ATR below/above entry price
- Take Profit: RSI-based target levels

## Strategy Development

### Creating a Custom Strategy

To create a new strategy, implement the `IStrategy` interface:

```python
from forexsmartbot.core.interfaces import IStrategy
import pandas as pd
from typing import Dict, Any, Optional

class MyCustomStrategy(IStrategy):
    def __init__(self, param1: float = 1.0, param2: int = 10):
        self._param1 = param1
        self._param2 = param2
        self._name = "My Custom Strategy"
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'param1': self._param1,
            'param2': self._param2
        }
    
    def set_params(self, **kwargs) -> None:
        if 'param1' in kwargs:
            self._param1 = float(kwargs['param1'])
        if 'param2' in kwargs:
            self._param2 = int(kwargs['param2'])
    
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Calculate your indicators here
        out = df.copy()
        # Add your indicator calculations
        return out
    
    def signal(self, df: pd.DataFrame) -> int:
        # Return +1 for buy, -1 for sell, 0 for hold
        # Your signal logic here
        return 0
    
    def volatility(self, df: pd.DataFrame) -> Optional[float]:
        # Return volatility measure for position sizing
        # Return None if volatility cannot be calculated
        return None
    
    def stop_loss(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        # Calculate stop loss price
        # Return None if no stop loss
        return None
    
    def take_profit(self, df: pd.DataFrame, entry_price: float, side: int) -> Optional[float]:
        # Calculate take profit price
        # Return None if no take profit
        return None
```

### Registering a Strategy

Add your strategy to the registry in `forexsmartbot/strategies/__init__.py`:

```python
from .my_custom_strategy import MyCustomStrategy

STRATEGIES = {
    'SMA_Crossover': SMACrossover,
    'BreakoutATR': BreakoutATR,
    'RSI_Reversion': RSIRevertion,
    'MyCustom': MyCustomStrategy,  # Add your strategy here
}
```

## Strategy Parameters

### Parameter Types

- **int**: Integer parameters (periods, lookback windows)
- **float**: Floating-point parameters (thresholds, multipliers)
- **bool**: Boolean parameters (enable/disable features)

### Parameter Validation

Strategies should validate their parameters in the `set_params` method:

```python
def set_params(self, **kwargs) -> None:
    if 'period' in kwargs:
        period = int(kwargs['period'])
        if period < 1:
            raise ValueError("Period must be >= 1")
        self._period = period
```

### Parameter Ranges

Common parameter ranges:
- **Periods**: 1-200 (typical range for technical indicators)
- **Thresholds**: 0.0-100.0 (for percentage-based thresholds)
- **Multipliers**: 0.1-10.0 (for ATR and volatility multipliers)

## Performance Considerations

### Indicator Calculation

- Use vectorized operations with pandas/numpy when possible
- Cache expensive calculations when appropriate
- Avoid recalculating indicators for the same data

### Signal Generation

- Keep signal logic simple and fast
- Avoid complex nested conditions
- Use early returns for performance

### Memory Usage

- Don't store large amounts of historical data in strategy objects
- Use efficient data structures
- Clean up unused data regularly

## Testing Strategies

### Unit Tests

Create tests for your strategy:

```python
import pytest
import pandas as pd
from forexsmartbot.strategies.my_custom_strategy import MyCustomStrategy

def test_my_custom_strategy():
    strategy = MyCustomStrategy(param1=1.5, param2=20)
    
    # Test with sample data
    df = pd.DataFrame({
        'Close': [100, 101, 102, 101, 100],
        'High': [101, 102, 103, 102, 101],
        'Low': [99, 100, 101, 100, 99],
        'Volume': [1000, 1100, 1200, 1100, 1000]
    })
    
    # Test indicators
    result_df = strategy.indicators(df)
    assert 'MyIndicator' in result_df.columns
    
    # Test signal
    signal = strategy.signal(result_df)
    assert signal in [-1, 0, 1]
    
    # Test volatility
    volatility = strategy.volatility(result_df)
    assert volatility is None or volatility > 0
```

### Backtesting

Test your strategy with historical data:

```python
from forexsmartbot.services.backtest import BacktestService
from forexsmartbot.adapters.data import YFinanceProvider

# Run backtest
data_provider = YFinanceProvider()
backtest_service = BacktestService(data_provider)

result = backtest_service.run_backtest(
    strategy=MyCustomStrategy(),
    symbol='EURUSD',
    start_date='2023-01-01',
    end_date='2023-12-31'
)

print(f"Total Return: {result['total_return']:.2%}")
print(f"Max Drawdown: {result['max_drawdown']:.2%}")
print(f"Win Rate: {result['win_rate']:.2%}")
```

## Best Practices

### Signal Quality

- Avoid over-optimization
- Test on out-of-sample data
- Consider market conditions
- Use multiple timeframes when appropriate

### Risk Management

- Always implement stop losses
- Use appropriate position sizing
- Consider correlation between symbols
- Monitor drawdown limits

### Code Quality

- Write clear, documented code
- Use type hints
- Follow PEP 8 style guidelines
- Add comprehensive tests

### Performance

- Profile your strategy for bottlenecks
- Use efficient algorithms
- Minimize memory usage
- Consider execution speed

## Common Pitfalls

### Overfitting

- Don't optimize too many parameters
- Use walk-forward analysis
- Test on different market conditions
- Avoid curve fitting

### Data Leakage

- Don't use future data for past signals
- Be careful with indicator calculations
- Validate your data pipeline
- Check for look-ahead bias

### Risk Management

- Don't ignore position sizing
- Implement proper stop losses
- Monitor correlation risk
- Consider market impact

### Performance

- Don't ignore execution costs
- Consider slippage and spreads
- Test with realistic data
- Monitor resource usage

# Risk Management

ForexSmartBot includes a comprehensive risk management system designed to protect capital and manage trading risk effectively. This document explains the risk management features and how to configure them.

## Overview

The risk management system consists of several layers:

1. **Position Sizing**: Dynamic position sizing based on volatility and risk parameters
2. **Drawdown Control**: Protection against excessive drawdowns
3. **Daily Risk Limits**: Limits on daily losses
4. **Symbol-Specific Risk**: Different risk parameters for different symbols
5. **Strategy Risk Multipliers**: Adjustable risk for different strategies

## Risk Configuration

### Basic Risk Parameters

```python
from forexsmartbot.core.risk_engine import RiskConfig

config = RiskConfig(
    base_risk_pct=0.02,        # Base risk per trade (2%)
    max_risk_pct=0.05,         # Maximum risk per trade (5%)
    daily_risk_cap=0.05,       # Daily risk limit (5%)
    max_drawdown_pct=0.25,     # Maximum drawdown (25%)
    min_trade_amount=10.0,     # Minimum trade amount
    max_trade_amount=100.0,    # Maximum trade amount
)
```

### Advanced Risk Parameters

```python
config = RiskConfig(
    # ... basic parameters ...
    
    # Symbol-specific risk multipliers
    symbol_risk_multipliers={
        'EURUSD': 1.0,      # Standard risk
        'GBPUSD': 1.2,      # Higher risk (more volatile)
        'USDJPY': 0.8,      # Lower risk (less volatile)
    },
    
    # Strategy-specific risk multipliers
    strategy_risk_multipliers={
        'SMA_Crossover': 1.0,      # Standard risk
        'BreakoutATR': 1.5,        # Higher risk (more aggressive)
        'RSI_Reversion': 0.7,      # Lower risk (more conservative)
    },
    
    # Kelly Criterion settings
    kelly_fraction=0.25,           # Conservative Kelly fraction
    
    # Volatility targeting
    volatility_target=0.01,        # Target daily volatility (1%)
    
    # Drawdown recovery
    drawdown_recovery_pct=0.10,    # Recovery threshold (10%)
)
```

## Position Sizing

### Base Position Sizing

The base position size is calculated as:

```
position_size = balance * base_risk_pct * symbol_multiplier * strategy_multiplier
```

### Volatility Targeting

When volatility data is available, position size is adjusted to target a specific daily volatility:

```
vol_target_size = base_size * (target_volatility / current_volatility)
```

### Kelly Criterion

For strategies with known win rates, the Kelly Criterion is applied:

```
kelly_fraction = max(0, 2 * win_rate - 1)
kelly_size = balance * kelly_fraction * kelly_multiplier
```

### Final Position Size

The final position size is the minimum of:
- Base position size
- Volatility-targeted size
- Kelly-sized position
- Maximum trade amount

## Drawdown Control

### Drawdown Monitoring

The system continuously monitors:
- Current equity vs. peak equity
- Rolling drawdown over recent trades
- Maximum historical drawdown

### Drawdown Throttle

When drawdown exceeds the limit:
- Position sizes are reduced by 50%
- New trades may be restricted
- Recovery threshold must be reached to resume normal trading

### Recovery Mechanism

The throttle is lifted when:
- Current drawdown falls below `max_drawdown_pct - drawdown_recovery_pct`
- This prevents rapid re-entry after drawdown

## Daily Risk Limits

### Daily PnL Tracking

The system tracks:
- Realized PnL from completed trades
- Unrealized PnL from open positions
- Total daily PnL

### Risk Limit Enforcement

When daily losses exceed the limit:
- New trades are blocked
- Existing positions may be closed
- Alert is generated

### Daily Reset

Risk limits reset at the start of each trading day.

## Symbol-Specific Risk

### Risk Multipliers

Different symbols can have different risk profiles:

```python
symbol_risk_multipliers = {
    'EURUSD': 1.0,      # Major pair - standard risk
    'GBPUSD': 1.2,      # More volatile - higher risk
    'USDJPY': 0.8,      # Less volatile - lower risk
    'AUDUSD': 1.1,      # Commodity currency - slightly higher risk
}
```

### Correlation Risk

Consider correlation between symbols:
- Highly correlated pairs increase portfolio risk
- Diversification reduces overall risk
- Monitor correlation in portfolio mode

## Strategy Risk Multipliers

### Strategy-Specific Risk

Different strategies can have different risk profiles:

```python
strategy_risk_multipliers = {
    'SMA_Crossover': 1.0,      # Trend following - standard risk
    'BreakoutATR': 1.5,        # Breakout - higher risk
    'RSI_Reversion': 0.7,      # Mean reversion - lower risk
}
```

### Strategy Performance

Risk multipliers can be adjusted based on:
- Historical performance
- Win rate
- Maximum drawdown
- Sharpe ratio

## Risk Monitoring

### Real-Time Monitoring

The system provides real-time risk metrics:

```python
risk_summary = risk_engine.get_risk_summary()

print(f"Daily PnL: {risk_summary['daily_pnl']:.2f}")
print(f"Current Drawdown: {risk_summary['current_drawdown']:.2%}")
print(f"Drawdown Throttle: {risk_summary['drawdown_throttle']}")
print(f"Recent Win Rate: {risk_summary['recent_win_rate']:.2%}")
```

### Risk Alerts

The system generates alerts for:
- Drawdown limit exceeded
- Daily risk limit exceeded
- Unusual volatility
- Strategy performance degradation

## Portfolio Risk

### Portfolio-Level Risk

In portfolio mode, risk is managed at the portfolio level:

```python
# Total portfolio risk
total_risk = sum(symbol_risk for symbol_risk in symbol_risks)

# Correlation-adjusted risk
correlation_risk = total_risk * correlation_factor

# Portfolio drawdown
portfolio_drawdown = (peak_equity - current_equity) / peak_equity
```

### Risk Allocation

Risk is allocated across:
- Symbols (based on volatility and correlation)
- Strategies (based on performance and risk profile)
- Time (based on market conditions)

## Risk Reporting

### Daily Risk Report

The system generates daily risk reports:

```
=== DAILY RISK REPORT ===
Date: 2023-12-01
Portfolio Value: $10,500.00
Daily PnL: -$150.00
Current Drawdown: 2.5%
Max Drawdown: 8.2%
Risk Status: NORMAL

Symbol Risk:
- EURUSD: $200.00 (1.9%)
- GBPUSD: $180.00 (1.7%)
- USDJPY: $120.00 (1.1%)

Strategy Risk:
- SMA_Crossover: $300.00 (2.9%)
- BreakoutATR: $200.00 (1.9%)
```

### Risk Metrics

Key risk metrics:
- **VaR (Value at Risk)**: Potential loss over time horizon
- **Expected Shortfall**: Expected loss beyond VaR
- **Sharpe Ratio**: Risk-adjusted return
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Calmar Ratio**: Return / Maximum Drawdown

## Risk Limits by Account Size

### Small Accounts (< $10,000)

```python
config = RiskConfig(
    base_risk_pct=0.01,        # 1% per trade
    max_risk_pct=0.02,         # 2% maximum
    daily_risk_cap=0.03,       # 3% daily limit
    max_drawdown_pct=0.15,     # 15% max drawdown
)
```

### Medium Accounts ($10,000 - $100,000)

```python
config = RiskConfig(
    base_risk_pct=0.02,        # 2% per trade
    max_risk_pct=0.05,         # 5% maximum
    daily_risk_cap=0.05,       # 5% daily limit
    max_drawdown_pct=0.20,     # 20% max drawdown
)
```

### Large Accounts (> $100,000)

```python
config = RiskConfig(
    base_risk_pct=0.015,       # 1.5% per trade
    max_risk_pct=0.03,         # 3% maximum
    daily_risk_cap=0.04,       # 4% daily limit
    max_drawdown_pct=0.15,     # 15% max drawdown
)
```

## Risk Management Best Practices

### 1. Start Conservative

- Begin with low risk parameters
- Gradually increase as you gain experience
- Monitor performance closely

### 2. Diversify

- Trade multiple symbols
- Use different strategies
- Avoid over-concentration

### 3. Monitor Continuously

- Check risk metrics daily
- Review performance weekly
- Adjust parameters monthly

### 4. Use Stop Losses

- Always set stop losses
- Use appropriate stop loss levels
- Don't move stops against you

### 5. Manage Drawdown

- Set maximum drawdown limits
- Reduce size during drawdowns
- Take breaks if needed

### 6. Test Thoroughly

- Backtest with realistic data
- Use walk-forward analysis
- Test in paper trading first

## Common Risk Management Mistakes

### 1. Over-Leverage

- Don't risk too much per trade
- Consider correlation between positions
- Monitor total exposure

### 2. Ignoring Drawdown

- Don't ignore growing drawdowns
- Reduce size when losing
- Take breaks if needed

### 3. Revenge Trading

- Don't increase size after losses
- Stick to your risk parameters
- Take breaks after big losses

### 4. Over-Optimization

- Don't over-optimize parameters
- Use out-of-sample testing
- Consider market conditions

### 5. Ignoring Correlation

- Don't ignore correlation between symbols
- Diversify across different asset classes
- Monitor portfolio correlation

## Emergency Procedures

### Market Crash

1. Close all positions immediately
2. Assess damage
3. Review risk parameters
4. Resume with reduced size

### System Failure

1. Stop all trading
2. Check system status
3. Verify positions
4. Resume when stable

### Extreme Volatility

1. Reduce position sizes
2. Increase stop losses
3. Monitor closely
4. Consider closing positions

## Risk Management Tools

### Risk Calculator

```python
from forexsmartbot.core.risk_engine import RiskEngine

# Calculate position size
risk_engine = RiskEngine(config)
position_size = risk_engine.calculate_position_size(
    symbol='EURUSD',
    strategy='SMA_Crossover',
    balance=10000,
    volatility=0.01,
    win_rate=0.6
)
```

### Risk Monitor

```python
# Monitor risk in real-time
risk_summary = risk_engine.get_risk_summary()
if risk_summary['drawdown_throttle']:
    print("WARNING: Drawdown throttle active!")
```

### Risk Alerts

```python
# Set up risk alerts
if risk_engine.check_daily_risk_limit(daily_pnl, balance):
    send_alert("Daily risk limit exceeded!")
```

## Conclusion

Effective risk management is essential for successful trading. The ForexSmartBot risk management system provides comprehensive tools to protect capital and manage risk effectively. Always start with conservative parameters and gradually increase as you gain experience and confidence.

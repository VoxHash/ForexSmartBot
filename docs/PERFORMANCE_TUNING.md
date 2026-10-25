# Performance Tuning Guide

Canonical performance and memory guide for ForexSmartBot.

## Targets

- Startup time: < 2s
- Signal generation: < 100ms
- Trade execution path: < 200ms
- UI response: < 50ms
- Memory usage: < 500MB without heavy ML models

## Runtime Profile Recommendations

### Live / Sniper Trading
- Prefer traditional strategies (SMA/RSI/Breakout/Scalping MA)
- Use shorter intervals only when broker/data latency is stable
- Keep concurrent positions bounded
- Avoid running model training in live execution loops

### Analysis / Backtesting
- Use ML strategies (LSTM/Transformer/RL) in backtests or research sessions
- Enable parallel backtesting where available
- Restrict dataset ranges during parameter sweeps

## Memory Optimization

- Keep bounded history for portfolio/trade state
- Use rolling windows instead of unbounded in-memory series
- Clear cached indicator/model artifacts between long test runs
- Track memory periodically during optimization sessions

## Optional Rust native core (`fsb_core`)

Indicator and compact backtest loops are CPU-bound and run often during strategy evaluation. The optional Rust extension under `native/fsb_core` (PyO3 + rayon) offloads SMA/EMA/ATR/RSI/MACD/Bollinger/Stochastic, batch SMA, SMA/EMA-crossover and MACD-signal equity curves, **Bollinger mean-reversion equity/sweeps**, **Stochastic %K/%D crossover equity/sweeps**, **walk-forward / grid parameter sweeps**, **RSI mean-reversion equity/sweeps**, and **multi-symbol equity aggregation** so the PyQt process shares the machine more cleanly with other apps. PyPI wheels cover Linux, Windows, and macOS.

```bash
pip install fsb-core
# or: pip install maturin && cd native/fsb_core && maturin develop --release
python -c "from forexsmartbot.utils.native_indicators import native_status; print(native_status())"
```

Call sites: `forexsmartbot.utils.native_indicators` (`sma`, `ema`, `atr`, `rsi`, `macd`, `bollinger`, `stochastic`, `batch_sma`, `equity_sma_crossover`, `equity_ema_crossover`, `equity_macd_crossover`, `equity_bollinger_mean_reversion`, `equity_stochastic_crossover`, `sweep_sma_crossover`, `sweep_ema_crossover`, `sweep_macd`, `sweep_bollinger_mean_reversion`, `sweep_stochastic_crossover`, `sweep_rsi_mean_reversion`, `walk_forward_sma_sweep`, `multi_symbol_equity_aggregate`), wired into `SMACrossover` / core `Strategy` indicators and `CalculationEngine.fast_rolling_mean`. If the module is missing, NumPy (and Numba where already used) remains the path — no mocks.

## Data Provider Optimization

- Configure provider fallback chain via `MultiProvider`
- Use provider keys via environment variables for paid/official feeds
- Validate provider availability before live sessions

## Practical Checklist

- Verify broker/data connectivity before session start
- Use the settings connection tests
- Run only required modules (disable unused heavy features)
- Monitor logs for timeout/retry loops
- Keep strategy set minimal for latency-critical sessions

## Related Docs

- `docs/DATA_PROVIDERS_SETUP.md`
- `docs/TESTING.md`
- `docs/TROUBLESHOOTING.md`

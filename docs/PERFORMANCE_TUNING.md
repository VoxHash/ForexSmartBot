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

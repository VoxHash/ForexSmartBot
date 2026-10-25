# fsb_core

Optional Rust (PyO3) extension for ForexSmartBot indicator and equity hot paths.

**0.4.0** adds EMA + MACD indicators and EMA/MACD crossover equity sweeps (on top of 0.3.x RSI mean-reversion and 0.2.x SMA walk-forward / multi-symbol workers).

## Build

```bash
# Requires rustup + maturin
pip install maturin
maturin develop --release
```

## Smoke test

```bash
python -c "import fsb_core; print(fsb_core.__version__, fsb_core.ema([1,2,3,4,5], 3))"
python -c "from forexsmartbot.utils.native_indicators import sweep_ema_crossover, sweep_macd; import numpy as np; c=np.linspace(1.1,1.2,200); print(sweep_ema_crossover(c,[5,8],[15,20]).shape, sweep_macd(c,[8],[17],[5]).shape)"
```

Python wrappers with NumPy fallback live in `forexsmartbot.utils.native_indicators`.

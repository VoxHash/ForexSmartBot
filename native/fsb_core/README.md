# fsb_core

Optional Rust (PyO3) extension for ForexSmartBot indicator and equity hot paths.

**0.5.0** adds Bollinger Bands + mean-reversion equity/sweeps and multi-platform PyPI wheels (on top of 0.4.x EMA/MACD, 0.3.x RSI mean-reversion, and 0.2.x SMA walk-forward / multi-symbol workers).

## Install (PyPI)

```bash
pip install fsb-core
```

## Build from source

```bash
# Requires rustup + maturin
pip install maturin
maturin develop --release
```

## Smoke test

```bash
python -c "import fsb_core; print(fsb_core.__version__, fsb_core.bollinger([1,2,3,4,5,6,7,8,9,10], 5, 2.0)[0][-1])"
python -c "from forexsmartbot.utils.native_indicators import sweep_bollinger_mean_reversion; import numpy as np; c=np.linspace(1.1,1.2,200); print(sweep_bollinger_mean_reversion(c,[10,20],[1.5,2.0]).shape)"
```


Python wrappers with NumPy fallback live in `forexsmartbot.utils.native_indicators`.

# fsb_core

Optional Rust (PyO3) extension for ForexSmartBot indicator and equity hot paths.

**0.6.0** adds Stochastic Oscillator `%K`/`%D` + crossover equity/sweeps (on top of 0.5.x Bollinger, 0.4.x EMA/MACD, 0.3.x RSI mean-reversion, and 0.2.x SMA walk-forward / multi-symbol workers).

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
python -c "import fsb_core; print(fsb_core.__version__, fsb_core.stochastic([1,2,3,4,5,6,7,8,9,10],[1,2,3,4,5,6,7,8,9,10],[1,2,3,4,5,6,7,8,9,10], 5, 3)[0][-1])"
python -c "from forexsmartbot.utils.native_indicators import sweep_stochastic_crossover; import numpy as np; c=np.linspace(1.1,1.2,200); print(sweep_stochastic_crossover(c,[10,14],[3,5]).shape)"
```


Python wrappers with NumPy fallback live in `forexsmartbot.utils.native_indicators`.

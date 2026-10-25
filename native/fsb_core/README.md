# fsb_core

Optional Rust (PyO3) extension for ForexSmartBot indicator and equity hot paths.

**0.2.0** adds rayon-backed SMA-crossover parameter sweeps, walk-forward window sweeps, and multi-symbol portfolio aggregation workers.

## Build

```bash
# Requires rustup + maturin
pip install maturin
maturin develop --release
```

## Smoke test

```bash
python -c "import fsb_core; print(fsb_core.__version__, fsb_core.sma([1,2,3,4,5], 3))"
python -c "from forexsmartbot.utils.native_indicators import sweep_sma_crossover, walk_forward_windows; import numpy as np; c=np.linspace(1.1,1.2,200); print(sweep_sma_crossover(c,[5,8],[15,20]).shape)"
```

Python wrappers with NumPy fallback live in `forexsmartbot.utils.native_indicators`.

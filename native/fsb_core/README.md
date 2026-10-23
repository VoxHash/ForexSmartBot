# fsb_core

Optional Rust (PyO3) extension for ForexSmartBot indicator and equity hot paths.

## Build

```bash
# Requires rustup + maturin
pip install maturin
maturin develop --release
```

## Smoke test

```bash
python -c "import fsb_core; print(fsb_core.__version__, fsb_core.sma([1,2,3,4,5], 3))"
```

Python wrappers with NumPy fallback live in `forexsmartbot.utils.native_indicators`.

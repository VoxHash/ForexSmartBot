# Roadmap — ForexSmartBot

High-level milestones aligned with the current **3.2.x** line (latest **3.2.3**). See [CHANGELOG.md](CHANGELOG.md) for shipped work.

## Completed (3.2.0)
- Interactive Brokers TWS broker adapter and settings connection test
- Twelve Data and Stooq data providers with multi-provider fallback
- Fear Index strategy with documented mathematical specification
- Trading-path memory and execution performance improvements
- CI workflow updates (GitHub Actions v4)

## Q4 2026
- [x] Fix multi-timeframe strategy registration (`IDataProvider` via `core.interfaces`; `get_strategy('Multi_Timeframe')` works without kwargs; no `adapters.data`/`zmq` import dependency)
- [x] Linux-friendly optional dependencies (`win10toast` / platform markers in `requirements.txt`)
- [x] Expand automated tests beyond placeholder `tests/` package (MTF, strategy registry, native_indicators NumPy fallback, risk, config)
- [x] PyPI publish parity with source install (document Python 3.10–3.12)

## Q1 2027
- [x] Advanced analytics dashboard (UI polish and live metrics) — live KPI cards + portfolio/risk tables (`build_live_metrics` / `PortfolioAnalyticsWidget`); risk dialog loads portfolio trades; main-window refresh hook
- [ ] Strategy backtesting UI improvements
- [ ] Remote monitoring and cloud sync hardening

## Q2 2027
- Mobile monitoring companion (read-only portfolio/alerts)
- Web dashboard for strategy health

## Native performance core (in progress)
- **Rust (`native/fsb_core` via PyO3/maturin)** for indicator math (SMA/ATR/RSI), rayon batch SMA, and a compact SMA-crossover equity loop — chosen over Go/Zig/C for memory safety + strong Python interop; Ruby is a poor fit for this CPU-bound goal.
- Optional build: `cd native/fsb_core && maturin develop --release`. Python call sites fall back to NumPy when the extension is missing.
- Further candidates: walk-forward parameter sweeps and multi-symbol aggregation workers (keep PyQt on the Python side).

## Future — Android / GrapheneOS
- **Companion app** (not a full trading rewrite): read-only portfolio, P&L, and alert push while the desktop PyQt bot remains the execution host.
- Prefer a **hardened Android** path (GrapheneOS-friendly): minimal permissions, no unnecessary trackers, local-first sync over TLS to the existing cloud/API surface when enabled.
- Realistic scope: status/monitor + approve/reject high-level actions; broker keys and order routing stay on the desktop (or a trusted always-on host), not on the phone.
- Tech TBD after API hardening: Kotlin client talking to the current remote-monitor / cloud endpoints.

## Future
- Social / copy trading and marketplace growth
- Multi-asset support (equities, crypto) where data providers allow
- Enterprise and compliance tooling (audit logs, role-based access)

For historical goals, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and version feature docs under `docs/V3.*_FEATURES.md`.

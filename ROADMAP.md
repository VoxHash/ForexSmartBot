# Roadmap — ForexSmartBot

High-level milestones aligned with the current **3.3.x** line (latest **3.3.8**). See [CHANGELOG.md](CHANGELOG.md) for shipped work.

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
- [x] CI / Strategy Tests infra: optional TA-Lib + heavy ML (`FSB_SKIP_HEAVY_ML`), mplfinance pin, module-style strategy pipeline invoke

## Q1 2027
- [x] Advanced analytics dashboard (UI polish and live metrics) — live KPI cards + portfolio/risk tables (`build_live_metrics` / `PortfolioAnalyticsWidget`); risk dialog loads portfolio trades; main-window refresh hook
- [x] Strategy backtesting UI improvements — KPI cards, equity curve tab, trades table, date presets, cancel, JSON/CSV export; combo stores strategy id via `userData`
- [x] Remote monitoring and cloud sync hardening — auth (Bearer/`X-API-Key`, constant-time), `/healthz` + monitor health, sync retry/backoff + pending queue + auto-sync thread, JWT/PBKDF2 security fixes, docs + `tests/test_cloud_hardening.py` (first production-ready slice; hosted multi-tenant cloud backend and full mobile companion remain Q2+)

## Q2 2027
- [x] Mobile monitoring companion (read-only portfolio/alerts) — first slice: `CompanionAPI` at `/api/v1/companion/*` (portfolio, positions, alerts, strategies, webhook register); mounted on `RemoteMonitorServer`; GrapheneOS-friendly `WebhookNotifier` (HTTPS, no FCM required); Android Kotlin scaffold under `mobile/android-companion/` (Retrofit client, no Play Services). Full store-ready Android UX / push UX still open.
- [x] Web dashboard for strategy health — `GET /api/v1/strategies` (+ per-name), `StrategyMonitor.get_dashboard_payload()` / `StrategyHealth.to_dict()`, remote-monitor HTML Strategy Health table with live poll. Further polish (history charts, multi-host) still open.
- [x] **Q2 polish (3.3.1)**: strategy history charts API + dashboard sparklines; QR pairing session/redeem; companion approve/reject action queue; Android Compose UI + ZXing QR image pairing + cert pinning hooks; F-Droid metadata draft.
- [x] **Q2 hardening (3.3.2)**: live CameraX QR; encrypted local session/portfolio cache; production cert-pin defaults (`FSB_COMPANION_CERT_PIN`, `-PFSB_CERT_PINS`); multi-host dashboard poll; companion **0.3.0**. Remaining: published F-Droid / Play listing (external store submit).

## Native performance core
- [x] **Indicators + equity (fsb_core 0.1.x)**: SMA/ATR/RSI, rayon batch SMA, compact SMA-crossover equity loop (PyO3/maturin; NumPy fallback).
- [x] **Walk-forward + multi-symbol (3.3.3 / fsb_core 0.2.0)**: parallel SMA parameter grid sweep, walk-forward train/test window sweep, multi-symbol equity aggregation workers (PyQt stays on Python side).
- [x] **RSI mean-reversion + CI wheels (3.3.4 / fsb_core 0.3.0)**: RSI mean-reversion equity + parallel parameter sweep; maturin `fsb_core` wheels as CI artifacts.
- [x] **EMA / MACD kernels (3.3.5 / fsb_core 0.4.0)**: EMA + MACD indicators; EMA-crossover and MACD-signal equity + parallel sweeps; Actions pinned to `ubuntu-24.04`.
- [x] **Publish fsb_core to PyPI (3.3.6 / fsb-core 0.4.0)**: `pip install fsb-core`; `publish-fsb-core.yml` for multi-Python manylinux wheels on `fsb-core-v*` tags.
- [x] **Bollinger + multi-platform wheels (3.3.7 / fsb-core 0.5.0)**: Bollinger Bands indicator + mean-reversion equity/sweep; `publish-fsb-core.yml` builds Linux + Windows + macOS (arm64/x86_64) wheels for Python 3.10–3.13.
- [x] **Stochastic kernels (3.3.8 / fsb-core 0.6.0)**: Stochastic Oscillator `%K`/`%D` + `%K/%D` crossover equity/sweep (`stochastic`, `equity_stochastic_crossover`, `sweep_stochastic_crossover`).
- Optional build: `cd native/fsb_core && maturin develop --release` (or `pip install fsb-core`).
- Further candidates (later): Donchian channel kernels; Linux aarch64 cross wheels.

## Future — Android / GrapheneOS
- [x] **API + scaffold (3.3.0)**: Kotlin client talks to remote-monitor `/api/v1/companion/*`; webhook alerts; no Google deps in scaffold; broker keys stay on desktop.
- [x] **Compose + pairing + approve/reject + pinning hooks (3.3.1)**: Material3 UI; QR paste / gallery decode (ZXing); action requests with host approve/reject; OkHttp `CertificatePinner` via `CERT_PINS` / pairing pin; F-Droid metadata draft.
- [x] **CameraX + encrypted cache + pin defaults (3.3.2)**: live QR scan; EncryptedSharedPreferences; host/Gradle production pin env; multi-host dashboard.
- Remaining: published F-Droid / Play store listing (metadata draft ready; submit outside this repo).

## Future
- Social / copy trading and marketplace growth
- Multi-asset support (equities, crypto) where data providers allow
- Enterprise and compliance tooling (audit logs, role-based access)

For historical goals, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and version feature docs under `docs/V3.*_FEATURES.md`.

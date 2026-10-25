# Roadmap — ForexSmartBot

High-level milestones aligned with the current **3.4.x** line (latest **3.4.0**; prior **3.3.9**). See [CHANGELOG.md](CHANGELOG.md) for shipped work.

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
- [x] **Donchian + Linux aarch64 (3.3.9 / fsb-core 0.7.0)**: Donchian Channel + breakout equity/sweep (`donchian`, `equity_donchian_breakout`, `sweep_donchian_breakout`); `publish-fsb-core.yml` manylinux aarch64 cross wheels.
- Optional build: `cd native/fsb_core && maturin develop --release` (or `pip install fsb-core`).
- Further candidates (later): ADX / Supertrend kernels; musllinux wheels.

## Desktop UX (3.4.0)
- [x] **Modern trading desk shell**: left nav + content stage + bottom session strip; VoxHash dark palette (not a third-party brand clone); offscreen E2E smoke (`tests/test_gui_shell.py`); methodology notes in `docs/V3.4.0_FEATURES.md`.

## Future — Android / GrapheneOS
- [x] **API + scaffold (3.3.0)**: Kotlin client talks to remote-monitor `/api/v1/companion/*`; webhook alerts; no Google deps in scaffold; broker keys stay on desktop.
- [x] **Compose + pairing + approve/reject + pinning hooks (3.3.1)**: Material3 UI; QR paste / gallery decode (ZXing); action requests with host approve/reject; OkHttp `CertificatePinner` via `CERT_PINS` / pairing pin; F-Droid metadata draft.
- [x] **CameraX + encrypted cache + pin defaults (3.3.2)**: live QR scan; EncryptedSharedPreferences; host/Gradle production pin env; multi-host dashboard.
- Remaining: published F-Droid / Play store listing (metadata draft ready; submit outside this repo).

## Future — Multi-venue CEX / DEX (commodities + FX / crypto pairs)
Desktop bot stays the execution host (same `IBroker` / adapter pattern as Paper, MT4, IB TWS, REST). **Not started** — research and adapters only when scheduled; no live CEX/DEX trading in the current 3.3.x line.

Phased delivery (realistic order):
- [ ] **Research**: Map symbol/asset coverage (FX pairs, commodities, spot crypto) and venue capabilities for **centralized exchanges/brokers** (explicitly including **Binance**, **Kraken**, and similar REST/WebSocket APIs) and **decentralized exchanges/platforms** (on-chain or aggregator APIs where suitable). Prefer testnet/sandbox docs first.
- [ ] **Adapters**: Implement thin `IBroker` (+ optional market-data) adapters behind existing settings/env config; keep PyQt UI on the host; no keys in the mobile companion.
- [ ] **Paper / sandbox**: Wire paper or venue testnet paths end-to-end (orders, positions, reconnect) before any mainnet funds.
- [ ] **Live (opt-in)**: Production credentials only via local `.env` / UI secrets store; least-privilege API keys (trade-only where possible; no withdraw); kill-switch and risk limits reuse existing risk engine.

Opsec (required for this milestone):
- [ ] API keys and secrets never committed; `.env` gitignored; `.env.example` placeholders only
- [ ] Secrets not logged (requests, health, companion, or crash dumps)
- [ ] Document required env vars without real values; recommend IP allowlists / key rotation per venue

Related existing work to reuse: `docs/EXTENDING_BROKERS.md`, paper broker, REST broker scaffold, remote-monitor auth hardening.

## Future
- [ ] Social / copy trading and marketplace growth
- [ ] Multi-asset support (equities, crypto) where data providers allow — partly overlaps multi-venue CEX/DEX above
- [ ] Enterprise and compliance tooling (audit logs, role-based access)

For historical goals, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and version feature docs under `docs/V3.*_FEATURES.md`.

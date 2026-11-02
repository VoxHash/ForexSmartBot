# Roadmap — ForexSmartBot

High-level milestones aligned with the current **3.4.x** line (latest **3.4.5**; prior **3.4.4** / **3.4.3** / **3.4.2** / **3.4.1** / **3.4.0**). See [CHANGELOG.md](CHANGELOG.md) for shipped work.

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
**Brand note:** product name stays **ForexSmartBot** (PyPI / GitHub / `import forexsmartbot`); marketing copy positions it as a multi-venue desk (FX + spot crypto + DEX), not forex-only.
Desktop bot stays the execution host (same `IBroker` / adapter pattern as Paper, MT4, IB TWS, REST). **Research + public adapters in 3.4.1; paper/sandbox E2E in 3.4.2; Binance live in 3.4.3; Kraken live in 3.4.4; 1inch DEX dry-run execution in 3.4.5**.

Phased delivery (realistic order):
- [x] **Research (3.4.1)**: Map symbol/asset coverage (FX pairs, commodities, spot crypto) and venue capabilities for **centralized exchanges/brokers** (**Binance**, **Kraken**) and **DEX aggregators** (**1inch**). Live public probes + `docs/MULTI_VENUE_RESEARCH.md`; prefer testnet/sandbox docs first.
- [x] **Adapters (3.4.1, public/read-only)**: Thin `KrakenPublicBroker` + `BinancePublicBroker` behind Settings broker mode / env; PyQt stays on the host; no keys in the mobile companion. Authenticated trade adapters still open.
- [x] **Paper / sandbox (3.4.2)**: `VenuePaperBroker` (live public MD + local fills) and `BinanceSandboxBroker` (Spot Test Network HMAC orders/positions/reconnect); Settings modes; mainnet URLs refused; `tests/test_paper_sandbox.py`.
- [x] **Live (opt-in) (3.4.3)**: `BinanceLiveBroker` on `api.binance.com` only when `FSB_LIVE_TRADING=1`; dedicated `BINANCE_LIVE_API_*` keys; testnet refused; kill-switch via `RiskEngine` + `FSB_KILL_SWITCH`; `tests/test_binance_live.py` (mocked — no CI mainnet orders).
- [x] **Kraken Live (opt-in) (3.4.4)**: `KrakenLiveBroker` on `api.kraken.com` Spot private REST when `FSB_LIVE_TRADING=1`; dedicated `KRAKEN_LIVE_API_*` keys; demo/futures hosts refused; same kill-switch; `tests/test_kraken_live.py` (mocked — no CI mainnet orders).
- [x] **DEX aggregator execution (3.4.5)**: `OneInchDexBroker` Classic Swap `/quote` + `/swap` (v6.1); dry-run local fills by default; broadcast only with `FSB_LIVE_TRADING=1` + `FSB_DEX_BROADCAST=1` + injected `broadcast_fn` (no default private-key signer); Settings **1inch DEX**; `tests/test_oneinch_dex.py` (mocked — no CI mainnet spends).

Opsec (required for this milestone):
- [x] API keys and secrets never committed; `.env` gitignored; `.env.example` placeholders only (`KRAKEN_*` / `BINANCE_*` / `ONEINCH_*`)
- [x] Secrets not logged — `forexsmartbot.venues.secrets` redaction helpers for mappings / bearer text
- [x] Document required env vars without real values; recommend IP allowlists / key rotation per venue (`docs/MULTI_VENUE_RESEARCH.md`)
- [x] DEX broadcast double opt-in (`FSB_DEX_BROADCAST`); wallet private keys never read from env by the default broker path

Related existing work to reuse: `docs/EXTENDING_BROKERS.md`, paper broker, REST broker scaffold, remote-monitor auth hardening.

## Future — Polymarket prediction markets + LP / liquidity rewards
**Brand note:** product name stays **ForexSmartBot**; this extends the multi-venue desk (FX + CEX/DEX already in 3.4.x) toward prediction-market venues. Desktop bot remains the execution host behind the same `IBroker` / adapter pattern.

**Geo / legal flags (not legal advice):** Polymarket availability, KYC, and permitted categories (Politics, Sports, Crypto, etc.) vary by jurisdiction and change over time. Ship geo/eligibility checks as product flags and document user responsibility; do not treat roadmap checkboxes as permission to offer the product everywhere. Prefer official public docs / test surfaces first.

Phased delivery (realistic order):
- [ ] **Research**: Map Polymarket public API / CLOB / Gamma (or successor) coverage for **Politics, Sports, Crypto**, and other listed categories; document order types, settlement, fee model, geo/KYC gates, and rate limits. Separate research notes for **LP Farming** and **Liquidity Rewards** (eligibility, claim flow, reward token, risk of impermanent loss / reward clawback).
- [ ] **Adapters (read-only / public)**: Thin Polymarket market + order-book adapter behind Settings venue mode; list markets by category; no keys or wallet secrets in repo; PyQt stays on the host.
- [ ] **Paper / sandbox**: Local or documented test/sandbox path for quote + simulated fills against live or recorded Polymarket books; refuse mainnet spends without opt-in.
- [ ] **Live (opt-in)**: Authenticated Polymarket trading only with explicit live flags (same spirit as `FSB_LIVE_TRADING` / DEX double opt-in); kill-switch reuse; mocked CI — no CI mainnet orders.
- [ ] **LP Farming (opt-in)**: Research → adapter for position/LP entry-exit on supported Polymarket liquidity surfaces → paper/sandbox → live opt-in; document IL and reward volatility risks.
- [ ] **Liquidity Rewards (opt-in)**: Claim / accrual adapter after research; dry-run first; live claim only with opt-in; never embed reward-claim private keys in the default path.

Opsec (required for this milestone):
- [ ] API keys, session tokens, and wallet material never committed; `.env` gitignored; `.env.example` placeholders only
- [ ] Secrets not logged (reuse `forexsmartbot.venues.secrets` redaction)
- [ ] Document geo/eligibility flags without claiming legal clearance for any region

Related: multi-venue CEX/DEX section above; wallet-connect section below for e2e signing where Polymarket requires a wallet.

## Future — Crypto wallet connect (e2e)
Enable users to **connect crypto wallets** properly so Polymarket / DEX / rewards flows can complete end-to-end inside ForexSmartBot without shipping private keys in the repo.

Phased delivery:
- [ ] **Research**: Prefer **WalletConnect** and/or **browser-extension** patterns (injected provider); document supported chains, session lifecycle, disconnect, and how desktop PyQt hosts a connect UI (deep link / local bridge / embedded webview — pick one after research).
- [ ] **Adapters**: Session connect/disconnect + address display; sign-message / typed-data hooks behind a narrow interface; **no private-key import UI and no default env-based signer** (align with 3.4.5 DEX `broadcast_fn` injection).
- [ ] **Paper / sandbox**: Connect against test/demo WalletConnect project or mock provider; exercise quote → user-approve → simulated broadcast without mainnet value.
- [ ] **Live (opt-in)**: Real WalletConnect / extension sessions only when live flags are set; user confirms each spend; kill-switch still blocks new orders; never log seed phrases or raw private keys.

Opsec (required):
- [ ] Private keys / mnemonics never stored in git, logs, or default config files
- [ ] Prefer hardware-wallet / extension / WalletConnect remote signing over in-process key material
- [ ] Document phishing risks (fake WC URIs) and recommend verifying dApp / project IDs from official docs

## Future — Strategy marketplace via GitHub PR (remote packs)
Update the **marketplace** so contributors **add strategies via GitHub PR**; after merge, other users can **download strategies without updating** their local installed ForexSmartBot app version.

Phased delivery:
- [ ] **Research**: Define strategy-pack manifest schema (id, version, entry module, min app version, checksum); map PR → CI → publish path (GitHub Releases and/or raw index on default branch); inventory current `marketplace/` listings vs remote index.
- [ ] **Adapters / index client**: App fetches a **remote strategy pack index** (GitHub Releases assets and/or raw `marketplace` index URL); list / filter packs; download into a user data dir — **no app reinstall required** to get new merged strategies.
- [ ] **Paper / sandbox**: Install a signed-or-checksummed sample pack from a test release; load in paper broker / backtest only; refuse execution if checksum fails.
- [ ] **Live / opt-in publish path**: Document contributor flow (fork → PR → review → merge → automated release/index bump); optional maintainer signing key; users opt in to “remote marketplace” channel in Settings.
- [ ] **Integrity (later)**: Versioned packs with **SHA-256 checksums** in the index; optional **signature** verification (maintainers’ key) as a follow-on checkbox once checksums ship.

Opsec / trust:
- [ ] Never execute arbitrary remote code without checksum (and later signature) verification + user consent
- [ ] Sandbox imported strategies where feasible; document that community packs are not endorsed trading advice
- [ ] CI on strategy PRs (lint / import / smoke backtest) before merge

Related existing: local `marketplace/` listings; strategy registry; docs on extending strategies.

## Future
- [ ] Social / copy trading (marketplace PR/download packs tracked in section above)
- [ ] Broader multi-asset coverage (equities; deeper commodities) where data providers allow — spot crypto / CEX / DEX already shipped in 3.4.x under the ForexSmartBot name; Polymarket categories tracked above
- [ ] Enterprise and compliance tooling (audit logs, role-based access)

For historical goals, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and version feature docs under `docs/V3.*_FEATURES.md`.

# Changelog — ForexSmartBot

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 

### Changed
- 

### Fixed
- 

## [3.4.4] - 2026-10-26

### Added
- **Kraken Live broker (opt-in)**: `KrakenLiveBroker` for Spot mainnet (`api.kraken.com`); requires `FSB_LIVE_TRADING=1` + `KRAKEN_LIVE_API_KEY` / `KRAKEN_LIVE_API_SECRET`; demo/futures hosts refused; Settings mode **Kraken Live**
- **Kraken HMAC vector test**: published AddOrder signature fixture in `kraken_api_sign` / `tests/test_kraken_live.py`
- **Docs**: `docs/V3.4.4_FEATURES.md`

### Changed
- **Version**: Package/app bumped to **3.4.4**

## [3.4.3] - 2026-10-25

### Added
- **Binance Live broker (opt-in)**: `BinanceLiveBroker` for Spot mainnet (`api.binance.com`); requires `FSB_LIVE_TRADING=1` + `BINANCE_LIVE_API_KEY` / `BINANCE_LIVE_API_SECRET`; testnet URLs refused; Settings mode **Binance Live**
- **Kill-switch**: `RiskEngine.trip_kill_switch` / `evaluate_kill_switch` (daily risk + max drawdown); env `FSB_KILL_SWITCH=1`; UI stop/flatten; live orders blocked while active
- **Live guard**: `forexsmartbot.venues.live_guard` (`live_trading_enabled`, `require_live_opt_in`)
- **Tests**: `tests/test_binance_live.py` (opt-in refusal, kill-switch, mocked mainnet path — no real funds)
- **Docs**: `docs/V3.4.3_FEATURES.md`

### Changed
- **Version**: Package/app bumped to **3.4.3**

## [3.4.2] - 2026-10-25

### Added
- **Venue Paper broker**: `VenuePaperBroker` fills local paper orders/positions against live Binance testnet or Kraken public prices (no keys); `reconnect()` re-opens the feed
- **Binance Sandbox broker**: authenticated Spot Test Network adapter (`BINANCE_API_KEY` / `BINANCE_API_SECRET`); HMAC market orders, balance, positions, reconnect; **mainnet URLs refused**
- **Settings**: Broker Mode entries **Venue Paper** and **Binance Sandbox**
- **Tests**: `tests/test_paper_sandbox.py` (HMAC vector, mainnet refusal, mocked sandbox E2E, optional live venue-paper probe)
- **Docs**: `docs/V3.4.2_FEATURES.md`

### Changed
- **Version**: Package/app bumped to **3.4.2**
- Public brokers / paper expose `reconnect()` helpers

## [3.4.1] - 2026-10-25

### Added
- **Multi-venue research**: `forexsmartbot.venues` registry + live public probes for Kraken Spot/Futures and Binance Spot testnet; DEX aggregator profile for 1inch (`docs/MULTI_VENUE_RESEARCH.md`)
- **Public broker adapters**: read-only `KrakenPublicBroker` and `BinancePublicBroker` (Settings → Broker Mode); orders refused until authenticated sandbox path
- **Opsec helpers**: `venues.secrets` redaction; `.env.example` placeholders for Kraken / Binance / 1inch (no real values)
- **Tests**: `tests/test_multi_venue.py` (registry, redaction, live `@pytest.mark.network` probes)

### Changed
- **Version**: Package/app bumped to **3.4.1**

## [3.4.0] - 2026-10-25

### Added
- **Modern trading desk shell**: persistent left `NavRail`, content stage, bottom `SessionBar` (equity / P&L / connection) in `forexsmartbot/ui/shell.py`
- **VoxHash dark QSS**: unique palette tokens (`#0B0F14` / `#3D9CF0` / `#26C281`) applied via `ThemeManager` for dark mode
- **GUI smoke tests**: `tests/test_gui_shell.py` (offscreen launch, nav, paper path)
- **Docs**: `docs/V3.4.0_FEATURES.md` (rea methodology + layout inspiration cites; no Spotify affiliation)

### Changed
- **Version**: Package/app bumped to **3.4.0**
- **EnhancedMainWindow**: tab bar hidden; stages driven by left nav; session strip mirrors desk status

## [3.3.9] - 2026-10-25

### Added
- **Donchian kernels**: `donchian`, `equity_donchian_breakout`, `sweep_donchian_breakout` in `fsb_core` / `native_indicators` (NumPy fallback; Turtle-style prior-bar breakout)
- **Linux aarch64 wheels**: `publish-fsb-core.yml` cross-builds manylinux aarch64 wheels (Python 3.10–3.13) alongside x86_64
- **Docs**: `docs/V3.3.9_FEATURES.md`

### Changed
- **Version**: Package/app bumped to **3.3.9**; optional `fsb_core` to **0.7.0**

## [3.3.8] - 2026-10-25

### Added
- **Stochastic kernels**: `stochastic`, `equity_stochastic_crossover`, `sweep_stochastic_crossover` in `fsb_core` / `native_indicators` (NumPy fallback; `%D` uses finite-window SMA of `%K`)
- **Docs**: `docs/V3.3.8_FEATURES.md`

### Changed
- **Version**: Package/app bumped to **3.3.8**; optional `fsb_core` to **0.6.0**

## [3.3.7] - 2026-10-25

### Added
- **Bollinger kernels**: `bollinger`, `equity_bollinger_mean_reversion`, `sweep_bollinger_mean_reversion` in `fsb_core` / `native_indicators` (NumPy fallback; sample std ddof=1)
- **Multi-platform wheels**: `publish-fsb-core.yml` builds Windows x64 and macOS arm64/x86_64 wheels (Python 3.10–3.13) alongside manylinux
- **Docs**: `docs/V3.3.7_FEATURES.md`

### Changed
- **Version**: Package/app bumped to **3.3.7**; optional `fsb_core` to **0.5.0**

## [3.3.6] - 2026-10-25

### Added
- **`fsb-core` on PyPI**: optional native package published as [`fsb-core`](https://pypi.org/project/fsb-core/) **0.4.0** (sdist + wheel); install with `pip install fsb-core`
- **CI**: `publish-fsb-core.yml` builds manylinux wheels (3.10–3.13) + sdist for future `fsb-core-v*` tags / Trusted Publisher
- **Docs**: `docs/V3.3.6_FEATURES.md`

### Changed
- **Version**: Package/app bumped to **3.3.6**

## [3.3.5] - 2026-10-25

### Added
- **EMA / MACD kernels**: `ema`, `macd`, `equity_ema_crossover`, `sweep_ema_crossover`, `equity_macd_crossover`, `sweep_macd` in `fsb_core` / `native_indicators` (NumPy fallback)
- **Docs**: `docs/V3.3.5_FEATURES.md`
- **CI**: pin GitHub Actions Ubuntu jobs to `ubuntu-24.04` (avoid `ubuntu-latest` migration queue stalls)

### Changed
- **Version**: Package/app bumped to **3.3.5**; optional `fsb_core` to **0.4.0**

## [3.3.4] - 2026-10-25

### Added
- **RSI mean-reversion kernel**: `equity_rsi_mean_reversion` + `sweep_rsi_mean_reversion` in `fsb_core` / `native_indicators` (NumPy fallback)
- **CI native wheels**: `native-wheels` job builds `fsb_core` via maturin and uploads `fsb-core-wheels` artifacts
- **Docs**: `docs/V3.3.4_FEATURES.md`

### Changed
- **Version**: Package/app bumped to **3.3.4**; optional `fsb_core` to **0.3.0**

## [3.3.3] - 2026-10-24

### Added
- **Native walk-forward sweeps**: `fsb_core` `sweep_sma_crossover` + `walk_forward_sma_sweep` (rayon); Python helpers `walk_forward_windows` / wrappers in `native_indicators`
- **Multi-symbol aggregation workers**: `multi_symbol_equity_aggregate` (parallel per-symbol equity + weighted portfolio curve)
- **Docs**: `docs/V3.3.3_FEATURES.md`; PERFORMANCE_TUNING / README native section updated
- **Tests**: sweep, walk-forward, multi-symbol (+ NumPy fallback) in `tests/test_native_indicators.py`

### Changed
- **Version**: Package/app bumped to **3.3.3**; optional `fsb_core` to **0.2.0**

## [3.3.2] - 2026-10-24

### Added
- **Live CameraX QR**: Android companion `QrScanActivity` / `QrAnalyzer` (CameraX + ZXing, no GMS)
- **Encrypted local cache**: `EncryptedSharedPreferences` for pairing session + portfolio snapshot; offline fallback
- **Production cert-pin defaults**: host env `FSB_COMPANION_CERT_PIN` / `COMPANION_CERT_PIN`; public base `FSB_PUBLIC_BASE_URL`; Android `-PFSB_CERT_PINS`
- **Multi-host dashboard**: remote-monitor UI polls additional host health / strategy counts (browser localStorage)
- **Helpers**: `normalize_cert_pin` / `resolve_companion_cert_pin` in companion API
- **Docs**: `docs/V3.3.2_FEATURES.md`

### Changed
- **Version**: Package/app bumped to **3.3.2**; Android companion to **0.3.0** (versionCode 3)
- **F-Droid metadata draft**: updated for 0.3.0

## [3.3.1] - 2026-10-24

### Added
- **Strategy history charts**: `GET /api/v1/strategies/history` (+ per-strategy); companion `/api/v1/companion/strategies/.../history`; dashboard canvas sparklines; ISO timestamps in `StrategyMonitor` history
- **QR pairing**: `POST /api/v1/companion/pairing/session` (host) + `POST .../pairing/redeem` (phone); dashboard QR + JSON payload (`fsb-companion` scheme, 5‑minute TTL, single-use)
- **Approve/reject actions**: companion action queue for `start_trading` / `stop_trading` / `pause_trading`; host approve runs registered callbacks; dashboard pending list
- **Android Compose companion (0.2.0)**: Material3 UI, paste/QR-image pairing (ZXing, no GMS), session prefs, request start/stop, OkHttp cert pinning via `CERT_PINS` / pairing `pin_sha256`
- **F-Droid metadata draft**: `mobile/android-companion/metadata/dev.voxhash.fsbcompanion.yml`

### Changed
- **Version**: Package/app bumped to **3.3.1**
- **Remote monitor**: wires companion history + control callbacks into approve path

## [3.3.0] - 2026-10-24

### Added
- **Companion API** (`forexsmartbot.cloud.companion_api`): read-only `/api/v1/companion/*` — health, portfolio, positions, alerts, strategies, webhook device register; Bearer / X-API-Key; control off by default
- **WebhookNotifier**: HTTPS (or localhost HTTP) alert delivery without FCM / Google Play Services
- **Strategy health dashboard**: `GET /api/v1/strategies` and `GET /api/v1/strategies/<name>` on remote monitor; HTML Strategy Health table; `StrategyHealth.to_dict()` / `StrategyMonitor.get_dashboard_payload()`
- **Remote monitor**: mounts companion API; optional `strategy_monitor=` / `set_strategy_monitor()`
- **Android scaffold**: `mobile/android-companion/` Kotlin + Retrofit read-only client (GrapheneOS-friendly: no Firebase, `allowBackup=false`, cleartext limited to loopback)
- **Examples / tests**: `examples/companion_monitor_example.py`; `tests/test_companion_q2.py`
- **Docs**: `docs/V3.3.0_FEATURES.md` rewritten for the shipped Q2 slice

### Changed
- **MobileAppAPI**: wraps `CompanionAPI` (read-only by default); optional FCM kept but webhook preferred
- **Version**: Package/app bumped to **3.3.0**

## [3.2.5] - 2026-10-24

### Added
- **Remote monitor**: Public `/healthz` and `/api/v1/health`; alert ring buffer with POST/GET; dashboard session API-key field (Bearer / `X-API-Key`)
- **Cloud sync**: Exponential backoff + jitter retries, failed-payload pending queue with `flush_pending()`, real auto-sync daemon thread, `check_endpoint_health()`
- **Auth helpers**: `forexsmartbot.cloud.auth_utils` (constant-time compare, token extract, insecure-secret detection, credential bind checks)
- **API client**: `health()` probe, request retries, WebSocket `auth` command support
- **Tests**: `tests/test_cloud_hardening.py` for auth, retry, sync queue, and remote monitor Flask routes

### Changed
- **Security**: JWT includes `jti`/`iss`; PBKDF2 password hashing (legacy SHA-256 still verified); ephemeral secret when `API_SECRET_KEY` is weak
- **API / remote servers**: Refuse weak keys on non-loopback binds unless `FSB_ALLOW_INSECURE_MONITOR=1`; constant-time API key checks
- **Version**: Package/app bumped to **3.2.5** (includes post-`v3.2.4` Strategy Tests CI fixes on main)

### Fixed
- **CI / Strategy Tests** (post-tag on main): Soft SL/TP sandbox non-fatal; PaperBroker API alignment; volatility sizing; empty-market harden; SMA/RSI-only CI set; `test_config` wiring into Strategy Tests check step

## [3.2.4] - 2026-10-24

### Added
- **Backtest UI**: KPI cards (return, Sharpe, max DD, win rate, trades, profit factor), equity-curve chart tab, trades table tab
- **Backtest UI**: Date-range presets (1M/3M/1Y/5Y/YTD), 15m interval, cancel control, JSON/CSV export via file dialog
- **Tests**: `tests/test_backtest_dialog_ui.py` for strategy label parsing

### Fixed
- **Strategy Tests workflow**: Invoke pipeline as `python -m forexsmartbot.testing.ci_cd_pipeline` (relative imports failed when run as a script)
- **Strategy Tests**: MultiProvider + synthetic OHLCV fallback when Yahoo returns empty; CI runs SMA_Crossover/RSI_Reversion; sandbox aligned to PaperBroker + RiskEngine APIs
- **Backtest dialog**: Strategy combo stores registry name in `userData`; worker emits error payload so the UI re-enables after failures; equity curve included in results

## [3.2.3] - 2026-10-24

### Fixed
- **CI / Strategy Tests**: Core `requirements.txt` no longer hard-requires TA-Lib or TensorFlow/PyTorch (moved to `requirements-optional.txt` and extras `talib` / `ml` / `remote`)
- **CI**: Install path prefers TA-Lib binary wheels (`--only-binary=:all:`) and continues without TA-Lib when no wheel exists (fixes Ubuntu/macOS Python 3.10 source-build failures)
- **Strategy Tests**: Skip heavy ML imports via `FSB_SKIP_HEAVY_ML` to avoid TensorFlow SIGSEGV (exit 139) on CPU runners; validate_installation isolates TF/torch checks in a subprocess
- **Package**: Soft-optional `talib` import in TradingView chart; GPU utils skip TF/torch when `FSB_SKIP_HEAVY_ML` is set
- **pyproject.toml**: Pin `mplfinance>=0.12.10b0` (PEP 440: `>=0.12.10` rejects the published `0.12.10b0` wheel)

### Changed
- **pyproject.toml**: TA-Lib removed from hard dependencies; optional extras `talib`, `ml`, `remote`, `full`

## [3.2.2] - 2026-10-24

### Added
- **Live analytics dashboard**: `build_live_metrics` / `LiveMetricsSnapshot` aggregate equity, P&L, Sharpe/Sortino, drawdown, VaR/CVaR from the live `Portfolio`
- **UI polish**: Analytics tab KPI cards + portfolio/risk tables with 5s timer refresh; main window real-time hook refreshes the dashboard
- **Tests**: `tests/test_live_metrics.py` for empty/winning portfolios, equity sync, and card tone

### Fixed
- **Risk analytics dialog**: Loads portfolio trades (previously showed zeros when portfolio had data)
- **PortfolioAnalytics.calculate_metrics**: Syncs equity history from `Portfolio` and restores internal state after calculation
- **RiskAnalytics**: Lazy `scipy` import so historical VaR works without scipy installed
- **Analytics package import**: Qt-backed widgets optional so headless/test imports succeed without PyQt6

## [3.2.1] - 2026-10-23

### Fixed
- **Multi_Timeframe registration**: Import `IDataProvider` from `core.interfaces` so the strategy loads without pulling `adapters.data` / `zmq`; `get_strategy('Multi_Timeframe')` defaults to `SMA_Crossover` for UI/backtest call sites; trend detection recognizes `SMA_fast`/`SMA_slow`

### Added
- **Tests**: `tests/test_multi_timeframe_strategy.py` covering registry availability, provider contract, and signal path with a real in-process `IDataProvider`
- **Tests**: Broader automated suite for strategy registry / SMA·Breakout·RSI paths, `native_indicators` NumPy fallback, `RiskManager`/`RiskEngine`, and `AppConfig` env loading (`tests/test_strategies.py`, `test_native_indicators.py`, `test_risk.py`, `test_config.py`)

## [3.2.0] - 2026-10-05

### Added
- **Data providers**: Twelve Data (`TwelveDataProvider`) and Stooq (`StooqProvider`) adapters with multi-provider fallback wiring ([#](https://github.com/VoxHash/ForexSmartBot))
- **Interactive Brokers**: TWS broker integration via `ib-insync` with settings UI connection test (`3c1c534`)
- **Fear Index strategy**: Mathematical specification and registered `Fear_Index` strategy (`f8e215a`)

### Changed
- **Documentation**: Consolidated API reference; expanded data provider setup (Twelve Data, Stooq); trimmed duplicate performance guides
- **LICENSE**: Copyright holder updated to VoxHash LLC (2026)
- **README**: Documentation links updated (unified API reference, data providers guide)

### Fixed
- **CI**: GitHub Actions upgraded to `@v4` artifacts/cache/checkout (`9236c32`)

### Changed (performance)
- Memory and execution-speed optimizations for low-latency trading paths (`35294cd`)

## [3.1.0] - 2026-03-12

### Added
- **Enhanced ML Strategies**: 7 new machine learning strategies
  - LSTM Strategy for time series prediction
  - Transformer Strategy using BERT/GPT-style models
  - Reinforcement Learning Strategy (DQN/PPO)
  - SVM Strategy for classification-based trading
  - Ensemble ML Strategy combining Random Forest and Gradient Boosting
  - Multi-Timeframe Strategy for analyzing multiple timeframes simultaneously
- **Strategy Optimization Tools**: Comprehensive optimization suite
  - Genetic Algorithm Optimizer using DEAP
  - Hyperparameter Optimizer using Optuna (TPE algorithm)
  - Walk-Forward Analyzer for rolling window validation
  - Monte Carlo Simulator for risk assessment (VaR/CVaR)
  - Parameter Sensitivity Analyzer
- **Custom Strategy Builder**: Visual strategy construction framework
  - Component-based architecture (Indicators, Signals, Filters, Risk Management)
  - Pre-built strategy templates (SMA Crossover, RSI, Breakout)
  - Automatic Python code generation from visual builder
  - Strategy validation and testing tools
- **Strategy Marketplace**: Community-driven strategy sharing
  - Strategy listing and discovery platform
  - Rating and review system
  - Performance tracking integration
- **Enhanced Monitoring**: Real-time strategy health monitoring
  - Strategy Monitor for real-time health checks
  - Performance Tracker with comprehensive metrics (Sharpe, Sortino, drawdown)
  - Health Checker with automated alerts
- **Enhanced Backtesting**: Production-ready backtesting engine
  - Parallel processing support
  - Comprehensive error handling with graceful degradation
  - Transaction rollback on errors
  - Detailed logging and debugging tools
- **Command-Line Tools**: Utility scripts for optimization and analysis
  - `optimize_strategy.py` - Parameter optimization tool
  - `analyze_sensitivity.py` - Sensitivity analysis tool
- **Documentation**: Comprehensive guides and examples
  - Quick Start Guide for v3.1.0 features
  - Comprehensive feature documentation
  - Multiple example scripts demonstrating all features

### Changed
- **Dependencies**: Added 8 new ML/optimization libraries
  - TensorFlow, PyTorch, Transformers for deep learning
  - Gymnasium, Stable-Baselines3 for reinforcement learning
  - Optuna for hyperparameter optimization
  - DEAP for genetic algorithms
- **Strategy Registry**: Enhanced with conditional loading for optional ML strategies
- **Backtesting Service**: Improved error handling and reliability

### Fixed
- **Strategy Execution**: Enhanced error handling prevents crashes
- **Parameter Optimization**: Improved stability for edge cases
- **Multi-Timeframe**: Fixed data provider integration
- **Version Consistency**: Fixed version mismatch between app.py and pyproject.toml
- **Error Handling**: Replaced bare except clauses with proper exception handling

## [3.0.0] - 2025-09-25

### Added
- **Version 3.0.0 Release**: Major version update with comprehensive improvements
- **Theme System**: Complete theme management with Light, Dark, Auto, and Dracula themes
- **Real-time Updates**: Live portfolio monitoring with color-coded performance metrics
- **Machine Learning Strategies**: ML Adaptive SuperTrend and Adaptive Trend Flow algorithms
- **Multi-Broker Support**: Paper trading, MT4, and REST API integration
- **Donation Support**: Cryptocurrency donation addresses for project support
- **Professional UI**: Modern, responsive interface with real-time data display
- **Advanced Risk Management**: Kelly Criterion and drawdown protection
- **Comprehensive Documentation**: Complete user guide and API reference

### Changed
- **UI/UX Improvements**: Enhanced user interface with better organization
- **Performance Optimization**: Improved real-time updates and reduced UI freezing
- **Code Structure**: Better organized codebase with improved maintainability
- **Documentation**: Comprehensive documentation with examples and guides

### Fixed
- **Theme Switching**: Fixed theme color changes not applying in Settings UI tab
- **Real-time Updates**: Fixed Trading Status and Performance Metrics real-time updates
- **Position Display**: Fixed open positions not appearing in the Open Positions table
- **PnL Calculation**: Fixed PnL calculation with realistic price variations
- **Closed Positions Order**: Fixed Closed Positions table to show newest trades first
- **Widget References**: Fixed incorrect widget references causing crashes
- **Trade Objects**: Fixed trade object creation for proper position management

### Removed
- **Duplicate Files**: Removed all unnecessary summary and duplicate files
- **Legacy Code**: Cleaned up old and unused code
- **Redundant Documentation**: Consolidated documentation into essential files

## [2.0.0] - 2025-01-20

### Added
- **Enhanced Main Window**: Complete UI redesign with modern interface
- **Trading Status Widget**: Real-time trading status display
- **Strategy Configuration**: Multi-strategy selection with risk levels
- **Performance Metrics**: Live performance tracking and analytics
- **Position Management**: Open and closed positions tracking
- **Settings Dialog**: Comprehensive settings management
- **Theme Manager**: Theme management with persistence
- **Risk Engine**: Advanced risk management system

### Changed
- **UI Framework**: Upgraded to PyQt6 for better performance
- **Architecture**: Improved code organization and structure
- **Settings System**: Enhanced settings management with validation

### Fixed
- **UI Responsiveness**: Fixed UI freezing and unresponsive behavior
- **Position Tracking**: Fixed position display and management
- **Settings Persistence**: Fixed settings not saving properly

## [1.0.0] - 2025-01-15

### Added
- **Initial Release**: First stable release of ForexSmartBot
- **Basic Trading**: Core trading functionality
- **Strategy System**: Basic strategy implementation
- **Risk Management**: Basic risk controls
- **UI Framework**: Basic user interface

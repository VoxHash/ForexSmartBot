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

## [3.2.4] - 2026-10-24

### Added
- **Backtest UI**: KPI cards (return, Sharpe, max DD, win rate, trades, profit factor), equity-curve chart tab, trades table tab
- **Backtest UI**: Date-range presets (1M/3M/1Y/5Y/YTD), 15m interval, cancel control, JSON/CSV export via file dialog
- **Tests**: `tests/test_backtest_dialog_ui.py` for strategy label parsing

### Fixed
- **Strategy Tests workflow**: Invoke pipeline as `python -m forexsmartbot.testing.ci_cd_pipeline` (relative imports failed when run as a script)
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

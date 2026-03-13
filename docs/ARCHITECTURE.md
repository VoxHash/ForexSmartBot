# ForexSmartBot Architecture

## Directory Overview

```
ForexSmartBot/
├── app.py                      # Main application entry point
├── README.md                   # Project README
├── ROADMAP.md                  # Development roadmap
├── CHANGELOG.md                # Version changelog
├── LICENSE                     # MIT License
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project configuration
│
├── forexsmartbot/              # Main package
│   ├── adapters/               # Broker and data adapters
│   ├── analytics/              # Analytics modules (v3.2.0)
│   ├── builder/                # Strategy builder (v3.1.0)
│   ├── cloud/                  # Cloud integration (v3.3.0)
│   ├── core/                   # Core trading engine
│   ├── monitoring/             # Monitoring tools (v3.1.0)
│   ├── optimization/           # Optimization tools (v3.1.0)
│   ├── marketplace/           # Strategy marketplace (v3.1.0)
│   ├── services/               # Services layer
│   ├── strategies/             # Trading strategies
│   ├── testing/                # Testing utilities (v3.1.0)
│   └── ui/                     # User interface
│
├── docs/                       # Documentation
│   ├── INDEX.md                # Documentation index
│   ├── API_DOCUMENTATION.md    # REST/WebSocket API (v3.3.0)
│   ├── API-REFERENCE.md        # Python API reference
│   └── ...                     # Additional guides
│
├── examples/                   # Example scripts
├── scripts/                    # Utility scripts
├── tests/                      # Test suite
├── mt4/                        # MT4 Expert Advisor
├── config/                     # Configuration files
└── assets/                     # Assets (icons, etc.)
```

## Key Components

### Core Trading Engine (`forexsmartbot/core/`)
- **Portfolio**: Account balance and position management
- **Risk Engine**: Risk calculation and position sizing
- **Strategy**: Base strategy interface
- **Interfaces**: Abstract base classes for brokers, strategies, data providers

### Strategies (`forexsmartbot/strategies/`)
- Traditional strategies (SMA, RSI, Breakout, etc.)
- ML strategies (LSTM, Transformer, RL, SVM, Ensemble)
- Multi-timeframe strategies

### Adapters (`forexsmartbot/adapters/`)
- **Brokers**: Paper, MT4, REST API implementations
- **Data Providers**: YFinance, Alpha Vantage, OANDA, CSV, Multi-provider

### Services (`forexsmartbot/services/`)
- Backtesting engine
- Trading controller
- Settings persistence
- Notification service
- Language management

### UI (`forexsmartbot/ui/`)
- Enhanced main window
- Settings dialog
- Backtest dialog
- Strategy builder dialog
- Analytics widgets
- Theme management

## Version Structure

### v3.3.0 - Cloud Integration
- `forexsmartbot/cloud/` - Cloud sync, remote monitoring, REST/WebSocket APIs
- `docs/CLOUD_INTEGRATION_GUIDE.md`
- `docs/API_DOCUMENTATION.md`

### v3.2.0 - Advanced Analytics
- `forexsmartbot/analytics/` - Advanced analytics modules
- `docs/V3.2.0_FEATURES.md`

### v3.1.0 - Enhanced Strategies
- `forexsmartbot/optimization/` - Optimization tools
- `forexsmartbot/builder/` - Strategy builder
- `forexsmartbot/marketplace/` - Strategy marketplace
- `forexsmartbot/monitoring/` - Monitoring tools
- `docs/V3.1.0_FEATURES.md`

## Data Flow

1. **Data Provider** → Fetches market data
2. **Strategy** → Analyzes data and generates signals
3. **Risk Engine** → Calculates position size
4. **Broker** → Executes trades
5. **Portfolio** → Updates positions and balance
6. **UI** → Displays real-time updates

## Extension Points

- **Custom Strategies**: Implement `IStrategy` interface
- **Custom Brokers**: Implement `IBroker` interface
- **Custom Data Providers**: Implement `IDataProvider` interface
- **Custom Indicators**: Add to strategy builder components

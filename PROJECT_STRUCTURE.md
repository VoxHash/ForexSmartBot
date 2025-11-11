# ForexSmartBot Project Structure

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
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
│
├── forexsmartbot/              # Main package
│   ├── adapters/               # Broker and data adapters
│   ├── analytics/              # Analytics modules (v3.2.0)
│   ├── builder/                # Strategy builder (v3.1.0)
│   ├── cloud/                  # Cloud integration (v3.3.0)
│   ├── core/                   # Core trading engine
│   ├── monitoring/             # Monitoring tools (v3.1.0)
│   ├── optimization/           # Optimization tools (v3.1.0)
│   ├── marketplace/            # Strategy marketplace (v3.1.0)
│   ├── services/               # Services layer
│   ├── strategies/             # Trading strategies
│   ├── testing/                # Testing utilities (v3.1.0)
│   └── ui/                     # User interface
│
├── docs/                       # Documentation
│   ├── RELEASES.md             # Release notes
│   ├── API_DOCUMENTATION.md    # API reference (v3.3.0)
│   ├── V3.1.0_FEATURES.md      # v3.1.0 features
│   ├── V3.2.0_FEATURES.md      # v3.2.0 features
│   ├── V3.3.0_FEATURES.md      # v3.3.0 features
│   └── ...                     # Additional guides
│
├── examples/                    # Example scripts
│   ├── comprehensive_example.py
│   ├── api_usage_example.py    # API examples (v3.3.0)
│   ├── cloud_sync_example.py   # Cloud sync (v3.3.0)
│   └── ...                     # More examples
│
├── scripts/                     # Utility scripts
│   ├── optimize_strategy.py
│   ├── analyze_sensitivity.py
│   └── ...
│
├── tests/                       # Test suite
│   ├── test_backtest.py
│   ├── test_strategies.py
│   └── ...
│
├── mt4/                         # MT4 Expert Advisor
│   └── ForexSmartBotBridge.mq4  # Main EA file
│
├── config/                      # Configuration files
│   ├── optimization_config.json
│   └── strategy_configs.json
│
├── assets/                      # Assets (icons, etc.)
│   └── icons/
│
└── data/                        # Data directory (gitignored)
    ├── backtests/
    └── walk_forward/
```

## Key Files

### Root Level
- `app.py` - Application entry point
- `README.md` - Main project documentation
- `ROADMAP.md` - Development roadmap
- `CHANGELOG.md` - Version history
- `requirements.txt` - Python dependencies

### Documentation
- `docs/README.md` - Documentation index
- `docs/RELEASES.md` - Release notes
- `docs/API_DOCUMENTATION.md` - API reference
- Version-specific feature docs in `docs/`

### Configuration
- `.env.example` - Environment variables template
- `config/` - JSON configuration files
- `pyproject.toml` - Project metadata

### Code Organization
- `forexsmartbot/` - Main Python package
- `examples/` - Usage examples
- `scripts/` - CLI utilities
- `tests/` - Test suite

## Version Structure

### v3.3.0 - Cloud Integration
- `forexsmartbot/cloud/` - Cloud sync, remote monitoring, APIs
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

---

**Last Updated**: January 2026


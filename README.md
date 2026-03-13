# ForexSmartBot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.7+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Version](https://img.shields.io/badge/version-3.1.0-blue.svg)](https://github.com/VoxHash/ForexSmartBot/releases)

> Professional-grade desktop application for automated forex trading with advanced risk management, multiple trading strategies, and real-time portfolio monitoring.

## ✨ Features

- **Multi-Strategy Trading**: 17+ built-in strategies including 7 ML-based approaches
- **Real-time Monitoring**: Live portfolio tracking with P&L updates and health checks
- **Risk Management**: Advanced risk controls with Kelly Criterion and drawdown protection
- **Multi-Broker Support**: Paper trading, MT4, and REST API integration
- **Enhanced Backtesting**: Comprehensive strategy testing with parallel processing
- **GPU Acceleration**: CUDA support for 5-20x faster ML training and inference
- **Strategy Builder**: Visual strategy construction with code generation
- **Strategy Marketplace**: Community-driven strategy sharing platform

## 🧭 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Quick Start

```bash
# 1) Install
pip install forexsmartbot

# 2) Run
python app.py
```

For detailed installation instructions, see [docs/installation.md](docs/Installation-Guide.md).

## 💿 Installation

### From PyPI (Recommended)
```bash
pip install forexsmartbot
```

### From Source
```bash
git clone https://github.com/VoxHash/ForexSmartBot.git
cd ForexSmartBot
pip install -r requirements.txt
python app.py
```

### With GPU Acceleration (Optional)
```bash
# For CUDA 12.x
pip install cupy-cuda12x

# For CUDA 11.x
pip install cupy-cuda11x
```

See [docs/GPU_ACCELERATION.md](docs/GPU_ACCELERATION.md) for detailed setup instructions.

## 🛠 Usage

### Basic Workflow

1. Launch the application: `python app.py`
2. Configure settings: Go to Settings → General tab
3. Select strategy: Choose from available trading strategies
4. Set risk parameters: Configure risk per trade and leverage
5. Start trading: Click "Connect" then "Start Trading"

For advanced usage, see [docs/usage.md](docs/QUICK_START_V3.1.0.md) and [docs/cli.md](docs/API-REFERENCE.md).

## ⚙️ Configuration

| Variable | Description | Default |
|---|---|---|
| `INITIAL_BALANCE` | Starting account balance | 10000.0 |
| `RISK_PER_TRADE` | Risk percentage per trade | 0.02 |
| `MAX_LEVERAGE` | Maximum leverage | 1:100 |
| `DATA_INTERVAL` | Data update interval | 1h |

Full configuration reference: [docs/Configuration-Guide.md](docs/Configuration-Guide.md)

## 📚 Documentation

- **Getting Started**: [Quick Start Guide](docs/QUICK_START_V3.1.0.md)
- **API Reference**: [Python API](docs/API-REFERENCE.md) | [REST API](docs/API_DOCUMENTATION.md)
- **Architecture**: [System Architecture](docs/ARCHITECTURE.md)
- **Examples**: [Example Scripts](examples/)
- **FAQ**: [Frequently Asked Questions](docs/FAQ.md)
- **Troubleshooting**: [Common Issues](docs/TROUBLESHOOTING.md)

Complete documentation index: [docs/INDEX.md](docs/INDEX.md)

## 🗺 Roadmap

Planned milestones live in [ROADMAP.md](ROADMAP.md). For changes, see [CHANGELOG.md](CHANGELOG.md).

## 🤝 Contributing

We welcome PRs! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and follow the PR template.

## 🔒 Security

Please report vulnerabilities via [SECURITY.md](SECURITY.md).

## 📄 License

This project is licensed under the terms in [LICENSE](LICENSE).

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **FAQ**: [docs/FAQ.md](docs/FAQ.md)
- **Issues**: [GitHub Issues](https://github.com/VoxHash/ForexSmartBot/issues)
- **Email**: contact@voxhash.dev

See [SUPPORT.md](SUPPORT.md) for more support options.

## ⚠️ Disclaimer

This application is for educational and legitimate business purposes only. Users are responsible for complying with applicable laws and regulations. The developers are not responsible for any financial losses or misuse of this application.

---

Made with ❤️ by [VoxHash Technologies](https://voxhash.dev)

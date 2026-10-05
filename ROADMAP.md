# Roadmap — ForexSmartBot

High-level milestones aligned with the current **3.2.x** line. See [CHANGELOG.md](CHANGELOG.md) for shipped work.

## Completed (3.2.0)
- Interactive Brokers TWS broker adapter and settings connection test
- Twelve Data and Stooq data providers with multi-provider fallback
- Fear Index strategy with documented mathematical specification
- Trading-path memory and execution performance improvements
- CI workflow updates (GitHub Actions v4)

## Q4 2026
- Fix multi-timeframe strategy registration (`IDataProvider` export / provider contract)
- Linux-friendly optional dependencies (`win10toast` / platform markers in `requirements.txt`)
- Expand automated tests beyond placeholder `tests/` package
- PyPI publish parity with source install (document Python 3.10–3.12)

## Q1 2027
- Advanced analytics dashboard (UI polish and live metrics)
- Strategy backtesting UI improvements
- Remote monitoring and cloud sync hardening

## Q2 2027
- Mobile monitoring companion (read-only portfolio/alerts)
- Web dashboard for strategy health

## Future
- Social / copy trading and marketplace growth
- Multi-asset support (equities, crypto) where data providers allow
- Enterprise and compliance tooling (audit logs, role-based access)

For historical goals, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and version feature docs under `docs/V3.*_FEATURES.md`.

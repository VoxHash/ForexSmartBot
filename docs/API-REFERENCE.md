# API Reference

Canonical API reference for ForexSmartBot.

## Scope

This document includes:
- Python core interfaces used by strategies/brokers/providers
- Broker adapter contracts and expected behavior
- REST/WebSocket cloud endpoints used by remote/mobile integrations

## Python Interfaces

### `IBroker`
Implemented in `forexsmartbot/core/interfaces.py`.

Required methods:
- `connect() -> bool`
- `disconnect() -> None`
- `is_connected() -> bool`
- `get_price(symbol: str) -> Optional[float]`
- `submit_order(symbol: str, side: int, quantity: float, stop_loss: Optional[float], take_profit: Optional[float]) -> Optional[str]`
- `close_all(symbol: str) -> bool`
- `get_positions() -> Dict[str, Position]`
- `get_balance() -> float`
- `get_equity() -> float`

### `IDataProvider`
Implemented in `forexsmartbot/core/interfaces.py`.

Required methods:
- `get_data(symbol: str, start: str, end: str, interval: str = "1h") -> pd.DataFrame`
- `get_latest_price(symbol: str) -> Optional[float]`
- `get_historical_data(symbol: str, period: str = '1d', interval: str = '1h') -> pd.DataFrame`
- `is_available() -> bool`

### `IStrategy`
Implemented in `forexsmartbot/core/interfaces.py`.

Required methods:
- `name`
- `params`
- `set_params(**kwargs)`
- `indicators(df)`
- `signal(df)`
- `volatility(df)`
- `stop_loss(df, entry_price, side)`
- `take_profit(df, entry_price, side)`

## Broker Adapters

Located in `forexsmartbot/adapters/brokers/`:
- `PaperBroker`
- `MT4Broker`
- `RestBroker`
- `IBTWSBroker` (Interactive Brokers TWS / IB Gateway)

## Data Provider Adapters

Located in `forexsmartbot/adapters/data/`:
- `MT4Provider`
- `OANDAProvider`
- `AlphaVantageProvider`
- `TwelveDataProvider`
- `StooqProvider`
- `YFinanceProvider`
- `MultiProvider` (fallback chain)

## Cloud API Endpoints

Base URLs:
- REST API: `http://localhost:5000/api/v1`
- WebSocket API: `ws://localhost:8765`
- Remote Monitor: `http://localhost:8080`

Typical endpoints:
- `GET /api/v1/health`
- `GET /api/v1/account/balance`
- `GET /api/v1/account/positions`
- `POST /api/v1/orders`

Authentication:
- Bearer API key or JWT token depending on cloud module configuration.

## Notes

- `side` convention is `+1` (long/buy) and `-1` (short/sell).
- Providers should return standardized OHLCV DataFrames with columns: `Open`, `High`, `Low`, `Close`, `Volume`.
- For integration examples, see `examples/` and `docs/CLOUD_INTEGRATION_GUIDE.md`.

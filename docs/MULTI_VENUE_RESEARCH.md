# Multi-venue CEX / DEX research (3.4.1)

Desktop ForexSmartBot remains the execution host (`IBroker`). This note records
**live** public-catalog research used to schedule adapters. No production trade
keys are required for the probes.

## Venues mapped

| Id | Kind | Public / sandbox | Asset coverage (live probe) | Auth |
| --- | --- | --- | --- | --- |
| `kraken_spot` | CEX | `https://api.kraken.com/0/public` — Spot UAT only via Account Manager | ~1400+ online pairs; crypto + small fiat FX set (e.g. EUR/USD) | API key + secret (trade); public MD free |
| `kraken_futures` | CEX | Public catalog `https://futures.kraken.com/derivatives/api/v3`; demo UI `https://demo-futures.kraken.com` | ~230 tradeable instruments; crypto perps + FX (`PF_EURUSD`, …) + commodities (`PF_XAUUSD`, WTI/Brent/NatGas) | Separate demo vs prod keys |
| `binance_spot` | CEX | Testnet `https://testnet.binance.vision/api`; prod `https://api.binance.com/api` | Testnet 1000+ `TRADING` symbols; prod includes tokenized gold (PAXG/XAUT), not classic FX CFDs | Testnet keys from testnet.binance.vision; `/api` only on testnet |
| `oneinch` | Aggregator | `https://api.1inch.com` (Bearer) | On-chain / intent swaps (EVM + Solana modes); tokenized RWAs where listed | Business portal API key (KYC) |

Code registry: `forexsmartbot.venues.registry.VENUE_PROFILES`.  
Live probes: `forexsmartbot.venues.probes.probe_all_public()`.

## Thin adapters shipped

- `KrakenPublicBroker` — public Time + Ticker (`get_price`); orders refused.
- `BinancePublicBroker` — testnet ping + ticker/price; orders refused.
- `VenuePaperBroker` (3.4.2) — paper fills at live public prices (binance|kraken feed); orders/positions/reconnect; no keys.
- `BinanceSandboxBroker` (3.4.2) — HMAC signed Spot **Test Network** orders; mainnet refused; keys from env only.
- `BinanceLiveBroker` (3.4.3) — HMAC Spot **mainnet** orders; requires `FSB_LIVE_TRADING=1` + `BINANCE_LIVE_API_*`; testnet refused; kill-switch via `RiskEngine` / `FSB_KILL_SWITCH`.

Select **Venue Paper**, **Binance Sandbox**, **Binance Live**, **Kraken Public**, or
**Binance Public** in Settings → Broker Mode. Never set `FSB_LIVE_TRADING` in CI.

## Opsec

- Secrets only in local `.env` / UI settings (gitignored). Placeholders in `.env.example`.
- Use `forexsmartbot.venues.secrets.redact_mapping` / `mask_secret` before logging.
- Prefer trade-only keys, IP allowlists, and key rotation per venue; never put
  venue keys in the mobile companion.

## Reproduce probes

```bash
.venv/bin/python -c "from forexsmartbot.venues import probe_all_public; \
from pprint import pprint; pprint([{ 'id': r.venue_id, 'ok': r.ok, 'n': r.symbol_count, \
'classes': r.by_asset_class} for r in probe_all_public()])"
```

## References

- [Kraken Spot REST](https://docs.kraken.com/exchange/guides/rest/introduction)
- [Kraken Futures](https://docs.kraken.com/exchange/guides/futures/introduction)
- [Binance Spot Test Network](https://testnet.binance.vision/)
- [1inch Getting Started](https://business.1inch.com/portal/documentation/overview/getting-started)
- Extending brokers: [EXTENDING_BROKERS.md](EXTENDING_BROKERS.md)

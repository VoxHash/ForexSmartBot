# Security Policy

## Reporting a Vulnerability

Email contact@voxhash.dev with details and reproduction steps.

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

For detailed security best practices, see [docs/SECURITY.md](docs/SECURITY.md).

## Secrets and API keys (opsec)

- Copy `.env.example` → `.env` locally. **Never commit `.env`** (gitignored).
- Required/optional secret **names** are listed in `.env.example` with empty placeholders only — no real values in the repo.
- Do not log API keys, secrets, JWT material, or broker session tokens (including debug/health/companion paths).
- For any future exchange/broker work (Binance, Kraken, DEX adapters, etc.): use **least-privilege** keys (trade/read as needed; **no withdraw**), prefer testnet/sandbox first, rotate keys if exposed, and keep secrets on the desktop host only (not in the mobile companion).

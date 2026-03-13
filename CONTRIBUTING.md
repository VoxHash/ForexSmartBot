# Contributing to ForexSmartBot

Thanks for helping improve ForexSmartBot!

## Code of Conduct

Please read and follow our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Development Setup

```bash
# Clone
git clone https://github.com/VoxHash/ForexSmartBot.git
cd ForexSmartBot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Branching & Commit Style

- **Branches**: `feature/…`, `fix/…`, `docs/…`, `chore/…`
- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

Examples:
- `feat: add new LSTM strategy`
- `fix: resolve position sizing calculation error`
- `docs: update installation guide`

## Pull Requests

- Link related issues
- Add tests for new features
- Update documentation
- Follow the PR template
- Keep diffs focused and reviewable

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=forexsmartbot --cov-report=html

# Run specific test file
pytest tests/test_strategies.py
```

## Code Style

- Follow PEP 8
- Use `black` for formatting: `black forexsmartbot/`
- Use `ruff` for linting: `ruff check forexsmartbot/`
- Type hints encouraged for new code

## Release Process

- Semantic Versioning (MAJOR.MINOR.PATCH)
- Update [CHANGELOG.md](CHANGELOG.md)
- Tag releases: `git tag v3.1.0`

## Questions?

- Open an issue for questions
- Check [docs/](docs/) for detailed guides
- See [SUPPORT.md](SUPPORT.md) for support options

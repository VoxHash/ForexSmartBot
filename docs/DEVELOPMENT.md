# Development Guide

This guide covers the development workflow, architecture, and best practices for ForexSmartBot.

## Table of Contents

- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Code Organization](#code-organization)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Documentation](#documentation)
- [Release Process](#release-process)
- [Contributing](#contributing)

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- Virtual environment (recommended)

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/voxhash/ForexSmartBot.git
   cd ForexSmartBot
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

5. **Run tests to verify setup:**
   ```bash
   python -m pytest
   ```

### IDE Setup

#### VS Code

1. Install Python extension
2. Install recommended extensions:
   - Python
   - Pylance
   - Black Formatter
   - Ruff
   - GitLens

3. Configure settings (`.vscode/settings.json`):
   ```json
   {
     "python.defaultInterpreterPath": "./venv/bin/python",
     "python.formatting.provider": "black",
     "python.linting.enabled": true,
     "python.linting.ruffEnabled": true,
     "editor.formatOnSave": true,
     "editor.codeActionsOnSave": {
       "source.organizeImports": true
     }
   }
   ```

#### PyCharm

1. Open project
2. Configure Python interpreter to use virtual environment
3. Enable Black formatter
4. Configure Ruff as external tool

## Architecture Overview

ForexSmartBot follows a modular, layered architecture:

```
forexsmartbot/
├── core/           # Core business logic
│   ├── interfaces.py    # Abstract base classes
│   ├── portfolio.py     # Portfolio management
│   └── risk_engine.py   # Risk management
├── adapters/       # External integrations
│   ├── brokers/    # Broker implementations
│   └── data/       # Data providers
├── strategies/     # Trading strategies
├── services/       # Application services
│   ├── backtest.py     # Backtesting engine
│   ├── controller.py   # Trading controller
│   └── persistence.py  # Data persistence
└── ui/            # User interface
    ├── main_window.py     # Main window
    ├── settings_dialog.py # Settings dialog
    ├── charts.py          # Charting widgets
    └── theme.py           # Theme management
```

### Key Design Principles

1. **Separation of Concerns**: Each layer has a specific responsibility
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Interface Segregation**: Small, focused interfaces
4. **Open/Closed Principle**: Open for extension, closed for modification

## Code Organization

### Core Layer (`core/`)

Contains the fundamental business logic:

- **`interfaces.py`**: Abstract base classes defining contracts
- **`portfolio.py`**: Portfolio state management
- **`risk_engine.py`**: Risk calculation and position sizing

### Adapters Layer (`adapters/`)

Handles external system integration:

- **`brokers/`**: Broker implementations (Paper, MT4, REST)
- **`data/`**: Data provider implementations (YFinance, CSV)

### Strategies Layer (`strategies/`)

Trading strategy implementations:

- Each strategy is a separate module
- Implements `IStrategy` interface
- Contains strategy-specific logic

### Services Layer (`services/`)

Application services that orchestrate components:

- **`controller.py`**: Main trading controller
- **`backtest.py`**: Backtesting engine
- **`persistence.py`**: Data persistence

### UI Layer (`ui/`)

User interface components:

- **`main_window.py`**: Main application window
- **`settings_dialog.py`**: Settings management
- **`charts.py`**: Charting functionality
- **`theme.py`**: Theme management

## Development Workflow

### 1. Feature Development

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes:**
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test changes:**
   ```bash
   python -m pytest
   python -m ruff check .
   python -m mypy forexsmartbot/
   ```

4. **Commit changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

### 2. Bug Fixes

1. **Create bugfix branch:**
   ```bash
   git checkout -b bugfix/issue-description
   ```

2. **Fix the issue:**
   - Write failing test first (if applicable)
   - Implement fix
   - Ensure all tests pass

3. **Commit fix:**
   ```bash
   git commit -m "fix: description of the fix"
   ```

### 3. Pull Request Process

1. **Push branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request:**
   - Use the PR template
   - Provide clear description
   - Link related issues

3. **Code Review:**
   - Address reviewer feedback
   - Update tests if needed
   - Update documentation

4. **Merge:**
   - Squash and merge
   - Delete feature branch

## Testing

### Test Structure

```
tests/
├── __init__.py
├── test_risk.py          # Risk engine tests
├── test_strategies.py    # Strategy tests
├── test_backtest.py      # Backtesting tests
└── integration/          # Integration tests
    ├── __init__.py
    └── test_full_workflow.py
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_risk.py

# Run with coverage
python -m pytest --cov=forexsmartbot

# Run specific test
python -m pytest tests/test_risk.py::TestRiskEngine::test_position_sizing
```

### Writing Tests

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Arrange-Act-Assert**: Structure tests clearly
3. **Test Coverage**: Aim for high coverage of business logic
4. **Mocking**: Mock external dependencies

Example:
```python
def test_position_sizing_with_volatility_targeting(self):
    """Test that position size is reduced for high volatility."""
    # Arrange
    config = RiskConfig(volatility_target=0.02)
    engine = RiskEngine(config)
    
    # Act
    size_high_vol = engine.calculate_position_size("EURUSD", "SMA", 10000, 0.05)
    size_low_vol = engine.calculate_position_size("EURUSD", "SMA", 10000, 0.01)
    
    # Assert
    assert size_high_vol < size_low_vol
```

## Code Quality

### Style Guidelines

1. **Python Style**: Follow PEP 8
2. **Line Length**: 100 characters maximum
3. **Imports**: Use absolute imports, group by standard/third-party/local
4. **Docstrings**: Use Google style docstrings
5. **Type Hints**: Use type hints for all public functions

### Tools

- **Ruff**: Linting and formatting
- **Black**: Code formatting
- **MyPy**: Type checking
- **Pre-commit**: Automated quality checks

### Pre-commit Hooks

Configured hooks:
- `ruff`: Linting
- `black`: Formatting
- `mypy`: Type checking

## Documentation

### Documentation Structure

```
docs/
├── README.md              # Main documentation
├── Installation-Guide.md  # Installation instructions
├── Quick-Start-Tutorial.md # Getting started
├── Configuration-Guide.md  # Configuration
├── STRATEGIES.md          # Strategy development
├── RISK.md               # Risk management
├── EXTENDING_BROKERS.md   # Broker development
└── DEVELOPMENT.md         # This file
```

### Writing Documentation

1. **Use Markdown**: All docs in Markdown format
2. **Code Examples**: Include working code examples
3. **Screenshots**: Add UI screenshots where helpful
4. **Keep Updated**: Update docs with code changes

### Docstring Standards

```python
def calculate_position_size(self, symbol: str, strategy: str, 
                          balance: float, volatility: Optional[float]) -> float:
    """Calculate position size using risk management rules.
    
    Args:
        symbol: Trading symbol (e.g., 'EURUSD')
        strategy: Strategy name (e.g., 'SMA_Crossover')
        balance: Current account balance
        volatility: Recent volatility (0.0-1.0)
        
    Returns:
        Position size in account currency
        
    Raises:
        ValueError: If balance is negative
    """
```

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Steps

1. **Update version:**
   ```bash
   # Update pyproject.toml version
   # Update CHANGELOG.md
   ```

2. **Create release branch:**
   ```bash
   git checkout -b release/v3.0.0
   ```

3. **Final testing:**
   ```bash
   python -m pytest
   python -m ruff check .
   python -m mypy forexsmartbot/
   ```

4. **Create tag:**
   ```bash
   git tag v3.0.0
   git push origin v3.0.0
   ```

5. **GitHub Actions will:**
   - Build the package
   - Run tests
   - Create GitHub release
   - Publish to PyPI

### Pre-release Testing

1. **Test installation:**
   ```bash
   pip install forexsmartbot==3.0.0
   ```

2. **Test functionality:**
   ```bash
   python -m forexsmartbot
   ```

## Contributing

### Getting Started

1. Fork the repository
2. Clone your fork
3. Create feature branch
4. Make changes
5. Submit pull request

### Contribution Guidelines

1. **Code Quality**: Follow style guidelines
2. **Tests**: Add tests for new features
3. **Documentation**: Update docs as needed
4. **Commits**: Use conventional commit messages
5. **PRs**: Provide clear descriptions

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation improvements
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `question`: Further information is requested

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated
2. **Test Failures**: Check test data and dependencies
3. **Type Errors**: Run `mypy` for detailed type checking
4. **Style Issues**: Run `ruff` and `black` to fix

### Getting Help

1. Check existing issues
2. Search documentation
3. Create new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details

## Performance Considerations

### Optimization Guidelines

1. **Data Processing**: Use pandas efficiently
2. **Memory Usage**: Avoid large data copies
3. **UI Responsiveness**: Use threading for long operations
4. **Database**: Use connection pooling

### Profiling

```bash
# Profile memory usage
python -m memory_profiler app.py

# Profile execution time
python -m cProfile app.py
```

## Security

### Security Guidelines

1. **API Keys**: Never commit API keys
2. **Sensitive Data**: Use environment variables
3. **Input Validation**: Validate all inputs
4. **Dependencies**: Keep dependencies updated

### Security Checklist

- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] Dependencies up to date
- [ ] Security headers configured
- [ ] Error messages don't leak information

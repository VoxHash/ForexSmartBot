# Contributing to ForexSmartBot

Thank you for your interest in contributing to the ForexSmartBot! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

Before creating an issue, please:
1. Check if the issue already exists
2. Search through closed issues
3. Verify you're using the latest version

When creating an issue, please include:
- **Clear title**: Brief description of the issue
- **Description**: Detailed explanation of the problem
- **Steps to reproduce**: How to reproduce the issue
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, app version
- **Screenshots**: If applicable
- **Logs**: Relevant error messages or logs

### Suggesting Features

We welcome feature suggestions! Please:
1. Check if the feature already exists
2. Search through existing feature requests
3. Provide a clear description
4. Explain the use case and benefits
5. Consider implementation complexity

### Code Contributions

#### Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/ForexSmartBot.git
   cd ForexSmartBot
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

#### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clean, readable code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests**:
   ```bash
   pytest
   pytest --cov=forexsmartbot tests/  # With coverage
   ```

4. **Check code style**:
   ```bash
   black forexsmartbot/
   isort forexsmartbot/
   flake8 forexsmartbot/
   mypy forexsmartbot/
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: Brief description of changes"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**

## 📋 Development Guidelines

### Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

### Project Structure

```
forexsmartbot/
├── core/           # Core functionality
├── ui/             # UI components
├── strategies/     # Trading strategies
├── adapters/       # Data and broker adapters
├── services/       # Business logic
└── tests/          # Test files
```

### Architecture Principles

- **MVC Pattern**: Model-View-Controller architecture
- **Service Layer**: Business logic in services
- **Dependency Injection**: Loose coupling between components
- **Error Handling**: Comprehensive error handling
- **Logging**: Detailed logging for debugging
- **Testing**: Unit and integration tests

## 🧪 Testing

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── ui/            # UI tests
```

### Writing Tests

- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test component interactions
- **UI tests**: Test user interface functionality
- **Coverage**: Aim for high test coverage

## 📚 Documentation

### Documentation Standards

- **Clear and concise**: Write clear, easy-to-understand documentation
- **Examples**: Include code examples
- **Up-to-date**: Keep documentation current
- **Comprehensive**: Cover all aspects of the project

### Types of Documentation

- **API Documentation**: Function and class documentation
- **User Guide**: End-user documentation
- **Developer Guide**: Developer documentation
- **README**: Project overview and quick start
- **Changelog**: Version history and changes

## 🐛 Bug Reports

### Before Reporting

1. **Check existing issues**: Search for similar issues
2. **Update to latest version**: Ensure you're using the latest version
3. **Check documentation**: Review relevant documentation
4. **Test in clean environment**: Test in a fresh installation

## ✨ Feature Requests

### Before Requesting

1. **Check existing features**: Ensure the feature doesn't already exist
2. **Search requests**: Look for similar feature requests
3. **Consider alternatives**: Think about workarounds
4. **Assess complexity**: Consider implementation complexity

## 🔒 Security

### Security Issues

If you discover a security vulnerability, please:
1. **Do not** create a public issue
2. Email us at security@voxhash.dev
3. Include detailed information about the vulnerability
4. Allow time for us to address the issue before disclosure

## 📝 Commit Messages

### Commit Message Format

```
type(scope): brief description

Detailed description of changes

Closes #123
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes
- **refactor**: Code refactoring
- **test**: Test changes
- **chore**: Maintenance tasks

## 🏷️ Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version numbers updated
- [ ] Release notes prepared
- [ ] Builds tested
- [ ] Release created

## 🤔 Questions?

If you have questions about contributing:

- **GitHub Discussions**: Use GitHub Discussions for general questions
- **Issues**: Create an issue for specific problems
- **Email**: Contact us at contact@voxhash.dev

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- **README**: Listed in the contributors section
- **Release Notes**: Mentioned in relevant releases
- **Changelog**: Credited for their contributions

Thank you for contributing to the ForexSmartBot! 🎉

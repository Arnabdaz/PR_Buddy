# Contributing to PR Buddy

Thank you for your interest in contributing to PR Buddy! This guide will help you get started with contributing to our AI-powered pull request assistant.

## 🎯 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## 🚀 Getting Started

### Prerequisites

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment following the main README
4. Create a new branch for your feature/fix

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/pr-buddy.git
cd pr-buddy

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/pr-buddy.git

# Create a feature branch
git checkout -b feature/your-feature-name
```

## 📝 Contribution Guidelines

### 1. Types of Contributions

We welcome various types of contributions:

- **🐛 Bug Fixes** - Fix issues in existing functionality
- **✨ New Features** - Add new capabilities to PR Buddy
- **📚 Documentation** - Improve guides, add examples, fix typos
- **🧪 Tests** - Add test coverage for existing or new features
- **🎨 UI/UX** - Improve user experience and interfaces
- **🔧 Performance** - Optimize speed and resource usage

### 2. Before You Start

- Check existing issues and PRs to avoid duplicates
- For major changes, open an issue first to discuss
- Ensure your idea aligns with the project's goals

### 3. Development Process

#### For MCP Server Changes

```bash
# Navigate to specific server
cd servers/[cve-search|git|github-mcp-server|jira-mcp]

# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black .
uv run ruff check . --fix
```

#### For AI Rules Changes

```bash
# Edit rule files
vim .cursor/rules/pr_[creation|review|update].mdc

# Test with Cursor
# Open Cursor and test your changes with sample PRs
```

### 4. Commit Guidelines

We follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples:**

```bash
feat(github): add support for draft PRs
fix(cve): handle rate limiting gracefully
docs(readme): add troubleshooting section
perf(jira): implement connection pooling
```

### 5. Testing Requirements

#### Unit Tests

```python
# Example test structure
def test_pr_creation():
    """Test PR creation with valid inputs."""
    # Arrange
    mock_github = Mock()

    # Act
    result = create_pr(mock_github, ...)

    # Assert
    assert result.success == True
```

#### Integration Tests

```bash
# Run integration tests
cd servers/[server-name]
uv run pytest tests/integration/
```

#### Manual Testing Checklist

- [ ] Test with Cursor IDE
- [ ] Verify all MCP servers start correctly
- [ ] Test each AI rule (creation, review, update)
- [ ] Check error handling
- [ ] Verify token security

## 📋 Pull Request Process

### 1. PR Checklist

Before submitting your PR, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] PR description clearly explains changes
- [ ] No sensitive data (tokens, passwords) included

### 2. PR Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Other (specify)

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)

Add screenshots for UI changes

## Related Issues

Fixes #123
Relates to #456
```

### 3. Review Process

1. Submit PR against `main` branch
2. Automated checks will run
3. Maintainers will review within 48 hours
4. Address feedback promptly
5. Once approved, PR will be merged

## 🏗️ Architecture Guidelines

### MCP Server Development

```python
# Follow MCP protocol standards
from mcp.server import Server
from mcp.server.models import Tool

class CustomServer(Server):
    """Your server implementation."""

    @tool()
    async def custom_tool(self, param: str) -> str:
        """Tool documentation."""
        # Implementation
        pass
```

### AI Rule Development

```markdown
# Rule Structure

## ROLE DEFINITION

Define the assistant's role and expertise

## CRITICAL REQUIREMENT

Specify mandatory behaviors

## WORKFLOW

Detail step-by-step process

## RESPONSE PATTERNS

Provide example responses
```

## 🧪 Testing Guidelines

### Test Coverage Requirements

- Minimum 80% code coverage for new features
- Critical paths must have 100% coverage
- Include edge cases and error scenarios

### Test Organization

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── fixtures/       # Test data
└── mocks/         # Mock objects
```

## 📚 Documentation Standards

### Code Documentation

```python
def process_pr(pr_number: int, action: str) -> dict:
    """
    Process a pull request with specified action.

    Args:
        pr_number: The PR number to process
        action: The action to perform ('review', 'merge', 'close')

    Returns:
        dict: Result containing status and details

    Raises:
        GitHubError: If GitHub API call fails
        ValueError: If action is invalid
    """
```

### README Updates

- Keep examples current
- Update configuration when adding features
- Include troubleshooting for new issues

## 🔧 Development Tools

### Recommended VS Code Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "github.copilot",
    "eamodio.gitlens"
  ]
}
```

### Debugging MCP Servers

```bash
# Enable debug logging
export MCP_LOG_LEVEL=DEBUG

# Run server in debug mode
uv run python -m debugpy --listen 5678 main.py

# Check logs
tail -f ~/Library/Logs/Cursor/mcp*.log
```

## 🚀 Release Process

1. **Version Bump** - Update version in `pyproject.toml`
2. **Changelog** - Update CHANGELOG.md
3. **Testing** - Run full test suite
4. **Documentation** - Update README if needed
5. **Tag** - Create version tag
6. **Release** - Create GitHub release

## 📮 Getting Help

### Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [Project Issues](https://github.com/YOUR_REPO/issues)
- [Discussions](https://github.com/YOUR_REPO/discussions)

### Contact

- Open an issue for bugs/features
- Start a discussion for questions
- Tag maintainers for urgent issues

## 🏆 Recognition

Contributors are recognized in:

- README.md contributors section
- GitHub contributors page
- Release notes

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to PR Buddy! Your efforts help make PR management better for everyone. 🎉

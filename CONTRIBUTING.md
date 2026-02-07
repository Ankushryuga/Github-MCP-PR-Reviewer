# Contributing to GitHub PR Reviewer MCP

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. **Fork and clone the repository**

```bash
git clone https://github.com/yourusername/github-pr-reviewer-mcp.git
cd github-pr-reviewer-mcp
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
pip install pytest  # For running tests
```

4. **Install pre-commit hooks (optional)**

```bash
pip install pre-commit
pre-commit install
```

## Code Style

We follow these conventions:

- **PEP 8** for Python code
- **Type hints** for all function parameters and returns
- **Docstrings** for all public functions (Google style)
- **Pydantic models** for input validation
- **Async/await** for I/O operations

Example:

```python
async def example_function(param: str, count: int = 5) -> Dict[str, Any]:
    """
    Brief description of what this function does.

    Args:
        param (str): Description of param
        count (int): Description of count, defaults to 5

    Returns:
        Dict[str, Any]: Description of return value
    """
    # Implementation
    pass
```

## Adding New Tools

To add a new MCP tool:

1. **Define Pydantic input model**

```python
class NewToolInput(BaseModel):
    """Input for new tool."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    param: str = Field(..., description="Parameter description")
```

2. **Create the tool function**

```python
@mcp.tool(
    name="github_pr_new_tool",
    annotations={
        "title": "Human-Readable Title",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def new_tool(params: NewToolInput) -> str:
    """
    Tool description.

    Args:
        params (NewToolInput): Input parameters

    Returns:
        str: Tool output
    """
    # Implementation
    pass
```

3. **Add tests**

```python
def test_new_tool():
    """Test the new tool."""
    # Test implementation
    pass
```

4. **Update documentation**

- Add tool to README.md
- Update ARCHITECTURE.md if needed
- Add usage examples

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test_github_pr_mcp.py

# Run with coverage
pytest --cov=github_pr_mcp --cov-report=html
```

### Writing Tests

- Test file names: `test_*.py`
- Test class names: `Test*`
- Test function names: `test_*`
- Use pytest fixtures for common setups
- Mock external dependencies

Example:

```python
import pytest
from unittest.mock import Mock, patch

def test_example():
    """Test description."""
    # Arrange
    input_data = {"key": "value"}

    # Act
    result = function_to_test(input_data)

    # Assert
    assert result["success"] is True
```

## Pull Request Process

1. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**

- Write code
- Add tests
- Update documentation

3. **Run tests and linting**

```bash
pytest
python -m pylint github_pr_mcp.py
```

4. **Commit your changes**

```bash
git add .
git commit -m "feat: add new feature description"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding tests
- `refactor:` Code refactoring

5. **Push to your fork**

```bash
git push origin feature/your-feature-name
```

6. **Open a Pull Request**

- Describe your changes
- Reference any related issues
- Ensure CI checks pass

## Code Review

Your PR will be reviewed for:

- Code quality and style
- Test coverage
- Documentation completeness
- Backward compatibility
- Security implications

## Release Process

Maintainers follow this process for releases:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. Build and publish package

## Questions?

- Open an issue for bugs
- Start a discussion for feature ideas
- Join our Discord for chat

Thank you for contributing! 🎉

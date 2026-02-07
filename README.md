# GitHub PR Reviewer MCP Server

An MCP (Model Context Protocol) server that provides automated code review capabilities for Go repositories. This server enables Claude to analyze pull requests, run tests, perform static analysis, and post review comments to GitHub.

## Features

- 🔍 **Static Code Analysis**: Run golangci-lint, gofmt, and go vet on Go code
- ✅ **Automated Testing**: Execute Go tests with coverage analysis
- 📊 **PR Diff Analysis**: Fetch and analyze GitHub PR changes
- 💬 **Review Comments**: Automatically post review feedback to GitHub
- 🤖 **Comprehensive Review**: End-to-end PR review workflow orchestration

## Architecture

```
┌─────────────────┐
│                 │
│  Claude.ai /    │
│  Claude Desktop │
│                 │
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────────────────────────┐
│  GitHub PR Reviewer MCP Server      │
│                                     │
│  Tools:                             │
│  • github_pr_analyze_code           │
│  • github_pr_run_tests              │
│  • github_pr_get_diff               │
│  • github_pr_post_review            │
│  • github_pr_comprehensive_review   │
└────────┬────────────────────────────┘
         │
         ├──────────────┬──────────────┐
         │              │              │
    ┌────▼───┐    ┌────▼────┐    ┌───▼─────┐
    │ GitHub │    │  Local  │    │   Go    │
    │  API   │    │  Files  │    │  Tools  │
    └────────┘    └─────────┘    └─────────┘
```

## Prerequisites

### System Requirements

- Python 3.10 or higher
- Go 1.20 or higher (for Go project analysis)
- Git

### Go Tools Installation

Install required Go analysis tools:

```bash
# Install golangci-lint
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Ensure Go tools are in PATH
export PATH=$PATH:$(go env GOPATH)/bin
```

### GitHub Authentication

You need a GitHub Personal Access Token with the following permissions:

- `repo` (for private repositories)
- `pull_requests:write` (for posting comments)

Create a token at: https://github.com/settings/tokens

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/github-pr-reviewer-mcp.git
cd github-pr-reviewer-mcp
```

### 2. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Environment Variables

```bash
# Set your GitHub token
export GITHUB_TOKEN="ghp_your_token_here"
```

For persistent configuration, add to `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Configure Claude Desktop

Add the server to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "github-pr-reviewer": {
      "command": "python",
      "args": ["/absolute/path/to/github-pr-reviewer-mcp/github_pr_mcp.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

Replace `/absolute/path/to/github-pr-reviewer-mcp/` with the actual path.

### 5. Restart Claude Desktop

After updating the configuration, restart Claude Desktop for changes to take effect.

## Usage

### Available Tools

#### 1. `github_pr_analyze_code`

Analyze Go code for quality issues using static analysis tools.

**Parameters:**

- `file_path` (string): Path to Go file or directory
- `analysis_type` (string): "lint", "fmt", "vet", or "all"
- `response_format` (string): "markdown" or "json"

**Example:**

```
Can you analyze the code in /path/to/myproject/main.go?
```

#### 2. `github_pr_run_tests`

Run Go tests with optional coverage analysis.

**Parameters:**

- `package_path` (string): Go package path (default: "./...")
- `verbose` (bool): Enable verbose output
- `coverage` (bool): Generate coverage report
- `response_format` (string): "markdown" or "json"

**Example:**

```
Run tests on my Go project at /path/to/myproject with coverage
```

#### 3. `github_pr_get_diff`

Fetch the diff for a GitHub pull request.

**Parameters:**

- `owner` (string): Repository owner
- `repo` (string): Repository name
- `pr_number` (int): Pull request number
- `response_format` (string): "markdown" or "json"

**Example:**

```
Show me the diff for PR #123 in owner/repo
```

#### 4. `github_pr_post_review`

Post a review comment to a GitHub pull request.

**Parameters:**

- `owner` (string): Repository owner
- `repo` (string): Repository name
- `pr_number` (int): Pull request number
- `body` (string): Review comment text
- `event` (string): "COMMENT", "APPROVE", or "REQUEST_CHANGES"
- `commit_id` (string, optional): Specific commit to review

**Example:**

```
Post a review comment to PR #123 in owner/repo saying "LGTM! Great work on the refactoring."
```

#### 5. `github_pr_comprehensive_review`

Perform comprehensive automated review of a GitHub pull request.

**Parameters:**

- `owner` (string): Repository owner
- `repo` (string): Repository name
- `pr_number` (int): Pull request number
- `local_path` (string, optional): Local path to cloned repository
- `run_tests` (bool): Whether to run tests
- `post_comments` (bool): Auto-post review to GitHub
- `response_format` (string): "markdown" or "json"

**Example:**

```
Review PR #456 in myorg/myrepo. The local clone is at /home/user/myrepo. Run tests and post the review.
```

### Example Workflows

#### Workflow 1: Quick Static Analysis

```
User: Analyze the Go code in my-project/handlers/api.go

Claude will:
1. Use github_pr_analyze_code tool
2. Run golangci-lint, gofmt, and go vet
3. Return formatted results with any issues found
```

#### Workflow 2: Test a Local Change

```
User: Run tests on my Go project at /home/user/awesome-app with coverage

Claude will:
1. Use github_pr_run_tests tool
2. Execute tests with coverage
3. Return test results and coverage percentages
```

#### Workflow 3: Review a GitHub PR

```
User: Review PR #42 in acme/rocket-engine. Local copy is at /home/user/rocket-engine.

Claude will:
1. Use github_pr_get_diff to fetch PR changes
2. Identify changed Go files
3. Use github_pr_analyze_code on each changed file
4. Use github_pr_run_tests to run the test suite
5. Generate comprehensive review summary
6. Optionally post review to GitHub (if requested)
```

#### Workflow 4: Complete Automated Review

```
User: Do a full automated review of PR #789 in myorg/backend-api, local path is /projects/backend-api, and post the results.

Claude will:
1. Use github_pr_comprehensive_review tool
2. Fetch PR diff
3. Analyze all changed Go files
4. Run full test suite
5. Generate review with recommendations
6. Post review comment to GitHub PR
```

## Configuration

### Environment Variables

| Variable       | Required | Description                  |
| -------------- | -------- | ---------------------------- |
| `GITHUB_TOKEN` | Yes      | GitHub Personal Access Token |

### Tool-Specific Settings

You can customize analysis behavior by modifying the MCP server code:

```python
# In github_pr_mcp.py

# Change default golangci-lint settings
lint_result = _run_command(
    ["golangci-lint", "run", "--config", ".golangci.yml", str(file_path)]
)

# Adjust test timeout
result = subprocess.run(
    cmd,
    timeout=600  # 10 minutes instead of 5
)
```

## Troubleshooting

### Issue: "GITHUB_TOKEN environment variable not set"

**Solution:** Ensure the token is set in Claude Desktop config:

```json
{
  "mcpServers": {
    "github-pr-reviewer": {
      "env": {
        "GITHUB_TOKEN": "ghp_your_actual_token"
      }
    }
  }
}
```

### Issue: "golangci-lint: command not found"

**Solution:** Install golangci-lint and ensure it's in PATH:

```bash
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
export PATH=$PATH:$(go env GOPATH)/bin
```

### Issue: MCP server not appearing in Claude Desktop

**Solution:**

1. Verify the config file path is correct for your OS
2. Check JSON syntax (use a JSON validator)
3. Ensure the Python script path is absolute
4. Restart Claude Desktop completely
5. Check Claude Desktop logs for errors

### Issue: Tests failing with "no Go files in package"

**Solution:** Ensure you're running tests from the correct directory:

- Set `local_path` parameter to repository root
- Check that test files exist and have `_test.go` suffix

## Development

### Running Tests

```bash
# Run Python tests
python -m pytest tests/

# Test MCP server directly
python github_pr_mcp.py
```

### Adding New Tools

To add a new analysis tool:

1. Define a Pydantic input model
2. Create a helper function for the operation
3. Add an `@mcp.tool` decorated function
4. Update documentation

Example:

```python
class NewToolInput(BaseModel):
    param: str = Field(..., description="Parameter description")

@mcp.tool(name="github_pr_new_tool")
async def new_tool(params: NewToolInput) -> str:
    """Tool description."""
    # Implementation
    pass
```

### Code Style

This project follows:

- PEP 8 for Python code
- Type hints for all functions
- Pydantic models for input validation
- Comprehensive docstrings

## Security Best Practices

1. **Never commit tokens**: Keep `GITHUB_TOKEN` in environment variables only
2. **Use minimal permissions**: Grant only necessary GitHub token scopes
3. **Validate inputs**: All inputs are validated via Pydantic models
4. **Limit file access**: Server only reads/writes to specified directories
5. **Timeout operations**: All commands have reasonable timeouts

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code passes linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:

- GitHub Issues: https://github.com/yourusername/github-pr-reviewer-mcp/issues
- MCP Documentation: https://modelcontextprotocol.io/
- Anthropic Discord: https://discord.gg/anthropic

## Changelog

### v1.0.0 (2025-02-07)

- Initial release
- Static code analysis support (golangci-lint, gofmt, go vet)
- Test execution with coverage
- GitHub PR integration
- Comprehensive review workflow

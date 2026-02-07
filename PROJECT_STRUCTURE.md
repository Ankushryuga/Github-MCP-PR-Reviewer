# Project Structure

```
github-pr-reviewer-mcp/
│
├── github_pr_mcp.py              # Main MCP server implementation
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project metadata and build config
├── pytest.ini                     # Pytest configuration
├── test_github_pr_mcp.py         # Test suite
├── install.sh                     # Installation script (executable)
│
├── README.md                      # Main documentation
├── QUICKSTART.md                  # 5-minute setup guide
├── ARCHITECTURE.md                # System architecture documentation
├── FAQ.md                         # Frequently asked questions
├── CONTRIBUTING.md                # Contribution guidelines
├── CHANGELOG.md                   # Version history
├── LICENSE                        # MIT License
│
├── .env.example                   # Environment variable template
├── .gitignore                     # Git ignore rules
├── claude_desktop_config.json.example  # Claude Desktop config template
│
└── examples/
    └── sample-go-project/         # Example Go project for testing
        ├── main.go                # Main application code
        ├── main_test.go           # Test file
        ├── go.mod                 # Go module definition
        └── .golangci.yml          # Linter configuration
```

## File Descriptions

### Core Files

- **`github_pr_mcp.py`**: The main MCP server implementation containing all tools and logic
- **`requirements.txt`**: Lists all Python package dependencies
- **`pyproject.toml`**: Modern Python project configuration (PEP 518)
- **`install.sh`**: Automated installation script for quick setup

### Documentation

- **`README.md`**: Comprehensive guide covering installation, usage, and troubleshooting
- **`QUICKSTART.md`**: Get started in 5 minutes with step-by-step instructions
- **`ARCHITECTURE.md`**: Detailed system design and component documentation
- **`FAQ.md`**: Common questions and answers
- **`CONTRIBUTING.md`**: Guidelines for contributors
- **`CHANGELOG.md`**: Version history and release notes

### Configuration

- **`.env.example`**: Template for environment variables (GITHUB_TOKEN)
- **`claude_desktop_config.json.example`**: Template for Claude Desktop MCP configuration
- **`.gitignore`**: Specifies files Git should ignore (tokens, cache, etc.)

### Testing

- **`test_github_pr_mcp.py`**: Comprehensive test suite using pytest
- **`pytest.ini`**: Configuration for pytest test runner

### Examples

- **`examples/sample-go-project/`**: A complete Go project for testing the MCP server
  - **`main.go`**: Example Go application with HTTP handlers
  - **`main_test.go`**: Unit tests demonstrating test execution
  - **`go.mod`**: Go module file
  - **`.golangci.yml`**: Example linter configuration

## Usage Flow

```
1. User installs via install.sh
   ↓
2. User configures Claude Desktop with claude_desktop_config.json
   ↓
3. Claude Desktop loads github_pr_mcp.py as MCP server
   ↓
4. User interacts with Claude to review code
   ↓
5. MCP server executes tools (analyze, test, review)
   ↓
6. Results returned to Claude and displayed to user
```

## Development Workflow

```
1. Clone repository
   ↓
2. Run install.sh (creates venv, installs deps)
   ↓
3. Make changes to github_pr_mcp.py or tests
   ↓
4. Run pytest to verify changes
   ↓
5. Test manually with Claude Desktop
   ↓
6. Update documentation as needed
   ↓
7. Submit PR
```

## Adding New Features

To add a new tool:
1. Define Pydantic model for input validation
2. Implement tool function with `@mcp.tool` decorator
3. Add helper functions as needed
4. Write tests in `test_github_pr_mcp.py`
5. Update `README.md` with usage examples
6. Update `ARCHITECTURE.md` if design changes

## Security Considerations

- `GITHUB_TOKEN` should NEVER be committed
- Use `.gitignore` to exclude sensitive files
- Store tokens only in environment variables
- Review `.env.example` for proper format
- Never log tokens or credentials

## Next Steps

After setting up:
1. Read `QUICKSTART.md` for 5-minute setup
2. Try the example in `examples/sample-go-project/`
3. Review `FAQ.md` for common issues
4. Check `CONTRIBUTING.md` to contribute

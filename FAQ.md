# Frequently Asked Questions (FAQ)

## General Questions

### What is MCP?

MCP (Model Context Protocol) is an open protocol developed by Anthropic that allows Claude to connect to external data sources and tools. It enables Claude to interact with your local files, APIs, and services in a standardized way.

### Why use this instead of GitHub Actions?

This MCP server is designed for interactive code review with Claude, not automated CI/CD:

- **Interactive**: Ask Claude questions about code quality
- **Conversational**: Get explanations and suggestions
- **Local-first**: Works on your machine before pushing
- **Flexible**: Ad-hoc reviews without configuration files

GitHub Actions is better for automated checks on every commit. This tool is better for interactive development and review.

### Does this support languages other than Go?

Currently, this MCP server is optimized for Go projects. However, the architecture can be extended:

- The code analysis framework is modular
- Adding new language support requires implementing language-specific tools
- PRs for other languages are welcome!

## Installation Questions

### Do I need to install Go to use this?

Yes, if you want to analyze Go code. The server uses Go tools:
- `go vet` (included with Go)
- `gofmt` (included with Go)
- `golangci-lint` (installed separately)
- `go test` (included with Go)

### Where do I get a GitHub token?

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` and `pull_requests:write`
4. Copy the token (starts with `ghp_`)

### Can I use this without Claude Desktop?

Yes! While this guide focuses on Claude Desktop integration, the MCP server can be used with:
- Claude.ai (if MCP support is enabled)
- Any MCP-compatible client
- Direct testing via command line

### Why isn't my MCP server showing up in Claude Desktop?

Common issues:
1. **Path is not absolute**: Use full path like `/Users/you/github-pr-reviewer-mcp/github_pr_mcp.py`
2. **JSON syntax error**: Validate your config file
3. **Python not in PATH**: Use full path to Python executable
4. **Didn't restart**: Completely quit and reopen Claude Desktop

## Usage Questions

### Can I review private repositories?

Yes! As long as your GitHub token has access to the repository:
- Personal token needs `repo` scope for private repos
- OAuth app needs to be installed on the organization

### How do I review a PR without a local clone?

You can do a limited review:
```
Get the diff for PR #123 in owner/repo
```

For comprehensive analysis (linting, tests), you need a local clone.

### Can this automatically comment on all PRs?

Not currently. The tool requires manual invocation. For automatic reviews, you'd need to:
- Switch to streamable HTTP transport
- Set up webhooks
- Deploy as a service

This is a planned feature for future versions.

### What if I don't want to post comments to GitHub?

Set `post_comments=false`:
```
Review PR #123 in owner/repo, local path is /path/to/repo, but don't post the review
```

Claude will analyze and show you the results without posting.

## Technical Questions

### What data does this send to Anthropic?

When using Claude Desktop:
- Your prompts and the MCP tool results are sent to Claude
- Code snippets analyzed may be included in context
- GitHub tokens are NOT sent to Anthropic (they stay local)
- See Anthropic's privacy policy for details

### How secure is my GitHub token?

The token:
- Stored only in your local Claude config file
- Used only for GitHub API calls from your machine
- Never sent to Anthropic servers
- Should have minimal necessary permissions

### Can I use different linters?

Yes! Edit `github_pr_mcp.py`:

```python
# Change from golangci-lint to your preferred linter
lint_result = _run_command(
    ["your-linter", "args", str(file_path)]
)
```

### How do I customize the review format?

Edit the `_format_markdown_analysis()` function in `github_pr_mcp.py` to change:
- Emoji usage
- Section ordering
- Verbosity level
- Formatting style

### What's the difference between 'lint', 'fmt', and 'vet'?

- **golangci-lint**: Comprehensive linter (runs 30+ different linters)
- **gofmt**: Official Go formatting checker
- **go vet**: Official Go static analysis tool (catches common mistakes)

Use "all" to run all three for comprehensive analysis.

## Troubleshooting

### "GITHUB_TOKEN environment variable not set"

Check that:
1. Token is set in `claude_desktop_config.json` under `env`
2. No typos in the variable name
3. Token value is in quotes
4. Claude Desktop was restarted after config change

### "golangci-lint: command not found"

Install it:
```bash
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
export PATH=$PATH:$(go env GOPATH)/bin
```

Add the export to your `~/.bashrc` or `~/.zshrc` for persistence.

### Tests are failing but they work locally

Ensure:
1. You're running tests from the repository root
2. Go modules are initialized (`go.mod` exists)
3. Dependencies are installed (`go mod tidy`)
4. Working directory is set correctly in the tool call

### API rate limit exceeded

GitHub API has limits:
- 5000 requests/hour (authenticated)
- 60 requests/hour (unauthenticated)

If you hit the limit:
- Wait for the rate limit to reset
- Use a different token
- Reduce the number of API calls

### "Permission denied" errors

Check:
1. File permissions on the script: `chmod +x install.sh`
2. Python has permission to execute commands
3. You have read access to the Go files
4. GitHub token has the right scopes

## Performance Questions

### How long does a typical review take?

Depends on project size:
- Single file analysis: 2-5 seconds
- Small PR (< 5 files): 10-30 seconds
- Medium PR (5-20 files): 30-90 seconds
- Large PR (20+ files): 2-5 minutes

### Can I speed it up?

Yes:
- Use selective analysis (only `lint` or `fmt`, not `all`)
- Run tests separately if they're slow
- Analyze only changed files, not entire codebase
- Use faster linters (skip golangci-lint)

### Does it cache results?

Not currently. Each analysis is fresh. Caching is a planned feature.

## Feature Requests

### Can this support JavaScript/TypeScript?

Not yet, but it's on the roadmap! Contributions welcome.

### Can this integrate with Slack/Discord?

Not currently, but you could:
- Use the comprehensive review tool
- Parse the JSON output
- Send to Slack/Discord via their APIs

### Can I customize the review criteria?

Yes! Edit the golangci-lint configuration in `.golangci.yml`:
```yaml
linters:
  enable:
    - your-preferred-linters
```

### Will this work with GitHub Enterprise?

You can modify the `GITHUB_API_BASE` constant in `github_pr_mcp.py`:
```python
GITHUB_API_BASE = "https://your-github-enterprise.com/api/v3"
```

## Getting Help

Still have questions?

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For general questions
- **Discord**: Real-time chat support
- **Documentation**: Check README.md and ARCHITECTURE.md

## Contributing

Want to improve this FAQ?
- Add questions you wish were here
- Improve existing answers
- Submit a PR!

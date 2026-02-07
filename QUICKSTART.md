# Quick Start Guide

Get started with the GitHub PR Reviewer MCP Server in 5 minutes!

## Prerequisites Checklist

Before you begin, make sure you have:

- [ ] Python 3.10 or higher installed
- [ ] Go 1.20 or higher installed (for analyzing Go projects)
- [ ] Git installed
- [ ] A GitHub account with a Personal Access Token

## Step 1: Installation (2 minutes)

```bash
# Clone the repository
git clone https://github.com/yourusername/github-pr-reviewer-mcp.git
cd github-pr-reviewer-mcp

# Run the installation script
./install.sh
```

The script will:
- Create a Python virtual environment
- Install all dependencies
- Install golangci-lint (if Go is available)
- Provide configuration instructions

## Step 2: Get Your GitHub Token (1 minute)

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name like "MCP PR Reviewer"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `pull_requests:write` (Ability to write PR reviews)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)

## Step 3: Configure Environment (1 minute)

### Option A: Using Environment Variable

```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
source ~/.bashrc
```

### Option B: Using .env File

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your token
# GITHUB_TOKEN=ghp_your_token_here
```

## Step 4: Configure Claude Desktop (1 minute)

Find and edit your Claude Desktop config file:

### macOS
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Linux
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

### Windows
```
notepad %APPDATA%\Claude\claude_desktop_config.json
```

Add this configuration (replace the path with your actual path):

```json
{
  "mcpServers": {
    "github-pr-reviewer": {
      "command": "python",
      "args": ["/full/path/to/github-pr-reviewer-mcp/github_pr_mcp.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_actual_token_here"
      }
    }
  }
}
```

**Important:** Use the full absolute path to `github_pr_mcp.py`!

## Step 5: Restart Claude Desktop

Completely quit and restart Claude Desktop for the changes to take effect.

## Step 6: Test It! (30 seconds)

Open Claude Desktop and try these commands:

### Test 1: Analyze Local Code
```
Analyze the Go code in /path/to/github-pr-reviewer-mcp/examples/sample-go-project
```

### Test 2: Run Tests
```
Run tests on the sample Go project at /path/to/github-pr-reviewer-mcp/examples/sample-go-project with coverage
```

### Test 3: Review a GitHub PR (if you have one)
```
Review PR #123 in owner/repo
```

## Common First-Time Issues

### "MCP server not found"
- ✅ Check that the path in `claude_desktop_config.json` is absolute
- ✅ Verify the path actually exists: `ls /path/to/github_pr_mcp.py`
- ✅ Restart Claude Desktop completely

### "GITHUB_TOKEN not set"
- ✅ Check the token is in your config file
- ✅ Make sure there are no extra spaces or quotes
- ✅ Verify the token starts with `ghp_`

### "golangci-lint: command not found"
```bash
# Install golangci-lint
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Add to PATH
export PATH=$PATH:$(go env GOPATH)/bin
```

### "Permission denied" on install.sh
```bash
chmod +x install.sh
./install.sh
```

## What's Next?

Now that you're set up, you can:

1. **Clone a Go repository** you want to review
2. **Create test PRs** to practice automated reviews
3. **Customize the linting rules** in `.golangci.yml`
4. **Integrate into your workflow** for all PR reviews

## Example Workflows

### Review Your Own PR

```bash
# 1. Clone your repository
git clone https://github.com/you/your-go-project.git
cd your-go-project

# 2. In Claude Desktop, ask:
Review PR #42 in you/your-go-project. The local clone is at /path/to/your-go-project
```

### Quick Code Check Before Committing

```bash
# Before you commit, ask Claude:
Analyze the Go code in /path/to/your-project/pkg/handlers/api.go
```

### Full Pre-Merge Review

```bash
# Ask Claude for comprehensive review:
Do a full automated review of PR #789 in org/repo, local path is /projects/repo, and post the results to GitHub
```

## Getting Help

If you run into issues:

1. Check the main [README.md](README.md) for detailed docs
2. Review the example in `examples/sample-go-project/`
3. Open an issue on GitHub
4. Join the Anthropic Discord

## Success! 🎉

You now have an AI-powered Go code reviewer at your fingertips!

Try asking Claude to review your next PR and see how it:
- Catches linting issues
- Identifies formatting problems
- Runs tests automatically
- Provides improvement suggestions
- Posts reviews directly to GitHub

Happy reviewing! 🚀

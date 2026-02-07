#!/bin/bash

# GitHub PR Reviewer MCP Server - Installation Script

set -e

echo "======================================"
echo "GitHub PR Reviewer MCP Server Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.10 or higher is required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version detected"
echo ""

# Check Go installation
echo "Checking Go installation..."
if ! command -v go &> /dev/null; then
    echo "Warning: Go is not installed. You need Go 1.20+ to analyze Go projects."
    echo "Install Go from: https://go.dev/doc/install"
else
    go_version=$(go version | awk '{print $3}')
    echo "✓ $go_version detected"
fi
echo ""

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Check for golangci-lint
echo "Checking for golangci-lint..."
if ! command -v golangci-lint &> /dev/null; then
    echo "Warning: golangci-lint not found"
    echo "Installing golangci-lint..."
    if command -v go &> /dev/null; then
        go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
        export PATH=$PATH:$(go env GOPATH)/bin
        echo "✓ golangci-lint installed"
    else
        echo "Cannot install golangci-lint without Go. Please install Go first."
    fi
else
    echo "✓ golangci-lint found"
fi
echo ""

# GitHub token setup
echo "GitHub Token Setup"
echo "=================="
if [ -z "$GITHUB_TOKEN" ]; then
    echo "GITHUB_TOKEN environment variable is not set."
    echo ""
    echo "To set it up:"
    echo "1. Go to https://github.com/settings/tokens"
    echo "2. Create a new token with 'repo' and 'pull_requests:write' scopes"
    echo "3. Add to your shell profile (~/.bashrc or ~/.zshrc):"
    echo "   export GITHUB_TOKEN='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'"
    echo ""
    echo "Or copy .env.example to .env and fill in your token:"
    echo "   cp .env.example .env"
    echo "   # Edit .env with your token"
else
    echo "✓ GITHUB_TOKEN is set"
fi
echo ""

# Claude Desktop configuration
echo "Claude Desktop Configuration"
echo "============================"
echo ""
echo "To use this MCP server with Claude Desktop:"
echo ""
echo "1. Find your Claude Desktop config file:"
echo "   - macOS: ~/Library/Application\ Support/Claude/claude_desktop_config.json"
echo "   - Windows: %APPDATA%\\Claude\\claude_desktop_config.json"
echo "   - Linux: ~/.config/Claude/claude_desktop_config.json"
echo ""
echo "2. Add this configuration:"
echo ""
echo "{"
echo '  "mcpServers": {'
echo '    "github-pr-reviewer": {'
echo '      "command": "python",'
echo "      \"args\": [\"$(pwd)/github_pr_mcp.py\"],"
echo '      "env": {'
echo '        "GITHUB_TOKEN": "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"'
echo '      }'
echo '    }'
echo '  }'
echo "}"
echo ""
echo "3. Restart Claude Desktop"
echo ""

# Test installation
echo "Testing installation..."
python github_pr_mcp.py --help 2>&1 | grep -q "MCP" && echo "✓ MCP server loads successfully" || echo "✗ MCP server test failed"
echo ""

echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Set your GITHUB_TOKEN environment variable"
echo "2. Configure Claude Desktop (see above)"
echo "3. Restart Claude Desktop"
echo "4. Test with: 'Analyze the Go code in examples/sample-go-project'"
echo ""
echo "For more information, see README.md"

#!/bin/bash
# GitHub PR Reviewer MCP Server - Installation Script

set -e

echo "======================================"
echo "GitHub PR Reviewer MCP Server Setup"
echo "======================================"

# Check Python and Go
echo "Checking dependencies..."
python3 --version
go version

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Python dependencies installed"

# Install golangci-lint if missing
if ! command -v golangci-lint &> /dev/null; then
    echo "Installing golangci-lint..."
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
    # Add to path for the current session
    export PATH=$PATH:$(go env GOPATH)/bin
    echo "✓ golangci-lint installed"
fi

# FIXED: Verify the script without starting the server loop
echo "Verifying server module..."
python3 -c "import github_pr_mcp; print('✓ Server module is valid')"

echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo "Next Steps:"
echo "1. Run: export PATH=\$PATH:\$(go env GOPATH)/bin"
echo "2. Set GITHUB_TOKEN in your environment."
echo "3. Configure Claude Desktop with the absolute path to github_pr_mcp.py."
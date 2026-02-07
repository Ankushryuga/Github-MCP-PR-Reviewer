# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-07

### Added
- Initial release of GitHub PR Reviewer MCP Server
- Static code analysis support with golangci-lint, gofmt, and go vet
- Automated test execution with coverage reporting
- GitHub PR diff fetching and parsing
- Automated review comment posting to GitHub
- Comprehensive PR review workflow orchestration
- Five MCP tools:
  - `github_pr_analyze_code` - Static analysis
  - `github_pr_run_tests` - Test execution
  - `github_pr_get_diff` - PR diff fetching
  - `github_pr_post_review` - Review posting
  - `github_pr_comprehensive_review` - Full workflow
- Pydantic v2 input validation for all tools
- Markdown and JSON output format support
- Complete documentation:
  - README.md with full usage guide
  - QUICKSTART.md for 5-minute setup
  - ARCHITECTURE.md with system design
  - FAQ.md with common questions
  - CONTRIBUTING.md for developers
- Example Go project for testing
- Installation script (install.sh)
- Configuration examples
- Comprehensive test suite
- MIT License

### Security
- GitHub token stored only in environment variables
- Input validation via Pydantic models
- Command injection prevention
- Subprocess timeout protection

## [Unreleased]

### Planned Features
- Support for additional languages (JavaScript, Python, Rust)
- Result caching for improved performance
- Parallel file analysis
- Webhook integration for automatic reviews
- Streamable HTTP transport for multi-client support
- Review history tracking
- Custom linting rule configuration
- Integration with other code quality tools

---

## Version History

- **1.0.0** - Initial release (2025-02-07)

# System Architecture

This document describes the architecture of the GitHub PR Reviewer MCP Server.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
│                   (Claude.ai / Claude Desktop)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ MCP Protocol (stdio)
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              GitHub PR Reviewer MCP Server                  │
│                    (github_pr_mcp.py)                       │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │              Tool Registry                       │       │
│  ├─────────────────────────────────────────────────┤       │
│  │  • github_pr_analyze_code                       │       │
│  │  • github_pr_run_tests                          │       │
│  │  • github_pr_get_diff                           │       │
│  │  • github_pr_post_review                        │       │
│  │  • github_pr_comprehensive_review               │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │          Helper Functions Layer                  │       │
│  ├─────────────────────────────────────────────────┤       │
│  │  • _run_command() - Execute shell commands      │       │
│  │  • _format_markdown_analysis() - Format output  │       │
│  │  • _github_api_request() - API calls            │       │
│  │  • _parse_diff_for_go_files() - Parse diffs     │       │
│  └─────────────────────────────────────────────────┘       │
└──────────┬────────────┬────────────┬─────────────────────┘
           │            │            │
           │            │            │
┌──────────▼────┐  ┌───▼──────┐  ┌─▼──────────────┐
│  GitHub API   │  │  Local   │  │  Go Toolchain  │
│               │  │  Files   │  │                │
│ • Get PR      │  │          │  │ • golangci-lint│
│ • Get Diff    │  │ • Read   │  │ • gofmt        │
│ • Post Review │  │ • Write  │  │ • go vet       │
│               │  │          │  │ • go test      │
└───────────────┘  └──────────┘  └────────────────┘
```

## Component Details

### 1. MCP Server Core

**File:** `github_pr_mcp.py`

The main server implementation using FastMCP framework:

- **Initialization**: `mcp = FastMCP("github_pr_mcp")`
- **Transport**: stdio (standard input/output)
- **Protocol**: Model Context Protocol (MCP)

### 2. Input Validation Layer

**Technology:** Pydantic v2 BaseModel

Each tool has a dedicated input model:

```python
AnalyzeCodeInput      → github_pr_analyze_code
RunTestsInput         → github_pr_run_tests
GetPRDiffInput        → github_pr_get_diff
PostReviewCommentInput → github_pr_post_review
AnalyzePRInput        → github_pr_comprehensive_review
```

Benefits:

- Automatic type validation
- Field constraints (min/max length, ranges)
- Custom validators
- Clear error messages

### 3. Tool Layer

Five main tools exposed via MCP:

#### Tool 1: github_pr_analyze_code

- **Purpose**: Static code analysis
- **Calls**: golangci-lint, gofmt, go vet
- **Output**: Linting issues, formatting errors, vet warnings
- **Annotations**: readOnly, idempotent

#### Tool 2: github_pr_run_tests

- **Purpose**: Execute Go test suite
- **Calls**: go test with coverage
- **Output**: Test results, coverage percentages
- **Annotations**: readOnly, idempotent

#### Tool 3: github_pr_get_diff

- **Purpose**: Fetch PR changes from GitHub
- **Calls**: GitHub API
- **Output**: Diff content, changed files list
- **Annotations**: readOnly, idempotent, openWorld

#### Tool 4: github_pr_post_review

- **Purpose**: Submit review comments to PR
- **Calls**: GitHub API (POST)
- **Output**: Review confirmation, URL
- **Annotations**: NOT readOnly, NOT idempotent, openWorld

#### Tool 5: github_pr_comprehensive_review

- **Purpose**: Orchestrate full review workflow
- **Calls**: All other tools in sequence
- **Output**: Complete review analysis
- **Annotations**: NOT readOnly, NOT idempotent, openWorld

### 4. Helper Functions

Reusable utilities to avoid code duplication:

```python
_run_command()
├─ Execute subprocess with timeout
├─ Capture stdout/stderr
└─ Return structured result

_format_markdown_analysis()
├─ Convert analysis results to markdown
├─ Add emojis for status (✅/❌/⚠️)
└─ Format code blocks

_format_test_results_markdown()
├─ Format test output
├─ Include coverage data
└─ Highlight failures

_github_api_request()
├─ Authenticated HTTP requests
├─ Error handling
└─ JSON parsing

_parse_diff_for_go_files()
├─ Extract .go files from diff
└─ Return file list
```

### 5. External Dependencies

#### GitHub API

- **Endpoint**: `https://api.github.com`
- **Auth**: Bearer token (GITHUB_TOKEN)
- **Operations**: GET PRs, GET diffs, POST reviews
- **Rate Limit**: 5000/hour (authenticated)

#### Go Toolchain

- **golangci-lint**: Comprehensive linter (30+ linters)
- **gofmt**: Code formatting checker
- **go vet**: Suspicious construct analyzer
- **go test**: Test runner with coverage

#### Local Filesystem

- **Read**: Source files, test files
- **Write**: Coverage reports, temporary files
- **Paths**: Validated via Pydantic

## Data Flow

### Example: Comprehensive PR Review

```
1. User Request
   ↓
2. Claude calls github_pr_comprehensive_review
   ↓
3. Tool validates input (AnalyzePRInput)
   ↓
4. Fetch PR diff
   ├─ Call GitHub API
   ├─ Parse changed Go files
   └─ Store in review_results["stages"]["diff"]
   ↓
5. Analyze each changed file
   ├─ For each .go file:
   │  ├─ Run golangci-lint
   │  ├─ Run gofmt
   │  └─ Run go vet
   └─ Store in review_results["stages"]["analysis"]
   ↓
6. Run tests (if requested)
   ├─ Execute go test
   ├─ Generate coverage
   └─ Store in review_results["stages"]["tests"]
   ↓
7. Generate review summary
   ├─ Count issues found
   ├─ Format review body
   └─ Determine recommendation (APPROVE/REQUEST_CHANGES)
   ↓
8. Post to GitHub (if requested)
   ├─ Call GitHub API
   ├─ POST review comment
   └─ Return confirmation
   ↓
9. Return results to Claude
   └─ Format as JSON or Markdown
```

## Security Architecture

### Authentication

- GitHub token stored in environment variable
- Never logged or exposed in output
- Validated on first API call

### Input Validation

- All inputs validated via Pydantic
- Path traversal prevention
- Command injection prevention
- Size limits on inputs

### Execution Safety

- Subprocess timeouts (5 minutes)
- No shell=True in subprocess calls
- Working directory constraints
- Resource limits

### API Security

- HTTPS only
- Token-based authentication
- Rate limit awareness
- Error handling without token exposure

## Performance Characteristics

### Typical Operation Times

- Analyze single file: 2-5 seconds
- Run test suite: 5-30 seconds (depends on tests)
- Fetch PR diff: 1-2 seconds
- Post review: 1-2 seconds
- Comprehensive review: 30-90 seconds (depends on PR size)

### Bottlenecks

1. **golangci-lint**: Slowest operation (runs 30+ linters)
2. **Test execution**: Variable (depends on test suite)
3. **GitHub API**: Rate limits (5000/hour)

### Optimization Strategies

- Parallel file analysis (future improvement)
- Caching of lint results
- Selective linting (only changed files)
- Incremental test runs

## Scalability Considerations

### Current Limitations

- Single PR at a time (stdio transport)
- No persistent state between calls
- Rate limited by GitHub API

### Future Enhancements

- Switch to streamable HTTP for multiple clients
- Add result caching
- Support for batch PR reviews
- Webhook integration for automatic reviews

## Error Handling

### Strategy

```python
Try
├─ Attempt operation
├─ Catch specific exceptions
│  ├─ httpx.HTTPStatusError → API errors
│  ├─ subprocess.TimeoutExpired → Command timeouts
│  └─ Exception → Unexpected errors
└─ Return structured error
   ├─ Error type
   ├─ Message
   └─ Success: false
```

### Error Propagation

- Tool-level errors return structured JSON
- Don't expose internal details
- Provide actionable error messages
- Log errors server-side (stderr)

## Configuration Management

### Environment Variables

```bash
GITHUB_TOKEN=ghp_...   # Required for GitHub API
```

### MCP Configuration

```json
{
  "mcpServers": {
    "github-pr-reviewer": {
      "command": "python",
      "args": ["path/to/github_pr_mcp.py"],
      "env": {
        "GITHUB_TOKEN": "..."
      }
    }
  }
}
```

### Tool Configuration

- Hardcoded in tool implementations
- Can be extended to read from config files
- Go tool paths resolved from PATH

## Future Architecture Improvements

1. **Caching Layer**
   - Cache lint results for unchanged files
   - Cache test results for unchanged code

2. **Queue System**
   - Handle multiple PRs concurrently
   - Priority queue for reviews

3. **Webhook Integration**
   - Automatic review on PR creation/update
   - No manual triggering needed

4. **Database Layer**
   - Store review history
   - Track metrics over time
   - Compare PRs

5. **Plugin Architecture**
   - Support languages beyond Go
   - Custom linting rules
   - Third-party integrations

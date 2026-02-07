#!/usr/bin/env python3
"""
GitHub PR Review MCP Server

This MCP server provides tools for automated Go code review, including:
- Static analysis with golangci-lint
- Code formatting checks with gofmt
- Running Go tests
- GitHub PR integration for posting review comments
- Code quality analysis and suggestions
"""

import os
import json
import subprocess
import asyncio
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
import httpx

# Initialize MCP server
mcp = FastMCP("github_pr_mcp")

# Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_API_BASE = "https://api.github.com"


# ============================================================================
# Pydantic Models for Input Validation
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class AnalyzeCodeInput(BaseModel):
    """Input for analyzing Go code files."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    file_path: str = Field(
        ...,
        description="Path to Go file or directory to analyze",
        min_length=1
    )
    analysis_type: Literal["lint", "fmt", "vet", "all"] = Field(
        default="all",
        description="Type of analysis: 'lint' (golangci-lint), 'fmt' (gofmt), 'vet' (go vet), or 'all'"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class RunTestsInput(BaseModel):
    """Input for running Go tests."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    package_path: str = Field(
        default="./...",
        description="Go package path to test (e.g., './...', './pkg/...')"
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose test output"
    )
    coverage: bool = Field(
        default=True,
        description="Generate code coverage report"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class GetPRDiffInput(BaseModel):
    """Input for fetching GitHub PR diff."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1)
    repo: str = Field(..., description="Repository name", min_length=1)
    pr_number: int = Field(..., description="Pull request number", ge=1)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class PostReviewCommentInput(BaseModel):
    """Input for posting review comments to GitHub PR."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1)
    repo: str = Field(..., description="Repository name", min_length=1)
    pr_number: int = Field(..., description="Pull request number", ge=1)
    body: str = Field(..., description="Review comment body", min_length=1)
    event: Literal["COMMENT", "APPROVE", "REQUEST_CHANGES"] = Field(
        default="COMMENT",
        description="Review event type"
    )
    commit_id: Optional[str] = Field(
        default=None,
        description="Specific commit ID to review (latest if not provided)"
    )


class AnalyzePRInput(BaseModel):
    """Input for comprehensive PR analysis."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    owner: str = Field(..., description="Repository owner", min_length=1)
    repo: str = Field(..., description="Repository name", min_length=1)
    pr_number: int = Field(..., description="Pull request number", ge=1)
    local_path: Optional[str] = Field(
        default=None,
        description="Local path to cloned repository (if analyzing locally)"
    )
    run_tests: bool = Field(
        default=True,
        description="Run automated tests"
    )
    post_comments: bool = Field(
        default=False,
        description="Automatically post review comments to GitHub"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _run_command(cmd: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a shell command and return results.
    
    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        
    Returns:
        Dict with stdout, stderr, returncode, and success flag
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Command timed out after 5 minutes",
            "returncode": -1,
            "success": False
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "success": False
        }


def _format_markdown_analysis(results: Dict[str, Any]) -> str:
    """Format analysis results as markdown."""
    sections = []
    
    if "lint" in results:
        sections.append("## Linting Results (golangci-lint)\n")
        if results["lint"]["success"]:
            sections.append("✅ No linting issues found!\n")
        else:
            sections.append(f"❌ Linting issues detected:\n\n```\n{results['lint']['stdout']}\n```\n")
    
    if "fmt" in results:
        sections.append("## Formatting Check (gofmt)\n")
        if results["fmt"]["success"] and not results["fmt"]["stdout"]:
            sections.append("✅ Code is properly formatted!\n")
        else:
            sections.append(f"⚠️ Formatting issues found:\n\n```\n{results['fmt']['stdout']}\n```\n")
    
    if "vet" in results:
        sections.append("## Go Vet Analysis\n")
        if results["vet"]["success"]:
            sections.append("✅ No issues found by go vet!\n")
        else:
            sections.append(f"❌ Issues detected:\n\n```\n{results['vet']['stderr']}\n```\n")
    
    return "\n".join(sections)


def _format_test_results_markdown(result: Dict[str, Any], coverage: bool) -> str:
    """Format test results as markdown."""
    sections = ["# Test Results\n"]
    
    if result["success"]:
        sections.append("✅ **All tests passed!**\n")
    else:
        sections.append("❌ **Tests failed!**\n")
    
    sections.append("## Output\n")
    sections.append(f"```\n{result['stdout']}\n```\n")
    
    if result["stderr"]:
        sections.append("## Errors\n")
        sections.append(f"```\n{result['stderr']}\n```\n")
    
    if coverage and "coverage" in result:
        sections.append(f"\n## Coverage\n{result['coverage']}\n")
    
    return "\n".join(sections)


async def _github_api_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Make authenticated GitHub API request.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        data: Request body data
        
    Returns:
        Response JSON data
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    url = f"{GITHUB_API_BASE}{endpoint}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers)
        elif method.upper() == "POST":
            response = await client.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()


def _parse_diff_for_go_files(diff_text: str) -> List[str]:
    """Extract list of changed Go files from git diff."""
    go_files = []
    for line in diff_text.split('\n'):
        if line.startswith('+++') and line.endswith('.go'):
            # Extract filename from "+++ b/path/to/file.go"
            file_path = line.split(' ')[1][2:]  # Remove "b/" prefix
            go_files.append(file_path)
    return go_files


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool(
    name="github_pr_analyze_code",
    annotations={
        "title": "Analyze Go Code Quality",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def analyze_code(params: AnalyzeCodeInput) -> str:
    """
    Analyze Go code for quality issues using static analysis tools.
    
    Runs golangci-lint, gofmt, and/or go vet on the specified file or directory.
    Returns detailed analysis results including any detected issues.
    
    Args:
        params (AnalyzeCodeInput): Analysis parameters containing:
            - file_path (str): Path to analyze
            - analysis_type (str): Type of analysis to run
            - response_format (str): Output format
            
    Returns:
        str: Analysis results in requested format
    """
    file_path = Path(params.file_path)
    
    if not file_path.exists():
        return json.dumps({
            "error": f"Path not found: {params.file_path}",
            "success": False
        })
    
    results = {}
    
    # Run linting
    if params.analysis_type in ["lint", "all"]:
        lint_result = _run_command(
            ["golangci-lint", "run", "--out-format", "colored-line-number", str(file_path)],
            cwd=str(file_path.parent) if file_path.is_file() else str(file_path)
        )
        results["lint"] = lint_result
    
    # Run formatting check
    if params.analysis_type in ["fmt", "all"]:
        fmt_result = _run_command(
            ["gofmt", "-l", str(file_path)]
        )
        results["fmt"] = fmt_result
    
    # Run go vet
    if params.analysis_type in ["vet", "all"]:
        vet_result = _run_command(
            ["go", "vet", str(file_path)],
            cwd=str(file_path.parent) if file_path.is_file() else str(file_path)
        )
        results["vet"] = vet_result
    
    if params.response_format == ResponseFormat.JSON:
        return json.dumps(results, indent=2)
    else:
        return _format_markdown_analysis(results)


@mcp.tool(
    name="github_pr_run_tests",
    annotations={
        "title": "Run Go Tests",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def run_tests(params: RunTestsInput) -> str:
    """
    Run Go tests with optional coverage analysis.
    
    Executes go test on specified packages and generates coverage reports
    if requested. Useful for validating PR changes don't break tests.
    
    Args:
        params (RunTestsInput): Test parameters containing:
            - package_path (str): Go package path to test
            - verbose (bool): Enable verbose output
            - coverage (bool): Generate coverage report
            - response_format (str): Output format
            
    Returns:
        str: Test results with optional coverage data
    """
    cmd = ["go", "test"]
    
    if params.verbose:
        cmd.append("-v")
    
    if params.coverage:
        cmd.extend(["-coverprofile=coverage.out", "-covermode=atomic"])
    
    cmd.append(params.package_path)
    
    test_result = _run_command(cmd)
    
    # Get coverage summary if enabled
    if params.coverage and test_result["success"]:
        coverage_result = _run_command(["go", "tool", "cover", "-func=coverage.out"])
        test_result["coverage"] = coverage_result["stdout"]
    
    if params.response_format == ResponseFormat.JSON:
        return json.dumps(test_result, indent=2)
    else:
        return _format_test_results_markdown(test_result, params.coverage)


@mcp.tool(
    name="github_pr_get_diff",
    annotations={
        "title": "Get GitHub PR Diff",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_pr_diff(params: GetPRDiffInput) -> str:
    """
    Fetch the diff for a GitHub pull request.
    
    Retrieves the complete diff showing all changes in the PR, which can
    be used to identify which files to analyze.
    
    Args:
        params (GetPRDiffInput): PR information containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - pr_number (int): Pull request number
            - response_format (str): Output format
            
    Returns:
        str: PR diff content and metadata
    """
    try:
        endpoint = f"/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}"
        
        # Get PR data
        pr_data = await _github_api_request("GET", endpoint)
        
        # Fetch diff
        async with httpx.AsyncClient() as client:
            diff_response = await client.get(
                pr_data["diff_url"],
                headers={"Accept": "application/vnd.github.v3.diff"}
            )
            diff_response.raise_for_status()
            diff_content = diff_response.text
        
        # Parse changed Go files
        go_files = _parse_diff_for_go_files(diff_content)
        
        result = {
            "pr_number": params.pr_number,
            "title": pr_data["title"],
            "state": pr_data["state"],
            "changed_files": pr_data["changed_files"],
            "additions": pr_data["additions"],
            "deletions": pr_data["deletions"],
            "go_files_changed": go_files,
            "diff": diff_content
        }
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)
        else:
            markdown = f"""# PR #{params.pr_number}: {result['title']}

**Status:** {result['state']}
**Files Changed:** {result['changed_files']}
**Additions:** +{result['additions']} / **Deletions:** -{result['deletions']}

## Go Files Changed
{chr(10).join(f'- {f}' for f in go_files) if go_files else 'No Go files changed'}

## Diff
```diff
{diff_content[:5000]}{'...' if len(diff_content) > 5000 else ''}
```
"""
            return markdown
            
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "error": f"GitHub API error: {e.response.status_code}",
            "message": str(e),
            "success": False
        })
    except Exception as e:
        return json.dumps({
            "error": f"Unexpected error: {type(e).__name__}",
            "message": str(e),
            "success": False
        })


@mcp.tool(
    name="github_pr_post_review",
    annotations={
        "title": "Post GitHub PR Review",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def post_review_comment(params: PostReviewCommentInput) -> str:
    """
    Post a review comment to a GitHub pull request.
    
    Submits automated review feedback to the PR, including analysis results,
    test outcomes, and improvement suggestions.
    
    Args:
        params (PostReviewCommentInput): Review data containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - pr_number (int): Pull request number
            - body (str): Review comment text
            - event (str): Review type (COMMENT, APPROVE, REQUEST_CHANGES)
            - commit_id (Optional[str]): Specific commit to review
            
    Returns:
        str: Confirmation of posted review
    """
    try:
        endpoint = f"/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}/reviews"
        
        review_data = {
            "body": params.body,
            "event": params.event
        }
        
        if params.commit_id:
            review_data["commit_id"] = params.commit_id
        
        result = await _github_api_request("POST", endpoint, review_data)
        
        return json.dumps({
            "success": True,
            "review_id": result["id"],
            "state": result["state"],
            "html_url": result["html_url"],
            "message": "Review posted successfully"
        }, indent=2)
        
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "error": f"GitHub API error: {e.response.status_code}",
            "message": str(e),
            "success": False
        })
    except Exception as e:
        return json.dumps({
            "error": f"Unexpected error: {type(e).__name__}",
            "message": str(e),
            "success": False
        })


@mcp.tool(
    name="github_pr_comprehensive_review",
    annotations={
        "title": "Comprehensive PR Review",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def analyze_pr(params: AnalyzePRInput) -> str:
    """
    Perform comprehensive automated review of a GitHub pull request.
    
    This tool orchestrates a complete PR review workflow:
    1. Fetches PR diff and metadata
    2. Identifies changed Go files
    3. Runs static analysis (lint, fmt, vet)
    4. Executes tests with coverage
    5. Generates review summary
    6. Optionally posts review to GitHub
    
    Args:
        params (AnalyzePRInput): Review configuration containing:
            - owner (str): Repository owner
            - repo (str): Repository name
            - pr_number (int): Pull request number
            - local_path (Optional[str]): Local repo path for analysis
            - run_tests (bool): Whether to run tests
            - post_comments (bool): Auto-post review to GitHub
            - response_format (str): Output format
            
    Returns:
        str: Complete review analysis with recommendations
    """
    review_results = {
        "pr_number": params.pr_number,
        "timestamp": asyncio.get_event_loop().time(),
        "stages": {}
    }
    
    try:
        # Stage 1: Get PR diff
        diff_params = GetPRDiffInput(
            owner=params.owner,
            repo=params.repo,
            pr_number=params.pr_number,
            response_format=ResponseFormat.JSON
        )
        diff_result = json.loads(await get_pr_diff(diff_params))
        review_results["stages"]["diff"] = diff_result
        
        if "error" in diff_result:
            return json.dumps(review_results, indent=2)
        
        go_files = diff_result.get("go_files_changed", [])
        
        # Stage 2: Analyze changed Go files
        if params.local_path and go_files:
            analysis_results = []
            for go_file in go_files:
                file_path = Path(params.local_path) / go_file
                if file_path.exists():
                    analyze_params = AnalyzeCodeInput(
                        file_path=str(file_path),
                        analysis_type="all",
                        response_format=ResponseFormat.JSON
                    )
                    result = json.loads(await analyze_code(analyze_params))
                    analysis_results.append({
                        "file": go_file,
                        "analysis": result
                    })
            review_results["stages"]["analysis"] = analysis_results
        
        # Stage 3: Run tests
        if params.run_tests and params.local_path:
            test_params = RunTestsInput(
                package_path="./...",
                verbose=True,
                coverage=True,
                response_format=ResponseFormat.JSON
            )
            # Change to local repo directory for tests
            test_result = _run_command(
                ["go", "test", "-v", "-coverprofile=coverage.out", "-covermode=atomic", "./..."],
                cwd=params.local_path
            )
            review_results["stages"]["tests"] = test_result
        
        # Stage 4: Generate review summary
        issues_found = []
        
        # Check analysis results
        if "analysis" in review_results["stages"]:
            for file_analysis in review_results["stages"]["analysis"]:
                for check_type, check_result in file_analysis["analysis"].items():
                    if not check_result.get("success", True):
                        issues_found.append({
                            "file": file_analysis["file"],
                            "type": check_type,
                            "details": check_result.get("stdout", "") or check_result.get("stderr", "")
                        })
        
        # Check test results
        if "tests" in review_results["stages"]:
            if not review_results["stages"]["tests"].get("success", True):
                issues_found.append({
                    "file": "tests",
                    "type": "test_failure",
                    "details": review_results["stages"]["tests"].get("stderr", "")
                })
        
        review_results["issues_found"] = len(issues_found)
        review_results["issues"] = issues_found
        
        # Generate review body
        if issues_found:
            review_body = f"## 🤖 Automated Code Review\n\n"
            review_body += f"Found {len(issues_found)} issue(s) in this PR:\n\n"
            for i, issue in enumerate(issues_found, 1):
                review_body += f"### {i}. {issue['type']} in `{issue['file']}`\n"
                review_body += f"```\n{issue['details'][:500]}\n```\n\n"
            review_body += "\n**Recommendations:**\n"
            review_body += "- Fix linting issues before merging\n"
            review_body += "- Ensure all tests pass\n"
            review_body += "- Follow Go formatting standards\n"
            recommendation = "REQUEST_CHANGES"
        else:
            review_body = "## 🤖 Automated Code Review\n\n✅ All checks passed! Code looks good.\n\n"
            review_body += "- No linting issues\n"
            review_body += "- Tests passing\n"
            review_body += "- Code properly formatted\n"
            recommendation = "APPROVE"
        
        review_results["review_body"] = review_body
        review_results["recommendation"] = recommendation
        
        # Stage 5: Post review if requested
        if params.post_comments:
            post_params = PostReviewCommentInput(
                owner=params.owner,
                repo=params.repo,
                pr_number=params.pr_number,
                body=review_body,
                event=recommendation
            )
            post_result = json.loads(await post_review_comment(post_params))
            review_results["stages"]["posted_review"] = post_result
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(review_results, indent=2)
        else:
            return review_body
            
    except Exception as e:
        review_results["error"] = str(e)
        return json.dumps(review_results, indent=2)


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run with stdio transport (default for local tools)
    mcp.run()

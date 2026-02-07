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
from pydantic import BaseModel, Field, ConfigDict
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
    """Execute a shell command and return results."""
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
    
    FIXED: Added follow_redirects=True to handle API redirects (302) correctly.
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    url = f"{GITHUB_API_BASE}{endpoint}"
    
    # Enable follow_redirects to handle GitHub API redirection behaviors
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
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
            file_path = line.split(' ')[1][2:]  # Remove "b/" prefix
            go_files.append(file_path)
    return go_files


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool(name="github_pr_analyze_code")
async def analyze_code(params: AnalyzeCodeInput) -> str:
    """Analyze Go code for quality issues using static analysis tools."""
    file_path = Path(params.file_path)
    
    if not file_path.exists():
        return json.dumps({"error": f"Path not found: {params.file_path}", "success": False})
    
    results = {}
    
    if params.analysis_type in ["lint", "all"]:
        results["lint"] = _run_command(
            ["golangci-lint", "run", "--out-format", "colored-line-number", str(file_path)],
            cwd=str(file_path.parent) if file_path.is_file() else str(file_path)
        )
    
    if params.analysis_type in ["fmt", "all"]:
        results["fmt"] = _run_command(["gofmt", "-l", str(file_path)])
    
    if params.analysis_type in ["vet", "all"]:
        results["vet"] = _run_command(
            ["go", "vet", str(file_path)],
            cwd=str(file_path.parent) if file_path.is_file() else str(file_path)
        )
    
    if params.response_format == ResponseFormat.JSON:
        return json.dumps(results, indent=2)
    return _format_markdown_analysis(results)


@mcp.tool(name="github_pr_run_tests")
async def run_tests(params: RunTestsInput) -> str:
    """Run Go tests with optional coverage analysis."""
    cmd = ["go", "test"]
    if params.verbose:
        cmd.append("-v")
    if params.coverage:
        cmd.extend(["-coverprofile=coverage.out", "-covermode=atomic"])
    cmd.append(params.package_path)
    
    test_result = _run_command(cmd)
    
    if params.coverage and test_result["success"]:
        coverage_result = _run_command(["go", "tool", "cover", "-func=coverage.out"])
        test_result["coverage"] = coverage_result["stdout"]
    
    if params.response_format == ResponseFormat.JSON:
        return json.dumps(test_result, indent=2)
    return _format_test_results_markdown(test_result, params.coverage)


@mcp.tool(name="github_pr_get_diff")
async def get_pr_diff(params: GetPRDiffInput) -> str:
    """Fetch the diff for a GitHub pull request."""
    try:
        endpoint = f"/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}"
        pr_data = await _github_api_request("GET", endpoint)
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            diff_response = await client.get(
                pr_data["diff_url"],
                headers={"Accept": "application/vnd.github.v3.diff"}
            )
            diff_response.raise_for_status()
            diff_content = diff_response.text
        
        go_files = _parse_diff_for_go_files(diff_content)
        result = {
            "pr_number": params.pr_number,
            "title": pr_data["title"],
            "state": pr_data["state"],
            "go_files_changed": go_files,
            "diff": diff_content
        }
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)
            
        markdown = f"# PR #{params.pr_number}: {result['title']}\n"
        markdown += f"**Status:** {result['state']}\n\n"
        markdown += "## Go Files Changed\n"
        markdown += "\n".join(f"- {f}" for f in go_files) if go_files else "No Go files changed"
        return markdown
            
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool(name="github_pr_post_review")
async def post_review_comment(params: PostReviewCommentInput) -> str:
    """Post a review comment to a GitHub pull request."""
    try:
        endpoint = f"/repos/{params.owner}/{params.repo}/pulls/{params.pr_number}/reviews"
        review_data = {"body": params.body, "event": params.event}
        if params.commit_id:
            review_data["commit_id"] = params.commit_id
        
        result = await _github_api_request("POST", endpoint, review_data)
        return json.dumps({"success": True, "html_url": result["html_url"]}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool(name="github_pr_comprehensive_review")
async def analyze_pr(params: AnalyzePRInput) -> str:
    """Perform comprehensive automated review of a GitHub pull request."""
    try:
        # Step 1: Get Diff
        diff_params = GetPRDiffInput(
            owner=params.owner, repo=params.repo, 
            pr_number=params.pr_number, response_format=ResponseFormat.JSON
        )
        diff_res_str = await get_pr_diff(diff_params)
        diff_result = json.loads(diff_res_str)
        
        if "error" in diff_result:
            return f"Error fetching diff: {diff_result['error']}"

        go_files = diff_result.get("go_files_changed", [])
        
        # Step 2: Analysis & Tests
        summary = f"## 🤖 Automated Review for PR #{params.pr_number}\n\n"
        
        if params.local_path and go_files:
            summary += "### 🔍 Static Analysis\n"
            for f in go_files:
                f_path = Path(params.local_path) / f
                if f_path.exists():
                    analysis = await analyze_code(AnalyzeCodeInput(file_path=str(f_path)))
                    summary += f"#### File: `{f}`\n{analysis}\n"
            
            if params.run_tests:
                summary += "### 🧪 Test Results\n"
                test_res = await run_tests(RunTestsInput(package_path="./..."))
                summary += test_res

        if params.post_comments:
            await post_review_comment(PostReviewCommentInput(
                owner=params.owner, repo=params.repo, 
                pr_number=params.pr_number, body=summary
            ))
            
        return summary
    except Exception as e:
        return f"Comprehensive review failed: {str(e)}"


if __name__ == "__main__":
    mcp.run()
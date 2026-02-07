"""
Tests for GitHub PR Reviewer MCP Server

Run with: python -m pytest test_github_pr_mcp.py -v
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import subprocess

# Import the MCP server
import sys
sys.path.insert(0, str(Path(__file__).parent))
from github_pr_mcp import (
    _run_command,
    _format_markdown_analysis,
    _parse_diff_for_go_files,
    AnalyzeCodeInput,
    RunTestsInput,
    GetPRDiffInput,
    ResponseFormat
)


class TestRunCommand:
    """Test the _run_command helper function."""
    
    def test_successful_command(self):
        """Test executing a successful command."""
        result = _run_command(["echo", "hello"])
        assert result["success"] is True
        assert result["returncode"] == 0
        assert "hello" in result["stdout"]
    
    def test_failed_command(self):
        """Test executing a command that fails."""
        result = _run_command(["false"])
        assert result["success"] is False
        assert result["returncode"] != 0
    
    def test_command_timeout(self):
        """Test command timeout handling."""
        # This would timeout in real execution
        # For unit tests, we'll mock the timeout
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 1)):
            result = _run_command(["sleep", "1000"])
            assert result["success"] is False
            assert "timed out" in result["stderr"]


class TestFormatMarkdownAnalysis:
    """Test markdown formatting function."""
    
    def test_format_successful_analysis(self):
        """Test formatting successful analysis results."""
        results = {
            "lint": {"success": True, "stdout": ""},
            "fmt": {"success": True, "stdout": ""},
            "vet": {"success": True, "stdout": ""}
        }
        
        markdown = _format_markdown_analysis(results)
        assert "✅" in markdown
        assert "No linting issues found" in markdown
        assert "properly formatted" in markdown
    
    def test_format_failed_analysis(self):
        """Test formatting failed analysis results."""
        results = {
            "lint": {"success": False, "stdout": "error: unused variable"},
            "fmt": {"success": True, "stdout": "main.go"},
        }
        
        markdown = _format_markdown_analysis(results)
        assert "❌" in markdown or "⚠️" in markdown
        assert "unused variable" in markdown


class TestParseDiffForGoFiles:
    """Test diff parsing function."""
    
    def test_parse_simple_diff(self):
        """Test parsing a simple diff with Go files."""
        diff = """
diff --git a/main.go b/main.go
index abc123..def456 100644
--- a/main.go
+++ b/main.go
@@ -1,5 +1,5 @@
 package main
"""
        
        go_files = _parse_diff_for_go_files(diff)
        assert "main.go" in go_files
    
    def test_parse_multiple_files(self):
        """Test parsing diff with multiple Go files."""
        diff = """
diff --git a/main.go b/main.go
--- a/main.go
+++ b/main.go
diff --git a/utils.go b/utils.go
--- a/utils.go
+++ b/utils.go
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
"""
        
        go_files = _parse_diff_for_go_files(diff)
        assert "main.go" in go_files
        assert "utils.go" in go_files
        assert "README.md" not in go_files
    
    def test_parse_nested_paths(self):
        """Test parsing diff with nested file paths."""
        diff = """
diff --git a/pkg/handlers/api.go b/pkg/handlers/api.go
--- a/pkg/handlers/api.go
+++ b/pkg/handlers/api.go
"""
        
        go_files = _parse_diff_for_go_files(diff)
        assert "pkg/handlers/api.go" in go_files


class TestPydanticModels:
    """Test Pydantic input models."""
    
    def test_analyze_code_input_valid(self):
        """Test valid AnalyzeCodeInput."""
        data = {
            "file_path": "/path/to/file.go",
            "analysis_type": "lint",
            "response_format": "markdown"
        }
        model = AnalyzeCodeInput(**data)
        assert model.file_path == "/path/to/file.go"
        assert model.analysis_type == "lint"
    
    def test_analyze_code_input_defaults(self):
        """Test AnalyzeCodeInput with defaults."""
        data = {"file_path": "/path/to/file.go"}
        model = AnalyzeCodeInput(**data)
        assert model.analysis_type == "all"
        assert model.response_format == ResponseFormat.MARKDOWN
    
    def test_analyze_code_input_invalid(self):
        """Test AnalyzeCodeInput with invalid data."""
        with pytest.raises(Exception):  # Pydantic validation error
            AnalyzeCodeInput(file_path="")  # Empty string should fail
    
    def test_run_tests_input_valid(self):
        """Test valid RunTestsInput."""
        data = {
            "package_path": "./...",
            "verbose": True,
            "coverage": True
        }
        model = RunTestsInput(**data)
        assert model.package_path == "./..."
        assert model.verbose is True
    
    def test_get_pr_diff_input_valid(self):
        """Test valid GetPRDiffInput."""
        data = {
            "owner": "testuser",
            "repo": "testrepo",
            "pr_number": 42
        }
        model = GetPRDiffInput(**data)
        assert model.owner == "testuser"
        assert model.repo == "testrepo"
        assert model.pr_number == 42
    
    def test_get_pr_diff_input_invalid_pr_number(self):
        """Test GetPRDiffInput with invalid PR number."""
        with pytest.raises(Exception):
            GetPRDiffInput(
                owner="test",
                repo="test",
                pr_number=0  # Must be >= 1
            )


class TestIntegration:
    """Integration tests (require actual Go installation)."""
    
    @pytest.mark.skipif(
        _run_command(["go", "version"])["returncode"] != 0,
        reason="Go not installed"
    )
    def test_go_fmt_check(self):
        """Test that gofmt works on example project."""
        example_dir = Path(__file__).parent / "examples" / "sample-go-project"
        if example_dir.exists():
            result = _run_command(["gofmt", "-l", str(example_dir)])
            # Should succeed even if files need formatting
            assert result["returncode"] == 0
    
    @pytest.mark.skipif(
        _run_command(["go", "version"])["returncode"] != 0,
        reason="Go not installed"
    )
    def test_go_vet_check(self):
        """Test that go vet works on example project."""
        example_dir = Path(__file__).parent / "examples" / "sample-go-project"
        if example_dir.exists():
            result = _run_command(["go", "vet", "./..."], cwd=str(example_dir))
            # May or may not succeed depending on code, but should run
            assert isinstance(result["returncode"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

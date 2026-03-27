"""Unit tests for src/tools.py."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from src.tools import read_file, read_file_signatures, write_file, run_grep, run_tests


def test_read_file_exists(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text("print('hello')")
    result = read_file(str(f))
    assert result == "print('hello')"


def test_read_file_missing():
    result = read_file("/nonexistent/path/file.py")
    assert "[ERROR]" in result
    assert "not found" in result


def test_read_file_signatures(tmp_path):
    f = tmp_path / "mod.py"
    f.write_text(
        "import os\n\nclass Foo:\n    x = 1\n\ndef bar(a, b):\n    return a + b\n"
    )
    result = read_file_signatures(str(f))
    assert "class Foo:" in result
    assert "def bar(a, b):" in result
    assert "import os" not in result
    assert "return a + b" not in result


def test_write_file(tmp_path):
    target = tmp_path / "output" / "new_file.py"
    result = write_file(str(target), "x = 1")
    assert "[OK]" in result
    assert target.read_text() == "x = 1"


def test_run_grep_found(tmp_path):
    f = tmp_path / "code.py"
    f.write_text("def toggle_done(self):\n    self.done = True\n")
    result = run_grep("toggle_done", str(tmp_path))
    assert "toggle_done" in result


def test_run_grep_no_match(tmp_path):
    f = tmp_path / "code.py"
    f.write_text("x = 1\n")
    result = run_grep("nonexistent_function", str(tmp_path))
    assert "(no matches)" in result or result == "(no matches)"


def test_run_tests_returns_dict():
    """run_tests should always return a dict with required keys."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="2 passed\n", stderr=""
        )
        result = run_tests("target_app/tests")
    assert "success" in result
    assert "summary" in result
    assert "output" in result
    assert "returncode" in result
    assert result["success"] is True


def test_run_tests_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1, stdout="1 failed\n", stderr=""
        )
        result = run_tests("target_app/tests")
    assert result["success"] is False
    assert result["returncode"] == 1

#!/usr/bin/env python3
"""
Project Title: Git Setup Tests

Pytest smoke tests for git_setup.py functionality.

Author: Kris Armstrong
"""
__version__ = "1.0.0"

import os
import pytest
import subprocess
from pathlib import Path
import git_setup

@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for testing.

    Args:
        tmp_path: Pytest-provided temporary path.

    Returns:
        Path to temporary directory.
    """
    return tmp_path

def test_git_init(temp_dir: Path) -> None:
    """Test Git repository initialization."""
    git_setup.run_cmd(['git', 'init'], temp_dir)
    assert (temp_dir / '.git').is_dir()

def test_create_gitignore(temp_dir: Path) -> None:
    """Test .gitignore creation."""
    git_setup.create_file(temp_dir / '.gitignore', "# Test\n")
    assert (temp_dir / '.gitignore').exists()
    assert (temp_dir / '.gitignore').read_text() == "# Test\n"

def test_keyboard_interrupt(temp_dir: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test KeyboardInterrupt handling.

    Args:
        temp_dir: Temporary directory for testing.
        caplog: Pytest fixture to capture log output.
    """
    with pytest.raises(SystemExit) as exc:
        git_setup.setup_logging(False)
        raise KeyboardInterrupt
    assert exc.value.code == 0
    assert "Cancelled by user" in caplog.text

def test_version_bumper_generation(temp_dir: Path) -> None:
    """Test version_bumper.py generation."""
    git_setup.create_file(temp_dir / 'version_bumper.py', git_setup.VERSION_BUMPER_TEMPLATE)
    assert (temp_dir / 'version_bumper.py').exists()
    result = subprocess.run(['python', 'version_bumper.py', '--help'], cwd=temp_dir, capture_output=True, text=True)
    assert result.returncode == 0
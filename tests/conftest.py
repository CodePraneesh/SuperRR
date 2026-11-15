"""
tests/conftest.py
Central pytest configuration, fixtures, and data-dependency skip helpers
for SupeRR Intelligence test suite.
"""
from pathlib import Path
import unittest
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def require_data_file(relative_path: str, generator_cmd: str) -> Path:
    """
    Check if a required data file exists.
    If absent, raises unittest.SkipTest with the exact standard reason format:
    'Requires <path>; run `<command that generates it>`'
    Compatible with both pytest and standard unittest TestRunner.
    """
    full_path = REPO_ROOT / relative_path
    if not full_path.exists():
        raise unittest.SkipTest(f"Requires {relative_path}; run `{generator_cmd}`")
    return full_path


def require_data_files(files_with_cmds: list) -> list:
    """
    Check multiple required files. If any is missing, skips with standard reason.
    """
    paths = []
    for rel_path, cmd in files_with_cmds:
        paths.append(require_data_file(rel_path, cmd))
    return paths


@pytest.fixture
def require_file():
    """Pytest fixture returning the require_data_file helper."""
    return require_data_file

"""
tests/conftest.py
Central pytest configuration, fixtures, and data-dependency skip helpers
for SupeRR Intelligence test suite.
"""
from pathlib import Path
import unittest
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


CANONICAL_GENERATORS = {
    "output/processed/matches_enriched.csv": "python supeRR_phase1_pipeline.py --zip 6af458274c1e8_data_pack.zip --out output",
    "output/processed/deliveries_enriched.csv": "python supeRR_phase1_pipeline.py --zip 6af458274c1e8_data_pack.zip --out output",
    "output/phase2/pressure_scored_deliveries.csv": "python ml/phase2/pressure_validation.py",
    "output/phase2/pressure_distribution.csv": "python ml/phase2/pressure_validation.py",
    "output/phase2/win_probability_predictions.csv": "python ml/phase2/pressure_validation.py",
    "output/phase2/batter_delivery_expectations.csv": "python ml/phase2/model_evaluation.py",
    "output/phase2/bowler_delivery_expectations.csv": "python ml/phase2/model_evaluation.py",
    "output/phase2/batter_performance_summary.csv": "python ml/phase2/model_evaluation.py",
    "output/phase2/bowler_performance_summary.csv": "python ml/phase2/model_evaluation.py",
    "output/phase2/delivery_wpa.csv": "python ml/phase2/wpa_evaluation.py",
    "output/phase2/player_wpa_summary.csv": "python ml/phase2/wpa_evaluation.py",
}

def require_data_file(relative_path: str, generator_cmd: str = None) -> Path:
    """
    Check if a required data file exists.
    If absent, raises unittest.SkipTest with the exact standard reason format:
    'Requires <path>; run `<command that generates it>`'
    Compatible with both pytest and standard unittest TestRunner.
    """
    cmd = CANONICAL_GENERATORS.get(relative_path, generator_cmd or "reproduce pipeline")
    full_path = REPO_ROOT / relative_path
    if not full_path.exists():
        raise unittest.SkipTest(f"Requires {relative_path}; run `{cmd}`")
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

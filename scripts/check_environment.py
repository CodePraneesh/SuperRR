#!/usr/bin/env python3
"""
scripts/check_environment.py
SupeRR Intelligence — Environment Verification & Dependency Pinning Validator

Verifies current Python runtime and library versions against requirements.lock.
Alerts the user if unpinned package versions are detected, which can induce
floating-point model shifts on borderline pressure deliveries (Finding F1).
"""
from __future__ import annotations
import sys
from pathlib import Path

PINNED_VERSIONS = {
    "numpy": "2.4.2",
    "pandas": "2.3.3",
    "scipy": "1.17.0",
    "scikit-learn": "1.8.0",
    "lightgbm": "4.7.0",
}

def check_environment(strict: bool = False) -> bool:
    print("=" * 70)
    print("SUPERR INTELLIGENCE: ENVIRONMENT VERIFICATION")
    print("=" * 70)
    print(f"Python Runtime: {sys.version.split()[0]} ({sys.platform})")

    discrepancies = []
    for pkg_name, pinned_ver in PINNED_VERSIONS.items():
        try:
            import_name = "sklearn" if pkg_name == "scikit-learn" else pkg_name
            mod = __import__(import_name)
            installed_ver = getattr(mod, "__version__", "unknown")
            if installed_ver == pinned_ver:
                print(f"  [OK] {pkg_name:<15} : {installed_ver} (matches requirements.lock)")
            else:
                discrepancies.append((pkg_name, pinned_ver, installed_ver))
                print(f"  [WARN] {pkg_name:<13} : {installed_ver} != {pinned_ver} (PINNED)")
        except ImportError:
            discrepancies.append((pkg_name, pinned_ver, "NOT INSTALLED"))
            print(f"  [MISSING] {pkg_name:<10} : NOT INSTALLED (pinned: {pinned_ver})")

    print("-" * 70)
    if discrepancies:
        print("ATTENTION: ENVIRONMENT DIVERGENCE DETECTED (Finding F1)")
        print("The SupeRR Intelligence Phase 2 models use learned gradient-boosted trees")
        print("and ridge regressors. Minor numerical variations across library versions")
        print("(e.g., scikit-learn 1.9.1 / pandas 3.0.5) can perturb win-probability")
        print("predictions on borderline deliveries near PI=50 by 1-5 balls, potentially")
        print("swapping closely tied ranks (e.g., Batters 4/5, 8/9; Bowler 10).")
        print("\nTo achieve exact byte-for-byte SHA-256 reproducibility, run:")
        print("  pip install -r requirements.lock")
        print("=" * 70)
        if strict:
            return False
        return True
    else:
        print("SUCCESS: Environment perfectly matches requirements.lock pinned versions.")
        print("=" * 70)
        return True

if __name__ == "__main__":
    is_strict = "--strict" in sys.argv
    success = check_environment(strict=is_strict)
    if is_strict and not success:
        sys.exit(1)
    sys.exit(0)

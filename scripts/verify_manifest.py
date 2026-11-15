#!/usr/bin/env python3
"""
scripts/verify_manifest.py
Verifies SHA-256 cryptographic hashes for all deliverables listed in
output/phase8_ranking_reconsideration/reproducibility_manifest.json.

Exits with code 0 on complete match, or non-zero if any file mismatches or is missing.
"""
import sys
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE8_DIR = REPO_ROOT / "output" / "phase8_ranking_reconsideration"
MANIFEST_PATH = PHASE8_DIR / "reproducibility_manifest.json"


def verify_manifest() -> bool:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: Manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        return False

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    deliverable_hashes = manifest.get("deliverable_hashes", {})
    if not deliverable_hashes:
        print("ERROR: No deliverable_hashes found in manifest.", file=sys.stderr)
        return False

    all_matched = True
    print("=" * 80)
    print("REPRODUCIBILITY MANIFEST CRYPTOGRAPHIC VERIFICATION")
    print(f"Manifest: {MANIFEST_PATH.relative_to(REPO_ROOT)}")
    print("=" * 80)

    for filename, expected_hash in deliverable_hashes.items():
        file_path = PHASE8_DIR / filename
        if not file_path.exists():
            print(f"MISSING : {filename:<35} (File not found on disk)")
            all_matched = False
            continue

        with open(file_path, "rb") as fp:
            data = fp.read()
        actual_hash = hashlib.sha256(data).hexdigest()

        if actual_hash == expected_hash:
            print(f"MATCH   : {filename:<35} -> {actual_hash[:16]}...")
        else:
            print(f"MISMATCH: {filename:<35}")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual  : {actual_hash}")
            all_matched = False

    print("=" * 80)
    if all_matched:
        print(f"SUCCESS: All {len(deliverable_hashes)} deliverables match manifest hashes exactly.")
    else:
        print("FAILURE: Cryptographic hash verification failed for one or more files.", file=sys.stderr)
    print("=" * 80)

    return all_matched


if __name__ == "__main__":
    success = verify_manifest()
    sys.exit(0 if success else 1)

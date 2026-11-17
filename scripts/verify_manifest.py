#!/usr/bin/env python3
"""
scripts/verify_manifest.py
Verifies SHA-256 cryptographic hashes for all deliverables listed in:
1. output/phase13_evidence_floor/reproducibility_manifest.json (Official Submission)
2. output/phase8_ranking_reconsideration/reproducibility_manifest.json (Pre-Floor Baseline, 17/17)

Exits with code 0 on complete match, or non-zero if any file mismatches or is missing.
"""
import sys
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE13_DIR = REPO_ROOT / "output" / "phase13_evidence_floor"
PHASE8_DIR = REPO_ROOT / "output" / "phase8_ranking_reconsideration"


def verify_manifest_section(target_dir: Path, manifest_name: str, section_title: str) -> bool:
    manifest_path = target_dir / manifest_name
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found at {manifest_path}", file=sys.stderr)
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    deliverable_hashes = manifest.get("deliverable_hashes", {})
    if not deliverable_hashes:
        print(f"ERROR: No deliverable_hashes found in {manifest_path}.", file=sys.stderr)
        return False

    all_matched = True
    print("=" * 80)
    print(f"{section_title}")
    print(f"Manifest: {manifest_path.relative_to(REPO_ROOT)}")
    print("=" * 80)

    for filename, expected_hash in deliverable_hashes.items():
        file_path = target_dir / filename
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


def verify_manifest() -> bool:
    ok_p13 = True
    if (PHASE13_DIR / "reproducibility_manifest.json").exists():
        ok_p13 = verify_manifest_section(
            PHASE13_DIR,
            "reproducibility_manifest.json",
            "OFFICIAL DELIVERABLES CRYPTOGRAPHIC VERIFICATION (Phase 13: >= 250 Balls Floor)"
        )
        print()

    ok_p8 = verify_manifest_section(
        PHASE8_DIR,
        "reproducibility_manifest.json",
        "PRE-FLOOR BASELINE CRYPTOGRAPHIC VERIFICATION (Phase 8 Frozen: 17/17 Deliverables)"
    )

    return ok_p13 and ok_p8


if __name__ == "__main__":
    success = verify_manifest()
    sys.exit(0 if success else 1)

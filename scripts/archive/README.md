# Historical Archive Scripts

The scripts in this directory (`scripts/archive/`) were developed during intermediate research and validation phases (Phase 1 through Phase 8) of the SupeRR Intelligence project.

## Important Notes:
1. **Provenance & Audit Trail:** These scripts are preserved strictly for methodological provenance and reproducibility audits.
2. **Environment Specific:** Many scripts in this folder contain hardcoded Windows filesystem paths and references to intermediate exploratory datasets that are not tracked in version control.
3. **Execution Notice:** These scripts are not intended to be executed on other operating systems or fresh git clones. For reproducible end-to-end execution, use the root-level production scripts:
   - `python scripts/build_official_store.py` (Builds official runtime scouting stores from frozen Phase 8 rankings)
   - `python -m pytest tests test_phase1_validation.py` (Runs automated test suite)
   - `python scripts/verify_manifest.py` (Validates deliverable cryptographic SHA-256 signatures)

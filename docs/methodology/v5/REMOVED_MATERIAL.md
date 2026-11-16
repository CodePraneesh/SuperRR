# Removed Material: Post-Hoc Retirement Claims & External Registries

**Date**: November 16, 2026  
**Status**: Removed from Repository & Competition Submission  

## Summary of Removal

All hand-typed player retirement registries, coaching assertions, auction status flags, and external eligibility reports previously generated under informal requests have been completely purged from this repository. 

Specifically, the following materials were permanently removed:
- `docs/reports/PLAYER_ELIGIBILITY_AND_DATA_COVERAGE_REPORT.md`
- `docs/reports/SupeRR_Player_Eligibility_and_Active_Rankings_Report.docx` and `.pdf`
- `scripts/generate_eligibility_document.py`
- `scripts/audit_player_eligibility.py`
- `scripts/build_active_rankings.py`
- `data/player_eligibility_registry.csv`
- `output/eligibility/` (and all contained CSV and JSON registries)
- `tests/test_player_eligibility.py`
- All frontend and backend "RETIRED" badges, retirement filters, and associated claims.

## Justification & Principles

1. **Reliance on Unsupplied External Facts**: The SupeRR Selector problem statement strictly requires all evaluations to be supported by the supplied match data, not reputation, external news, or outside knowledge. Hand-typed claims regarding player retirement, mentoring contracts, or auction participation violate this foundational rule.
2. **Numerical Inconsistencies with Frozen Baseline Deliverables**: The removed ad-hoc scripts contained pressure delivery counts and statistics that directly contradicted the certified, frozen Phase 8 CSVs. For example:
   - **Varun Chakravarthy**: The removed report cited 398 pressure balls; the official frozen Phase 8 deliverable (`official_top10_bowlers.csv`) certifies **892** pressure deliveries.
   - **Yuzvendra Chahal**: The removed report cited 557 pressure balls; the official frozen Phase 8 deliverable certifies **859** pressure deliveries.
   - **Mohammad Nawaz**: The removed report cited 185 pressure balls; the official frozen Phase 8 deliverable certifies **301** pressure deliveries.
   - **Jasprit Bumrah**: The removed report cited 609 pressure balls; the official frozen Phase 8 deliverable certifies **606** pressure deliveries.
3. **Data-Driven Recency Definition**: Player availability for squad selection is now evaluated strictly through the documented, post-hoc eligibility window (`docs/methodology/v5/ELIGIBILITY_RULE.md`), derived exclusively from match timestamps in the supplied dataset. A player without recent deliveries in this dataset is designated as *"not recently active in the supplied data"*, never *"retired"*.

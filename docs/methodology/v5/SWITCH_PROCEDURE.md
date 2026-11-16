# Procedure for Switching Official Submission to Active-Only Lists (Phase 12)

> **STATUS: PREPARED ONLY — NOT APPLIED**  
> **CURRENT OFFICIAL DEFAULT: Phase 8 Frozen Rankings (`output/phase8_ranking_reconsideration/`)**  
> *Per competition submission rules, this switch procedure must ONLY be executed upon explicit decision/instruction from the team lead. Do not execute without explicit confirmation.*

---

## 1. Overview and Intent

The official Unstop competition submission currently designates the frozen Phase 8 rankings as the authoritative primary lists. If the selection committee formally decides to enforce the post-hoc 12-month recency filter as the official submission standard (replacing Matthew Wade and Dinesh Karthik with Shashank Singh and Ashutosh Sharma in the batter list, while retaining the 100% concordant bowler list), this document defines the exact deterministic steps and affected files.

---

## 2. Step-by-Step Execution Procedure

If approval is granted to swap the primary submission to the active-only view:

### Step 1: Execute the Active Store Builder
Run the official store builder with the active version flag:
```bash
python scripts/build_official_store.py --version active
```
This reads `output/phase12_active/active_top10_batters.csv` and `output/phase12_active/active_top10_bowlers.csv` and outputs `output/phase4/data/official_scouting_store_active.json`.

To replace the main store directly:
```bash
cp output/phase4/data/official_scouting_store_active.json output/phase4/data/official_scouting_store.json
```

### Step 2: Swap Authoritative Submission CSVs (If Designating Active as Primary)
If the Phase 8 output directory itself is replaced or pointed to Phase 12:
1. Update `scripts/verify_submission.py` target paths or copy:
   - `output/phase12_active/active_top10_batters.csv` -> primary batter roster
   - `output/phase12_active/active_top10_bowlers.csv` -> primary bowler roster
2. Note: If `output/phase8_ranking_reconsideration/` files are replaced, `manifest.json` SHA-256 hashes must be re-hashed, and `docs/methodology/v5/REMOVED_MATERIAL.md` updated with the transition audit trail.

### Step 3: Regenerate Methodology Reports & Dropdown Matrices
Rebuild both publication documents to update the Unstop Dropdown Reference Tables on Pages 2 and 3:
```bash
python scripts/generate_methodology_report_md.py
python scripts/generate_pdf_report.py
```
Verify the PDF builds cleanly and remains within the 16-page maximum constraint.

### Step 4: Update Frontend Default View
In `frontend/src/App.tsx` and `frontend/src/pages/RankingsPage.tsx`:
- Point default route `/rankings` to `/rankings/active`.
- Update the Unstop dropdown podium view on `OverviewPage.tsx` to display Tim David (#1) and Suryakumar Yadav (#2) as the top batter podium.

### Step 5: Run Full Verification Suite
Verify zero discrepancies between store, CSVs, reports, and frontend:
```bash
python scripts/verify_manifest.py
python scripts/verify_submission.py
python -m pytest tests test_phase1_validation.py -q -rs
```

---

## 3. Inventory of Files Affected if Switched

If the official submission is switched to the active-only view, the following files would be updated:

1. **Official Store & Data**:
   - `output/phase4/data/official_scouting_store.json` (swapped to active roster)
   - `output/phase8_ranking_reconsideration/manifest.json` (only if primary directory swapped)
2. **Methodology Documentation & Reports**:
   - `docs/reports/METHODOLOGY_REPORT.md` (Pages 2-3 dropdown reference matrix updated)
   - `docs/reports/SupeRR_Intelligence_Methodology_Report.pdf` (Pages 2-3 dropdown reference matrix re-rendered)
3. **Frontend Application**:
   - `frontend/src/App.tsx` (default routing)
   - `frontend/src/pages/RankingsPage.tsx` (default tab)
   - `frontend/src/pages/OverviewPage.tsx` (podium display)
4. **Safety & Verification**:
   - `scripts/verify_submission.py` (authoritative rosters updated)

---

## 4. Current Default Stance

As of 16 November 2026, **no switch has been performed**. The Phase 8 Frozen Rankings remain the sole primary submission, with Phase 12 Active provided as a transparent, reproducible supplementary view.

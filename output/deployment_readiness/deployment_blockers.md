# SupeRR Intelligence — Deployment Blockers & Issue Classification Log
**Project:** SupeRR Selector Season 2 — SupeRR Intelligence  
**Phase:** Stage 2 Deployment Readiness  
**Audit Date:** November 15, 2026  
**Auditor:** Senior DevOps & Full-Stack QA Engineer  
**Classification Standard:** BLOCKER (Must fix before deployment), WARNING (Mitigate or monitor), PASS (Verified clean)

---

## 1. Summary of Identified Issues

| Issue ID | Severity | Category | Target Component | Description / Impact |
|:---:|:---:|---|---|---|
| **B-01** | **BLOCKER** | Git Repository / GitHub | Intermediate Analytical CSVs | Files > 100 MB will be rejected by GitHub's push hook. |
| **W-01** | **WARNING** | Backend Dependencies | `requirements.txt` | Unpinned `>=` version bounds allow dependency drift. |
| **W-02** | **WARNING** | Security & CORS | `render.yaml` | Permissive wildcard `*` in default CORS configuration. |
| **W-03** | **WARNING** | Code Portability | Standalone Check Scripts | 23 offline diagnostic scripts contain Windows path strings. |
| **W-04** | **WARNING** | Cloud Infrastructure | Render Free Tier Hosting | Cold-start latency (30–50s) after 15 minutes of inactivity. |
| **P-01** | **PASS** | Runtime Portability | Backend & Frontend Runtime | Dynamic `pathlib.Path` resolution; 0 Windows paths at runtime. |
| **P-02** | **PASS** | Security & Secrets | Source Code & Config | 0 hardcoded tokens, passwords, or credentials. |
| **P-03** | **PASS** | Credential Isolation | Frontend Vite Client | `HF_TOKEN` strictly confined to backend; never exposed to browser. |
| **P-04** | **PASS** | Offline Resilience | Scouting AI Service | Tier 3 Deterministic Engine guarantees 100% offline uptime. |
| **P-05** | **PASS** | Health Diagnostics | `/api/v1/health` | Verified HTTP 200 with loaded stores status. |
| **P-06** | **PASS** | Frontend Production | `tsc -b && vite build` | 0 errors, 15.98s compile time, Rollup chunked. |
| **P-07** | **PASS** | Routing Integrity | `frontend/vercel.json` | Single-page application rewrites prevent 404 on page refresh. |
| **P-08** | **PASS** | Data Completeness | `output/phase4/data/` | All 3 JSON databases present, valid, and indexed in RAM. |
| **P-09** | **PASS** | Methodological Freeze | CPRI v1.0 & Phase 8 | Zero changes to formulas, component weights, or Top 10 rankings. |

---

## 2. BLOCKERS (Action Required Prior to Git Push)

---

### [BLOCKER] B-01: GitHub 100 MB Single-File Limit on Intermediate Analytical CSVs
- **Affected Files:**
  - `output/phase2/pressure_scored_deliveries.csv` — **171.67 MB**
  - `output/processed/deliveries_enriched.csv` — **149.71 MB**
  - *(Additional large files near limit: `output/phase2/delivery_wpa.csv` 53.5 MB, `output/phase2/bowler_delivery_expectations.csv` 53.2 MB, `output/phase2/batter_delivery_expectations.csv` 53.1 MB).*
- **Root Cause:**  
  During analytical Phases 1 and 2, full ball-by-ball delivery populations (194,014 deliveries) were enriched with expected runs, win probability added, and pressure indices. These intermediate training datasets exceed GitHub’s strict **100.0 MB** single-file ceiling.
- **Deployment Impact:**  
  Running `git push origin main` on a repository containing these unstaged files will trigger a fatal rejection by GitHub's pre-receive hook:
  ```text
  remote: error: GH001: Large files detected.
  remote: error: File output/phase2/pressure_scored_deliveries.csv is 171.67 MB; this exceeds GitHub's file size limit of 100.00 MB
  ```
- **Why This Does NOT Affect the Production Application:**  
  The runtime FastAPI backend and React frontend **do not touch Phase 2 CSVs**. The runtime relies exclusively on the pre-compiled, indexed Phase 4 JSON databases located in `output/phase4/data/`:
  - `player_scouting_profiles.json` (0.86 MB)
  - `player_contextual_splits.json` (0.71 MB)
  - `head_to_head_matrix.json` (38.21 MB)
  All runtime data files are well under 40 MB.
- **Required Remediation (Before Initial Push):**  
  Add the following rules to the project's `.gitignore`:
  ```gitignore
  # Exclude large analytical intermediate datasets exceeding GitHub limits
  output/phase2/*.csv
  output/processed/deliveries_enriched.csv
  ```
  This immediately eliminates the blocker while preserving all runtime data stores and official Phase 8 ranking CSVs (which are only ~1.2 kB).

---

## 3. WARNINGS (Pre-Flight Mitigations & Monitoring)

---

### [WARNING] W-01: Unpinned Dependency Lower Bounds in `requirements.txt`
- **Affected File:** [requirements.txt](requirements.txt)
- **Observed State:**  
  Dependencies specify `>=` lower bounds (e.g., `fastapi>=0.110.0`, `pandas>=2.0.0`, `scikit-learn>=1.2.0`).
- **Potential Risk:**  
  Cloud buildpacks (such as Render) may install newly released upstream packages during automated builds, which could introduce minor deprecation warnings (e.g., Starlette TestClient transport changes in Python 3.14).
- **Remediation Recommendation:**  
  For 100% reproducible builds, maintain the pinned environment tested during Stage 1:
  - Python: `3.11.9`
  - FastAPI: `0.110.0`
  - Uvicorn: `0.28.0`
  - Pydantic: `2.6.4`
  - Pandas: `2.2.2`
  - Scikit-Learn: `1.4.1.post1`

---

### [WARNING] W-02: Permissive Default CORS Origins
- **Affected File:** [render.yaml](render.yaml#L18-L19)
- **Observed State:**  
  The default `CORS_ORIGINS` setting includes `*` alongside localhost URLs.
- **Potential Risk:**  
  A wildcard origin allows browser scripts hosted on any third-party domain to call the API.
- **Remediation Recommendation:**  
  Immediately after deploying the Vercel frontend, update the `CORS_ORIGINS` environment variable in the Render Dashboard to:
  ```text
  https://superr-intelligence.vercel.app,http://localhost:5173
  ```

---

### [WARNING] W-03: Hardcoded Windows Paths in Standalone Diagnostic Scripts
- **Affected Files:** 23 offline scripts in the project root (e.g., `check_comp_summary.py`, `check_consistency.py`, `execute_phase3_2.py`).
- **Observed State:**  
  These scripts contain hardcoded fallback paths of the form `C:\Users\Praneesh\OneDrive\Desktop\...`.
- **Production Impact:**  
  **Zero impact on production.** None of these 23 scripts are imported or executed by `backend.app.main` or the React frontend.
- **Remediation Recommendation:**  
  If reproducing historical offline analytical phases on Linux, execute them with explicit path arguments or allow them to use their relative path fallbacks.

---

### [WARNING] W-04: Render Free-Tier Web Service Spin-Down
- **Affected Component:** Cloud hosting platform (Render Free Tier)
- **Observed State:**  
  Render’s free web services automatically spin down into a sleep state after 15 minutes of zero incoming traffic.
- **User Impact:**  
  The first request after a period of dormancy will incur a cold-start delay of approximately **30 to 50 seconds** while the container re-spins and loads the Phase 4 stores. Subsequent requests respond in `< 15ms`.
- **Remediation Recommendation:**  
  - Document this cold-start delay for competition judges in demo instructions.
  - Optionally set up a free scheduled cron monitor (e.g., UptimeRobot or Cron-job.org) to ping `/api/v1/health` every 10 minutes during the evaluation window.

---

## 4. PASSED AUDIT CRITERIA (Verified Complete & Secure)

- **[PASS] P-01: Runtime OS Agnosticism:**  
  All runtime services ([backend/app/core/config.py](backend/app/core/config.py), `scouting_data_engine.py`) utilize `pathlib.Path(__file__).resolve()`. No Windows-specific path separators exist in production code.
- **[PASS] P-02: Zero Secret Leakage:**  
  Static scanning confirmed zero hardcoded API keys, tokens, or private credentials across the repository.
- **[PASS] P-03: Hugging Face Token Isolation:**  
  `HF_TOKEN` is loaded strictly on the backend. It is never transmitted to or bundled in the frontend.
- **[PASS] P-04: Offline Inference Resilience:**  
  When running without an `HF_TOKEN`, the system seamlessly engages Tier 3 Deterministic Fallback, guaranteeing 100% uptime with zero external network dependency.
- **[PASS] P-05: Health-Check Endpoint:**  
  `GET /api/v1/health` returns HTTP 200 with runtime memory status, loaded store confirmation, and active inference tier.
- **[PASS] P-06: Frontend Production Compilation:**  
  `npm run build` compiles in 15.98s with 0 errors and Rollup vendor code-splitting.
- **[PASS] P-07: Single Page Application Routing:**  
  `vercel.json` rewrites `/(.*)` to `/index.html`, eliminating 404 errors on deep-link page refreshes.
- **[PASS] P-08: Complete Data Inclusion:**  
  All 3 required Phase 4 JSON databases (`player_scouting_profiles.json`, `player_contextual_splits.json`, `head_to_head_matrix.json`) are present, intact, and verified.
- **[PASS] P-09: Methodology & Ranking Immutability:**  
  CPRI v1.0 formula, component weights (40/25/20/15), and Phase 8 official rankings are 100% preserved without modification.

# SupeRR Intelligence — Recommended `.gitignore` Specification
**Project:** SupeRR Selector Season 2 — SupeRR Intelligence  
**Phase:** Stage 3 Repository Inspection & GitHub Preparation  
**Target:** `SupeRR_Intelligence_Phase1/SupeRR_Phase1/.gitignore`  
**Purpose:** Prevent GitHub 100 MB push rejection, protect local datasets, and secure credentials.

---

## 1. Executive Summary & Strategy

To successfully push **SupeRR Intelligence** to [CodePraneesh/SuperRR](https://github.com/CodePraneesh/SuperRR.git) while strictly preserving local analytical data and official rankings, the `.gitignore` must balance three non-negotiable requirements:

1. **Avoid GitHub's 100 MB Rejection (Blocker B-01):**  
   `output/phase2/pressure_scored_deliveries.csv` (171.7 MB) and `output/processed/deliveries_enriched.csv` (142.8 MB) must be ignored.
2. **Preserve Runtime Data Stores:**  
   `output/phase4/data/*.json` (including `head_to_head_matrix.json` at 38.2 MB) must be tracked because the FastAPI backend requires them on startup.
3. **Preserve Official Rankings & Audit Documentation:**  
   All Phase 8 official rankings (`official_top10_batters.csv`, `official_top10_bowlers.csv`, etc.) and markdown audit reports must be tracked.

> [!IMPORTANT]
> Adding a file to `.gitignore` **does NOT delete the file from your local disk**. All 194,014 raw delivery records and enriched CSVs remain 100% intact locally for auditing and re-running pipelines.

---

## 2. Production `.gitignore` Content

Below is the complete, production-hardened `.gitignore` file recommended for `SupeRR_Intelligence_Phase1/SupeRR_Phase1/.gitignore`:

```gitignore
# ==============================================================================
# SupeRR Intelligence — Production .gitignore
# Target: SupeRR_Intelligence_Phase1/SupeRR_Phase1/.gitignore
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Environment Variables & Secret Credentials (Zero Leakage)
# ------------------------------------------------------------------------------
.env
*.env
.env.local
.env.production
.env.*.local
*.pem
*.key
*.token

# ------------------------------------------------------------------------------
# 2. Large Analytical Intermediate Datasets (> 50 MB / > 100 MB GitHub Limit)
# NOTE: These files remain intact on local disk. Runtime backend does not need them.
# ------------------------------------------------------------------------------
output/phase2/*.csv
output/processed/deliveries_enriched.csv
*.zip
*.tar.gz

# ------------------------------------------------------------------------------
# 3. Model Training Logs, Checkpoints & Scratch Files
# ------------------------------------------------------------------------------
catboost_info/
lightning_logs/
wandb/
*.safetensors
*.bin
*.gguf
*.onnx
models/
hf_cache/

# ------------------------------------------------------------------------------
# 4. Python Bytecode, Caches & Virtual Environments
# ------------------------------------------------------------------------------
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/

# ------------------------------------------------------------------------------
# 5. Frontend Node.js Dependencies, Bundles & Build Info
# ------------------------------------------------------------------------------
frontend/node_modules/
frontend/dist/
frontend/dist-ssr/
frontend/*.tsbuildinfo
frontend/vite.config.d.ts
frontend/vite.config.js
npm-debug.log*
yarn-debug.log*
pnpm-debug.log*

# ------------------------------------------------------------------------------
# 6. IDE, Operating System & Workspace Metadata
# ------------------------------------------------------------------------------
.vscode/*
!.vscode/extensions.json
.idea/
.DS_Store
Thumbs.db
Desktop.ini
*.suo
*.user

# ------------------------------------------------------------------------------
# 7. Explicit Whitelist: MUST BE TRACKED (Critical Runtime & Official Outputs)
# ------------------------------------------------------------------------------
!output/phase4/data/*.json
!output/phase4/data/*.md
!output/phase8_ranking_reconsideration/*.csv
!output/phase8_ranking_reconsideration/*.md
!output/phase8_ranking_reconsideration/*.json
!output/final_application_testing/*.csv
!output/final_application_testing/*.md
!output/deployment_readiness/*.md
!output/repository_inspection/*.csv
!output/repository_inspection/*.md
```

---

## 3. Line-by-Line Technical Rationale

| Section / Pattern | Why It Is Excluded / Whitelisted |
|---|---|
| `output/phase2/*.csv` | Excludes 4 large CSVs totaling ~330 MB (including `pressure_scored_deliveries.csv` at 171.7 MB). These were intermediate calculations used during model training and are not queried by the web application. |
| `output/processed/deliveries_enriched.csv` | Excludes the 142.8 MB enriched delivery table from GitHub while retaining it locally. |
| `!output/phase4/data/*.json` | **Explicit whitelist safety net:** Ensures the 3 pre-compiled JSON databases (`head_to_head_matrix.json`, `player_scouting_profiles.json`, `player_contextual_splits.json`) are committed to Git so Render and Vercel have runtime data. |
| `!output/phase8_ranking_reconsideration/*` | **Explicit whitelist safety net:** Protects the competition-critical official Top 10 rankings and reproducibility manifest. |
| `frontend/node_modules/` | Excludes third-party npm packages. Vercel automatically runs `npm install` during cloud build. |
| `frontend/dist/` | Excludes local build output. Vercel generates its own optimized production build via `npm run build`. |
| `.env*` | Prevents accidental commitment of local developer secrets or private tokens. |

---

## 4. Verification & Dry-Run Testing

Before running `git commit`, verify that `.gitignore` correctly filters out the large CSVs using Git's built-in dry-run flag:

```bash
# 1. Preview what Git WOULD stage without actually staging:
git add --dry-run .

# 2. Specifically verify that the 171 MB file is ignored:
git check-ignore -v output/phase2/pressure_scored_deliveries.csv
# Expected Output: .gitignore:17:output/phase2/*.csv output/phase2/pressure_scored_deliveries.csv

# 3. Specifically verify that the runtime data store IS tracked:
git check-ignore -v output/phase4/data/head_to_head_matrix.json
# Expected Output: (No output, exit code 1 -> Not ignored, correctly tracked)
```

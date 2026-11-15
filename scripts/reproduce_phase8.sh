#!/usr/bin/env bash
# ==============================================================================
# scripts/reproduce_phase8.sh
# SupeRR Intelligence — End-to-End Phase 8 Reproduction Pipeline
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "========================================================================"
echo "SUPERR INTELLIGENCE — END-TO-END PHASE 8 REPRODUCTION PIPELINE"
echo "========================================================================"

# 1. Environment Verification
echo "[Step 1/6] Verifying Python Environment..."
python scripts/check_environment.py

# 2. Locate Raw Data Pack Archive
ZIP_PATH="${1:-}"
if [ -z "$ZIP_PATH" ]; then
    if [ -f "6af458274c1e8_data_pack.zip" ]; then
        ZIP_PATH="6af458274c1e8_data_pack.zip"
    elif [ -f "D:/Download/6af458274c1e8_data_pack.zip" ]; then
        ZIP_PATH="D:/Download/6af458274c1e8_data_pack.zip"
    elif [ -f "../6af458274c1e8_data_pack.zip" ]; then
        ZIP_PATH="../6af458274c1e8_data_pack.zip"
    fi
fi

if [ -z "$ZIP_PATH" ] || [ ! -f "$ZIP_PATH" ]; then
    echo "ERROR: Raw data pack archive not found!"
    echo "Please provide the path to 6af458274c1e8_data_pack.zip as an argument:"
    echo "  ./scripts/reproduce_phase8.sh /path/to/6af458274c1e8_data_pack.zip"
    exit 1
fi
echo "[Step 2/6] Using Data Pack: $ZIP_PATH"

# 3. Phase 1 Data Ingestion & Audit
echo "[Step 3/6] Running Phase 1 Data Ingestion..."
python supeRR_phase1_pipeline.py --zip "$ZIP_PATH" --out output

# 4. Phase 2 Pressure & WPA Pipeline Generators
echo "[Step 4/6] Running Phase 2 ML Analytical Generators..."
export PYTHONPATH=.
echo "  -> Running Pressure Validation Generator..."
python ml/phase2/pressure_validation.py
echo "  -> Running Model Evaluation Generator..."
python ml/phase2/model_evaluation.py
echo "  -> Running WPA Evaluation Generator..."
python ml/phase2/wpa_evaluation.py

# 5. Phase 8 Analysis Recalculation
echo "[Step 5/6] Running Phase 8 Official Selection Engine..."
python scripts/execute_phase8_analysis.py

# 6. Cryptographic Manifest & Submission Verification
echo "[Step 6/6] Verifying Cryptographic Manifest and Submission Safety..."
python scripts/verify_manifest.py
python scripts/verify_submission.py

echo "========================================================================"
echo "PHASE 8 REPRODUCTION COMPLETE & FULLY VERIFIED."
echo "========================================================================"

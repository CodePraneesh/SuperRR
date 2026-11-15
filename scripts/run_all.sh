#!/usr/bin/env bash
# scripts/run_all.sh
# SupeRR Intelligence - Unified Automation Script
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMMAND="${1:-all}"

case "$COMMAND" in
  setup)
    echo "=== [1/2] Installing Python Dependencies ==="
    pip install -r requirements.txt
    echo "=== [2/2] Installing Frontend Dependencies ==="
    cd frontend && npm install && cd ..
    echo "Setup complete."
    ;;

  build-store)
    echo "=== Building Official Phase 8 Scouting Store ==="
    python scripts/build_official_store.py
    ;;

  test)
    echo "=== Running Full Test Suite ==="
    python run_all_tests_suite.py
    ;;

  build-frontend)
    echo "=== Building Production Frontend ==="
    cd frontend && npm run build && cd ..
    ;;

  run-api)
    echo "=== Starting FastAPI Backend on :8000 ==="
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
    ;;

  run-frontend)
    echo "=== Starting Vite Frontend Dev Server ==="
    cd frontend && npm run dev
    ;;

  all)
    echo "=== Running Full Pipeline ==="
    python scripts/build_official_store.py
    python run_all_tests_suite.py
    cd frontend && npm run build && cd ..
    echo "Pipeline executed successfully."
    ;;

  *)
    echo "Usage: $0 {setup|build-store|test|build-frontend|run-api|run-frontend|all}"
    exit 1
    ;;
esac

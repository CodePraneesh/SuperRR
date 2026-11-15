# SupeRR Intelligence — AI-Powered Cricket Scouting Platform

**SupeRR Intelligence** is an advanced, evidence-grounded cricket scouting and performance intelligence platform. It combines ball-by-ball contextual state modeling, pressure index quantification, win probability added (WPA), and Bayesian reliability shrinkage into the **Clutch Performance Rating Index (CPRI)**, layered with a **Three-Tier AI Scouting Intelligence Engine**.

---

## 1. Quick Start & Setup

### Prerequisites
- Python 3.10+ (Tested up to Python 3.14.3 64-bit)
- Windows, Linux, or macOS

### Installation
1. **Clone or navigate to the repository**:
   ```bash
   cd SupeRR_Intelligence_Phase1/SupeRR_Phase1
   ```

2. **Install production dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment (Optional for Tier 1 AI generation)**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Hugging Face API token:
   ```ini
   HF_TOKEN=your_huggingface_token_here
   ```
   > **Note**: The platform runs 100% offline out-of-the-box using **Tier 3 (Deterministic Python Fallback)** even without internet access or an API token.

---

## 2. Command-Line Scouting Interface (`scouting_cli.py`)

Run interactive queries or system self-tests directly from your terminal:

### Run System Self-Test (Verifies All 7 Scouting Features):
```bash
python scouting_cli.py --test
```

### Feature 1: Comprehensive Player Scouting Report
```bash
python scouting_cli.py --feature report --player "Rinku Singh" --scope IPL --role Batter
python scouting_cli.py --feature report --player "Matthew Wade" --scope T20I --role Batter
```

### Feature 2: Pressure Performance Dossier
```bash
python scouting_cli.py --feature pressure --player "Matheesha Pathirana" --scope IPL --role Bowler
```

### Feature 3 & 4: Tactical Strengths & Weaknesses
```bash
python scouting_cli.py --feature batter_sw --player "Rinku Singh" --scope IPL
python scouting_cli.py --feature bowler_sw --player "Matheesha Pathirana" --scope IPL
```

### Feature 5: Batter-versus-Batter Comparison
```bash
python scouting_cli.py --feature compare --player "Rinku Singh" --target "Suryakumar Yadav" --scope IPL
```

### Feature 6: Batter vs Bowler Head-to-Head Scouting
```bash
python scouting_cli.py --feature h2h --player "Rinku Singh" --target "Mohit Sharma" --scope IPL
```

### Feature 7: Natural Language Analytics QA
```bash
python scouting_cli.py --feature ask --query "Why is Rinku Singh ranked #1 under pressure?" --player "Rinku Singh" --scope IPL
```

---

## 3. Architecture Overview

The system is organized into modular phases:

```
[Phase 1: Ingestion & Feature Engineering]
   └── deliveries_enriched.csv (200k+ balls, pre-ball pressure state, zero lookahead leakage)

[Phase 2: Expectations & WPA Modeling]
   ├── LightGBM run expectancy & dismissal risk models
   └── Delivery-level Win Probability Added (WPA) attribution

[Phase 3: CPRI Engine & Methodology Freeze]
   ├── Pressure Impact (40%), Adaptability (25%), Consistency (20%), Reliability (15%)
   └── CPRI-v1.0.0-PROD-FREEZE (Official Top 10 + Provisional Top 5 rankings sealed)

[Phase 4: AI Scouting Intelligence Engine]
   ├── Phase 4.2: Fast Scouting Stores (<8 MB JSON stores)
   ├── Phase 4.3: Scouting Data Engine & Grounded Prompt Assembler
   ├── Phase 4.4: Three-Tier Generation Service (HF API + Deterministic Fallback)
   └── Phase 4.5: Response Verifier & Anti-Hallucination Guardrails
```

---

## 4. Running the Test Suites

The platform includes exhaustive automated tests guaranteeing 100% test pass rates across all subsystems:

### Run Master Platform Test Suite (All 176 Tests):
```bash
python run_all_tests_suite.py
```

### Run Dedicated Subsystem Test Suites:
```bash
# 1. Phase 5 FastAPI Backend Suite (16 tests)
python -m unittest tests/test_phase5_api.py

# 2. Scouting Data Stores Test (9 tests)
python -m unittest tests/test_phase4_2_stores.py

# 3. Scouting Query Engine Test (9 tests)
python -m unittest tests/test_phase4_3_engine.py

# 4. AI Service & Guardrails Test (7 tests)
python -m unittest tests/test_phase4_4_ai_service.py

# 5. Integration Verification Test (7 tests)
python -m unittest tests/test_phase4_5_integration.py
```

---

## 5. Phase 5 FastAPI Backend Service

The high-performance REST API backend is implemented using FastAPI and Uvicorn. It exposes all frozen CPRI rankings, player profiles, situational splits, and multi-tier AI scouting capabilities.

### Launching the API Server

```bash
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running:
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI 3.1 Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Core API Endpoints

| Method | Endpoint | Description | Query / Body Params |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Health & Store Readiness | None |
| `GET` | `/api/v1/players/{scope}/{role}` | List cohort players & rankings | `official_only=bool`, `confidence_tier=str`, `limit=int`, `offset=int` |
| `GET` | `/api/v1/players/{scope}/{role}/{name}` | Full player profile & CPRI components | None |
| `GET` | `/api/v1/players/{scope}/{role}/{name}/splits` | Phase & pressure splits | None |
| `GET` | `/api/v1/scouting/report/{scope}/{role}/{name}` | AI scouting report | None |
| `GET` | `/api/v1/scouting/pressure/{scope}/{role}/{name}` | Pressure performance analysis | None |
| `POST` | `/api/v1/scouting/compare` | Side-by-side player comparison | `scope`, `role`, `player_a`, `player_b` |
| `GET` | `/api/v1/scouting/matchup/{scope}/{batter}/{bowler}` | H2H encounter & sample tier warning | None |
| `POST` | `/api/v1/scouting/ask` | Natural language analytics QA | `query`, `scope` (optional), `role` (optional) |

---

## 6. Phase 6 React Frontend Dashboard

The frontend is a modern dark-first web application built with **React 18**, **Vite 6**, **TypeScript**, **Tailwind CSS**, and **Recharts**.

### Launching the Frontend

```bash
cd frontend
npm install
npm run dev
```

Application will run locally at: **`http://localhost:5173`**

### Live Integration Verification
Run the automated end-to-end integration test against the running backend:
```bash
cd frontend
node test-integration.js
```
*Result: 9 / 9 live API endpoints verified.*

---

## 7. Phase 7 Production Cloud Deployment

SupeRR Intelligence is prepared for cloud deployment:
- **Backend**: Hosted on **Render** using [`render.yaml`](./render.yaml) and dynamic `$PORT` binding.
- **Frontend**: Hosted on **Vercel** with SPA client-side routing rewrites configured in [`frontend/vercel.json`](./frontend/vercel.json).

For complete step-by-step instructions, environment variable setup, memory profiling details, and the 5-minute competition demo script, refer to:
👉 **[`DEPLOYMENT.md`](./DEPLOYMENT.md)**

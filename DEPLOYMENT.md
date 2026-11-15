# SupeRR Intelligence — Public Cloud Deployment Guide

**SupeRR Intelligence**  
*Tagline: "Beyond Performance. Measuring Pressure."*

This guide provides end-to-end instructions for deploying the **SupeRR Intelligence** platform publicly using **Render** for the FastAPI backend and **Vercel** for the React + Vite frontend.

---

## 1. Pre-Deployment Verification Summary

All code and data files have undergone strict pre-deployment certification:
- **OS Path Agnosticism**: All path lookups use dynamic `pathlib.Path(__file__).resolve()`. Zero hardcoded Windows drive letters or user directories in execution logic.
- **Data Store Accommodation**:
  - `player_scouting_profiles.json` (0.86 MB)
  - `player_contextual_splits.json` (0.71 MB)
  - `head_to_head_matrix.json` (38.21 MB)
  - **Memory Profile**: Peak RAM during JSON deserialization is **118.09 MB**, and steady-state RAM is **73.29 MB**. This comfortably fits within Render's 512 MB free tier.
  - **Git Compliance**: All files are well under GitHub’s 100 MB single-file threshold.
- **Frontend Bundle Optimization**: Rollup vendor chunking (`vendor-react`, `vendor-charts`, `vendor-icons`) prevents any bundle chunk from exceeding 500 kB.
- **Security Guardrails**:
  - `HF_TOKEN` resides exclusively on the backend server; never bundled in the frontend.
  - `.env` files are ignored in `.gitignore`.
  - Offline deterministic fallback operates 100% reliably if `HF_TOKEN` is unset.
  - `vercel.json` contains single-page application (SPA) rewrite rules to prevent 404 errors on browser page reloads.

---

## 2. Part A — Deploying the FastAPI Backend (Render)

Render is recommended for hosting Python FastAPI services with dynamic port binding and zero-configuration SSL.

### Method 1: Automated Blueprint Deployment (Recommended)
1. Commit and push your code to your GitHub repository.
2. In the [Render Dashboard](https://dashboard.render.com), click **New +** → **Blueprint**.
3. Select your repository. Render will automatically detect [`render.yaml`](./render.yaml).
4. Review the service definition:
   - **Name**: `superr-intelligence-api`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/v1/health`
5. Under Environment Variables, optionally add:
   - `HF_TOKEN`: *(Optional)* Your Hugging Face user access token for Tier 1 inference. If left unset, the backend automatically runs in Tier 3 (Deterministic Fallback Engine).
   - `CORS_ORIGINS`: Add your deployed Vercel URL once known (e.g. `https://superr-intelligence.vercel.app,*`).
6. Click **Apply**. Render will build and deploy the web service. Note your public backend URL (e.g., `https://superr-intelligence-api.onrender.com`).

### Method 2: Manual Web Service Setup
If not using blueprints:
1. Click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure the following fields:
   - **Root Directory**: `SupeRR_Intelligence_Phase1/SupeRR_Phase1` (or repo root depending on repository structure)
   - **Environment**: `Python 3`
   - **Region**: `Oregon (US West)` or your preferred region
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. Under **Advanced**:
   - **Health Check Path**: `/api/v1/health`
   - **Environment Variables**:
     - `PYTHON_VERSION`: `3.11.9`
     - `API_HOST`: `0.0.0.0`
     - `HF_TOKEN`: *(optional)*
5. Click **Create Web Service**.

---

## 3. Part B — Deploying the React Frontend (Vercel)

Vercel provides edge CDN delivery for Vite/React applications with automatic SSL.

### Step-by-Step Vercel Deployment:
1. In the [Vercel Dashboard](https://vercel.com), click **Add New...** → **Project**.
2. Select your repository from GitHub.
3. Configure Project Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select `SupeRR_Intelligence_Phase1/SupeRR_Phase1/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
4. **Environment Variables**:
   - Add `VITE_API_BASE_URL` with the value of your deployed Render backend URL plus `/api/v1`:
     ```text
     VITE_API_BASE_URL = https://superr-intelligence-api.onrender.com/api/v1
     ```
5. Click **Deploy**.
6. Vercel will install dependencies, compile TypeScript, run Vite bundling, and assign a production URL (e.g., `https://superr-intelligence.vercel.app`).
7. Because [`vercel.json`](./frontend/vercel.json) defines SPA rewrites, navigating directly to deep links like `/rankings/ipl` or `/players/IPL/Batter/Rinku%20Singh` works without 404 errors.

---

## 4. Part C — Post-Deployment Verification Checklist

Once both services are deployed, perform these live checks against the production URLs:

| Check # | Target Component | Production Action | Expected Result |
| :---: | :--- | :--- | :--- |
| **1** | Backend Health | Visit `https://<render-url>/api/v1/health` | HTTP `200` with `"status": "healthy"`, `"stores_loaded": true`. |
| **2** | Swagger UI | Visit `https://<render-url>/docs` | Interactive OpenAPI documentation loads cleanly. |
| **3** | Overview Page | Visit `https://<vercel-url>/` | Headline view renders Official Phase 8 Unified Top 10 (Matthew Wade #1, Mitchell Santner #1) with 90% rank CIs. |
| **4** | Format Switching | Click *Official Unified*, *IPL*, or *T20I* | Smoothly switches between official competition baseline and contextual league views. |
| **5** | Rankings Table | Visit `https://<vercel-url>/rankings` | Authoritative leaderboard renders Wade #1 (85.36), David #2 (82.44), Suryakumar #3 (81.42), Rinku #5 (77.18), Santner #1 (79.84). |
| **6** | Player Dossier | Visit `/players/IPL/Batter/Rinku%20Singh` | Displays Official Phase 8 Standing card with 90% bootstrap rank CI [1, 51] and single-league contextual breakdown. |
| **7** | AI Scouting Report | Click **"Generate AI Scouting Report"** | Live report synthesizes in seconds and renders verified Markdown audited against immutable evidence. |
| **8** | Player Comparison | Visit `/compare`, select Rinku vs Suryakumar | Dual radar overlays, delta matrix shows comparative clutch metrics, AI comparison verdict renders. |
| **9** | Matchup Safety | Visit `/matchup`, select Dhoni vs Ashwin | Matchup card loads with **prominent exploratory sample warning (<18 balls)**. |
| **10** | Limitations & Uncertainty | Visit `/limitations` | Explores two-tier classification, wide CIs audit, and adaptability weight sensitivity tables. |
| **11** | AI Terminal QA | Visit `/assistant`, ask a suggested question | Grounded analytical response appears with deterministic verification audit badge. |

---

## 5. Competition Demo Walkthrough (5-Minute Script)

Use this structured walkthrough for judges and evaluators:

### Minute 1: The Core Problem & Brand Promise
- **Hook**: Standard cricket metrics (average, strike rate, economy) collapse when leverage spikes. Scoring 20 runs in over 2 is not the same as scoring 20 runs in over 19.
- **Solution**: Introduce **SupeRR Intelligence** (*"Beyond Performance. Measuring Pressure."*).
- **Hero**: Point out the live status indicator (*"Engine Online • CPRI v1.0.0 Certified"*), honoring Rajasthan Royals' data-forward legacy.

### Minute 2: Official Phase 8 Rankings & Bootstrap Rank Uncertainty
- Show the headline **Official Competition Submission** (unified dual-format baseline):
  - **Batters**: **Matthew Wade** (#1, CPRI 85.36, 90% CI [1, 22]), **Tim David** (#2, 82.44), **Suryakumar Yadav** (#3, 81.42), **Rinku Singh** (#5, 77.18).
  - **Bowlers**: **Mitchell Santner** (#1, CPRI 79.84, 90% CI [2, 36]), **Sufiyan Muqeem** (#2, 78.78), **Rashid Khan** (#3, 77.90), **Jasprit Bumrah** (#8, 73.36).
- Highlight the **Two-Tier System**:
  - **High Confidence**: Proven high-volume performers with bounded rank spans ($\le 65$).
  - **Exploratory**: Small-sample rate outliers (Wade [1, 22] on 191 balls, Muqeem [1, 74] on 151 balls, Overton [1, 71] on 168 balls).
- Switch to contextual **IPL** and **T20I** views to show how individual tournament slices compare.

### Minute 3: Deep Player Intelligence & AI Scouting Dossier
- Navigate to **Rinku Singh**'s Player Dossier (`/players/IPL/Batter/Rinku%20Singh`).
- Point out the **Official Phase 8 Standing Banner** showing his official rank (#5 Batter, 77.18 CPRI, [1, 51] 90% CI) above his IPL contextual performance.
- Highlight the **Pressure Contrast Matrix**:
  - Strike rate jumps by **+18.94** under pressure ($PI \ge 50$), classifying him as a *Clutch Accelerant*.
- Click **"Generate AI Scouting Report"**:
  - Demonstrate how the Three-Tier AI engine produces an evidence-grounded report verified by the anti-hallucination auditor.

### Minute 4: Player Comparison & Matchup Safeguards
- Open `/compare` and compare **Rinku Singh** vs **Suryakumar Yadav**:
  - Show the dual radar overlay and component delta matrix.
- Open `/matchup` and inspect **Mahendra Singh Dhoni** vs **Ravichandran Ashwin**:
  - Highlight the **Exploratory Sample Warning**: The system refuses to fabricate confidence on small samples ($< 18$ balls), demonstrating statistical integrity.
- Open `/limitations`:
  - Show the **Phase 8 Adaptability Formula** ($0.60 \cdot \text{PI} + 0.40 \cdot \max(\Delta, -5.0)$), effective 55% weight breakdown, and weight sensitivity invariance tables.

### Minute 5: AI Terminal & Methodology Transparency
- Open `/assistant` and ask: *"Who are the official Top 3 batters under pressure and what are their rank uncertainties?"*
  - Show the grounded statistical explanation citing Wade #1 [1, 22], David #2 [1, 19], and Suryakumar #3 [2, 25].
- Conclude on `/methodology`:
  - Review the formal mathematical transparency, pre-ball $PI \ge 50$ threshold, LightGBM run/wicket baselines, and Bayesian shrinkage confidence classifications.

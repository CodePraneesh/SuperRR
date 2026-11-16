# SupeRR Intelligence — End-to-End Cloud Deployment & Reproduction Guide
**Project:** SupeRR Selector Season 2 — SupeRR Intelligence  
**Phase:** Stage 2 Deployment Readiness  
**Target Topology:** Render (FastAPI Backend) + Vercel (React Frontend)

---

## 1. Pre-Deployment Git Preparation (Mandatory Pre-Flight)

Before committing files or pushing to GitHub, you **must resolve GitHub's 100 MB single-file limit** to prevent rejection during `git push`.

### Step 1.1: Update `.gitignore` for Large Analytical CSVs
Two intermediate files in `output/` exceed GitHub's 100 MB ceiling:
- `output/phase2/pressure_scored_deliveries.csv` (171.67 MB)
- `output/processed/deliveries_enriched.csv` (149.71 MB)

> [!NOTE]
> The production application **does NOT require these two files at runtime**. The runtime backend relies exclusively on the pre-compiled Phase 4 JSON databases in `output/phase4/data/` (total size ~39.8 MB, largest file 38.2 MB).

Add the following lines to your project root `.gitignore`:
```gitignore
# Exclude oversized intermediate analytical datasets (>100MB)
output/phase2/*.csv
output/processed/deliveries_enriched.csv
```

### Step 1.2: Verify Clean Git Commit
Run the following commands in your project root:
```bash
# Check status and verify no secrets or oversized files are staged
git status

# Stage only verified code, configurations, and Phase 4 runtime data
git add backend/ frontend/ output/phase4/ data_dictionary.md render.yaml Procfile requirements.txt DEPLOYMENT.md
git add .gitignore .env.example

# Commit with a formal version tag
git commit -m "feat: SupeRR Intelligence v1.0.0 production deployment release"
git push origin main
```

---

## 2. Deploying the Backend API (Render)

Render hosts the FastAPI service with dynamic port assignment, free SSL, and continuous deployment.

### Method A: Automated Blueprint Deployment (Recommended)
1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → **Blueprint**.
3. Connect your GitHub repository.
4. Render will automatically detect and parse [`render.yaml`](render.yaml):
   - **Service Name:** `superr-intelligence-api`
   - **Runtime:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/api/v1/health`
5. Under Environment Variables:
   - Add `HF_TOKEN` *(optional)* if you wish to enable Tier 1 Hugging Face inference. If omitted, the engine runs in 100% offline Tier 3.
6. Click **Apply**. Render will build the environment and deploy the service.
7. Copy your assigned public URL (e.g., `https://superr-intelligence-api.onrender.com`).

---

### Method B: Manual Web Service Setup
If not using the Blueprint:
1. Click **New +** → **Web Service**.
2. Select your repository.
3. Configure the following parameters:
   - **Name:** `superr-intelligence-api`
   - **Root Directory:** `SupeRR_Intelligence_Phase1/SupeRR_Phase1` *(or `.` if repo root)*
   - **Environment:** `Python 3`
   - **Region:** `Oregon (US West)` or closest to your users
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
4. Under **Advanced Settings**:
   - **Health Check Path:** `/api/v1/health`
   - **Environment Variables**:
     - `PYTHON_VERSION` = `3.11.9`
     - `API_HOST` = `0.0.0.0`
     - `CORS_ORIGINS` = `http://localhost:5173,http://localhost:3000,*`
5. Click **Create Web Service**.

---

## 3. Deploying the Frontend UI (Vercel)

Vercel provides edge CDN delivery for Vite/React applications with automatic asset compression and HTTPS.

### Step-by-Step Vercel Deployment:
1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Import your GitHub repository.
4. Configure Project Settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click *Edit* and select `SupeRR_Intelligence_Phase1/SupeRR_Phase1/frontend` (or `frontend` if repo is flat).
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`
5. **Add Environment Variable:**
   - **Key:** `VITE_API_BASE_URL`
   - **Value:** `https://<your-render-url>.onrender.com/api/v1` *(Ensure it ends with `/api/v1`)*
6. Click **Deploy**.
7. Vercel will install dependencies, compile TypeScript, run Vite Rollup bundling, and deploy the application.
8. Because [`vercel.json`](frontend/vercel.json) configures single-page application (SPA) rewrites, navigating directly to deep links like `/rankings/ipl` or `/players/IPL/Batter/Rinku%20Singh` works with zero 404 errors.

---

## 4. Post-Deployment Security Hardening: Update CORS

Once Vercel assigns your production frontend URL (e.g. `https://superr-intelligence.vercel.app`):
1. Return to the **Render Dashboard** → **superr-intelligence-api** → **Environment**.
2. Update `CORS_ORIGINS` from `*` to:
   ```text
   https://superr-intelligence.vercel.app,http://localhost:5173
   ```
3. Save changes. This locks your backend API so that only your verified frontend and local testing can make browser requests.

---

## 5. Local Reproduction from a Clean Machine

Follow these exact steps to verify the project on a clean computer or Linux/macOS server:

### Step 5.1: Clone & Navigate
```bash
git clone <your-repository-url>
cd SupeRR_Intelligence_Phase1/SupeRR_Phase1
```

### Step 5.2: Setup Python Virtual Environment
```bash
# Create and activate virtual environment
python -m venv venv

# On Linux/macOS:
source venv/bin/activate
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Install runtime dependencies
pip install -r requirements.txt
```

### Step 5.3: Start FastAPI Backend
```bash
# Run server on port 8000
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Verify health check in another terminal
curl http://127.0.0.1:8000/api/v1/health
```

### Step 5.4: Setup & Launch React Frontend
```bash
cd frontend

# Install Node modules
npm install

# Run Vite dev server
npm run dev
# App is now live on http://127.0.0.1:5173

# Or verify production build locally:
npm run build
npm run preview
```

---

## 6. Live Production Smoke Test (10-Point Checklist)

Verify these live checks against your deployed public URLs:

| Check # | Component | Production Target / Action | Expected Result |
|:---:|---|---|---|
| **1** | Backend Health | Visit `https://<render-url>/api/v1/health` | HTTP `200` with `"status": "healthy"`, `"stores_loaded": true`. |
| **2** | API Docs | Visit `https://<render-url>/docs` | Swagger UI documentation renders interactively. |
| **3** | Overview Dashboard | Visit `https://<vercel-url>/` | Top 3 podium, Top 10 CPRI bar chart, and radar chart render. |
| **4** | Format Toggle | Click *IPL* then *T20I* on Overview | Switch cohort leaderboards seamlessly with zero lag. |
| **5** | Rankings Deep Link | Refresh `https://<vercel-url>/rankings/ipl` | Page renders cleanly (SPA rewrite works; no 404). Rinku Singh is #1. |
| **6** | Player Dossier | Visit `/players/IPL/Batter/Rinku%20Singh` | 4 CPRI components render, phase splits load, net pressure delta (+18.94 SR). |
| **7** | AI Scouting Report | Click **"Generate AI Scouting Report"** | Live report synthesizes in seconds and renders verified markdown. |
| **8** | Player Comparison | Visit `/compare`, select Rinku vs Suryakumar | Dual radar overlay displays; +0.62 net CPRI delta calculated. |
| **9** | Matchup Safeguards | Visit `/matchup`, select Dhoni vs Ashwin | Matchup card renders with **Exploratory sample warning (<18 balls)**. |
| **10** | AI Terminal QA | Visit `/assistant`, submit a query | Analytical response renders with ground-truth CPRI citations. |

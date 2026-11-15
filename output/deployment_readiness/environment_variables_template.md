# SupeRR Intelligence — Environment Variables & Configuration Guide
**Project:** SupeRR Selector Season 2 — SupeRR Intelligence  
**Phase:** Stage 2 Deployment Readiness  
**Target Environments:** Local Development, Docker, Render (Backend), Vercel (Frontend)

---

## 1. Overview of System Environment Variables

SupeRR Intelligence separates backend server configuration from frontend client configuration to ensure **zero credential leakage** to the browser client.

```
+-------------------------------------------------------------+
|                      BACKEND SERVER                         |
|   (Render Web Service / Docker Container / Local Python)     |
|                                                             |
|   PORT             -> Dynamic port binding (e.g. 10000)     |
|   API_HOST         -> 0.0.0.0 (all interfaces)              |
|   DEBUG            -> False (disables debug stack traces)   |
|   CORS_ORIGINS     -> Whitelisted frontend domain(s)        |
|   HF_TOKEN         -> Hugging Face Access Token (OPTIONAL)  |
|   PYTHON_VERSION   -> 3.11.9 (runtime container version)    |
+-------------------------------------------------------------+
                              ^
                              | API calls to /api/v1
                              v
+-------------------------------------------------------------+
|                      FRONTEND CLIENT                        |
|        (Vercel Edge CDN / Local Vite Dev Server)            |
|                                                             |
|   VITE_API_BASE_URL -> Public URL pointing to backend       |
|                        e.g. https://<backend>/api/v1        |
+-------------------------------------------------------------+
```

---

## 2. Backend Environment Variables Reference

| Variable Name | Required? | Default Value | Production Recommended Value | Purpose & Description |
|---|:---:|:---:|:---:|---|
| `PORT` | **Auto** | `8000` | Injected by Host (`$PORT`) | HTTP server listener port. Render/Heroku inject this automatically. |
| `API_HOST` | No | `0.0.0.0` | `0.0.0.0` | Network binding interface. Must be `0.0.0.0` inside containers. |
| `DEBUG` | No | `False` | `False` | Enables FastAPI auto-reload and verbose logging. Must remain `False` in prod. |
| `CORS_ORIGINS` | No | `http://localhost:5173,...` | `https://<your-app>.vercel.app` | Comma-delimited list of permitted browser origins. |
| `HF_TOKEN` | **Optional** | *Empty* | *Your Hugging Face Token* | Token for Tier 1 LLM inference. If omitted, Tier 3 Offline Fallback is used. |
| `PYTHON_VERSION` | No | System | `3.11.9` | Declares target Python runtime for cloud buildpacks (Render/Heroku). |

> [!NOTE]
> `HF_TOKEN` is **strictly optional**. If `HF_TOKEN` is not provided, SupeRR Intelligence automatically operates in **Tier 3 (Deterministic Fallback Engine)**. In Tier 3, 100% of scouting dossiers, tactical contrast summaries, and player comparisons are generated directly from verified frozen analytical metrics without external API dependence.

---

## 3. Frontend Environment Variables Reference

| Variable Name | Required? | Default Value | Production Recommended Value | Purpose & Description |
|---|:---:|:---:|:---:|---|
| `VITE_API_BASE_URL` | **Yes (Prod)** | `http://127.0.0.1:8000/api/v1` | `https://<your-api>.onrender.com/api/v1` | Root URL for all Axios API requests made by the frontend. |

> [!IMPORTANT]
> Because Vite embeds environment variables prefixed with `VITE_` directly into client-side JavaScript bundles during `npm run build`, **NEVER** add `HF_TOKEN`, database passwords, or private keys to the frontend environment.

---

## 4. Ready-to-Copy Configuration Templates

### Template A: Backend Environment File (`.env` in backend root)
```bash
# =====================================================================
# SupeRR Intelligence — Backend Configuration
# Save as: SupeRR_Intelligence_Phase1/SupeRR_Phase1/.env
# =====================================================================

# Server Configuration
API_HOST=0.0.0.0
PORT=8000
DEBUG=False
PYTHON_VERSION=3.11.9

# Security & CORS (Replace with your actual Vercel domain in production)
CORS_ORIGINS=https://superr-intelligence.vercel.app,http://localhost:5173,http://localhost:3000

# AI Model Configuration (Optional: Leave blank for 100% Offline Tier 3)
HF_TOKEN=
```

---

### Template B: Frontend Environment File (`.env.production` in frontend root)
```bash
# =====================================================================
# SupeRR Intelligence — Frontend Production Configuration
# Save as: SupeRR_Intelligence_Phase1/SupeRR_Phase1/frontend/.env.production
# =====================================================================

# Backend API Base URL (Must end with /api/v1)
VITE_API_BASE_URL=https://superr-intelligence-api.onrender.com/api/v1
```

---

## 5. Cloud Platform Dashboard Setup

### Setting Variables in Render (Backend)
1. In the Render Dashboard, open your web service: **`superr-intelligence-api`**.
2. Navigate to **Environment**.
3. Under **Environment Variables**, add:
   - `PYTHON_VERSION` = `3.11.9`
   - `API_HOST` = `0.0.0.0`
   - `CORS_ORIGINS` = `https://<your-vercel-domain>.vercel.app,*`
   - `HF_TOKEN` = `hf_xxxxxxxxxxxxxxxxxxxx` *(optional)*
4. Click **Save Changes**. Render will automatically trigger a rolling redeployment.

### Setting Variables in Vercel (Frontend)
1. In the Vercel Dashboard, open your project: **`superr-intelligence`**.
2. Navigate to **Settings** → **Environment Variables**.
3. Add a new variable:
   - **Key:** `VITE_API_BASE_URL`
   - **Value:** `https://<your-render-domain>.onrender.com/api/v1`
   - **Target:** Check `Production`, `Preview`, and `Development`.
4. Click **Save**.
5. Trigger a redeploy under the **Deployments** tab so the new build bundles the updated base URL.

---

## 6. Security & Credential Hygiene Rules

1. **Keep `.env` files out of Git:** Ensure `.env`, `.env.local`, and `.env.production` remain listed in `.gitignore`.
2. **Never commit real tokens:** Only commit `.env.example` templates containing dummy placeholders.
3. **Least Privilege Token Permissions:** If generating an `HF_TOKEN` from Hugging Face, select a **Read-Only** Fine-Grained or User Access Token.
4. **CORS Restriction:** In production, remove wildcard `*` from `CORS_ORIGINS` and specify only your canonical frontend domain.

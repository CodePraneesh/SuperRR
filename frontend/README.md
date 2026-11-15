# SupeRR Intelligence — Frontend Web Application

**SupeRR Intelligence**  
*Tagline: "Beyond Performance. Measuring Pressure."*

A premium, modern, responsive cricket analytics dashboard built with **React**, **Vite**, **TypeScript**, **Tailwind CSS**, and **Recharts**. The frontend interfaces with the **SupeRR Intelligence FastAPI Backend** to deliver interactive CPRI leaderboards, radar component breakdowns, situational phase execution analysis, head-to-head matchup battlecards, and an AI scouting terminal.

---

## 1. Quick Start

### Prerequisites
- Node.js 18+ (tested on Node v24.18.0)
- npm 9+
- Running backend at `http://127.0.0.1:8000`

### Installation & Launch

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```
   Default `.env`:
   ```ini
   VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
   ```

3. **Start Development Server**:
   ```bash
   npm run dev
   ```
   The application will be live at: **`http://localhost:5173`**

4. **Run Live Backend Integration Verification**:
   ```bash
   node test-integration.js
   ```

5. **Production Build**:
   ```bash
   npm run build
   npm run preview
   ```

---

## 2. Application Architecture & Pages

| Route | Page | Purpose & Visualizations |
| :--- | :--- | :--- |
| `/` | **Overview Dashboard** | Hero intro, Top 3 podium, Top 10 CPRI bar chart, #1 player radar chart, master table. |
| `/rankings/ipl` | **IPL Rankings** | Full leaderboard with search, sorting across CPRI components, official vs provisional filter. |
| `/rankings/t20i` | **T20I Rankings** | Complete international T20I leaderboard with identical sorting and filtering. |
| `/players/:scope/:role/:name` | **Player Intelligence** | Deep dive profile with 4 component cards, overlay radar, phase splits, high vs low pressure contrast, and "Generate AI Scouting Report". |
| `/compare` | **Player Comparison** | Head-to-head matrix with side-by-side cards, net delta matrix, dual radar overlay, and AI comparative verdict. |
| `/matchup` | **Matchup Analysis** | Batter vs bowler direct encounter with balls, runs, strike rate, dot ball %, and exploratory small-sample warning badge. |
| `/assistant` | **AI Scouting Assistant** | Chat terminal with suggested prompts, Markdown rendering, and response verification badges. |
| `/methodology` | **Methodology** | Mathematical specification of CPRI v1.0.0, 4 component weights (40/25/20/15), and Bayesian shrinkage. |

---

## 3. Technology Stack

- **Framework**: React 18 with TypeScript 5
- **Build Tool**: Vite 6
- **Styling**: Tailwind CSS 3 (Dark-first palette: `#090d16` background, `#0f172a` cards, `#6366f1` indigo accents)
- **Routing**: React Router 6
- **Data Fetching**: Axios 1.7
- **Charts & Visualizations**: Recharts 2.15 (Radar charts, horizontal ranking curves, phase split bars)
- **Icons**: Lucide React
- **Markdown**: Custom safe inline parser with GitHub-flavored styling

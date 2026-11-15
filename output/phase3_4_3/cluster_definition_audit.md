# SupeRR Intelligence — Phase 3.4.3 Cluster Definition Audit

## 1. Audit of Cricket Series & Tournament Clusters

In Phase 3.4.2, a synthetic proxy (`YYYY-MM`) was evaluated. In Phase 3.4.3, we audited the raw match metadata in `matches_enriched.csv` and confirmed that explicit competition and series identifiers (`comp_id`) exist across all matches.

### Comparison of Resampling Designs:

| Feature | Independent Match Resampling | Calendar Month Proxy (Phase 3.4.2) | True Series Cluster Resampling (`comp_id`) |
| :--- | :--- | :--- | :--- |
| **Sampling Unit** | Individual Matches | Calendar Month Buckets | Actual Series / Tournament Editions |
| **T20I Cluster Count** | 482 matches | 49 monthly windows | **131 true series / tournaments** |
| **IPL Cluster Count** | 371 matches | 5 season-level buckets | **5 annual IPL editions** |
| **Multi-Team Tournaments** | Decomposed into matches | Split across months if cross-month | Kept intact as single tournament blocks |
| **Bilateral Series Integrity** | Split into independent games | Merged unrelated tours in same month | **100% Preserved** (all matches in series sampled together) |

## 2. Documented IPL Season-Cluster Limitation

In IPL, each tournament edition spans 71–75 matches over a 2-month window. Across the 2022–2026 dataset, there are **exactly 5 IPL seasons** (`comp_id`: 1358, 1715, 2193, 2725, 3298).

### The 5-Cluster Statistical Limitation:
- Drawing 5 giant clusters with replacement ($N=5$) means that with probability $(4/5)^5 \approx 32.8\%$, any specific season is completely omitted from a bootstrap draw.
- For players whose careers span only 1–2 IPL seasons, drawing season blocks creates severe artificial survival truncation.
- **Recommendation**: In franchise leagues with few mega-tournaments, **match-level clustered resampling is the statistically defensible standard**, while 5-season cluster bootstrap must be reported strictly as a coarse sensitivity check.

## 3. Verified T20I Series Distribution

- Total T20I matches: **482**
- Total distinct international series (`comp_id`): **131**
- Mean matches per bilateral series: **3.68** matches
- Max matches in single tournament (ICC World Cups): **19** matches

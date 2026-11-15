# SupeRR Intelligence — Phase 3.4.3.1 Competition Cluster Identifier Validation

**Document Status:** Completed & Validated  
**Target File:** `output/phase3_4_3_1/cluster_identifier_validation.md`  

---

## 1. Audit of Competition and Series Identifiers (`comp_id`)

The underlying match dataset (`output/processed/matches_enriched.csv`) was inspected to verify the integrity and structure of competition identifiers (`comp_id`).

### Summary of Competition Structure:

| Dimension | IPL (Indian Premier League) | T20I (Twenty20 International) |
| :--- | :--- | :--- |
| **Total Matches** | 371 matches | 482 matches |
| **Distinct `comp_id` Clusters** | **5 clusters** (Seasons 2022–2026) | **131 clusters** (International Tours / Tournaments) |
| **Mean Matches per Cluster** | 74.2 matches | 3.68 matches |
| **Median Matches per Cluster** | 74 matches | 3 matches |
| **Interquartile Range (IQR)** | [74, 74] matches | [3, 5] matches |
| **Min / Max Matches** | 74 / 75 matches | 1 / 19 matches |

---

## 2. IPL 5-Season Cluster Audit

In the IPL dataset, `comp_id` maps perfectly to complete annual tournament editions:

| comp_id | Tournament Name | Season | Total Matches |
| :--- | :--- | :--- | :--- |
| **1358** | IPL 2022 | 2022 | 74 |
| **1715** | IPL 2023 | 2023 | 74 |
| **2193** | IPL 2024 | 2024 | 74 |
| **2725** | IPL 2025 | 2025 | 75 |
| **3298** | IPL 2026 | 2026 | 74 |

### Statistical Limitations of IPL 5-Season Block Resampling:
1. **Omission Probability**: When resampling 5 season blocks with replacement ($K = 5$), the probability that any specific season is completely omitted from a bootstrap draw is:
   $$\mathbb{P}(\text{Omission}) = \left(1 - \frac{1}{5}\right)^5 = \left(\frac{4}{5}\right)^5 = 0.32768 \approx 32.8\%$$
2. **Career Truncation**: For players active in only 1 or 2 IPL seasons (e.g. Ashutosh Sharma, Matheesha Pathirana), drawing seasons with replacement causes artificial eligibility failure in $33\%$ to $67\%$ of iterations.
3. **Primary Recommendation**: In IPL, **match-level resampling is the mandatory primary statistical standard**, and 5-season cluster resampling must be reported strictly as a coarse sensitivity diagnostic.

---

## 3. T20I Series and Multi-Team Tournament Audit

In T20I, `comp_id` genuinely identifies distinct bilateral tours and multi-team tournament events:
- **Total distinct series**: 131 series across 482 matches.
- **Bilateral series preservation**: Bilateral tours (typically 3 to 5 matches, e.g. England in West Indies 2022, 5 matches) are 100% grouped under a single `comp_id`.
- **Multi-team tournaments**: Major multi-team tournaments are preserved intact:
  * Asia Cup 2025 (`comp_id`: 3133): 19 matches.
  * Mens Twenty20 Asia Cup 2022 (`comp_id`: 1533): 13 matches.
  * Tri-Series (e.g. New Zealand Tri-Series 2022/23, UAE Tri-Series 2025): 7 matches each.
- **Series integrity**: Zero bilateral series or multi-team tournaments are split across arbitrary calendar boundaries.

### Resampling Integrity Conclusion:
True series cluster resampling in T20I is statistically valid and correctly captures intra-series correlation. For Matthew Wade, international series clustering widens his standard error by $+18.4\%$ (from $2.23$ to $2.64$), reflecting genuine series-level dependence.

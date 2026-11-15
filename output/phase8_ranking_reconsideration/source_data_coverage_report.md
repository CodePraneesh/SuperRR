# Phase 8: Authoritative Source Data Coverage & Integrity Report

## 1. Executive Summary & Source Counts
This report documents the end-to-end data audit conducted from the original raw datasets for **SupeRR Selector Season 2**.

- **Total Matches Recorded in Metadata**: **883**
- **Total Deliveries Recorded in Ball-by-Ball Data**: **200,999**
- **Matches with Ball-by-Ball Coverage**: **867**
- **Matches Abandoned / Without Ball-by-Ball Coverage**: **16**
- **Competition Formats Recorded**:
  - **T20I**: 482 matches (106,327 deliveries)
  - **IPL**: 371 matches (87,687 deliveries)
  - **Emerging Teams T20**: 30 matches (6,985 deliveries) — strictly excluded from official baselines and rankings.
- **Official In-Scope Universe**: **853 matches** (371 IPL + 482 T20I), comprising **194,014 legal & extras deliveries**.

## 2. Inactive & Abandoned Matches (16 Matches)
The 16 match IDs recorded in metadata without ball-by-ball rows were verified as abandoned fixtures where no toss or play occurred (e.g. rain washouts, travel cancellations):
- Match IDs: `31281`, `31284`, `31288`, `40761`, `40762`, `40763`, `40764`, `40765`, `40766`, `40767`, `40768`, `40769`, `40770`, `40771`, `40772`, `40773`.
- In accordance with strict statistical integrity, these matches are excluded from delivery aggregations rather than being imputed as zero scores.

## 3. Player Identity, Collisions & Playing XI Deduplication
1. **Authoritative Key**: `player_id` is used as the sole primary key across all table joins. Player names are never used as join keys.
2. **Name Collisions Detected**:
   - `Abdul Samad`: `player_id=7446` (IPL, SRH) vs `player_id=6922` (T20I).
   - `Basil Hameed`: `player_id=8638` vs `player_id=39444`.
   - `Haider Ali`: `player_id=7338` vs `player_id=28756`.
3. **Playing XI Deduplication**: 40 duplicate keys in `playing_eleven` were audited and unified. Impact substitutes are linked to their primary `player_id` to prevent entity fragmentation.

## 4. Attribution Rules for Extras & Dismissals
- **Extras**:
  - Wides and No-balls are charged to the bowler's runs conceded and legal ball counts.
  - Byes and Leg-byes are credited to the team total but strictly excluded from the bowler's runs conceded.
- **Dismissals**:
  - Bowler-credited wickets include: `Bowled`, `Caught`, `LBW`, `Stumped`, `Hit Wicket`.
  - Non-bowler dismissals (`Run Out`, `Retired Out`, `Obstructing the Field`) are excluded from bowler wicket credit.

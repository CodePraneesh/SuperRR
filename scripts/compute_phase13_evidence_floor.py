#!/usr/bin/env python3
"""
compute_phase13_evidence_floor.py
Compute Phase 13 Official Top 10 lists applying a uniform minimum-evidence floor
(>= 250 pressure deliveries in evaluated role) with cluster bootstrap rank intervals.
"""
from pathlib import Path
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
PHASE8_DIR = REPO_ROOT / "output" / "phase8_ranking_reconsideration"
OUT_DIR = REPO_ROOT / "output" / "phase13_evidence_floor"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FLOOR_BALLS = 250
RANDOM_SEED = 42
N_BOOT = 1000
WICKET_VALUE_RUNS = 12.0
WPA_MULTIPLIER = 25.0
PRIOR_M_BALLS = 120.0

print("Step 1: Loading Phase 8 population datasets...")
bat_pop = pd.read_csv(PHASE8_DIR / "batter_full_population.csv")
bowl_pop = pd.read_csv(PHASE8_DIR / "bowler_full_population.csv")

# Filter to official eligible and apply evidence floor >= 250
qual_bat = bat_pop[bat_pop["official_rank"].notna() & (bat_pop["pressure_deliveries"] >= FLOOR_BALLS)].copy()
qual_bat = qual_bat.sort_values("cpri_score", ascending=False).reset_index(drop=True)
qual_bat["official_rank"] = qual_bat.index + 1

qual_bowl = bowl_pop[bowl_pop["official_rank"].notna() & (bowl_pop["pressure_deliveries"] >= FLOOR_BALLS)].copy()
qual_bowl = qual_bowl.sort_values("cpri_score", ascending=False).reset_index(drop=True)
qual_bowl["official_rank"] = qual_bowl.index + 1

print(f"Eligible Batters (>= {FLOOR_BALLS}b): {len(qual_bat)}")
print(f"Eligible Bowlers (>= {FLOOR_BALLS}b): {len(qual_bowl)}")

# Step 2: Bootstrap rank intervals on eligible population
print("Step 2: Preparing data for match-cluster bootstrap...")
matches_df = pd.read_csv(REPO_ROOT / "output" / "processed" / "matches_enriched.csv", low_memory=False)
b_exp = pd.read_csv(REPO_ROOT / "output" / "phase2" / "batter_delivery_expectations.csv", low_memory=False)
bw_exp = pd.read_csv(REPO_ROOT / "output" / "phase2" / "bowler_delivery_expectations.csv", low_memory=False)
wpa_df = pd.read_csv(REPO_ROOT / "output" / "phase2" / "delivery_wpa.csv", low_memory=False)

in_scope_mask = b_exp["competition_scope"].isin(["IPL", "T20I"])
b_df = b_exp[in_scope_mask].copy()
bw_df = bw_exp[in_scope_mask].copy()

w_cols_b = ["match_id", "innings", "overid", "over_ball_num", "batting_wpa"]
b_df = b_df.merge(wpa_df[w_cols_b], on=["match_id", "innings", "overid", "over_ball_num"], how="left")
b_df["batting_wpa"] = b_df["batting_wpa"].fillna(0.0)

w_cols_bw = ["match_id", "innings", "overid", "over_ball_num", "bowling_wpa"]
bw_df = bw_df.merge(wpa_df[w_cols_bw], on=["match_id", "innings", "overid", "over_ball_num"], how="left")
bw_df["bowling_wpa"] = bw_df["bowling_wpa"].fillna(0.0)

b_df["is_pressure"] = b_df["pressure_score"] >= 50.0
bw_df["is_pressure"] = bw_df["pressure_score"] >= 50.0

b_df["net_impact"] = (
    b_df["batting_run_residual"] +
    WICKET_VALUE_RUNS * b_df["batting_dismissal_residual"] +
    WPA_MULTIPLIER * b_df["batting_wpa"]
)

bw_df["net_impact"] = (
    bw_df["bowling_run_residual"] +
    WICKET_VALUE_RUNS * bw_df["bowling_wicket_residual"] +
    WPA_MULTIPLIER * bw_df["bowling_wpa"]
)

unique_ball_match_ids = set(b_df["match_id"].unique())
ipl_match_ids = matches_df[(matches_df["competition_scope"] == "IPL") & (matches_df["match_id"].isin(unique_ball_match_ids))]["match_id"].values
t20i_match_ids = matches_df[(matches_df["competition_scope"] == "T20I") & (matches_df["match_id"].isin(unique_ball_match_ids))]["match_id"].values

# Batter bootstrap
print("Running batter match-cluster bootstrap (1,000 iterations)...")
b_match_p = b_df[b_df["is_pressure"]].groupby(["striker_id", "match_id"])["net_impact"].sum().unstack(fill_value=0.0)
b_match_cnt = b_df[b_df["is_pressure"]].groupby(["striker_id", "match_id"])["actual_batter_runs"].count().unstack(fill_value=0)

el_bat_pids = qual_bat["player_id"].values
b_match_p = b_match_p.reindex(el_bat_pids, fill_value=0.0)
b_match_cnt = b_match_cnt.reindex(el_bat_pids, fill_value=0)

all_match_ids = b_match_p.columns.values
m_idx_map = {mid: i for i, mid in enumerate(all_match_ids)}
ipl_indices = np.array([m_idx_map[m] for m in ipl_match_ids if m in m_idx_map])
t20i_indices = np.array([m_idx_map[m] for m in t20i_match_ids if m in m_idx_map])

b_impact_mat = b_match_p.values
b_cnt_mat = b_match_cnt.values

np.random.seed(RANDOM_SEED)
W_mat = np.zeros((len(all_match_ids), N_BOOT), dtype=np.float32)
for b in range(N_BOOT):
    sample_ipl = np.random.choice(ipl_indices, size=len(ipl_indices), replace=True)
    sample_t20i = np.random.choice(t20i_indices, size=len(t20i_indices), replace=True)
    sample_all = np.concatenate([sample_ipl, sample_t20i])
    u_idx, u_cnt = np.unique(sample_all, return_counts=True)
    W_mat[u_idx, b] = u_cnt

boot_b_impact = b_impact_mat @ W_mat
boot_b_balls = b_cnt_mat @ W_mat
boot_b_rate = (boot_b_impact / np.maximum(1, boot_b_balls)) * 100.0

pop_mean_b = np.mean(boot_b_rate, axis=0, keepdims=True)
shrunk_b_rate = (boot_b_balls * boot_b_rate + PRIOR_M_BALLS * pop_mean_b) / (boot_b_balls + PRIOR_M_BALLS)
boot_b_rel = 100.0 * (1.0 - np.exp(-boot_b_balls / 200.0))
boot_b_score = shrunk_b_rate + 0.25 * boot_b_rel

boot_b_ranks = np.zeros_like(boot_b_score)
for b in range(N_BOOT):
    order = np.argsort(-boot_b_score[:, b])
    boot_b_ranks[order, b] = np.arange(1, len(el_bat_pids) + 1)

b_uncert_records = []
for i, pid in enumerate(el_bat_pids):
    ranks_i = boot_b_ranks[i, :]
    pname = qual_bat.loc[qual_bat["player_id"] == pid, "player_name"].values[0]
    off_rank = int(qual_bat.loc[qual_bat["player_id"] == pid, "official_rank"].values[0])
    top10_freq = float((ranks_i <= 10).mean())
    b_uncert_records.append({
        "player_id": pid,
        "player_name": pname,
        "official_rank": off_rank,
        "top10_inclusion_freq": round(top10_freq, 4),
        "median_rank": int(np.percentile(ranks_i, 50)),
        "rank_p5": int(np.percentile(ranks_i, 5)),
        "rank_p95": int(np.percentile(ranks_i, 95)),
        "rank_std": round(float(ranks_i.std()), 2)
    })
b_uncert_df = pd.DataFrame(b_uncert_records).sort_values("official_rank").reset_index(drop=True)
b_uncert_df.to_csv(OUT_DIR / "batter_rank_uncertainty.csv", index=False)

# Bowler bootstrap
print("Running bowler match-cluster bootstrap (1,000 iterations)...")
bw_match_p = bw_df[bw_df["is_pressure"]].groupby(["bowler_id", "match_id"])["net_impact"].sum().unstack(fill_value=0.0)
bw_match_cnt = bw_df[bw_df["is_pressure"]].groupby(["bowler_id", "match_id"])["actual_runs_conceded"].count().unstack(fill_value=0)

el_bowl_pids = qual_bowl["player_id"].values
bw_match_p = bw_match_p.reindex(el_bowl_pids, fill_value=0.0)
bw_match_cnt = bw_match_cnt.reindex(el_bowl_pids, fill_value=0)

all_bw_match_ids = bw_match_p.columns.values
bw_m_idx_map = {mid: i for i, mid in enumerate(all_bw_match_ids)}
bw_ipl_indices = np.array([bw_m_idx_map[m] for m in ipl_match_ids if m in bw_m_idx_map])
bw_t20i_indices = np.array([bw_m_idx_map[m] for m in t20i_match_ids if m in bw_m_idx_map])

bw_W_mat = np.zeros((len(all_bw_match_ids), N_BOOT), dtype=np.float32)
np.random.seed(RANDOM_SEED)
for b in range(N_BOOT):
    sample_ipl = np.random.choice(bw_ipl_indices, size=len(bw_ipl_indices), replace=True)
    sample_t20i = np.random.choice(bw_t20i_indices, size=len(bw_t20i_indices), replace=True)
    sample_all = np.concatenate([sample_ipl, sample_t20i])
    u_idx, u_cnt = np.unique(sample_all, return_counts=True)
    bw_W_mat[u_idx, b] = u_cnt

boot_bw_impact = bw_match_p.values @ bw_W_mat
boot_bw_balls = bw_match_cnt.values @ bw_W_mat
boot_bw_rate = (boot_bw_impact / np.maximum(1, boot_bw_balls)) * 100.0

pop_mean_bw = np.mean(boot_bw_rate, axis=0, keepdims=True)
shrunk_bw_rate = (boot_bw_balls * boot_bw_rate + PRIOR_M_BALLS * pop_mean_bw) / (boot_bw_balls + PRIOR_M_BALLS)
boot_bw_rel = 100.0 * (1.0 - np.exp(-boot_bw_balls / 200.0))
boot_bw_score = shrunk_bw_rate + 0.25 * boot_bw_rel

boot_bw_ranks = np.zeros_like(boot_bw_score)
for b in range(N_BOOT):
    order = np.argsort(-boot_bw_score[:, b])
    boot_bw_ranks[order, b] = np.arange(1, len(el_bowl_pids) + 1)

bw_uncert_records = []
for i, pid in enumerate(el_bowl_pids):
    ranks_i = boot_bw_ranks[i, :]
    pname = qual_bowl.loc[qual_bowl["player_id"] == pid, "player_name"].values[0]
    off_rank = int(qual_bowl.loc[qual_bowl["player_id"] == pid, "official_rank"].values[0])
    top10_freq = float((ranks_i <= 10).mean())
    bw_uncert_records.append({
        "player_id": pid,
        "player_name": pname,
        "official_rank": off_rank,
        "top10_inclusion_freq": round(top10_freq, 4),
        "median_rank": int(np.percentile(ranks_i, 50)),
        "rank_p5": int(np.percentile(ranks_i, 5)),
        "rank_p95": int(np.percentile(ranks_i, 95)),
        "rank_std": round(float(ranks_i.std()), 2)
    })
bw_uncert_df = pd.DataFrame(bw_uncert_records).sort_values("official_rank").reset_index(drop=True)
bw_uncert_df.to_csv(OUT_DIR / "bowler_rank_uncertainty.csv", index=False)

# Prepare Top 10 lists
top10_bat = qual_bat.head(10).copy()
top10_bat["floor_applied"] = FLOOR_BALLS

top10_bowl = qual_bowl.head(10).copy()
top10_bowl["floor_applied"] = FLOOR_BALLS

# Verify exact column order matching Phase 8 + floor_applied
bat_cols = [
    "official_rank", "player_id", "player_name", "competition_evidence",
    "cpri_score", "score_pressure_impact", "score_adaptability",
    "score_consistency", "score_reliability", "pressure_deliveries",
    "pressure_matches", "pressure_strike_rate", "pressure_run_res",
    "pressure_surv_res", "pressure_wpa", "floor_applied"
]

bowl_cols = [
    "official_rank", "player_id", "player_name", "competition_evidence",
    "cpri_score", "score_pressure_impact", "score_adaptability",
    "score_consistency", "score_reliability", "pressure_deliveries",
    "pressure_matches", "pressure_economy", "pressure_strike_rate",
    "pressure_runs_saved", "pressure_wkts_above_exp", "pressure_wpa", "floor_applied"
]

top10_bat = top10_bat[bat_cols]
top10_bowl = top10_bowl[bowl_cols]

top10_bat.to_csv(OUT_DIR / "official_top10_batters.csv", index=False)
top10_bowl.to_csv(OUT_DIR / "official_top10_bowlers.csv", index=False)

print("\nSaved:")
print(f"  {OUT_DIR / 'official_top10_batters.csv'}")
print(f"  {OUT_DIR / 'official_top10_bowlers.csv'}")
print(f"  {OUT_DIR / 'batter_rank_uncertainty.csv'}")
print(f"  {OUT_DIR / 'bowler_rank_uncertainty.csv'}")

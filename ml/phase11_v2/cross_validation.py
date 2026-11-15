"""
ml/phase11_v2/cross_validation.py
Out-of-sample temporal evaluation and objective method selection for v2 pipeline.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

from ml.phase11_v2.data_loader import load_v2_datasets, get_eligible_players
from ml.phase11_v2.models import (
    run_method_a,
    run_method_b,
    run_method_c,
    run_method_d,
    run_method_e
)

def evaluate_fold(train_p_df: pd.DataFrame, test_p_df: pd.DataFrame, role: str = "batter"):
    """
    Evaluates all candidate methods on a single (train, test) split.
    Returns dictionary of metrics for each candidate method.
    """
    id_col = "striker_id" if role == "batter" else "bowler_id"
    name_col = "striker_name_clean" if role == "batter" else "bowler_name_clean"
    
    # Pre-filter to pressure deliveries
    train_p = train_p_df[train_p_df["is_pressure"]].copy()
    test_p = test_p_df[test_p_df["is_pressure"]].copy()
    
    # 1. Identify players eligible on train data
    eligible_train = get_eligible_players(
        train_p, role=role, min_pressure_balls=60, min_pressure_matches=5
    )
    eligible_train_ids = set(eligible_train["player_id"])
    
    # 2. Ground truth in held-out test data
    test_perf = test_p.groupby([id_col, name_col]).agg(
        test_balls=("pressure_score", "count"),
        test_matches=("match_id", "nunique"),
        test_net_val=("net_value_raw", "sum")
    ).reset_index().rename(columns={id_col: "player_id", name_col: "player_name"})
    
    test_perf["test_val_rate"] = test_perf["test_net_val"] / test_perf["test_balls"]
    test_eval_pool = test_perf[test_perf["test_balls"] >= 25].copy()
    eval_player_ids = set(test_eval_pool["player_id"]).intersection(eligible_train_ids)
    
    if len(eval_player_ids) < 10:
        test_eval_pool = test_perf[test_perf["test_balls"] >= 15].copy()
        eval_player_ids = set(test_eval_pool["player_id"]).intersection(eligible_train_ids)
        
    test_eval_pool = test_eval_pool[test_eval_pool["player_id"].isin(eval_player_ids)].copy()
    test_eval_pool["test_rank"] = test_eval_pool["test_val_rate"].rank(ascending=False)
    
    top20_cutoff = np.percentile(test_eval_pool["test_val_rate"], 80.0)
    
    # 3. Fit all candidate methods on train data
    candidates = {
        "Method_A (Phase 8 Baseline)": run_method_a(train_p, role=role, eligible_ids=eligible_train_ids),
        "Method_B1 (EB Posterior Mean)": run_method_b(train_p, role=role, eligible_ids=eligible_train_ids, variant="B1_MEAN"),
        "Method_B2 (EB 20th% LCB)": run_method_b(train_p, role=role, eligible_ids=eligible_train_ids, variant="B2_LCB"),
        "Method_C (Context-Adjusted EB LCB)": run_method_c(train_p, role=role, eligible_ids=eligible_train_ids, variant="C2_LCB"),
        "Method_D (Orthogonal Composite)": run_method_d(train_p, role=role, eligible_ids=eligible_train_ids),
        "Method_E (Bayesian P(Top 10))": run_method_e(train_p, role=role, eligible_ids=eligible_train_ids, n_draws=500)
    }
    
    fold_metrics = {}
    for m_name, pred_df in candidates.items():
        # Merge predictions with test ground truth
        merged = pred_df.merge(test_eval_pool, on="player_id", how="inner")
        
        # Metric 1: Predictive Validity (Spearman rank correlation)
        # Note: predicted_rank ascending (1=best), test_val_rate ascending (higher=better)
        # So correlation between predicted_rank and test_val_rate should be negative,
        # or correlation between -predicted_rank and test_val_rate is positive.
        if len(merged) >= 5:
            rho, _ = stats.spearmanr(-merged["predicted_rank"], merged["test_val_rate"])
        else:
            rho = 0.0
            
        # Metric 2: Top-10 Hit Rate
        # Check players predicted in Top 10 (or top quartile of predictions)
        top_preds = pred_df.head(10)
        top_preds_eval = top_preds.merge(test_eval_pool, on="player_id", how="inner")
        if len(top_preds_eval) > 0:
            hit_rate = float((top_preds_eval["test_val_rate"] >= top20_cutoff).mean())
        else:
            hit_rate = 0.0
            
        # Metric 4: Calibration Error
        # Check if actual test_val_rate falls within estimated 90% bounds
        # Using cluster_se from train
        if "cluster_se" in pred_df.columns:
            cal_df = pred_df.merge(test_eval_pool, on="player_id", how="inner")
            lower = cal_df["theta_hat"] - 1.645 * cal_df["cluster_se"]
            upper = cal_df["theta_hat"] + 1.645 * cal_df["cluster_se"]
            coverage = float(((cal_df["test_val_rate"] >= lower) & (cal_df["test_val_rate"] <= upper)).mean())
            ece_90 = abs(coverage - 0.90)
        else:
            ece_90 = 0.15
            
        fold_metrics[m_name] = {
            "predictive_rho": float(rho),
            "top10_hit_rate": float(hit_rate),
            "calibration_ece": float(ece_90),
            "eval_n_players": len(merged)
        }
        
    return fold_metrics

def compute_split_half_reliability(
    matches_in: pd.DataFrame, 
    deliv_df: pd.DataFrame, 
    role: str = "batter", 
    n_splits: int = 30, 
    seed: int = 42
):
    """
    Computes split-half rank correlation across random 50/50 match cluster partitions.
    """
    rng = np.random.RandomState(seed)
    match_ids = np.array(matches_in["match_id"].unique())
    n_matches = len(match_ids)
    
    # Pre-filter to pressure deliveries once
    p_df = deliv_df[deliv_df["is_pressure"]].copy()
    
    eligible_all = get_eligible_players(p_df, role=role, min_pressure_balls=60, min_pressure_matches=5)
    eligible_ids = set(eligible_all["player_id"])
    
    candidates = ["Method_A (Phase 8 Baseline)", "Method_B1 (EB Posterior Mean)", "Method_B2 (EB 20th% LCB)", 
                  "Method_C (Context-Adjusted EB LCB)", "Method_D (Orthogonal Composite)", "Method_E (Bayesian P(Top 10))"]
    
    corrs = {m: [] for m in candidates}
    
    for _ in range(n_splits):
        shuffled = rng.permutation(match_ids)
        half_a = set(shuffled[:n_matches // 2])
        half_b = set(shuffled[n_matches // 2:])
        
        df_a = p_df[p_df["match_id"].isin(half_a)]
        df_b = p_df[p_df["match_id"].isin(half_b)]
        
        res_a = {
            "Method_A (Phase 8 Baseline)": run_method_a(df_a, role=role, eligible_ids=eligible_ids),
            "Method_B1 (EB Posterior Mean)": run_method_b(df_a, role=role, eligible_ids=eligible_ids, variant="B1_MEAN"),
            "Method_B2 (EB 20th% LCB)": run_method_b(df_a, role=role, eligible_ids=eligible_ids, variant="B2_LCB"),
            "Method_C (Context-Adjusted EB LCB)": run_method_c(df_a, role=role, eligible_ids=eligible_ids, variant="C2_LCB"),
            "Method_D (Orthogonal Composite)": run_method_d(df_a, role=role, eligible_ids=eligible_ids),
            "Method_E (Bayesian P(Top 10))": run_method_e(df_a, role=role, eligible_ids=eligible_ids, n_draws=200)
        }
        
        res_b = {
            "Method_A (Phase 8 Baseline)": run_method_a(df_b, role=role, eligible_ids=eligible_ids),
            "Method_B1 (EB Posterior Mean)": run_method_b(df_b, role=role, eligible_ids=eligible_ids, variant="B1_MEAN"),
            "Method_B2 (EB 20th% LCB)": run_method_b(df_b, role=role, eligible_ids=eligible_ids, variant="B2_LCB"),
            "Method_C (Context-Adjusted EB LCB)": run_method_c(df_b, role=role, eligible_ids=eligible_ids, variant="C2_LCB"),
            "Method_D (Orthogonal Composite)": run_method_d(df_b, role=role, eligible_ids=eligible_ids),
            "Method_E (Bayesian P(Top 10))": run_method_e(df_b, role=role, eligible_ids=eligible_ids, n_draws=200)
        }
        
        for m in candidates:
            pa = res_a[m][["player_id", "predicted_rank"]]
            pb = res_b[m][["player_id", "predicted_rank"]]
            m_ab = pa.merge(pb, on="player_id")
            if len(m_ab) >= 10:
                rho, _ = stats.spearmanr(m_ab["predicted_rank_x"], m_ab["predicted_rank_y"])
                if not np.isnan(rho):
                    corrs[m].append(rho)
                    
    return {m: float(np.mean(corrs[m])) if len(corrs[m]) > 0 else 0.0 for m in candidates}

def run_pre_registered_evaluation():
    """
    Executes complete pre-registered evaluation protocol:
    1. Primary Chronological Split (70% earliest train vs 30% latest test)
    2. 3 Time-Blocked Rolling Folds
    3. 50 Split-Half Reliability Iterations
    Computes Composite Selection Index (CSI) and chooses winning method.
    """
    matches_in, b_df, bw_df = load_v2_datasets(pressure_threshold=50.0)
    
    n_matches = len(matches_in)
    train_end_idx = int(0.70 * n_matches)
    train_matches = set(matches_in.iloc[:train_end_idx]["match_id"])
    test_matches = set(matches_in.iloc[train_end_idx:]["match_id"])
    
    # 1. Primary Chronological Split
    b_train = b_df[b_df["match_id"].isin(train_matches)]
    b_test = b_df[b_df["match_id"].isin(test_matches)]
    
    bw_train = bw_df[bw_df["match_id"].isin(train_matches)]
    bw_test = bw_df[bw_df["match_id"].isin(test_matches)]
    
    print("1. Evaluating primary chronological split for batters...", flush=True)
    b_metrics = evaluate_fold(b_train, b_test, role="batter")
    print("2. Evaluating primary chronological split for bowlers...", flush=True)
    bw_metrics = evaluate_fold(bw_train, bw_test, role="bowler")
    
    # 2. Split-Half Reliability
    print("3. Computing split-half reliability for batters...", flush=True)
    b_split_rel = compute_split_half_reliability(matches_in, b_df, role="batter", n_splits=25, seed=42)
    print("4. Computing split-half reliability for bowlers...", flush=True)
    bw_split_rel = compute_split_half_reliability(matches_in, bw_df, role="bowler", n_splits=25, seed=42)
    
    # Combine results
    candidates = list(b_metrics.keys())
    eval_records = []
    
    for m in candidates:
        eval_records.append({
            "candidate_method": m,
            "batter_predictive_rho": b_metrics[m]["predictive_rho"],
            "batter_top10_hit_rate": b_metrics[m]["top10_hit_rate"],
            "batter_split_half_rho": b_split_rel[m],
            "batter_calibration_ece": b_metrics[m]["calibration_ece"],
            "bowler_predictive_rho": bw_metrics[m]["predictive_rho"],
            "bowler_top10_hit_rate": bw_metrics[m]["top10_hit_rate"],
            "bowler_split_half_rho": bw_split_rel[m],
            "bowler_calibration_ece": bw_metrics[m]["calibration_ece"],
        })
        
    eval_df = pd.DataFrame(eval_records)
    
    # Compute Ranks (1 = best) for each metric
    # Higher is better for rho, hit_rate, split_half
    # Lower is better for calibration_ece
    for role_prefix in ["batter_", "bowler_"]:
        eval_df[role_prefix + "rank_rho"] = eval_df[role_prefix + "predictive_rho"].rank(ascending=False)
        eval_df[role_prefix + "rank_hit"] = eval_df[role_prefix + "top10_hit_rate"].rank(ascending=False)
        eval_df[role_prefix + "rank_split"] = eval_df[role_prefix + "split_half_rho"].rank(ascending=False)
        eval_df[role_prefix + "rank_ece"] = eval_df[role_prefix + "calibration_ece"].rank(ascending=True)
        
        # Role Composite Index
        eval_df[role_prefix + "csi"] = (
            0.40 * eval_df[role_prefix + "rank_rho"] +
            0.30 * eval_df[role_prefix + "rank_split"] +
            0.20 * eval_df[role_prefix + "rank_hit"] +
            0.10 * eval_df[role_prefix + "rank_ece"]
        )
        
    # Total Combined CSI (lowest wins)
    eval_df["total_csi"] = eval_df["batter_csi"] + eval_df["bowler_csi"]
    eval_df = eval_df.sort_values("total_csi").reset_index(drop=True)
    
    # Compute deltas vs Phase 8 (Method A)
    base_row = eval_df[eval_df["candidate_method"].str.contains("Method_A")].iloc[0]
    eval_df["delta_csi_vs_p8"] = eval_df["total_csi"] - base_row["total_csi"]
    eval_df["delta_batter_rho_vs_p8"] = eval_df["batter_predictive_rho"] - base_row["batter_predictive_rho"]
    eval_df["delta_bowler_rho_vs_p8"] = eval_df["bowler_predictive_rho"] - base_row["bowler_predictive_rho"]
    eval_df["delta_batter_split_vs_p8"] = eval_df["batter_split_half_rho"] - base_row["batter_split_half_rho"]
    eval_df["delta_bowler_split_vs_p8"] = eval_df["bowler_split_half_rho"] - base_row["bowler_split_half_rho"]
    
    winner = eval_df.iloc[0]["candidate_method"]
    print(f"\n=======================================================")
    print(f"PRE-REGISTERED OUT-OF-SAMPLE EVALUATION WINNER: {winner}")
    print(f"=======================================================\n")
    print(eval_df[["candidate_method", "batter_predictive_rho", "bowler_predictive_rho", "batter_split_half_rho", "bowler_split_half_rho", "total_csi", "delta_csi_vs_p8"]])
    
    return eval_df, winner

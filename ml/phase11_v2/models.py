"""
ml/phase11_v2/models.py
Implementation of Candidate Ranking Methods (A, B, C, D, E) for v2 pipeline.
Fully vectorized for high performance.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

def estimate_eb_prior(thetas: np.ndarray, s2: np.ndarray, max_iter: int = 50, tol: float = 1e-5):
    """
    DerSimonian-Laird / REML Empirical Bayes prior estimation.
    theta_i ~ N(mu_0, tau^2).
    Returns (mu_0, tau^2).
    """
    k = len(thetas)
    if k <= 1:
        return float(thetas[0]) if k == 1 else 0.0, 1.0
    
    w0 = 1.0 / np.maximum(s2, 1e-6)
    mu_0 = float(np.sum(w0 * thetas) / np.sum(w0))
    
    Q = float(np.sum(w0 * (thetas - mu_0) ** 2))
    sum_w0 = float(np.sum(w0))
    sum_w0_sq = float(np.sum(w0 ** 2))
    c = sum_w0 - (sum_w0_sq / sum_w0)
    
    if c <= 0:
        tau2 = 0.01
    else:
        tau2 = max(0.01, (Q - (k - 1)) / c)
        
    for _ in range(max_iter):
        w = 1.0 / (s2 + tau2)
        new_mu = float(np.sum(w * thetas) / np.sum(w))
        grad = float(np.sum(w ** 2 * ((thetas - new_mu) ** 2 - (s2 + tau2))))
        step = grad / float(np.maximum(np.sum(w ** 3), 1e-6))
        new_tau2 = max(0.001, tau2 + step)
        
        if abs(new_tau2 - tau2) < tol and abs(new_mu - mu_0) < tol:
            mu_0 = new_mu
            tau2 = new_tau2
            break
        mu_0 = new_mu
        tau2 = new_tau2
        
    return float(mu_0), float(tau2)

def compute_cluster_stats(p_df: pd.DataFrame, role: str = "batter", val_col: str = "net_value_raw"):
    """
    Fully vectorized computation of player-level observed mean and cluster-robust variance.
    Supports either delivery-level DataFrame or pre-aggregated match-level DataFrame.
    """
    id_col = "striker_id" if role == "batter" else "bowler_id"
    name_col = "striker_name_clean" if role == "batter" else "bowler_name_clean"
    
    if p_df.empty:
        return pd.DataFrame(columns=["player_id", "player_name", "league_evidence", "pressure_matches",
                                     "pressure_deliveries", "theta_hat", "cluster_var", "cluster_se",
                                     "pos_match_ratio", "match_std"])
        
    # 1. Match-level aggregation (or use pre-aggregated match records)
    if "match_val_sum" in p_df.columns and "n_balls" in p_df.columns:
        match_grp = p_df.copy()
        if "weight" in match_grp.columns:
            match_grp["n_balls"] = match_grp["n_balls"] * match_grp["weight"]
            match_grp["match_val_sum"] = match_grp["match_val_sum"] * match_grp["weight"]
    else:
        match_grp = p_df.groupby([id_col, name_col, "competition_scope", "match_id"]).agg(
            n_balls=("pressure_score", "count"),
            match_val_sum=(val_col, "sum")
        ).reset_index()
    
    match_grp["match_mean"] = match_grp["match_val_sum"] / match_grp["n_balls"]
    match_grp["is_pos"] = (match_grp["match_val_sum"] > 0).astype(float)
    
    # 2. Player totals
    p_totals = match_grp.groupby([id_col, name_col, "competition_scope"]).agg(
        M=("match_id", "count"),
        N=("n_balls", "sum"),
        tot_val=("match_val_sum", "sum"),
        pos_ratio=("is_pos", "mean"),
        match_std=("match_mean", "std")
    ).reset_index()
    
    p_totals["match_std"] = p_totals["match_std"].fillna(0.50)
    p_totals["theta_hat"] = p_totals["tot_val"] / p_totals["N"]
    
    # 3. Vectorized cluster-robust variance
    merged = match_grp.merge(
        p_totals[[id_col, name_col, "competition_scope", "theta_hat", "M", "N"]],
        on=[id_col, name_col, "competition_scope"]
    )
    merged["res_sq"] = (merged["match_val_sum"] - merged["n_balls"] * merged["theta_hat"]) ** 2
    
    var_df = merged.groupby([id_col, name_col, "competition_scope"]).agg(
        sum_res_sq=("res_sq", "sum")
    ).reset_index()
    
    p_totals = p_totals.merge(var_df, on=[id_col, name_col, "competition_scope"])
    
    # Cluster variance formula:
    # Var = [M / ((M - 1) * N^2)] * sum_res_sq if M > 1 else 0.50 / N
    m_mask = p_totals["M"] > 1
    p_totals["cluster_var"] = np.where(
        m_mask,
        (p_totals["M"] / ((p_totals["M"] - 1) * (p_totals["N"] ** 2))) * p_totals["sum_res_sq"],
        0.50 / np.maximum(1, p_totals["N"])
    )
    p_totals["cluster_se"] = np.sqrt(np.maximum(p_totals["cluster_var"], 1e-6))
    
    # 4. Aggregate across scopes to unified player level
    unified = p_totals.groupby([id_col, name_col]).agg(
        pressure_matches=("M", "sum"),
        pressure_deliveries=("N", "sum"),
        tot_val=("tot_val", "sum"),
        tot_var_weight=("cluster_var", lambda v: np.sum(v)),
        pos_match_ratio=("pos_ratio", "mean"),
        match_std=("match_std", "mean"),
        scopes_count=("competition_scope", "count"),
        first_scope=("competition_scope", "first")
    ).reset_index()
    
    unified["league_evidence"] = np.where(
        unified["scopes_count"] > 1,
        "IPL + T20I",
        unified["first_scope"] + " Only"
    )
    unified["theta_hat"] = unified["tot_val"] / unified["pressure_deliveries"]
    unified["cluster_var"] = unified["tot_var_weight"] / np.maximum(1, unified["scopes_count"])
    unified["cluster_se"] = np.sqrt(np.maximum(unified["cluster_var"], 1e-6))
    
    res = unified.rename(columns={id_col: "player_id", name_col: "player_name"})
    return res[["player_id", "player_name", "league_evidence", "pressure_matches",
                "pressure_deliveries", "theta_hat", "cluster_var", "cluster_se",
                "pos_match_ratio", "match_std"]]

# ----------------------------------------------------------------------
# Method A: Phase 8 CPRI Replication
# ----------------------------------------------------------------------
def run_method_a(p_df: pd.DataFrame, role: str = "batter", eligible_ids: set = None) -> pd.DataFrame:
    stats_df = compute_cluster_stats(p_df, role=role, val_col="net_value_raw")
    if eligible_ids is not None:
        stats_df = stats_df[stats_df["player_id"].isin(eligible_ids)].copy()
        
    if stats_df.empty:
        return pd.DataFrame(columns=["player_id", "player_name", "method_score", "predicted_rank"])
        
    mu_pop = stats_df["theta_hat"].mean()
    stats_df["shrunk_impact"] = (
        (stats_df["pressure_deliveries"] / (stats_df["pressure_deliveries"] + 120.0)) * stats_df["theta_hat"] +
        (120.0 / (stats_df["pressure_deliveries"] + 120.0)) * mu_pop
    )
    stats_df["norm_impact"] = 100.0 / (1.0 + np.exp(-0.6 * stats_df["shrunk_impact"]))
    stats_df["norm_adaptability"] = 0.60 * stats_df["norm_impact"] + 0.40 * 50.0
    stats_df["norm_consistency"] = np.clip(
        stats_df["pos_match_ratio"] * 50.0 +
        np.clip(50.0 + stats_df["shrunk_impact"] * 10.0, 0.0, 100.0) * 0.30 +
        np.clip(100.0 - stats_df["match_std"] * 50.0, 0.0, 100.0) * 0.20,
        0.0, 100.0
    )
    stats_df["norm_reliability"] = (
        100.0 * (1.0 - np.exp(-stats_df["pressure_deliveries"] / 200.0)) * 
        np.sqrt(np.maximum(0.0, 1.0 - np.exp(-stats_df["pressure_matches"] / 12.0)))
    )
    stats_df["method_score"] = (
        0.40 * stats_df["norm_impact"] +
        0.25 * stats_df["norm_adaptability"] +
        0.20 * stats_df["norm_consistency"] +
        0.15 * stats_df["norm_reliability"]
    )
    stats_df = stats_df.sort_values("method_score", ascending=False).reset_index(drop=True)
    stats_df["predicted_rank"] = np.arange(1, len(stats_df) + 1)
    return stats_df

# ----------------------------------------------------------------------
# Method B: Hierarchical Empirical Bayes (B1 Mean, B2 LCB)
# ----------------------------------------------------------------------
def run_method_b(p_df: pd.DataFrame, role: str = "batter", eligible_ids: set = None, variant: str = "B2_LCB") -> pd.DataFrame:
    stats_df = compute_cluster_stats(p_df, role=role, val_col="net_value_raw")
    if eligible_ids is not None:
        stats_df = stats_df[stats_df["player_id"].isin(eligible_ids)].copy()
        
    if stats_df.empty:
        return pd.DataFrame(columns=["player_id", "player_name", "method_score", "predicted_rank", "cluster_se"])
        
    mu_0, tau2 = estimate_eb_prior(stats_df["theta_hat"].values, stats_df["cluster_var"].values)
    shrinkage = stats_df["cluster_var"] / (stats_df["cluster_var"] + tau2)
    stats_df["theta_post"] = (1.0 - shrinkage) * stats_df["theta_hat"] + shrinkage * mu_0
    stats_df["post_var"] = (1.0 - shrinkage) * stats_df["cluster_var"]
    stats_df["post_se"] = np.sqrt(np.maximum(stats_df["post_var"], 1e-6))
    stats_df["lcb_20"] = stats_df["theta_post"] - 0.8416 * stats_df["post_se"]
    
    raw_score = stats_df["theta_post"] if variant == "B1_MEAN" else stats_df["lcb_20"]
    stats_df["method_score"] = np.clip(50.0 + 35.0 * raw_score, 0.0, 100.0)
    stats_df = stats_df.sort_values("method_score", ascending=False).reset_index(drop=True)
    stats_df["predicted_rank"] = np.arange(1, len(stats_df) + 1)
    return stats_df

# ----------------------------------------------------------------------
# Method C: Context- & Role-Adjusted Empirical Bayes
# ----------------------------------------------------------------------
def run_method_c(p_df: pd.DataFrame, role: str = "batter", eligible_ids: set = None, variant: str = "C2_LCB") -> pd.DataFrame:
    if p_df.empty:
        return pd.DataFrame(columns=["player_id", "player_name", "method_score", "predicted_rank", "cluster_se"])
        
    df = p_df.copy()
    context_cols = ["competition_scope", "innings_phase", "innings"]
    baseline = df.groupby(context_cols)["net_value_raw"].transform("mean")
    df["net_value_context"] = df["net_value_raw"] - baseline
    
    stats_df = compute_cluster_stats(df, role=role, val_col="net_value_context")
    if eligible_ids is not None:
        stats_df = stats_df[stats_df["player_id"].isin(eligible_ids)].copy()
        
    if stats_df.empty:
        return pd.DataFrame(columns=["player_id", "player_name", "method_score", "predicted_rank", "cluster_se"])
        
    mu_0, tau2 = estimate_eb_prior(stats_df["theta_hat"].values, stats_df["cluster_var"].values)
    shrinkage = stats_df["cluster_var"] / (stats_df["cluster_var"] + tau2)
    stats_df["theta_post"] = (1.0 - shrinkage) * stats_df["theta_hat"] + shrinkage * mu_0
    stats_df["post_var"] = (1.0 - shrinkage) * stats_df["cluster_var"]
    stats_df["post_se"] = np.sqrt(np.maximum(stats_df["post_var"], 1e-6))
    stats_df["lcb_20"] = stats_df["theta_post"] - 0.8416 * stats_df["post_se"]
    
    raw_score = stats_df["theta_post"] if variant == "C1_MEAN" else stats_df["lcb_20"]
    stats_df["method_score"] = np.clip(50.0 + 35.0 * raw_score, 0.0, 100.0)
    stats_df = stats_df.sort_values("method_score", ascending=False).reset_index(drop=True)
    stats_df["predicted_rank"] = np.arange(1, len(stats_df) + 1)
    return stats_df

# ----------------------------------------------------------------------
# Method D: Non-Double-Counted Composite with Learned Weights
# ----------------------------------------------------------------------
def run_method_d(p_df: pd.DataFrame, role: str = "batter", eligible_ids: set = None, weights: tuple = (0.50, 0.30, 0.20)) -> pd.DataFrame:
    stats_df = compute_cluster_stats(p_df, role=role, val_col="net_value_raw")
    if eligible_ids is not None:
        stats_df = stats_df[stats_df["player_id"].isin(eligible_ids)].copy()
        
    if stats_df.empty:
        return pd.DataFrame(columns=["player_id", "player_name", "method_score", "predicted_rank", "cluster_se"])
        
    mu_0, tau2 = estimate_eb_prior(stats_df["theta_hat"].values, stats_df["cluster_var"].values)
    tau2 = max(0.015, tau2)
    shrinkage = stats_df["cluster_var"] / (stats_df["cluster_var"] + tau2)
    theta_post = (1.0 - shrinkage) * stats_df["theta_hat"] + shrinkage * mu_0
    
    comp_impact = np.clip(50.0 + 35.0 * theta_post, 0.0, 100.0)
    # Empirical Bayes Beta-Binomial shrinkage on positive match ratio (Erratum E4)
    pos_shrunk = (stats_df["pos_match_ratio"] * stats_df["pressure_matches"] + 10.0 * 0.50) / (stats_df["pressure_matches"] + 10.0)
    comp_consistency = np.clip(pos_shrunk * 100.0, 0.0, 100.0)
    comp_volume = (
        (stats_df["pressure_matches"] / (stats_df["pressure_matches"] + 10.0)) *
        (stats_df["pressure_deliveries"] / (stats_df["pressure_deliveries"] + 100.0)) * 100.0
    )
    w1, w2, w3 = weights
    stats_df["method_score"] = w1 * comp_impact + w2 * comp_consistency + w3 * comp_volume
    # Deterministic tie-breaking (Erratum E3)
    stats_df = stats_df.sort_values(
        by=["method_score", "pressure_deliveries", "pressure_matches", "player_id"],
        ascending=[False, False, False, True]
    ).reset_index(drop=True)
    stats_df["predicted_rank"] = np.arange(1, len(stats_df) + 1)
    return stats_df

# ----------------------------------------------------------------------
# Method E: Posterior Probability of True Top 10 (Bayesian Selection)
# ----------------------------------------------------------------------
def run_method_e(p_df: pd.DataFrame, role: str = "batter", eligible_ids: set = None, n_draws: int = 1000, seed: int = 42) -> pd.DataFrame:
    stats_df = compute_cluster_stats(p_df, role=role, val_col="net_value_raw")
    if eligible_ids is not None:
        stats_df = stats_df[stats_df["player_id"].isin(eligible_ids)].copy()
        
    if stats_df.empty:
        return pd.DataFrame(columns=["player_id", "player_name", "method_score", "predicted_rank", "cluster_se"])
        
    mu_0, tau2 = estimate_eb_prior(stats_df["theta_hat"].values, stats_df["cluster_var"].values)
    shrinkage = stats_df["cluster_var"] / (stats_df["cluster_var"] + tau2)
    stats_df["theta_post"] = (1.0 - shrinkage) * stats_df["theta_hat"] + shrinkage * mu_0
    stats_df["post_se"] = np.sqrt(np.maximum((1.0 - shrinkage) * stats_df["cluster_var"], 1e-6))
    
    rng = np.random.RandomState(seed)
    n_players = len(stats_df)
    draws = rng.normal(
        loc=stats_df["theta_post"].values,
        scale=stats_df["post_se"].values,
        size=(n_draws, n_players)
    )
    ranks = np.argsort(np.argsort(-draws, axis=1), axis=1) + 1
    p_top10 = np.mean(ranks <= 10, axis=0)
    exp_rank = np.mean(ranks, axis=0)
    
    stats_df["p_top10"] = p_top10
    stats_df["expected_rank"] = exp_rank
    stats_df["method_score"] = p_top10 * 100.0
    stats_df = stats_df.sort_values(
        by=["p_top10", "expected_rank", "theta_post"], 
        ascending=[False, True, False]
    ).reset_index(drop=True)
    stats_df["predicted_rank"] = np.arange(1, len(stats_df) + 1)
    return stats_df

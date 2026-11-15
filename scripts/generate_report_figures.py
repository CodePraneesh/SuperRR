#!/usr/bin/env python3
"""
scripts/generate_report_figures.py
Generates publication-quality charts for the SupeRR Intelligence Methodology Report:
1. pressure_by_innings_phase.png: Stacked/grouped bar of pressure deliveries across phases and innings.
2. pressure_vs_ordinary_outcomes.png: Grouped bar chart comparing Wicket Rate, Dot Ball Rate, Boundary Rate, Strike Rate, Economy.
3. batter_own_baseline_deltas.png: Dumbbell / slope chart of Pressure SR vs Usual SR for Top 10 Batters.
4. bowler_own_baseline_deltas.png: Dumbbell / slope chart of Pressure Economy vs Usual Economy for Top 10 Bowlers.
5. rank_uncertainty_forest_plot.png: Forest plot showing point rank and 90% confidence intervals for Batters & Bowlers.
"""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = REPO_ROOT / "docs" / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "figure.titlesize": 14,
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.family": "sans-serif"
})

def generate_figure_1():
    # 1. Pressure Distribution by Innings & Phase
    labels = ["Powerplay (1-6)", "Middle (7-15)", "Death (16-20)"]
    # Data from exact counts
    inn1_ord = [30504, 40085, 16759]
    inn1_prs = [757, 5712, 8237]
    inn2_ord = [16386, 22562, 5999]
    inn2_prs = [14127, 21099, 11761]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)

    x = np.arange(len(labels))
    width = 0.55

    # Innings 1
    p1 = ax1.bar(x, inn1_prs, width, label="Pressure (PI >= 50)", color="#D32F2F")
    p2 = ax1.bar(x, inn1_ord, width, bottom=inn1_prs, label="Ordinary (PI < 50)", color="#1976D2", alpha=0.6)
    ax1.set_title("1st Innings (Setting Target)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylabel("Total Deliveries")
    for i in range(len(labels)):
        tot = inn1_prs[i] + inn1_ord[i]
        pct = inn1_prs[i] / tot * 100
        ax1.text(i, inn1_prs[i] / 2, f"{pct:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=9)
    ax1.legend(loc="upper left")

    # Innings 2
    ax2.bar(x, inn2_prs, width, label="Pressure (PI >= 50)", color="#D32F2F")
    ax2.bar(x, inn2_ord, width, bottom=inn2_prs, label="Ordinary (PI < 50)", color="#1976D2", alpha=0.6)
    ax2.set_title("2nd Innings (Chasing Target)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    for i in range(len(labels)):
        tot = inn2_prs[i] + inn2_ord[i]
        pct = inn2_prs[i] / tot * 100
        ax2.text(i, inn2_prs[i] / 2, f"{pct:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=9)

    plt.suptitle("Delivery Distribution Across Innings Phases (IPL + T20I, 194,014 Balls)", y=1.02)
    plt.tight_layout()
    out_path = FIG_DIR / "pressure_by_innings_phase.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")

def generate_figure_2():
    # 2. Pressure vs Ordinary Outcome Metrics
    metrics = ["Wicket Rate (%)", "Dot Ball Rate (%)", "Boundary Rate (%)", "Strike Rate", "Economy Rate"]
    ordinary = [5.07, 34.72, 18.90, 140.67, 8.44]
    pressure = [6.81, 36.38, 18.50, 138.50, 8.30]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    # Rates (%)
    x_rates = np.arange(3)
    w = 0.35
    axes[0].bar(x_rates - w/2, ordinary[:3], w, label="Ordinary (<50)", color="#1976D2", alpha=0.85)
    axes[0].bar(x_rates + w/2, pressure[:3], w, label="Pressure (>=50)", color="#D32F2F", alpha=0.85)
    axes[0].set_xticks(x_rates)
    axes[0].set_xticklabels(metrics[:3])
    axes[0].set_ylabel("Percentage (%)")
    axes[0].set_title("Delivery Event Rates")
    axes[0].legend()
    for i in range(3):
        axes[0].text(i - w/2, ordinary[i] + 0.6, f"{ordinary[i]:.1f}%", ha="center", fontsize=9)
        axes[0].text(i + w/2, pressure[i] + 0.6, f"{pressure[i]:.1f}%", ha="center", fontsize=9, fontweight="bold")
    axes[0].set_ylim(0, 45)

    # Scoring Rates
    x_scores = np.arange(2)
    axes[1].bar(x_scores - w/2, ordinary[3:], w, label="Ordinary (<50)", color="#1976D2", alpha=0.85)
    axes[1].bar(x_scores + w/2, pressure[3:], w, label="Pressure (>=50)", color="#D32F2F", alpha=0.85)
    axes[1].set_xticks(x_scores)
    axes[1].set_xticklabels(["Strike Rate (Runs/100b)", "Economy (Runs/Over)"])
    axes[1].set_title("Scoring & Concession Efficiency")
    axes[1].legend()
    for i in range(2):
        axes[1].text(i - w/2, ordinary[3+i] + (2.0 if i==0 else 0.2), f"{ordinary[3+i]:.1f}", ha="center", fontsize=9)
        axes[1].text(i + w/2, pressure[3+i] + (2.0 if i==0 else 0.2), f"{pressure[3+i]:.1f}", ha="center", fontsize=9, fontweight="bold")
    axes[1].set_ylim(0, 160)

    plt.suptitle("Statistical Comparison: Pressure vs Ordinary Deliveries (95% CIs Exclude Zero)", y=1.02)
    plt.tight_layout()
    out_path = FIG_DIR / "pressure_vs_ordinary_distributions.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")

def generate_figure_3_and_4():
    # 3. Top 10 Batters Own-Baseline Comparison (Dumbbell Plot)
    batters = [
        ("Matthew Wade", 172.28, 113.17, "+59.11", 184),
        ("Tim David", 183.30, 174.39, "+8.91", 449),
        ("Suryakumar Yadav", 168.28, 165.77, "+2.52", 722),
        ("Reeza Hendricks", 163.22, 133.55, "+29.67", 367),
        ("Rinku Singh", 157.08, 150.47, "+6.61", 431),
        ("Phil Salt", 191.44, 165.22, "+26.22", 257),
        ("Romario Shepherd", 150.00, 159.93, "-9.93", 400),
        ("Namboori Tilak Varma", 154.84, 139.11, "+15.73", 733),
        ("Dinesh Karthik", 182.21, 157.51, "+24.70", 253),
        ("Ravindra Jadeja", 146.24, 125.63, "+20.62", 439),
    ]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    y = np.arange(len(batters))

    for i, (name, p_sr, u_sr, delta, n) in enumerate(batters):
        ax.plot([u_sr, p_sr], [i, i], color="#B0BEC5", lw=2.5, zorder=1)
        ax.scatter(u_sr, i, color="#1976D2", s=80, zorder=2, label="Usual SR" if i==0 else "")
        ax.scatter(p_sr, i, color="#D32F2F", s=100, zorder=3, label="Pressure SR" if i==0 else "")
        ax.text(max(p_sr, u_sr) + 2.5, i, f"{delta} (N={n})", va="center", fontsize=8.5, fontweight="bold",
                color="#2E7D32" if "+" in delta else "#C62828")

    ax.axvline(140.67, color="#1976D2", linestyle="--", alpha=0.5, label="League Usual SR (140.7)")
    ax.axvline(138.50, color="#D32F2F", linestyle="--", alpha=0.5, label="League Pressure SR (138.5)")

    ax.set_yticks(y)
    ax.set_yticklabels([f"#{i+1} {b[0]}" for i, b in enumerate(batters)])
    ax.invert_yaxis()
    ax.set_xlabel("Batting Strike Rate (Runs per 100 Balls)")
    ax.set_title("Top 10 Batters: Own Usual vs Own Pressure Strike Rate\n(9 of 10 score faster under pressure; League delta: -2.17)")
    ax.legend(loc="lower right")
    plt.tight_layout()
    out_path = FIG_DIR / "batter_own_baseline_deltas.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")

    # 4. Top 10 Bowlers Own-Baseline Comparison (Dumbbell Plot)
    bowlers = [
        ("Mitchell Santner", 6.47, 7.62, "-1.15", 630),
        ("Sufiyan Muqeem", 5.59, 6.94, "-1.35", 147),
        ("Rashid Khan", 6.99, 7.51, "-0.52", 956),
        ("Jamie Overton", 6.26, 9.16, "-2.90", 161),
        ("Matheesha Pathirana", 6.88, 8.45, "-1.57", 484),
        ("Sunil Narine", 6.27, 7.00, "-0.72", 503),
        ("Mohammad Nawaz", 6.04, 7.46, "-1.42", 296),
        ("Jasprit Bumrah", 6.90, 6.81, "+0.09", 586),
        ("Varun Chakravarthy", 7.84, 7.79, "+0.06", 875),
        ("Yuzvendra Chahal", 7.99, 8.60, "-0.61", 825),
    ]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    y = np.arange(len(bowlers))

    for i, (name, p_ec, u_ec, delta, n) in enumerate(bowlers):
        ax.plot([u_ec, p_ec], [i, i], color="#B0BEC5", lw=2.5, zorder=1)
        ax.scatter(u_ec, i, color="#1976D2", s=80, zorder=2, label="Usual Econ" if i==0 else "")
        ax.scatter(p_ec, i, color="#D32F2F", s=100, zorder=3, label="Pressure Econ" if i==0 else "")
        ax.text(max(p_ec, u_ec) + 0.15, i, f"{delta} RPO (N={n})", va="center", fontsize=8.5, fontweight="bold",
                color="#2E7D32" if float(delta) <= 0 else "#C62828")

    ax.axvline(8.44, color="#1976D2", linestyle="--", alpha=0.5, label="League Usual Econ (8.44)")
    ax.axvline(8.30, color="#D32F2F", linestyle="--", alpha=0.5, label="League Pressure Econ (8.30)")

    ax.set_yticks(y)
    ax.set_yticklabels([f"#{i+1} {b[0]}" for i, b in enumerate(bowlers)])
    ax.invert_yaxis()
    ax.set_xlabel("Bowling Economy Rate (Runs Conceded per Over — Lower is Better)")
    ax.set_title("Top 10 Bowlers: Own Usual vs Own Pressure Economy Rate\n(8 of 10 concede fewer runs per over under pressure; Bumrah & Varun flat)")
    ax.legend(loc="lower right")
    plt.tight_layout()
    out_path = FIG_DIR / "bowler_own_baseline_deltas.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")

def generate_figure_5():
    # 5. Forest Plot of Rank Uncertainty (90% CIs from Match-Cluster Bootstrap)
    # Load Phase 8 uncertainty deliverables
    b_unc = pd.read_csv(REPO_ROOT / "output" / "phase8_ranking_reconsideration" / "batter_rank_uncertainty.csv")
    bw_unc = pd.read_csv(REPO_ROOT / "output" / "phase8_ranking_reconsideration" / "bowler_rank_uncertainty.csv")

    b_top10 = b_unc.head(10).copy()
    bw_top10 = bw_unc.head(10).copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5), sharex=True)

    y = np.arange(10)

    # Batters
    for i, row in b_top10.iterrows():
        low = row["rank_p5"]
        high = row["rank_p95"]
        ax1.plot([low, high], [i, i], color="#D32F2F", lw=2.5, alpha=0.7)
        ax1.scatter([row["official_rank"]], [i], color="#D32F2F", s=70, zorder=3)
        ax1.text(high + 0.8, i, f"[{int(low)}, {int(high)}]", va="center", fontsize=8)

    ax1.set_yticks(y)
    ax1.set_yticklabels([f"#{int(row['official_rank'])} {row['player_name']}" for i, row in b_top10.iterrows()])
    ax1.invert_yaxis()
    ax1.set_xlabel("Rank Range (90% Bootstrap CI)")
    ax1.set_title("Batters: Rank Uncertainty Intervals\n(Ranks 4-10 statistically close)")
    ax1.set_xlim(0, 30)

    # Bowlers
    for i, row in bw_top10.iterrows():
        low = row["rank_p5"]
        high = row["rank_p95"]
        ax2.plot([low, high], [i, i], color="#1976D2", lw=2.5, alpha=0.7)
        ax2.scatter([row["official_rank"]], [i], color="#1976D2", s=70, zorder=3)
        ax2.text(high + 0.8, i, f"[{int(low)}, {int(high)}]", va="center", fontsize=8)

    ax2.set_yticks(y)
    ax2.set_yticklabels([f"#{int(row['official_rank'])} {row['player_name']}" for i, row in bw_top10.iterrows()])
    ax2.invert_yaxis()
    ax2.set_xlabel("Rank Range (90% Bootstrap CI)")
    ax2.set_title("Bowlers: Rank Uncertainty Intervals\n(Santner #1 robust; Ranks 4-10 overlap)")

    plt.suptitle("Match-Cluster Bootstrap Rank Confidence Intervals (1,000 Draws, Seed=42)", y=1.02)
    plt.tight_layout()
    out_path = FIG_DIR / "rank_uncertainty_forest_plot.png"
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    generate_figure_1()
    generate_figure_2()
    generate_figure_3_and_4()
    generate_figure_5()
    print("All report figures successfully generated.")

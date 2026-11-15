"""
ml/phase11_v2/run_v2_pipeline.py
Single entry point to run the complete SupeRR Intelligence v2 Ranking Pipeline.
"""
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.phase11_v2.v2_ranking_generator import generate_v2_deliverables

def main():
    b_top10, bw_top10, comp_df, eval_df, winner = generate_v2_deliverables()
    
    print("\n" + "#" * 70)
    print("V2 TOP 10 BATTERS")
    print("#" * 70)
    print(b_top10[["v2_rank", "player_name", "league_evidence", "v2_score", "pressure_deliveries", "score_ci_lower_90", "score_ci_upper_90", "rank_ci_lower_90", "rank_ci_upper_90", "p_top10"]])
    
    print("\n" + "#" * 70)
    print("V2 TOP 10 BOWLERS")
    print("#" * 70)
    print(bw_top10[["v2_rank", "player_name", "league_evidence", "v2_score", "pressure_deliveries", "score_ci_lower_90", "score_ci_upper_90", "rank_ci_lower_90", "rank_ci_upper_90", "p_top10"]])

if __name__ == "__main__":
    main()

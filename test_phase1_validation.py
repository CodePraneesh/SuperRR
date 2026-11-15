#!/usr/bin/env python3
'''
test_phase1_validation.py
Comprehensive automated test suite for SupeRR Intelligence Phase 1 validation.
Verifies rules 1 to 10 specified in the Task Brief.
'''
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).parent / "output"
PROCESSED_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"
AUDIT_DIR = DATA_DIR / "audit"

class TestPhase1Validation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\nLoading Phase 1 processed and feature datasets...")
        deliv_path = PROCESSED_DIR / "deliveries_enriched.csv"
        match_path = PROCESSED_DIR / "matches_enriched.csv"
        if not deliv_path.exists() or not match_path.exists():
            cls.deliveries = None
            cls.matches = None
            cls.batters = None
            cls.bowlers = None
            return
        cls.deliveries = pd.read_csv(deliv_path, low_memory=False)
        cls.matches = pd.read_csv(match_path, low_memory=False)
        cls.batters = pd.read_csv(FEATURES_DIR / "batter_baselines_provisional.csv", low_memory=False)
        cls.bowlers = pd.read_csv(FEATURES_DIR / "bowler_baselines_provisional.csv", low_memory=False)
        print("Data loaded successfully.")

    def setUp(self):
        if getattr(self.__class__, "deliveries", None) is None:
            self.skipTest(
                "Requires output/processed/deliveries_enriched.csv; run `python supeRR_phase1_pipeline.py`"
            )

    # Task 2 & 3: Bowler wicket-crediting calculation
    def test_01_bowler_wicket_excludes_non_credited_modes(self):
        '''Test that bowler_wicket excludes Run Out, Retired Out, Obstructing the Field.'''
        d = self.deliveries
        norm_type = d["dismissal_type"].fillna("").astype(str).str.lower().str.strip()
        excluded_modes = ["runout", "retire out", "obstructing the field", "obstracting the field"]
        invalid_credited = d[norm_type.isin(excluded_modes) & d["bowler_wicket"]]
        self.assertEqual(len(invalid_credited), 0, f"Found {len(invalid_credited)} non-bowler wickets credited!")

    def test_02_bowler_wicket_excludes_no_balls_and_ambiguous_extras(self):
        '''Test that bowler_wicket strictly excludes No-ball and Ambiguous-extra deliveries.'''
        d = self.deliveries
        no_ball_credited = d[d["is_no_ball"] & d["bowler_wicket"]]
        ambig_credited = d[d["is_unknown_extra"] & d["bowler_wicket"]]
        self.assertEqual(len(no_ball_credited), 0, f"Found {len(no_ball_credited)} bowler wickets on no-balls!")
        self.assertEqual(len(ambig_credited), 0, f"Found {len(ambig_credited)} bowler wickets on ambiguous extras!")

    def test_03_bowler_wicket_strict_specification_equivalence(self):
        '''Test that bowler_wicket perfectly equals the exact 5-point cricket specification.'''
        d = self.deliveries
        credited_modes = ["bowled", "caught", "lbw", "stump", "hit wicket"]
        norm_type = d["dismissal_type"].fillna("").astype(str).str.lower().str.strip()
        expected = (
            d["is_wicket"] &
            ~d["is_no_ball"] &
            ~d["is_unknown_extra"] &
            norm_type.isin(credited_modes)
        )
        mismatches = (d["bowler_wicket"] != expected).sum()
        self.assertEqual(mismatches, 0, f"Found {mismatches} bowler_wicket logic mismatches!")

    # Task 4: Extras handling
    def test_04_extras_decomposition(self):
        '''Test total_delivery_runs is exact sum of batter runs and extras.'''
        d = self.deliveries
        computed_total = d["batter_runs"] + d["extras1"] + d["extras2"]
        diff = (d["total_delivery_runs"] != computed_total).sum()
        self.assertEqual(diff, 0, f"Found {diff} delivery total run mismatches!")

    def test_05_wides_and_no_balls_flagged_correctly(self):
        '''Test wide and overstep flags accurately reflect extras_type.'''
        d = self.deliveries
        wide_mismatch = (d["is_wide"] != d["extras_label"].eq("wide")).sum()
        nb_mismatch = (d["is_no_ball"] != d["extras_label"].eq("overstep")).sum()
        self.assertEqual(wide_mismatch, 0, f"Wide flag mismatches: {wide_mismatch}")
        self.assertEqual(nb_mismatch, 0, f"No-ball flag mismatches: {nb_mismatch}")

    # Task 5: Batter runs, bowler runs conceded and legal deliveries
    def test_06_legal_delivery_rules(self):
        '''Test legal_ball excludes wides, no-balls, and ambiguous extras.'''
        d = self.deliveries
        expected_illegal = d["is_wide"] | d["is_no_ball"] | d["is_unknown_extra"]
        illegal_mismatch = (d["legal_ball"] == expected_illegal).sum()
        self.assertEqual(illegal_mismatch, 0, f"Found {illegal_mismatch} legal delivery classification discrepancies!")

    def test_07_batter_balls_faced(self):
        '''Test batter_faced_ball excludes wides and standalone penalty/unlabelled events, includes no-balls.'''
        d = self.deliveries
        wides_faced = d[d["is_wide"] & d["batter_faced_ball"]]
        self.assertEqual(len(wides_faced), 0, "Wides must never count as batter faced balls!")
        nb_faced = d[d["is_no_ball"] & ~d["batter_faced_ball"]]
        self.assertEqual(len(nb_faced), 0, "Overstep no-balls must count as batter faced balls!")

    def test_08_bowler_runs_conceded_rules(self):
        '''Test bowler runs conceded includes batter runs, wide extras, and no-ball extras, excludes byes/legbyes.'''
        d = self.deliveries
        pure_byes_legbyes = d[d["extras_label"].isin(["byes", "legbyes"])]
        bye_conceded_diff = (pure_byes_legbyes["bowler_runs_conceded"] != pure_byes_legbyes["batter_runs"]).sum()
        self.assertEqual(bye_conceded_diff, 0, f"Byes/legbyes incorrectly charged to bowler on {bye_conceded_diff} rows!")

    # Task 6: Innings totals and match-state calculations
    def test_09_innings_target_consistency(self):
        '''Test that chasing target in 2nd innings is first innings total + 1 (unless revised).'''
        d = self.deliveries
        chase = d[d["innings"] == 2]
        self.assertTrue((chase["target_runs"] > 0).all(), "All chase target_runs must be positive!")
        unrevised_chase = chase[chase["revised_target"].isna()]
        diff = (unrevised_chase["target_runs"] != (unrevised_chase["first_innings_total"] + 1)).sum()
        self.assertEqual(diff, 0, f"Found {diff} unrevised chase target mismatches!")

    def test_10_cumulative_state_progression_zero_leakage(self):
        '''Test cumulative state columns strictly shift and use only prior deliveries (strictly zero lookahead).'''
        d = self.deliveries
        first_balls = d.groupby(["match_id", "innings"]).first()
        self.assertTrue((first_balls["score_before"] == 0).all(), "score_before must start at 0 for delivery 1!")
        self.assertTrue((first_balls["wickets_lost_before"] == 0).all(), "wickets_lost_before must start at 0 for delivery 1!")
        self.assertTrue((first_balls["legal_balls_before"] == 0).all(), "legal_balls_before must start at 0 for delivery 1!")

        next_score = d.groupby(["match_id", "innings"])["score_before"].shift(-1)
        score_diff = (d["score_before"] + d["total_delivery_runs"]) - next_score
        self.assertEqual(score_diff.dropna().ne(0).sum(), 0, "score_before progression mismatch!")

        next_wkt = d.groupby(["match_id", "innings"])["wickets_lost_before"].shift(-1)
        wkt_diff = (d["wickets_lost_before"] + d["is_team_wicket"].astype(int)) - next_wkt
        self.assertEqual(wkt_diff.dropna().ne(0).sum(), 0, "wickets_lost_before progression mismatch!")

        next_legal = d.groupby(["match_id", "innings"])["legal_balls_before"].shift(-1)
        legal_diff = (d["legal_balls_before"] + d["legal_ball"].astype(int)) - next_legal
        self.assertEqual(legal_diff.dropna().ne(0).sum(), 0, "legal_balls_before progression mismatch!")

    # Task 7: Pressure features use only information available BEFORE the delivery
    def test_11_pressure_features_bounds_and_validity(self):
        '''Test that pressure features respect logical bounds and contain no negative anomalies.'''
        d = self.deliveries
        self.assertTrue((d["balls_remaining"] >= 0).all(), "balls_remaining cannot be negative!")
        self.assertTrue((d["wickets_in_hand"] >= 0).all() and (d["wickets_in_hand"] <= 10).all(), "wickets_in_hand must be between 0 and 10!")
        chase = d[d["innings"] == 2]
        self.assertTrue((chase["runs_required"] >= 0).all(), "runs_required cannot be negative!")
        self.assertTrue((chase["required_run_rate"].dropna() >= 0).all(), "required_run_rate cannot be negative!")
        self.assertTrue((d["current_run_rate"].dropna() >= 0).all(), "current_run_rate cannot be negative!")

    # Task 8: Missing values, duplicates, and invalid mappings
    def test_12_no_duplicate_delivery_keys(self):
        '''Test no duplicate match/innings/ball delivery keys exist.'''
        d = self.deliveries
        dups = d.duplicated(["match_id", "innings", "innings_ball_num"]).sum()
        self.assertEqual(dups, 0, f"Found {dups} duplicate delivery keys!")

    def test_13_no_negative_values(self):
        '''Test that runs, extras, and sequence IDs have no negative values.'''
        d = self.deliveries
        self.assertTrue((d["batter_runs"] >= 0).all(), "batter_runs has negative values!")
        self.assertTrue((d["extras1"] >= 0).all(), "extras1 has negative values!")
        self.assertTrue((d["extras2"] >= 0).all(), "extras2 has negative values!")

    # Task 9: Super overs excluded from player baselines
    def test_14_super_overs_excluded_from_baselines(self):
        '''Test that super overs (innings >= 3) are completely excluded from baseline features.'''
        d = self.deliveries
        main = d[d["innings"].isin([1, 2]) & d["in_scope_competition"].fillna(False)]
        total_main_faced = main["batter_faced_ball"].sum()
        total_baseline_faced = self.batters["deliveries"].sum()
        self.assertEqual(total_main_faced, total_baseline_faced, "Batter baseline includes non-main innings deliveries!")

        total_main_legal = main["legal_ball"].sum()
        total_baseline_bowled = self.bowlers["balls_bowled"].sum()
        self.assertEqual(total_main_legal, total_baseline_bowled, "Bowler baseline includes non-main innings balls!")

    # Task 10: Official scope separation (IPL vs T20I) & Emerging Teams exclusion
    def test_15_emerging_teams_excluded_from_baselines(self):
        '''Test that Emerging Teams T20 matches are excluded from player baselines.'''
        self.assertNotIn("Emerging_T20", self.batters["competition_scope"].values, "Emerging_T20 found in batter baselines!")
        self.assertNotIn("Emerging_T20", self.bowlers["competition_scope"].values, "Emerging_T20 found in bowler baselines!")

    def test_16_ipl_and_t20i_strictly_separated(self):
        '''Test that baselines only contain IPL and T20I and they are separated.'''
        batter_scopes = set(self.batters["competition_scope"].unique())
        bowler_scopes = set(self.bowlers["competition_scope"].unique())
        expected_scopes = {"IPL", "T20I"}
        self.assertEqual(batter_scopes, expected_scopes, f"Batter scopes mismatch: {batter_scopes}")
        self.assertEqual(bowler_scopes, expected_scopes, f"Bowler scopes mismatch: {bowler_scopes}")

if __name__ == "__main__":
    unittest.main()

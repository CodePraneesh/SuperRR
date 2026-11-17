#!/usr/bin/env python3
"""
tests/test_official_rankings_api.py
Automated validation test ensuring the FastAPI backend strictly serves the
frozen Phase 8 official rankings without alteration or score drift.
"""
import os
import sys
import unittest
from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.main import app


class TestOfficialRankingsAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.official_dir = REPO_ROOT / "output" / "phase13_evidence_floor"
        cls.batters_csv = pd.read_csv(cls.official_dir / "official_top10_batters.csv")
        cls.bowlers_csv = pd.read_csv(cls.official_dir / "official_top10_bowlers.csv")

    def test_01_official_unified_rankings_match_phase8(self):
        """Verify GET /api/v1/official/rankings returns exact official Phase 13 top 10."""
        res = self.client.get("/api/v1/official/rankings")
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Check batters count and exact values
        batters = data["batters"]
        self.assertEqual(len(batters), 10, "Expected exactly 10 official batters")
        for i, row in self.batters_csv.iterrows():
            api_b = batters[i]
            expected_rank = int(row["official_rank"])
            expected_name = str(row["player_name"])
            expected_cpri = round(float(row["cpri_score"]), 2)
            self.assertEqual(api_b["official_rank"], expected_rank, f"Rank mismatch at index {i}")
            self.assertEqual(api_b["player_name"], expected_name, f"Name mismatch at rank {expected_rank}")
            self.assertAlmostEqual(api_b["cpri_score"], expected_cpri, places=2,
                                   msg=f"CPRI mismatch for {expected_name}: expected {expected_cpri}, got {api_b['cpri_score']}")

        # Check bowlers count and exact values
        bowlers = data["bowlers"]
        self.assertEqual(len(bowlers), 10, "Expected exactly 10 official bowlers")
        for i, row in self.bowlers_csv.iterrows():
            api_bw = bowlers[i]
            expected_rank = int(row["official_rank"])
            expected_name = str(row["player_name"])
            expected_cpri = round(float(row["cpri_score"]), 2)
            self.assertEqual(api_bw["official_rank"], expected_rank, f"Rank mismatch at index {i}")
            self.assertEqual(api_bw["player_name"], expected_name, f"Name mismatch at rank {expected_rank}")
            self.assertAlmostEqual(api_bw["cpri_score"], expected_cpri, places=2,
                                   msg=f"CPRI mismatch for {expected_name}: expected {expected_cpri}, got {api_bw['cpri_score']}")

    def test_02_official_batters_endpoint(self):
        """Verify GET /api/v1/official/batters returns complete Top 10 with 90% CIs."""
        res = self.client.get("/api/v1/official/batters")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["role"], "Batter")
        self.assertEqual(len(data["official_top10"]), 10)

        # Tim David must be #1 with CPRI 82.44
        david = data["official_top10"][0]
        self.assertEqual(david["official_rank"], 1)
        self.assertEqual(david["player_name"], "Tim David")
        self.assertAlmostEqual(david["cpri_score"], 82.44, places=2)
        self.assertEqual(david["rank_uncertainty"]["ci_display"], "[1, 16]")

        # Rinku Singh must be #4 with CPRI 77.18
        rinku = data["official_top10"][3]
        self.assertEqual(rinku["official_rank"], 4)
        self.assertEqual(rinku["player_name"], "Rinku Singh")
        self.assertAlmostEqual(rinku["cpri_score"], 77.18, places=2)
        self.assertEqual(rinku["rank_uncertainty"]["ci_display"], "[1, 37]")

    def test_03_official_bowlers_endpoint(self):
        """Verify GET /api/v1/official/bowlers returns complete Top 10 with 90% CIs."""
        res = self.client.get("/api/v1/official/bowlers")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["role"], "Bowler")
        self.assertEqual(len(data["official_top10"]), 10)

        # Mitchell Santner must be #1 with CPRI 79.84
        santner = data["official_top10"][0]
        self.assertEqual(santner["official_rank"], 1)
        self.assertEqual(santner["player_name"], "Mitchell Santner")
        self.assertAlmostEqual(santner["cpri_score"], 79.84, places=2)
        self.assertEqual(santner["rank_uncertainty"]["ci_display"], "[1, 26]")

        # Jasprit Bumrah must be #6 with CPRI 73.36
        bumrah = data["official_top10"][5]
        self.assertEqual(bumrah["official_rank"], 6)
        self.assertEqual(bumrah["player_name"], "Jasprit Bumrah")
        self.assertAlmostEqual(bumrah["cpri_score"], 73.36, places=2)
        self.assertEqual(bumrah["rank_uncertainty"]["ci_display"], "[2, 44]")

    def test_04_official_player_lookup(self):
        """Verify GET /api/v1/official/player/{name} returns exact player dossier."""
        res = self.client.get("/api/v1/official/player/Suryakumar%20Yadav")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["player_name"], "Suryakumar Yadav")
        self.assertEqual(data["official_rank"], 2)
        self.assertAlmostEqual(data["cpri_score"], 81.42, places=2)
        self.assertEqual(data["confidence_tier"], "High Confidence")

    def test_05_legacy_cohort_disclaimer_present(self):
        """Verify GET /api/v1/players/{scope}/{role} contains the secondary view notice."""
        res = self.client.get("/api/v1/players/IPL/Batter")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["view_type"], "contextual_league_view")
        self.assertIn("not the official ranking", data["disclaimer"])


if __name__ == "__main__":
    unittest.main()

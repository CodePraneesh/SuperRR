"""
tests/test_phase5_api.py
Phase 5 Comprehensive FastAPI Test Suite for SupeRR Intelligence API.

Validates:
1. Health and System Readiness (/api/v1/health)
2. Cohort listings with scope/role segregation and pagination (/api/v1/players/{scope}/{role})
3. Single player profiles, CPRI components, and peer percentiles (/api/v1/players/{scope}/{role}/{name})
4. Situational phase and pressure contrast splits (/api/v1/players/{scope}/{role}/{name}/splits)
5. Evidence-grounded AI scouting reports (/api/v1/scouting/report/{scope}/{role}/{name})
6. Pressure performance explanations (/api/v1/scouting/pressure/{scope}/{role}/{name})
7. Side-by-side player comparisons for Batters and Bowlers (/api/v1/scouting/compare)
8. Head-to-head encounters with sample tier warnings (/api/v1/scouting/matchup/{scope}/{batter}/{bowler})
9. Grounded natural language analytics QA (/api/v1/scouting/ask)
10. Error handling, invalid scope/role (422), missing players (404), and CORS middleware
"""
import os
import sys
import unittest
from pathlib import Path

# Add project base directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app


class TestPhase5API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize TestClient with app lifespan context
        cls.client_ctx = TestClient(app)
        cls.client = cls.client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_ctx.__exit__(None, None, None)

    # -------------------------------------------------------------------------
    # Test 1: Health & Readiness
    # -------------------------------------------------------------------------
    def test_01_health_endpoint(self):
        """Test GET /api/v1/health returns 200 with healthy stores."""
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "1.0.0")
        self.assertTrue(data["stores_loaded"])
        self.assertIn("tier_available", data)
        self.assertIn("timestamp", data)

    # -------------------------------------------------------------------------
    # Test 2: Cohort Players List (IPL Batters)
    # -------------------------------------------------------------------------
    def test_02_cohort_players_ipl_batters(self):
        """Test GET /api/v1/players/IPL/Batter returns cohort list with official Top 10."""
        res = self.client.get("/api/v1/players/IPL/Batter")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["competition_scope"], "IPL")
        self.assertEqual(data["role"], "Batter")
        self.assertEqual(data["cohort"], "IPL Batters")
        self.assertGreaterEqual(data["total_players"], 10)
        self.assertEqual(data["official_count"], 10)

        # Confirm Rinku Singh is #1 with 89.03 CPRI
        rinku = [p for p in data["players"] if p["player_name"] == "Rinku Singh"][0]
        self.assertEqual(rinku["official_rank"], 1)
        self.assertAlmostEqual(rinku["cpri_score"], 89.03, places=2)
        self.assertEqual(rinku["ranking_tier"], "Official Top 10")
        self.assertEqual(rinku["confidence_tier"], "High Confidence")
        self.assertTrue(rinku["is_official_top10"])
        self.assertEqual(rinku["pressure_deliveries"], 411)

    # -------------------------------------------------------------------------
    # Test 3: Cohort Filtering and Pagination
    # -------------------------------------------------------------------------
    def test_03_cohort_filtering_and_pagination(self):
        """Test official_only, confidence_tier filtering, and limit/offset pagination."""
        # official_only=true
        res_off = self.client.get("/api/v1/players/IPL/Batter?official_only=true")
        self.assertEqual(res_off.status_code, 200)
        data_off = res_off.json()
        self.assertEqual(len(data_off["players"]), 10)
        for p in data_off["players"]:
            self.assertTrue(p["is_official_top10"])
            self.assertIsNotNone(p["official_rank"])

        # Pagination: limit=5, offset=0 vs offset=5
        res_p1 = self.client.get("/api/v1/players/IPL/Batter?limit=5&offset=0")
        res_p2 = self.client.get("/api/v1/players/IPL/Batter?limit=5&offset=5")
        self.assertEqual(res_p1.status_code, 200)
        self.assertEqual(res_p2.status_code, 200)
        p1_names = [p["player_name"] for p in res_p1.json()["players"]]
        p2_names = [p["player_name"] for p in res_p2.json()["players"]]
        self.assertEqual(len(p1_names), 5)
        self.assertEqual(len(p2_names), 5)
        self.assertEqual(len(set(p1_names).intersection(set(p2_names))), 0)

    # -------------------------------------------------------------------------
    # Test 4: Single Player Profile Lookup
    # -------------------------------------------------------------------------
    def test_04_player_profile_lookup(self):
        """Test GET /api/v1/players/{scope}/{role}/{name} returns full profile."""
        res = self.client.get("/api/v1/players/IPL/Batter/Rinku Singh")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["player_name"], "Rinku Singh")
        self.assertEqual(data["official_rank"], 1)
        self.assertAlmostEqual(data["cpri_score"], 89.03, places=2)

        # 4 Components
        comps = data["components"]
        self.assertAlmostEqual(comps["pressure_impact"], 100.0, places=1)
        self.assertAlmostEqual(comps["pressure_adaptability"], 91.55, places=2)
        self.assertAlmostEqual(comps["clutch_consistency"], 56.32, places=2)
        self.assertAlmostEqual(comps["reliability_confidence"], 99.22, places=2)

        # Peer benchmarks attached
        self.assertIn("peer_benchmarks", data)
        self.assertIn("cohort_percentiles", data["peer_benchmarks"])

        # Empirical strengths attached
        self.assertIn("strengths_and_weaknesses", data)
        self.assertTrue(len(data["strengths_and_weaknesses"]["strengths"]) > 0)

    # -------------------------------------------------------------------------
    # Test 5: Contextual Performance Splits
    # -------------------------------------------------------------------------
    def test_05_player_contextual_splits(self):
        """Test GET /api/v1/players/{scope}/{role}/{name}/splits returns phase and pressure contrasts."""
        res = self.client.get("/api/v1/players/IPL/Batter/Rinku Singh/splits")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["player_name"], "Rinku Singh")
        self.assertIn("innings_phase_splits", data)
        phases = data["innings_phase_splits"]
        self.assertIn("death", phases)
        self.assertAlmostEqual(phases["death"]["strike_rate"], 192.52, places=1)

        # Pressure contrast
        self.assertIn("pressure_contrast", data)
        contrast = data["pressure_contrast"]
        self.assertIn("high_pressure", contrast)
        self.assertIn("delta_strike_rate", contrast)
        self.assertAlmostEqual(contrast["delta_strike_rate"], 18.94, places=1)

    # -------------------------------------------------------------------------
    # Test 6: AI Scouting Report Generation
    # -------------------------------------------------------------------------
    def test_06_scouting_report_generation(self):
        """Test GET /api/v1/scouting/report/{scope}/{role}/{name} returns verified report."""
        res = self.client.get("/api/v1/scouting/report/IPL/Batter/Rinku Singh")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["player_name"], "Rinku Singh")
        self.assertTrue(data["verified"])
        self.assertIn("89.03", data["response"])
        self.assertIn("Rinku Singh", data["response"])
        self.assertIn("tier_used", data)

    # -------------------------------------------------------------------------
    # Test 7: Pressure Explanation Generation
    # -------------------------------------------------------------------------
    def test_07_pressure_explanation_endpoint(self):
        """Test GET /api/v1/scouting/pressure/{scope}/{role}/{name} returns pressure breakdown."""
        res = self.client.get("/api/v1/scouting/pressure/IPL/Batter/Rinku Singh")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["verified"])
        self.assertIn("High-Pressure Execution Profile", data["response"])
        self.assertIn("Clutch Accelerant", data["response"])

    # -------------------------------------------------------------------------
    # Test 8: Side-by-Side Batter Comparison
    # -------------------------------------------------------------------------
    def test_08_player_comparison_batters(self):
        """Test POST /api/v1/scouting/compare for batters returns structured deltas."""
        payload = {
            "scope": "IPL",
            "role": "Batter",
            "player_a": "Rinku Singh",
            "player_b": "Suryakumar Yadav"
        }
        res = self.client.post("/api/v1/scouting/compare", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["player_a"], "Rinku Singh")
        self.assertEqual(data["player_b"], "Suryakumar Yadav")
        self.assertIn("structured_comparison", data)
        deltas = data["structured_comparison"]["deltas_a_minus_b"]
        self.assertIn("cpri_delta", deltas)
        self.assertIn("pressure_impact_delta", deltas)
        self.assertTrue(data["verified"])

    # -------------------------------------------------------------------------
    # Test 9: Side-by-Side Bowler Comparison
    # -------------------------------------------------------------------------
    def test_09_player_comparison_bowlers(self):
        """Test POST /api/v1/scouting/compare for bowlers returns valid comparison."""
        payload = {
            "scope": "IPL",
            "role": "Bowler",
            "player_a": "Mohit Sharma",
            "player_b": "Yuzvendra Chahal"
        }
        res = self.client.post("/api/v1/scouting/compare", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["role"], "Bowler")
        deltas = data["structured_comparison"]["deltas_a_minus_b"]
        self.assertAlmostEqual(deltas["cpri_delta"], 4.43, places=2)

    # -------------------------------------------------------------------------
    # Test 10: Head-to-Head Matchup and Small Sample Flag
    # -------------------------------------------------------------------------
    def test_10_matchup_endpoint_with_small_sample_check(self):
        """Test GET /api/v1/scouting/matchup/{scope}/{batter}/{bowler} with sample tiers."""
        # 1. Reliable sample (Virat Kohli vs Jasprit Bumrah: 24 balls >= 18)
        res_rel = self.client.get("/api/v1/scouting/matchup/IPL/Virat Kohli/Jasprit Bumrah")
        self.assertEqual(res_rel.status_code, 200)
        data_rel = res_rel.json()
        self.assertFalse(data_rel["is_small_sample"])
        self.assertIsNone(data_rel["sample_warning"])
        self.assertGreaterEqual(data_rel["h2h_data"]["balls_faced"], 18)

        # 2. Exploratory / small sample encounter (<18 balls: Dhoni vs Ashwin has 5 balls)
        res_small = self.client.get("/api/v1/scouting/matchup/IPL/Mahendra Singh Dhoni/Ravichandran Ashwin")
        self.assertEqual(res_small.status_code, 200)
        data_small = res_small.json()
        self.assertTrue(data_small["is_small_sample"])
        self.assertIsNotNone(data_small["sample_warning"])
        self.assertIn("exploratory", data_small["sample_warning"].lower())

    # -------------------------------------------------------------------------
    # Test 11: Grounded Analytics QA Endpoint
    # -------------------------------------------------------------------------
    def test_11_analytics_qa_ask_endpoint(self):
        """Test POST /api/v1/scouting/ask returns grounded evidence answer."""
        payload = {
            "query": "Who is the top death batter in IPL?",
            "scope": "IPL",
            "role": "Batter"
        }
        res = self.client.post("/api/v1/scouting/ask", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["verified"])
        self.assertGreater(len(data["answer"]), 50)

    # -------------------------------------------------------------------------
    # Test 12: Scope Validation Error (422)
    # -------------------------------------------------------------------------
    def test_12_validation_error_scope(self):
        """Test requesting invalid scope returns 422 with structured error envelope."""
        res = self.client.get("/api/v1/players/TEST_SCOPE/Batter")
        self.assertEqual(res.status_code, 422)
        data = res.json()
        self.assertEqual(data["error_type"], "INVALID_SCOPE")
        self.assertIn("Allowed scopes: 'IPL', 'T20I'", data["detail"])

    # -------------------------------------------------------------------------
    # Test 13: Role Validation Error (422)
    # -------------------------------------------------------------------------
    def test_13_validation_error_role(self):
        """Test requesting invalid role returns 422 with structured error envelope."""
        res = self.client.get("/api/v1/players/IPL/Allrounder")
        self.assertEqual(res.status_code, 422)
        data = res.json()
        self.assertEqual(data["error_type"], "INVALID_ROLE")
        self.assertIn("Allowed roles: 'Batter', 'Bowler'", data["detail"])

    # -------------------------------------------------------------------------
    # Test 14: Player Not Found (404)
    # -------------------------------------------------------------------------
    def test_14_player_not_found_404(self):
        """Test requesting unknown player returns 404 with clear message."""
        res = self.client.get("/api/v1/players/IPL/Batter/NonExistentPlayerXYZ")
        self.assertEqual(res.status_code, 404)
        data = res.json()
        self.assertEqual(data["error_type"], "PLAYER_NOT_FOUND")
        self.assertIn("NonExistentPlayerXYZ", data["detail"])

    # -------------------------------------------------------------------------
    # Test 15: CORS Middleware Validation
    # -------------------------------------------------------------------------
    def test_15_cors_middleware(self):
        """Test CORS headers are returned for frontend origins."""
        res = self.client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("access-control-allow-origin"), "http://localhost:3000")

    # -------------------------------------------------------------------------
    # Test 16: OpenAPI and Swagger Docs
    # -------------------------------------------------------------------------
    def test_16_openapi_and_docs(self):
        """Test OpenAPI schema and Swagger UI documentation endpoints."""
        res_docs = self.client.get("/docs")
        self.assertEqual(res_docs.status_code, 200)

        res_openapi = self.client.get("/openapi.json")
        self.assertEqual(res_openapi.status_code, 200)
        paths = res_openapi.json()["paths"]
        expected_endpoints = [
            "/api/v1/health",
            "/api/v1/players/{scope}/{role}",
            "/api/v1/players/{scope}/{role}/{name}",
            "/api/v1/players/{scope}/{role}/{name}/splits",
            "/api/v1/scouting/report/{scope}/{role}/{name}",
            "/api/v1/scouting/pressure/{scope}/{role}/{name}",
            "/api/v1/scouting/compare",
            "/api/v1/scouting/matchup/{scope}/{batter}/{bowler}",
            "/api/v1/scouting/ask"
        ]
        for ep in expected_endpoints:
            self.assertIn(ep, paths, f"Endpoint {ep} missing from OpenAPI schema")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
scouting_cli.py
SupeRR Intelligence - Production Scouting Service CLI Runner

Quick launch command-line interface for scouting intelligence queries and system self-tests.
Usage:
    python scouting_cli.py --test
    python scouting_cli.py --feature report --player "Rinku Singh" --scope IPL --role Batter
    python scouting_cli.py --feature pressure --player "Matheesha Pathirana" --scope IPL --role Bowler
    python scouting_cli.py --feature compare --player "Rinku Singh" --target "Suryakumar Yadav" --scope IPL
    python scouting_cli.py --feature h2h --player "Rinku Singh" --target "Mohit Sharma" --scope IPL
    python scouting_cli.py --feature ask --query "Who is the top death overs bowler in IPL?"
"""
import sys
import argparse
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scouting_ai_service import ScoutingAIService


def run_self_test():
    """Runs a quick operational self-test across all 7 scouting features."""
    print("=" * 70)
    print("SUPERR INTELLIGENCE — SYSTEM SELF-TEST")
    print("=" * 70)
    service = ScoutingAIService()
    tests = [
        ("Feature 1: Player Report", lambda: service.generate_player_report("Rinku Singh", "IPL")),
        ("Feature 2: Pressure Explanation", lambda: service.explain_pressure_performance("Matheesha Pathirana", "IPL", role="Bowler")),
        ("Feature 3: Batter Strengths", lambda: service.analyze_batter_strengths("Rinku Singh", "IPL")),
        ("Feature 4: Bowler Strengths", lambda: service.analyze_bowler_strengths("Matheesha Pathirana", "IPL")),
        ("Feature 5: Batter Comparison", lambda: service.compare_players("Rinku Singh", "Suryakumar Yadav", "IPL")),
        ("Feature 6: Head-to-Head Scouting", lambda: service.analyze_batter_bowler_matchup("Rinku Singh", "Mohit Sharma", "IPL")),
        ("Feature 7: Cricket Question QA", lambda: service.answer_cricket_question("Why is Rinku Singh rated so highly?", ["Rinku Singh"], "IPL")),
    ]

    all_passed = True
    for name, func in tests:
        try:
            res = func()
            if res.get("status") == "success" and len(res.get("response", "")) > 100:
                print(f"  [PASS] {name} -> {res['tier_used']} ({len(res['response'])} chars)")
            else:
                print(f"  [FAIL] {name} -> Empty or unverified response")
                all_passed = False
        except Exception as e:
            print(f"  [ERROR] {name} -> {e}")
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("ALL 7 CORE SCOUTING FEATURES OPERATIONAL (100% PASS)")
    else:
        print("SELF-TEST FAILED ON ONE OR MORE FEATURES")
    print("=" * 70)
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="SupeRR Intelligence Scouting CLI Runner")
    parser.add_argument("--test", action="store_true", help="Run full self-test across all 7 scouting features")
    parser.add_argument("--feature", choices=["report", "pressure", "batter_sw", "bowler_sw", "compare", "h2h", "ask"], help="Scouting feature to invoke")
    parser.add_argument("--player", type=str, help="Primary player name")
    parser.add_argument("--target", type=str, help="Comparison player or opposing bowler name")
    parser.add_argument("--scope", default="IPL", choices=["IPL", "T20I"], help="Competition format")
    parser.add_argument("--role", choices=["Batter", "Bowler"], help="Player role")
    parser.add_argument("--query", type=str, help="Analytical question for natural language QA")

    args = parser.parse_args()

    if args.test:
        success = run_self_test()
        sys.exit(0 if success else 1)

    if not args.feature:
        parser.print_help()
        sys.exit(1)

    service = ScoutingAIService()
    res = {}

    if args.feature == "report":
        if not args.player:
            print("Error: --player is required for scouting report.")
            sys.exit(1)
        res = service.generate_player_report(args.player, competition_scope=args.scope, role=args.role)

    elif args.feature == "pressure":
        if not args.player:
            print("Error: --player is required for pressure explanation.")
            sys.exit(1)
        res = service.explain_pressure_performance(args.player, competition_scope=args.scope, role=args.role)

    elif args.feature == "batter_sw":
        if not args.player:
            print("Error: --player is required.")
            sys.exit(1)
        res = service.analyze_batter_strengths(args.player, competition_scope=args.scope)

    elif args.feature == "bowler_sw":
        if not args.player:
            print("Error: --player is required.")
            sys.exit(1)
        res = service.analyze_bowler_strengths(args.player, competition_scope=args.scope)

    elif args.feature == "compare":
        if not args.player or not args.target:
            print("Error: Both --player and --target are required for comparison.")
            sys.exit(1)
        res = service.compare_players(args.player, args.target, competition_scope=args.scope, role=args.role)

    elif args.feature == "h2h":
        if not args.player or not args.target:
            print("Error: Both --player (batter) and --target (bowler) are required for H2H matchup.")
            sys.exit(1)
        res = service.analyze_batter_bowler_matchup(args.player, args.target, competition_scope=args.scope)

    elif args.feature == "ask":
        if not args.query:
            print("Error: --query is required for natural language QA.")
            sys.exit(1)
        entities = [args.player] if args.player else None
        res = service.answer_cricket_question(args.query, entities_involved=entities, competition_scope=args.scope)

    print("\n" + "=" * 70)
    print(f"TIER USED: {res.get('tier_used')} | VERIFIED: {res.get('verified')}")
    print("=" * 70 + "\n")
    print(res.get("response", ""))


if __name__ == "__main__":
    main()

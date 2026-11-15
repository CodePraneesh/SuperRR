#!/usr/bin/env python3
"""
SupeRR Intelligence — Phase 1 data audit, cleaning and feature engineering.
Usage:
  python supeRR_phase1_pipeline.py --zip "6af458274c1e8_data_pack.zip" --out phase1_output

Design principles:
- Preserve raw source files; never silently discard suspicious records.
- Use ball-by-ball data as the source of delivery events.
- Treat uncertain feed conventions explicitly and report them.
- Match-level chronological ordering prevents look-ahead in baselines.
"""
from __future__ import annotations
import argparse, json, zipfile, re, warnings
from pathlib import Path
import numpy as np
import pandas as pd

CSV_NAMES = [
    "competitions", "teams", "matches",
    "playing_eleven", "competition_team_player_mapping", "ball_by_ball"
]
BOOL_COLS = ["is_four", "is_six", "is_wicket", "is_played", "is_captain",
             "is_wk", "is_impact", "is_impact_off"]

def read_csv_from_zip(zf, name):
    path = f"Data Pack/{name}.csv"
    with zf.open(path) as f:
        return pd.read_csv(f, low_memory=False)

def json_safe(x):
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating,)): return None if np.isnan(x) else float(x)
    if isinstance(x, (np.bool_,)): return bool(x)
    if pd.isna(x): return None
    return x

def audit_table(df, name):
    return {
        "table": name, "rows": int(len(df)), "columns": int(len(df.columns)),
        "duplicate_full_rows": int(df.duplicated().sum()),
        "missing_cells": int(df.isna().sum().sum()),
        "columns_with_missing": {
            str(c): int(n) for c, n in df.isna().sum().items() if n > 0
        }
    }

def normalize_bool(series):
    if series.dtype == bool: return series
    return series.astype(str).str.lower().map({"true": True, "false": False, "1": True, "0": False})

def main(zip_path: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit").mkdir(exist_ok=True)
    (out / "processed").mkdir(exist_ok=True)
    (out / "features").mkdir(exist_ok=True)
    zf = zipfile.ZipFile(zip_path)
    tables = {n: read_csv_from_zip(zf, n) for n in CSV_NAMES}
    comps, teams, matches = tables["competitions"], tables["teams"], tables["matches"]
    xi, mapping, balls = (tables["playing_eleven"],
                          tables["competition_team_player_mapping"],
                          tables["ball_by_ball"])

    # Parse types and normalize booleans without changing source tables.
    matches["match_date"] = pd.to_datetime(matches["match_date"], errors="coerce", utc=True)
    for c in ["is_four","is_six","is_wicket"]:
        balls[c] = normalize_bool(balls[c]).fillna(False)
    for c in ["is_played","is_captain","is_wk"]:
        xi[c] = normalize_bool(xi[c]).fillna(False)

    # ---------- Structural and referential audit ----------
    table_audits = [audit_table(tables[n], n) for n in CSV_NAMES]
    issues = []
    def issue(severity, code, detail, count=None):
        issues.append({"severity":severity, "code":code, "count":count, "detail":detail})

    if matches["match_id"].duplicated().any():
        issue("ERROR","DUPLICATE_MATCH_ID","matches.match_id is not unique",int(matches.match_id.duplicated().sum()))
    if comps["comp_id"].duplicated().any():
        issue("ERROR","DUPLICATE_COMP_ID","competitions.comp_id is not unique",int(comps.comp_id.duplicated().sum()))
    if balls.duplicated(["match_id","innings","innings_ball_num"]).any():
        issue("ERROR","DUPLICATE_DELIVERY_KEY","Duplicate match/innings/innings_ball_num",int(balls.duplicated(["match_id","innings","innings_ball_num"]).sum()))
    missing_ball_matches = sorted(set(matches.match_id)-set(balls.match_id))
    extra_ball_matches = sorted(set(balls.match_id)-set(matches.match_id))
    issue("WARNING","MATCHES_WITHOUT_BALL_DATA","Match metadata has no ball-by-ball rows; exclude from delivery-based analysis.",len(missing_ball_matches))
    issue("ERROR" if extra_ball_matches else "INFO","ORPHAN_BALL_MATCHES","Ball records whose match_id is absent from matches.",len(extra_ball_matches))

    # Match/competition join.
    match_comp = matches.merge(comps, on="comp_id", how="left", validate="many_to_one", indicator=True)
    issue("ERROR" if (match_comp._merge!="both").any() else "INFO","MATCH_COMPETITION_JOIN","Every match should map to exactly one competition.",int((match_comp._merge!="both").sum()))
    match_comp = match_comp.drop(columns="_merge")

    # Official challenge scope is IPL + T20I. The supplied archive also contains
    # two Emerging Teams T20 competitions; retain them for audit but exclude from official rankings.
    match_comp["in_scope_competition"] = (
        match_comp["match_format"].eq("T20I") |
        match_comp["comp_name"].fillna("").str.startswith("IPL")
    )
    out_of_scope_matches=match_comp.loc[~match_comp.in_scope_competition,"match_id"].tolist()
    issue("INFO","OUT_OF_SCOPE_T20_COMPETITIONS","Emerging Teams T20 competitions are retained for audit but excluded because the brief specifies IPL and T20I.",len(out_of_scope_matches))
    comp_counts = (match_comp.groupby(["match_format","comp_name","season"], dropna=False)
                   .agg(match_rows=("match_id","nunique"),
                        matches_with_ball_data=("match_id",lambda s:s.isin(balls.match_id).sum()))
                   .reset_index())
    comp_counts.to_csv(out/"audit"/"competition_match_coverage.csv",index=False)

    # Referential checks.
    known_matches=set(matches.match_id)
    known_players=set(mapping.player_id)
    unknown_xi_matches=int((~xi.match_id.isin(known_matches)).sum())
    unknown_ball_matches=int((~balls.match_id.isin(known_matches)).sum())
    issue("WARNING","XI_UNKNOWN_MATCH","Playing XI rows refer to unknown match IDs.",unknown_xi_matches)
    issue("WARNING","BALL_UNKNOWN_MATCH","Ball rows refer to unknown match IDs.",unknown_ball_matches)
    map_key_dups=int(mapping.duplicated(["comp_id","team_id","player_id"]).sum())
    issue("WARNING","DUPLICATE_PLAYER_MAPPING","Duplicate competition/team/player mapping keys.",map_key_dups)
    xi_key_dups=int(xi.duplicated(["match_id","team_id","player_id"]).sum())
    issue("WARNING","DUPLICATE_XI_PLAYER","A player appears more than once for a team/match in playing_eleven; may reflect impact/substitution or source batting-order variants. Preserve and inspect.",xi_key_dups)

    # Ball-by-ball value checks.
    numeric_cols=["runs","extras1_runs","extras_2_runs","overid","over_ball_num","innings_ball_num"]
    for c in numeric_cols:
        balls[c]=pd.to_numeric(balls[c],errors="coerce")
    neg_count=int(((balls[["runs","extras1_runs","extras_2_runs"]]<0).any(axis=1)).sum())
    issue("ERROR" if neg_count else "INFO","NEGATIVE_RUN_VALUES","Negative batter-run or extras values.",neg_count)
    issue("WARNING","MISSING_CORE_DELIVERY_FIELDS","Missing match/innings/sequence/striker/bowler identifiers.",int(balls[["match_id","innings","innings_ball_num","striker_id","bowler_id"]].isna().any(axis=1).sum()))
    issue("WARNING","WICKET_WITHOUT_DISMISSAL","Wicket flag true but dismissal type missing.",int((balls.is_wicket & balls.dismissal_type.isna()).sum()))
    issue("WARNING","DISMISSAL_WITHOUT_WICKET","Dismissal type populated while wicket flag false.",int((~balls.is_wicket & balls.dismissal_type.notna()).sum()))
    issue("WARNING","FOUR_FLAG_MISMATCH","is_four does not match batter runs == 4.",int((balls.is_four != (balls.runs==4)).sum()))
    issue("WARNING","SIX_FLAG_MISMATCH","is_six does not match batter runs == 6.",int((balls.is_six != (balls.runs==6)).sum()))
    issue("WARNING","UNKNOWN_EXTRAS_TYPES","Unrecognized extras_type values require review.",int((~balls.extras_type.fillna("none").isin(["none","wide","legbyes","byes","Overstep","other","Penalty"])).sum()))
    issue("WARNING","UNLABELLED_NONZERO_EXTRAS","Extras runs exist while extras_type is missing.",int((balls.extras_type.isna() & ((balls.extras1_runs.fillna(0)>0)|(balls.extras_2_runs.fillna(0)>0))).sum()))

    # Duplicate and sequence audit per innings.
    innings_audit=(balls.groupby(["match_id","innings"],dropna=False)
       .agg(deliveries=("innings_ball_num","size"),
            distinct_seq=("innings_ball_num","nunique"),
            max_over=("overid","max"), max_ball_in_over=("over_ball_num","max"),
            wickets=("is_wicket","sum"), batter_runs=("runs","sum"),
            extras1=("extras1_runs","sum"), extras2=("extras_2_runs","sum"))
       .reset_index())
    innings_audit["sequence_gap_or_duplicate"] = innings_audit.deliveries != innings_audit.distinct_seq
    innings_audit.to_csv(out/"audit"/"innings_audit.csv",index=False)
    seq_count=int(innings_audit.sequence_gap_or_duplicate.sum())
    issue("ERROR" if seq_count else "INFO","INNINGS_SEQUENCE_DUPLICATES","Innings have repeated innings_ball_num values.",seq_count)

    # Extras diagnostics: source's runs field aligns with batter runs (4/6 flags);
    # extras1/extras2 are retained separately because 'other' and 'Overstep'
    # semantics should not be silently guessed.
    extras_audit=(balls.groupby("extras_type",dropna=False)
       .agg(deliveries=("match_id","size"),batter_runs=("runs","sum"),
            extras1_runs=("extras1_runs","sum"),extras2_runs=("extras_2_runs","sum"))
       .reset_index())
    extras_audit["extras_type"] = extras_audit["extras_type"].fillna("(no extras)")
    extras_audit.to_csv(out/"audit"/"extras_audit.csv",index=False)

    # ---------- Build enriched delivery table ----------
    # Join match/competition context. Ball data already has IDs/names for batter/bowler.
    keep_match=["match_id","comp_id","match_date","stage","venue_id","venue_country",
                "home_team_id","home_team","away_team_id","away_team",
                "first_inn_revised_overs","second_inn_revised_overs","revised_target",
                "win_team_id","result","match_format","comp_name","season","in_scope_competition"]
    d=balls.merge(match_comp[keep_match],on="match_id",how="left",validate="many_to_one")
    # Team and player mapping joins are on competition-specific IDs.
    team_lookup=teams.drop_duplicates(["comp_id","team_id"])
    d=d.merge(team_lookup.rename(columns={"team_id":"batting_team_id","team_name":"mapped_batting_team"}),
              on=["comp_id","batting_team_id"],how="left",validate="many_to_one")
    d=d.merge(team_lookup.rename(columns={"team_id":"bowling_team_id","team_name":"mapped_bowling_team"}),
              on=["comp_id","bowling_team_id"],how="left",validate="many_to_one")
    player_lookup=mapping.drop_duplicates(["comp_id","player_id"])[["comp_id","player_id","player_name","team_name"]]
    d=d.merge(player_lookup.rename(columns={"player_id":"striker_id","player_name":"mapped_striker_name"}),
              on=["comp_id","striker_id"],how="left",validate="many_to_one")
    d=d.merge(player_lookup.rename(columns={"player_id":"bowler_id","player_name":"mapped_bowler_name"}),
              on=["comp_id","bowler_id"],how="left",validate="many_to_one")
    d["striker_name_clean"]=d["mapped_striker_name"].fillna(d["striker_name"])
    d["bowler_name_clean"]=d["mapped_bowler_name"].fillna(d["bowler_name"])
    issue("WARNING","STRIKER_MAPPING_MISSING","Striker player ID has no competition-specific mapping; use source name fallback.",int(d["mapped_striker_name"].isna().sum()))
    issue("WARNING","BOWLER_MAPPING_MISSING","Bowler player ID has no competition-specific mapping; use source name fallback.",int(d["mapped_bowler_name"].isna().sum()))
    issue("WARNING","BATTING_TEAM_MAPPING_MISSING","Batting team ID has no competition-specific team mapping.",int(d["mapped_batting_team"].isna().sum()))
    d["batting_team_name_clean"]=d["mapped_batting_team"].fillna(d["batting_team_id"].astype("Int64").astype(str))
    d["bowling_team_name_clean"]=d["mapped_bowling_team"].fillna(d["bowling_team_id"].astype("Int64").astype(str))

    # Sort by actual delivery sequence. over_ball_num counts attempted deliveries;
    # innings_ball_num is retained as source sequence and used for state updates.
    d=d.sort_values(["match_id","innings","innings_ball_num"]).reset_index(drop=True)
    # Feed interpretation:
    # runs = batter runs (validated against four/six flags); extras fields retained.
    d["batter_runs"]=d["runs"].fillna(0).astype(int)
    d["extras1"]=d["extras1_runs"].fillna(0).astype(int)
    d["extras2"]=d["extras_2_runs"].fillna(0).astype(int)
    d["total_delivery_runs"]=d["batter_runs"]+d["extras1"]+d["extras2"]
    d["extras_label"]=d["extras_type"].fillna("none").astype(str).str.lower()
    d["is_wide"]=d["extras_label"].eq("wide")
    d["is_no_ball"]=d["extras_label"].eq("overstep")
    d["is_penalty_event"]=d["extras_label"].eq("penalty")
    d["unlabelled_extras"]=(d["extras_type"].isna() & ((d["extras1"]>0)|(d["extras2"]>0)))
    d["is_unknown_extra"]=d["extras_label"].eq("other") | d["is_penalty_event"] | d["unlabelled_extras"]
    d["derived_four"]=d["batter_runs"].eq(4)
    d["derived_six"]=d["batter_runs"].eq(6)
    # Official cricket convention: wides/no-balls do not count as legal balls.
    # 'other' is not classified as legal/non-legal without source documentation.
    d["legal_ball"]=~(d["is_wide"]|d["is_no_ball"]|d["is_unknown_extra"])
    # No-balls count as balls faced; wides and standalone penalty/unlabelled events do not.
    # 'other' is kept as a faced ball for the batter but flagged as uncertain for bowling/legal-ball stats.
    d["batter_faced_ball"]=~(d["is_wide"]|d["is_penalty_event"]|d["unlabelled_extras"])
    # Bowler-conceded runs: batter runs + wide/no-ball penalties. Byes/legbyes excluded.
    # For ambiguous 'other', keep a separate field and do not silently allocate extras2.
    d["bowler_runs_conceded"]=d["batter_runs"]+np.where(d["is_wide"],d["extras1"]+d["extras2"],0)+np.where(d["is_no_ball"],d["extras1"],0)
    d["bowler_runs_conceded_known"]=~(d["is_unknown_extra"]|d["unlabelled_extras"])
    d["bowler_wicket"]=d["is_wicket"] & d["dismissal_type"].fillna("").str.lower().isin(
        ["bowled","caught","lbw","stump","hit wicket"])
    # 'Retire Out' is a team wicket but not credited to bowler; run outs/obstructing excluded.
    d["is_team_wicket"]=d["is_wicket"]

    # XI lookup is diagnostic only: it can have multiple batting_order rows for one player.
    xi_s=xi.sort_values(["match_id","team_id","player_id","batting_order"]).drop_duplicates(
        ["match_id","team_id","player_id"],keep="first")
    d=d.merge(xi_s[["match_id","team_id","player_id","batting_order","is_wk","is_impact"]].rename(
        columns={"team_id":"xi_batting_team_id","player_id":"xi_striker_id",
                 "batting_order":"xi_batting_order","is_wk":"striker_is_wk","is_impact":"striker_is_impact"}),
        left_on=["match_id","batting_team_id","striker_id"],
        right_on=["match_id","xi_batting_team_id","xi_striker_id"],how="left")
    d["xi_striker_match"]=d["xi_striker_id"].notna()
    issue("WARNING","STRIKER_NOT_IN_XI","Striker not found in playing XI mapping; impact/substitution/source coverage may explain.",int((~d.xi_striker_match).sum()))

    # ---------- Pre-delivery match state ----------
    # Innings target comes from completed first innings total (innings 1); revised_target
    # overrides it when supplied. The target is constant within a chase.
    innings_totals=(d[d.innings==1].groupby("match_id").total_delivery_runs.sum().rename("first_innings_total"))
    d=d.merge(innings_totals,on="match_id",how="left")
    d["target_runs"]=np.where(d.innings==2,
        d["revised_target"].fillna(d["first_innings_total"]+1),np.nan)
    # Revised overs per innings; ordinary T20 defaults to 20. Super overs are separate.
    d["overs_limit"]=20.0
    d.loc[d.innings==1,"overs_limit"]=d.loc[d.innings==1,"first_inn_revised_overs"].fillna(20)
    d.loc[d.innings==2,"overs_limit"]=d.loc[d.innings==2,"second_inn_revised_overs"].fillna(20)
    d.loc[d.innings>=3,"overs_limit"]=1.0

    state_cols=[]
    # Per match-innings sequential state; values are before this delivery.
    for (mid,inn), idx in d.groupby(["match_id","innings"],sort=False).groups.items():
        g=d.loc[idx].sort_values("innings_ball_num")
        cum_runs=g["total_delivery_runs"].cumsum().shift(fill_value=0)
        cum_wk=g["is_team_wicket"].astype(int).cumsum().shift(fill_value=0)
        legal_before=g["legal_ball"].astype(int).cumsum().shift(fill_value=0)
        d.loc[g.index,"score_before"]=cum_runs.values
        d.loc[g.index,"wickets_lost_before"]=cum_wk.values
        d.loc[g.index,"legal_balls_before"]=legal_before.values
    d["balls_remaining"]=np.maximum(0,(d["overs_limit"]*6-d["legal_balls_before"]).fillna(0))
    d["wickets_in_hand"]=np.maximum(0,10-d["wickets_lost_before"])
    d["overs_elapsed"]=d["legal_balls_before"]/6.0
    # Phase boundaries adapt to shortened innings: first 6 overs (or whole innings
    # if shorter), middle overs, and final 5 overs.
    death_start=np.maximum(0,d["overs_limit"]-5)
    d["innings_phase"]=np.select(
        [d["innings"]>=3, d["overs_elapsed"]<np.minimum(6,d["overs_limit"]),
         d["overs_elapsed"]>=death_start],
        ["super_over_or_extra","powerplay","death"], default="middle")
    d["runs_required"]=np.where(d.innings==2,np.maximum(0,d["target_runs"]-d["score_before"]),np.nan)
    d["required_run_rate"]=np.where((d.innings==2)&(d.balls_remaining>0),
        d["runs_required"]/(d["balls_remaining"]/6),np.nan)
    d["current_run_rate"]=np.where(d["legal_balls_before"]>0,
        d["score_before"]/(d["legal_balls_before"]/6),np.nan)
    d["runs_remaining_to_par"] = np.where(d.innings==2,d["runs_required"],np.nan)
    d["chase_pressure_index"]=np.where(d.innings==2,
        (d["required_run_rate"].clip(0,30)/12)*0.45+
        ((10-d["wickets_in_hand"])/10)*0.25+
        (1-(d["balls_remaining"]/(d["overs_limit"]*6).replace(0,np.nan))).clip(0,1)*0.30,
        np.nan)
    # First innings: pressure is phase + wicket scarcity; add par-relative features in Phase 2.
    d["first_innings_pressure_index"]=np.where(d.innings==1,
        (d["overs_elapsed"]/d["overs_limit"].replace(0,np.nan)).clip(0,1)*0.35+
        ((10-d["wickets_in_hand"])/10)*0.45+
        (d["innings_phase"].eq("death").astype(float))*0.20,
        np.nan)
    d["pre_delivery_pressure_index"]=np.where(d.innings==2,d["chase_pressure_index"],
        np.where(d.innings==1,d["first_innings_pressure_index"],np.nan))
    # Current batter and bowler IDs/names are retained; no outcome from current ball is used above.

    # ---------- Player baselines ----------
    # Per-player non-pressure and overall summaries; pressure index is a provisional
    # feature for later calibrated pressure thresholding.
    main=d[d.innings.isin([1,2]) & d.in_scope_competition.fillna(False)].copy()
    main["is_pressure_provisional"]=main["pre_delivery_pressure_index"].ge(0.60)
    batter_agg=(main.groupby(["striker_id","striker_name_clean","match_format"],dropna=False)
       .agg(deliveries=("batter_faced_ball","sum"),
            batter_runs=("batter_runs","sum"),
            fours=("derived_four","sum"),sixes=("derived_six","sum"),
            matches=("match_id","nunique"),
            pressure_balls=("batter_faced_ball",lambda s:s[main.loc[s.index,"is_pressure_provisional"]].sum()),
            pressure_runs=("batter_runs",lambda s:s[main.loc[s.index,"is_pressure_provisional"]].sum()),
            nonpressure_balls=("batter_faced_ball",lambda s:s[~main.loc[s.index,"is_pressure_provisional"]].sum()),
            nonpressure_runs=("batter_runs",lambda s:s[~main.loc[s.index,"is_pressure_provisional"]].sum()))
       .reset_index())
    # Dismissals are attributed to the actual dismissed_player_id (not always striker).
    batter_outs=(main[main.dismissed_player_id.notna()]
       .groupby(["dismissed_player_id","match_format"]).size()
       .rename("dismissals").reset_index()
       .rename(columns={"dismissed_player_id":"striker_id"}))
    batter_agg=batter_agg.merge(batter_outs,on=["striker_id","match_format"],how="left")
    batter_agg["dismissals"]=batter_agg["dismissals"].fillna(0).astype(int)
    batter_agg["batting_average"]=batter_agg["batter_runs"]/batter_agg["dismissals"].replace(0,np.nan)
    batter_agg["strike_rate"]=100*batter_agg.batter_runs/batter_agg.deliveries.replace(0,np.nan)
    batter_agg["pressure_strike_rate"]=100*batter_agg.pressure_runs/batter_agg.pressure_balls.replace(0,np.nan)
    batter_agg["nonpressure_strike_rate"]=100*batter_agg.nonpressure_runs/batter_agg.nonpressure_balls.replace(0,np.nan)
    batter_agg["pressure_sr_delta"]=batter_agg.pressure_strike_rate-batter_agg.nonpressure_strike_rate
    batter_agg.to_csv(out/"features"/"batter_baselines_provisional.csv",index=False)

    bowl_main=main.copy()
    bowl_agg=(bowl_main.groupby(["bowler_id","bowler_name_clean","match_format"],dropna=False)
       .agg(balls_bowled=("legal_ball","sum"),
            runs_conceded=("bowler_runs_conceded",lambda s:s[bowl_main.loc[s.index,"bowler_runs_conceded_known"]].sum()),
            wickets=("bowler_wicket","sum"),
            matches=("match_id","nunique"),
            pressure_balls=("legal_ball",lambda s:s[bowl_main.loc[s.index,"is_pressure_provisional"]].sum()),
            pressure_runs=("bowler_runs_conceded",lambda s:s[bowl_main.loc[s.index,"is_pressure_provisional"] & bowl_main.loc[s.index,"bowler_runs_conceded_known"]].sum()),
            pressure_wickets=("bowler_wicket",lambda s:s[bowl_main.loc[s.index,"is_pressure_provisional"]].sum()))
       .reset_index())
    bowl_agg["economy"]=6*bowl_agg.runs_conceded/bowl_agg.balls_bowled.replace(0,np.nan)
    bowl_agg["pressure_economy"]=6*bowl_agg.pressure_runs/bowl_agg.pressure_balls.replace(0,np.nan)
    bowl_agg.to_csv(out/"features"/"bowler_baselines_provisional.csv",index=False)

    # Match-level summaries support chronological splits and match bootstrap.
    match_summary=(main.groupby(["match_id","comp_id","match_date","match_format","innings"])
       .agg(deliveries=("innings_ball_num","size"),total_runs=("total_delivery_runs","sum"),
            wickets=("is_team_wicket","sum"),legal_balls=("legal_ball","sum"))
       .reset_index())
    match_summary.to_csv(out/"features"/"match_innings_summary.csv",index=False)

    # Output cleaned delivery file. Keep audit fields so ambiguous feed semantics remain visible.
    out_cols=list(d.columns)
    d.to_csv(out/"processed"/"deliveries_enriched.csv",index=False)
    match_comp.to_csv(out/"processed"/"matches_enriched.csv",index=False)
    xi_s.to_csv(out/"processed"/"playing_eleven_deduplicated_diagnostic.csv",index=False)

    # Assumption register: explicit, testable, not silently asserted.
    assumptions=[
      {"item":"runs","decision":"Treat ball_by_ball.runs as batter runs. Source boundary flags disagree on 23 rows; derived four/six counts use runs==4/6, not source flags.","status":"validated_with_flag_exceptions"},
      {"item":"team_total","decision":"Provisional total_delivery_runs = runs + extras1_runs + extras_2_runs. Must reconcile to innings scorecards if available.","status":"needs_scorecard_reconciliation"},
      {"item":"legal_ball","decision":"wide and Overstep treated as illegal; 'other', Penalty and unlabelled nonzero extras treated as unknown/non-legal pending feed documentation.","status":"partially_validated"},
      {"item":"batter_ball_faced","decision":"Wides and standalone Penalty/unlabelled-extra events excluded; Overstep and 'other' count as faced balls provisionally. Confirm 'other' with feed documentation.","status":"partially_validated"},
      {"item":"bowler_runs","decision":"Batter runs + wide extras + Overstep penalty; byes/legbyes excluded. 'other', Penalty and unlabelled extras are flagged and excluded from known-concession baseline totals.","status":"partially_validated"},
      {"item":"bowler_wickets","decision":"Bowled, caught, LBW, stumped, hit wicket credited; run out, retire out and obstruction not credited.","status":"rule_based"},
      {"item":"pressure","decision":"Continuous pre-delivery state index created separately for chases and first innings; provisional threshold 0.60 only for baseline preview.","status":"provisional"},
      {"item":"first_innings_par","decision":"Not calculated in Phase 1; needs historical expected-score model in Phase 2.","status":"pending_phase_2"},
      {"item":"playing_eleven_duplicates","decision":"Do not treat repeated match/player rows as separate players; retain one diagnostic row using earliest batting_order, while preserving raw source and reporting conflicts.","status":"rule_based"},
      {"item":"missing_ball_data","decision":"16 match metadata rows have no ball-by-ball records; exclude from delivery-based analysis and document.","status":"validated"}
    ]
    pd.DataFrame(assumptions).to_csv(out/"audit"/"assumption_register.csv",index=False)
    pd.DataFrame(issues).to_csv(out/"audit"/"issues.csv",index=False)
    # Summary JSON
    summary={
      "tables":table_audits,
      "matches_rows":len(matches),"matches_with_ball_data":int(balls.match_id.nunique()),
      "matches_without_ball_data":len(missing_ball_matches),
      "official_scope_matches":int(match_comp.in_scope_competition.sum()),
      "official_scope_matches_with_ball_data":int(match_comp.loc[match_comp.in_scope_competition,"match_id"].isin(balls.match_id).sum()),
      "out_of_scope_t20_matches":len(out_of_scope_matches),
      "official_scope_deliveries":int(d.in_scope_competition.fillna(False).sum()),
      "ball_rows":len(balls),"innings_rows":len(innings_audit),
      "competition_formats":{str(k):int(v) for k,v in match_comp.match_format.value_counts(dropna=False).items()},
      "extras_types":{str(k):int(v) for k,v in balls.extras_type.fillna("(none)").value_counts().items()},
      "dismissal_types":{str(k):int(v) for k,v in balls.loc[balls.is_wicket,"dismissal_type"].fillna("(missing)").value_counts().items()},
      "duplicate_xi_player_keys":xi_key_dups,
      "duplicate_mapping_keys":map_key_dups,
      "unknown_ball_match_rows":unknown_ball_matches,
      "unknown_xi_match_rows":unknown_xi_matches,
      "four_flag_mismatches":int((balls.is_four != (balls.runs==4)).sum()),
      "six_flag_mismatches":int((balls.is_six != (balls.runs==6)).sum()),
      "unlabelled_nonzero_extras":int((balls.extras_type.isna() & ((balls.extras1_runs.fillna(0)>0)|(balls.extras_2_runs.fillna(0)>0))).sum()),
      "wicket_without_type":int((balls.is_wicket & balls.dismissal_type.isna()).sum()),
      "nonwicket_with_type":int((~balls.is_wicket & balls.dismissal_type.notna()).sum()),
      "innings_sequence_duplicates":int(innings_audit.sequence_gap_or_duplicate.sum()),
      "pressure_threshold_preview":0.60,
      "outputs":["processed/deliveries_enriched.csv","processed/matches_enriched.csv",
                 "features/batter_baselines_provisional.csv","features/bowler_baselines_provisional.csv",
                 "features/match_innings_summary.csv","audit/issues.csv","audit/assumption_register.csv"]
    }
    (out/"audit"/"audit_summary.json").write_text(json.dumps(summary,indent=2,default=json_safe))
    print(json.dumps(summary,indent=2,default=json_safe))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--zip",required=True,type=Path)
    p.add_argument("--out",default="phase1_output",type=Path)
    a=p.parse_args()
    main(a.zip,a.out)

"""Shared scoring logic for the shortlist (08) and the sensitivity analysis (10).

Pipeline per scenario
1. Percentiles are computed within each league and role (CB vs CB, FB vs FB), because the two data
   providers count events differently and leagues differ in style.
2. Each percentile is multiplied by the league-strength factor (PL = 1), so a 90th-percentile
   Eredivisie defender counts as roughly a 79th-percentile Premier League one.
3. Fit score = weighted mean of the adjusted percentiles; United's gap metrics count GAP_WEIGHT times.
4. Shortlist = age filter, every gap metric at or above GAP_FLOOR (adjusted), best fit per slot.
   The realistic shortlist adds the market rules: value within budget, not at a rival club,
   and not on loan to his current club.
"""
import numpy as np
import pandas as pd
from config import (PROCESSED, TABLES, COMMON_METRICS, LEAGUE_FACTOR, CONTRACT_REF_DATE,
                    RIVAL_CLUBS, CLUB)

UNITED_NAMES = {CLUB, "Manchester United"}

def load_pool():
    pl = pd.read_csv(PROCESSED / "pool_premier_league_market.csv")
    other = pd.read_csv(PROCESSED / "pool_other_leagues.csv")
    pool = pd.concat([pl, other], ignore_index=True)
    pool["contract_end"] = pd.to_datetime(pool.contract_end, errors="coerce")
    pool = add_percentiles(pool)
    pool = add_availability(pool)
    return pool

def add_percentiles(pool):
    out = []
    for (league, role), g in pool.groupby(["league", "role"]):
        g = g.copy()
        for label, col in COMMON_METRICS[role].items():
            g[f"pct_{label}"] = g[col].rank(pct=True) * 100
        out.append(g)
    return pd.concat(out, ignore_index=True)

def add_availability(pool):
    ref = pd.Timestamp(CONTRACT_REF_DATE)
    pool["years_left_jul27"] = ((pool.contract_end - ref).dt.days / 365.25).round(1)
    club_now = pool.current_club.fillna(pool.club_2526).astype(str).str.replace(" (2025/26)", "", regex=False)
    pool["rival_club"] = club_now.isin(RIVAL_CLUBS)
    pool["united_player"] = club_now.isin(UNITED_NAMES) | pool.club_2526.isin(UNITED_NAMES)
    status = np.select(
        [pool.rival_club, pool.on_loan.fillna(False).astype(bool), pool.years_left_jul27.isna(),
         pool.years_left_jul27 <= 1, pool.years_left_jul27 <= 2],
        ["Rival club (unlikely seller)", "On loan", "Contract unknown",
         "High (1 year or less left)", "Medium (2 years left)"],
        default="Low (3+ years left)")
    pool["availability"] = status
    return pool

def gap_metrics(threshold):
    """United gap metrics (from 05_gap_analysis) that exist in the cross-league metric set."""
    gaps = pd.read_csv(TABLES / "united_gap_analysis.csv")
    return {role: [m for m in t[t.united_weighted_percentile < threshold].metric if m in COMMON_METRICS[role]]
            for role, t in gaps.groupby("role")}

def score(pool, gaps, weight, factors=None):
    factors = factors or LEAGUE_FACTOR
    out = []
    for role, g in pool.groupby("role"):
        g = g.copy()
        f = g.league.map(factors)
        labels = list(COMMON_METRICS[role])
        w = {l: (weight if l in gaps[role] else 1) for l in labels}
        for l in labels:
            g[f"adj_{l}"] = g[f"pct_{l}"] * f
        g["fit_score"] = sum(g[f"adj_{l}"].fillna(0) * w[l] for l in labels) / sum(w.values())
        g["min_gap_adj"] = g[[f"adj_{l}" for l in gaps[role]]].min(axis=1) if gaps[role] else 100
        out.append(g)
    return pd.concat(out, ignore_index=True)

def shortlist(scored, floor, slots, max_age, budget=None, realistic=False):
    eligible = scored[(~scored.united_player) & (scored.age_aug27 <= max_age) & (scored.min_gap_adj >= floor)]
    if realistic:
        eligible = eligible[(eligible.market_value_m <= budget) & (~eligible.rival_club) &
                            (~eligible.on_loan.fillna(False).astype(bool))]
    picks = [eligible[eligible.side == side].sort_values("fit_score", ascending=False).head(n)
             for side, n in slots.items()]
    return pd.concat(picks, ignore_index=True)

"""Step 8: score every defender in the PL, Eredivisie and Belgian Pro League on United's gaps,
then build two 10-player shortlists:
- best fit: the strongest profiles regardless of price or availability
- realistic: same rules plus market value within budget, not at a rival club, not on loan
"""
import pandas as pd
from config import (TABLES, PROCESSED, GAP_THRESHOLD, GAP_WEIGHT, GAP_FLOOR, MAX_AGE, SLOTS,
                    BUDGET_EUR_M, LEAGUE_FACTOR, COMMON_METRICS)
from scoring import load_pool, gap_metrics, score, shortlist

pool = load_pool()
gaps = gap_metrics(GAP_THRESHOLD)
print("Gap metrics (weighted x%s):" % GAP_WEIGHT, gaps)
print("League factors:", LEAGUE_FACTOR)
print("Pool by league/side:\n", pool.groupby(["league", "side"]).size().unstack())

scored = score(pool, gaps, GAP_WEIGHT)
scored.to_csv(PROCESSED / "scored_all_leagues.csv", index=False)

cols = ["player", "league", "club_2526", "current_club", "age_aug27", "minutes", "fit_score", "min_gap_adj",
        "market_value_m", "value_source", "years_left_jul27", "availability"]

# Ranked lists per position (eligible by age, all prices)
for side in ["LB", "CB", "RB"]:
    role = "CB" if side == "CB" else "FB"
    t = scored[(scored.side == side) & (~scored.united_player) & (scored.age_aug27 <= MAX_AGE)]
    t = t.sort_values("fit_score", ascending=False).head(20)
    t[cols + [f"adj_{g}" for g in gaps[role]]].round(1).to_csv(TABLES / f"top20_{side}.csv", index=False)

out_cols = ["side"] + cols
best = shortlist(scored, GAP_FLOOR, SLOTS, MAX_AGE)
real = shortlist(scored, GAP_FLOOR, SLOTS, MAX_AGE, budget=BUDGET_EUR_M, realistic=True)
best[out_cols].round(1).to_csv(TABLES / "shortlist_best_fit.csv", index=False)
real[out_cols].round(1).to_csv(TABLES / "shortlist_realistic.csv", index=False)

pd.set_option("display.width", 250)
print(f"\n=== Best-fit shortlist (age <= {int(MAX_AGE)}, every gap metric >= {GAP_FLOOR} league-adjusted) ===")
print(best[out_cols].round(1).to_string(index=False))
print(f"\n=== Realistic shortlist (+ value <= EUR {BUDGET_EUR_M}m, not a rival club, not on loan) ===")
print(real[out_cols].round(1).to_string(index=False))

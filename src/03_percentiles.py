"""Step 3: PL per-90 metrics and percentile ranks within each role (CB vs CB, FB vs FB).

Two outputs:
- percentiles_{CB,FB}.csv : the 10-metric radar set used to diagnose United (04, 05)
- pool_premier_league.csv  : the cross-league scouting metrics (config.COMMON_METRICS) in a standard
                             format, so PL players can be scored alongside Eredivisie and Belgian players
Tackles, interceptions, clearances, blocks and recoveries use possession-adjusted (PAdj) values.
"""
import numpy as np
import pandas as pd
from config import PROCESSED, CB_METRICS, FB_METRICS, INVERTED, PADJ_STATS

df = pd.read_csv(PROCESSED / "defenders_2526_qualified.csv")
n90 = df.minutes_played / 90
for c in ["tackles", "interceptions", "clearances", "blocks", "aerial_duels_won", "ground_duels_won", "dribbled_past",
          "accurate_long_balls", "recoveries", "accurate_crosses", "chances_created", "xa", "final_third_passes",
          "successful_dribbles"] + [f"padj_{s}" for s in PADJ_STATS]:
    df[f"{c}_p90"] = df[c] / n90
df["pass_pct"] = df.accurate_passes / df.pass_att * 100
df["aerial_pct"] = df.aerial_duels_won / df.aer_att.replace(0, np.nan) * 100
df["ground_pct"] = df.ground_duels_won / df.ground_att.replace(0, np.nan) * 100

# --- radar percentiles (United diagnosis)
for role, metrics in [("CB", CB_METRICS), ("FB", FB_METRICS)]:
    g = df[df.role == role].copy()
    for label, col in metrics.items():
        values = -g[col] if label in INVERTED else g[col]   # lower is better for inverted metrics
        g[f"pct_{label}"] = values.rank(pct=True) * 100
    g.to_csv(PROCESSED / f"percentiles_{role}.csv", index=False)
    print(f"{role}: {len(g)} players, {len(metrics)} radar metrics")

# --- standardised scouting pool
pool = pd.DataFrame({
    "player": df.first_name.str.cat(df.second_name, sep=" "), "web_name": df.web_name,
    "club_2526": df.club, "league": "Premier League", "role": df.role, "side": df.side,
    "age_aug27": df.age_aug27, "minutes": df.minutes_played, "player_id": df.player_id,
    "long_balls_p90": df.accurate_long_balls_p90, "aerials_won_p90": df.aerial_duels_won_p90,
    "padj_int_p90": df.padj_interceptions_p90, "padj_blocks_p90": df.padj_blocks_p90,
    "aerial_pct": df.aerial_pct, "pass_pct": df.pass_pct, "ground_pct": df.ground_pct,
    "final_third_p90": df.final_third_passes_p90, "crosses_p90": df.accurate_crosses_p90,
    "dribbles_p90": df.successful_dribbles_p90, "xa_p90": df.xa_p90,
    "ground_won_p90": df.ground_duels_won_p90, "chances_p90": df.chances_created_p90,
})
pool.to_csv(PROCESSED / "pool_premier_league.csv", index=False)
print("PL scouting pool:", len(pool))

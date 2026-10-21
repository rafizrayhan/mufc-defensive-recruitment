"""Step 2: combine 38 gameweeks into season totals for every Premier League defender,
possession-adjust the defensive volume stats match by match,
classify each player as centre back (CB) or full back (FB) from average match position,
and tag full backs as left (LB) or right (RB).
"""
import glob
import numpy as np
import pandas as pd
from config import (PL_DIR, SEASON_DIR, FPL_PLAYERS_RAW, PROCESSED, TABLES, MIN_MINUTES,
                    CB_FB_WIDTH_THRESHOLD, BORDERLINE_RANGE, AGE_REFERENCE_DATE, PADJ_STATS)

def load(name, key=("player_id", "match_id")):
    files = sorted(glob.glob(str(PL_DIR / "GW*" / f"{name}.csv")))
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True).drop_duplicates(list(key))

pms = load("playermatchstats")
pos = load("average_positions")
lu = load("lineups")
matches = load("matches", key=("match_id",))[["match_id", "home_possession", "away_possession"]]
players = pd.read_csv(SEASON_DIR / "players.csv")
teams = pd.read_csv(SEASON_DIR / "teams.csv")[["code", "name"]]
print("Matches loaded:", pms.match_id.nunique())

defs = players.loc[players.position == "Defender", ["player_id", "web_name", "first_name", "second_name"]]
m = (pms.merge(defs, on="player_id")
        .merge(lu[["player_id", "match_id", "team_code", "team_side"]], on=["player_id", "match_id"], how="left")
        .merge(pos[["player_id", "match_id", "x", "y"]], on=["player_id", "match_id"], how="left")
        .merge(matches, on="match_id", how="left"))
m = m[m.minutes_played > 0].copy()

# Possession adjustment (sigmoid method popularised by StatsBomb):
# a defender whose team has more of the ball faces fewer chances to tackle, intercept or clear,
# so his defensive actions are scaled up; a defender on a low-possession team is scaled down.
# At 50% possession the factor is 1.
m["team_possession"] = np.where(m.team_side == "home", m.home_possession, m.away_possession)
m["padj_factor"] = 2 / (1 + np.exp(-0.1 * (m.team_possession.fillna(50) - 50)))
for s in PADJ_STATS:
    m[f"padj_{s}"] = m[s] * m.padj_factor

# Derive attempts so percentage stats can be rebuilt from season totals
m["pass_att"] = np.where(m.accurate_passes_percent > 0, m.accurate_passes / (m.accurate_passes_percent / 100), 0)
m["aer_att"] = np.where(m.aerial_duels_won_percent > 0, m.aerial_duels_won / (m.aerial_duels_won_percent / 100), 0)
m["ground_att"] = np.where(m.ground_duels_won_percent > 0, m.ground_duels_won / (m.ground_duels_won_percent / 100), 0)
m["width"] = (m.y - 50).abs()   # distance from the centre line, 0-50

count_cols = ["tackles", "tackles_won", "interceptions", "blocks", "clearances", "headed_clearances", "recoveries",
              "dribbled_past", "duels_won", "duels_lost", "ground_duels_won", "aerial_duels_won", "fouls_committed",
              "accurate_passes", "final_third_passes", "accurate_long_balls", "accurate_crosses", "chances_created",
              "successful_dribbles", "touches", "xa", "xg", "goals", "assists", "defensive_contributions",
              "pass_att", "aer_att", "ground_att", "minutes_played"] + [f"padj_{s}" for s in PADJ_STATS]
agg = m.groupby(["player_id", "web_name", "first_name", "second_name"])[count_cols].sum().reset_index()

def weighted(col):
    d = m.dropna(subset=[col])
    return d.groupby("player_id").apply(lambda g: np.average(g[col], weights=g.minutes_played),
                                        include_groups=False).rename(f"avg_{col}")

# Club = the club the player played most minutes for
club = (m.groupby(["player_id", "team_code"]).minutes_played.sum().reset_index()
          .sort_values("minutes_played").drop_duplicates("player_id", keep="last")
          .merge(teams, left_on="team_code", right_on="code")[["player_id", "name"]]
          .rename(columns={"name": "club"}))

agg = (agg.merge(club, on="player_id")
          .merge(weighted("width"), on="player_id", how="left")
          .merge(weighted("x"), on="player_id", how="left")
          .merge(weighted("y"), on="player_id", how="left")
          .merge(weighted("team_possession"), on="player_id", how="left"))

# Ages (FPL player IDs match between the two datasets)
births = pd.read_csv(FPL_PLAYERS_RAW)[["id", "birth_date"]].rename(columns={"id": "player_id"})
agg = agg.merge(births, on="player_id", how="left")
agg["age_aug27"] = ((pd.Timestamp(AGE_REFERENCE_DATE) - pd.to_datetime(agg.birth_date)).dt.days / 365.25).round(1)

# Roles
agg["role"] = np.where(agg.avg_width < CB_FB_WIDTH_THRESHOLD, "CB", "FB")
agg["side"] = np.where(agg.role == "CB", "CB", np.where(agg.avg_y > 50, "LB", "RB"))  # y > 50 = left flank
agg["borderline"] = agg.avg_width.between(*BORDERLINE_RANGE)

agg.to_csv(PROCESSED / "defenders_2526_all.csv", index=False)
q = agg[agg.minutes_played >= MIN_MINUTES].copy()
q.to_csv(PROCESSED / "defenders_2526_qualified.csv", index=False)
(q[["web_name", "first_name", "second_name", "club", "minutes_played", "avg_width", "avg_x", "role", "side", "borderline"]]
   .sort_values(["role", "club", "minutes_played"], ascending=[True, True, False])
   .round(1).to_csv(TABLES / "defender_roles_2526.csv", index=False))
print(f"Qualified defenders ({MIN_MINUTES}+ mins): {len(q)}  |  roles: {q.role.value_counts().to_dict()}  |  borderline: {q.borderline.sum()}")

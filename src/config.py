"""Shared settings and paths for the Man United defensive recruitment project.

Every analyst choice (thresholds, weights, league discounts, budget, rival clubs) lives here,
so the sensitivity analysis in 10_sensitivity.py can vary them in one place.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
CHARTS = ROOT / "outputs" / "charts"
TABLES = ROOT / "outputs" / "tables"

# ---------------------------------------------------------------- external data (01_fetch_data.py)
CORE_REPO = RAW / "FPL-Core-Insights"            # PL match-level stats, average positions, possession
FPL_REPO = RAW / "Fantasy-Premier-League"        # PL birth dates
WYSCOUT_REPO = RAW / "Eredivisie-Scouting"       # Eredivisie + Belgian Pro League season exports, team possession
VALUES_REPO = RAW / "player-value-analyzer"      # Big-5 Transfermarkt values and current clubs

SEASON_DIR = CORE_REPO / "data" / "2025-2026"
PL_DIR = SEASON_DIR / "By Tournament" / "Premier League"
FPL_PLAYERS_RAW = FPL_REPO / "data" / "2025-26" / "players_raw.csv"
BIG5_VALUES = VALUES_REPO / "dashboard_v2" / "players.csv"
WYSCOUT_POSSESSION = WYSCOUT_REPO / "data" / "processed" / "team_possession.csv"
WYSCOUT_FILES = {
    "Eredivisie": WYSCOUT_REPO / "data" / "raw" / "DEF_MID_GK 2526.xlsx",
    "Belgian Pro League": WYSCOUT_REPO / "data" / "raw" / "BELGIUM DEF_MID_GK 2526.xlsx",
}

# ---------------------------------------------------------------- core settings
CLUB = "Man Utd"
MIN_MINUTES = 900
CB_FB_WIDTH_THRESHOLD = 23.75          # PL role split: avg distance from centre line (0-50 scale)
BORDERLINE_RANGE = (20, 28)
AGE_REFERENCE_DATE = "2027-08-01"      # start of 2027/28
WYSCOUT_AGE_OFFSET = 1.0               # Wyscout gives age at export (end of 2025/26); +1 year to reach Aug 2027

# League strength: Opta Power Rankings average team rating relative to the Premier League
# (The Analyst, Oct 2024: PL 87.9, Belgian Pro League 79.2, Eredivisie 77.3).
LEAGUE_RATING = {"Premier League": 87.9, "Belgian Pro League": 79.2, "Eredivisie": 77.3}
LEAGUE_FACTOR = {k: round(v / LEAGUE_RATING["Premier League"], 3) for k, v in LEAGUE_RATING.items()}

# ---------------------------------------------------------------- PL radar metrics (United diagnosis)
PADJ_STATS = ["tackles", "interceptions", "clearances", "blocks", "recoveries"]
CB_METRICS = {
    "Tackles": "padj_tackles_p90",
    "Interceptions": "padj_interceptions_p90",
    "Clearances": "padj_clearances_p90",
    "Blocks": "padj_blocks_p90",
    "Aerials won": "aerial_duels_won_p90",
    "Aerial win %": "aerial_pct",
    "Ground duels won": "ground_duels_won_p90",
    "Not dribbled past": "dribbled_past_p90",
    "Pass accuracy %": "pass_pct",
    "Accurate long balls": "accurate_long_balls_p90",
}
FB_METRICS = {
    "Tackles": "padj_tackles_p90",
    "Interceptions": "padj_interceptions_p90",
    "Recoveries": "padj_recoveries_p90",
    "Not dribbled past": "dribbled_past_p90",
    "Ground duels won": "ground_duels_won_p90",
    "Accurate crosses": "accurate_crosses_p90",
    "Chances created": "chances_created_p90",
    "xA": "xa_p90",
    "Final-third passes": "final_third_passes_p90",
    "Successful dribbles": "successful_dribbles_p90",
}
INVERTED = {"Not dribbled past"}

# ---------------------------------------------------------------- cross-league scouting metrics
# Only metrics that both data providers (FotMob-style PL data and Wyscout) measure the same way.
# Labels match the PL radar labels so United's gap metrics carry over directly.
COMMON_METRICS = {
    "CB": {"Accurate long balls": "long_balls_p90", "Aerials won": "aerials_won_p90",
           "Interceptions": "padj_int_p90", "Blocks": "padj_blocks_p90",
           "Aerial win %": "aerial_pct", "Pass accuracy %": "pass_pct", "Ground duel win %": "ground_pct"},
    "FB": {"Final-third passes": "final_third_p90", "Accurate crosses": "crosses_p90",
           "Successful dribbles": "dribbles_p90", "xA": "xa_p90", "Ground duels won": "ground_won_p90",
           "Chances created": "chances_p90", "Interceptions": "padj_int_p90", "Ground duel win %": "ground_pct"},
}

# ---------------------------------------------------------------- scoring and shortlist rules
GAP_THRESHOLD = 50          # United squad percentile below this = gap metric
GAP_WEIGHT = 2              # gap metrics count this many times in the fit score
GAP_FLOOR = 40              # target must reach this league-adjusted percentile on every gap metric
MAX_AGE = 28.99             # age on AGE_REFERENCE_DATE
SLOTS = {"LB": 4, "CB": 4, "RB": 2}   # 10 options, weighted to contract exposure

# Market and availability (realistic shortlist only)
BUDGET_EUR_M = 40           # max Transfermarkt value (EUR m)
RIVAL_CLUBS = {"Arsenal", "Chelsea", "Liverpool", "Manchester City", "Man City",
               "Tottenham Hotspur", "Spurs"}   # direct rivals: treated as unwilling sellers
CONTRACT_REF_DATE = "2027-07-01"

# United player each target is compared with in the head-to-heads
REPLACES = {"LB": "Shaw", "CB": "Maguire", "RB": "Dalot"}

# ---------------------------------------------------------------- chart style
INK, MUTED, RING = "#1f2328", "#6e7781", "#e9ecef"
UTD_RED, TARGET_BLUE = "#c8102e", "#1f6feb"
LEAGUE_COLORS = {"Premier League": "#1f6feb", "Eredivisie": "#e8590c", "Belgian Pro League": "#2f9e44"}

for p in (RAW, PROCESSED, CHARTS, TABLES):
    p.mkdir(parents=True, exist_ok=True)

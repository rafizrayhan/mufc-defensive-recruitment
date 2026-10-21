"""Step 1: download the source data (sparse git clones, only the files needed).

Sources
- olbauday/FPL-Core-Insights: PL 2025/26 per-match player stats, lineups, average positions, possession
- vaastav/Fantasy-Premier-League: PL player birth dates
- juanrules7/Eredivisie-Scouting: Wyscout season exports for the Eredivisie and Belgian Pro League
  (incl. Transfermarkt value and contract expiry) and team possession
- shubhs1111/player-value-analyzer: Big-5 Transfermarkt market values and current (2026/27) clubs
"""
import subprocess
from config import RAW, CORE_REPO, FPL_REPO, WYSCOUT_REPO, VALUES_REPO

def sparse_clone(url, dest, patterns):
    if not (dest / ".git").exists():
        subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--no-checkout", url, str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "sparse-checkout", "set", "--no-cone", *patterns], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "-q"], check=True)

pl = "data/2025-2026/By Tournament/Premier League"
sparse_clone("https://github.com/olbauday/FPL-Core-Insights", CORE_REPO,
             [f"{pl}/*/playermatchstats.csv", f"{pl}/*/lineups.csv", f"{pl}/*/average_positions.csv",
              f"{pl}/*/matches.csv", "/data/2025-2026/*.csv"])
sparse_clone("https://github.com/vaastav/Fantasy-Premier-League", FPL_REPO,
             ["/data/2025-26/players_raw.csv"])
sparse_clone("https://github.com/juanrules7/Eredivisie-Scouting", WYSCOUT_REPO,
             ["/data/raw/DEF_MID_GK 2526.xlsx", "/data/raw/BELGIUM DEF_MID_GK 2526.xlsx",
              "/data/processed/team_possession.csv"])
sparse_clone("https://github.com/shubhs1111/player-value-analyzer", VALUES_REPO,
             ["/dashboard_v2/players.csv"])
print("Data downloaded to", RAW)

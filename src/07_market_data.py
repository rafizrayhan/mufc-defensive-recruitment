"""Step 7: market layer for Premier League players.

Transfermarkt market values and current clubs come from the Big-5 dataset in
shubhs1111/player-value-analyzer (FotMob stats joined to Transfermarkt; 2026/27 rows give each player's
current club). PL players are matched on surname plus 2025/26 minutes (within 60), which avoids
accent and nickname mismatches. Contract expiry is not in this source, so it is filled from
data/pl_contracts.csv (public reporting) where known.
"""
import unicodedata
import pandas as pd
from config import ROOT, PROCESSED, TABLES, BIG5_VALUES

def norm(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()

pl = pd.read_csv(PROCESSED / "pool_premier_league.csv")
big5 = pd.read_csv(BIG5_VALUES)
big5 = big5[big5.league == "Premier League"].copy()   # any position: some wing-backs are listed as MF
big5["tm_id"] = big5.id.str.split("-").str[0]
b25 = big5[big5.season == "2025/26"].copy()
b26 = big5[big5.season == "2026/27"][["tm_id", "team", "market_m"]].rename(
    columns={"team": "current_club", "market_m": "market_now_m"})
b25["name_n"] = b25.player.map(norm)

matches = []
for r in pl.itertuples():
    # any name token (full name or FPL short name) of 3+ letters, plus 2025/26 minutes within 60
    tokens = {t for t in (norm(r.player) + " " + norm(r.web_name).replace(".", " ")).split() if len(t) >= 3}
    near = b25[(b25.minutes - r.minutes).abs() <= 60]
    cand = near[near.name_n.apply(lambda n: any(t in n.split() for t in tokens))]
    if len(cand) >= 1:
        c = cand.loc[(cand.minutes - r.minutes).abs().idxmin()]
        matches.append({"player_id": r.player_id, "tm_id": c.tm_id, "market_2526_m": c.market_m})
m = pd.DataFrame(matches).merge(b26, on="tm_id", how="left")
pl = pl.merge(m, on="player_id", how="left")
pl["market_value_m"] = pl.market_now_m.fillna(pl.market_2526_m)
pl["current_club"] = pl.current_club.fillna(pl.club_2526 + " (2025/26)")

contracts = pd.read_csv(ROOT / "data" / "pl_contracts.csv")
pl = pl.merge(contracts[["web_name", "club_2526", "contract_end"]], on=["web_name", "club_2526"], how="left")
pl["contract_end"] = pd.to_datetime(pl.contract_end.astype("string").str.slice(0, 4) + "-06-30", errors="coerce")
pl["on_loan"] = False
pl["value_source"] = pl.market_value_m.notna().map({True: "Transfermarkt (player-value-analyzer)", False: ""})
pl.to_csv(PROCESSED / "pool_premier_league_market.csv", index=False)
print(f"PL market values matched: {pl.market_value_m.notna().sum()} / {len(pl)}  |  "
      f"current club found: {pl.current_club.str.contains('(2025/26)', regex=False).eq(False).sum()}")

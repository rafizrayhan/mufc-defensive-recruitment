"""Step 5: where United lack. Minutes-weighted squad percentile per metric, plus contract exposure."""
import numpy as np
import pandas as pd
from config import ROOT, PROCESSED, TABLES, CLUB

rows = []
for role in ["CB", "FB"]:
    g = pd.read_csv(PROCESSED / f"percentiles_{role}.csv")
    squad = g[g.club == CLUB]
    for c in [c for c in g.columns if c.startswith("pct_")]:
        rows.append({"role": role, "metric": c[4:],
                     "united_weighted_percentile": np.average(squad[c], weights=squad.minutes_played)})
gaps = pd.DataFrame(rows).sort_values(["role", "united_weighted_percentile"])
gaps["weakness"] = gaps.united_weighted_percentile < 50
gaps.round(1).to_csv(TABLES / "united_gap_analysis.csv", index=False)
for role, t in gaps.groupby("role"):
    print(f"\n{role} - United squad percentile (minutes-weighted)")
    print(t[["metric", "united_weighted_percentile"]].round(0).to_string(index=False))

contracts = pd.read_csv(ROOT / "data" / "united_contracts.csv")
print("\nContract exposure (expiring 2027 or 2028):")
print(contracts[contracts.contract_end <= 2028].to_string(index=False))

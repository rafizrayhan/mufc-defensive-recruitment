"""Step 10: sensitivity analysis. How much does the shortlist depend on the analyst's choices?

Varies four settings at once and rebuilds both shortlists in every scenario:
- gap threshold (which metrics count as United gaps): 45, 50, 55
- gap floor (minimum adjusted percentile on every gap metric): 30, 35, 40, 45, 50
- gap weight: 1.5, 2, 3
- league discount: Opta ratio (default), 5 points harsher, 10 points harsher
= 135 scenarios. A player's robustness = share of scenarios in which he is shortlisted.
"""
import itertools
import matplotlib.pyplot as plt
import pandas as pd
from config import (TABLES, CHARTS, LEAGUE_FACTOR, MAX_AGE, SLOTS, BUDGET_EUR_M, GAP_THRESHOLD, GAP_FLOOR,
                    GAP_WEIGHT, INK, MUTED, LEAGUE_COLORS)
from scoring import load_pool, gap_metrics, score, shortlist

THRESHOLDS = [45, 50, 55]
FLOORS = [30, 35, 40, 45, 50]
WEIGHTS = [1.5, 2, 3]
DISCOUNTS = {"Opta ratio": 0.0, "5 pts harsher": 0.05, "10 pts harsher": 0.10}

pool = load_pool()
runs = []
for th, fl, wt, (dname, d) in itertools.product(THRESHOLDS, FLOORS, WEIGHTS, DISCOUNTS.items()):
    factors = {k: (v if v == 1 else v - d) for k, v in LEAGUE_FACTOR.items()}
    scored = score(pool, gap_metrics(th), wt, factors)
    for kind in ["best_fit", "realistic"]:
        sl = shortlist(scored, fl, SLOTS, MAX_AGE, budget=BUDGET_EUR_M, realistic=(kind == "realistic"))
        for r in sl.itertuples():
            runs.append({"kind": kind, "threshold": th, "floor": fl, "weight": wt, "discount": dname,
                         "player": r.player, "side": r.side, "league": r.league, "club_2526": r.club_2526})
runs = pd.DataFrame(runs)
n_scen = len(THRESHOLDS) * len(FLOORS) * len(WEIGHTS) * len(DISCOUNTS)

rob = (runs.groupby(["kind", "side", "player", "league", "club_2526"]).size()
           .rename("scenarios").reset_index())
rob["robustness_pct"] = (rob.scenarios / n_scen * 100).round(0)
rob = rob.sort_values(["kind", "side", "robustness_pct"], ascending=[True, True, False])
rob.to_csv(TABLES / "sensitivity_robustness.csv", index=False)

# Which setting moves the realistic shortlist most? Average overlap with the default shortlist.
default = set(runs[(runs.kind == "realistic") & (runs.threshold == GAP_THRESHOLD) & (runs.floor == GAP_FLOOR) &
                   (runs.weight == GAP_WEIGHT) & (runs.discount == "Opta ratio")].player)
real = runs[runs.kind == "realistic"]
overlap = (real.groupby(["threshold", "floor", "weight", "discount"]).player
               .apply(lambda p: len(set(p) & default) / len(default) * 100).rename("overlap").reset_index())
effects = pd.concat([overlap.groupby(f).overlap.mean().round(0).rename("avg_overlap_with_default_%")
                       .reset_index().rename(columns={f: "value"}).assign(setting=f)
                     for f in ["threshold", "floor", "weight", "discount"]])
effects[["setting", "value", "avg_overlap_with_default_%"]].to_csv(TABLES / "sensitivity_by_setting.csv", index=False)

print(f"{n_scen} scenarios")
for kind in ["realistic", "best_fit"]:
    print(f"\n=== {kind}: players shortlisted in 25%+ of scenarios ===")
    t = rob[(rob.kind == kind) & (rob.robustness_pct >= 25)]
    print(t[["side", "player", "league", "club_2526", "robustness_pct"]].to_string(index=False))
print("\nAverage overlap of realistic shortlist with the default, by setting:")
print(effects[["setting", "value", "avg_overlap_with_default_%"]].to_string(index=False))

# Chart: robustness of everyone shortlisted in 20%+ of scenarios, both lists
fig, axes = plt.subplots(1, 2, figsize=(17, 9), facecolor="white")
for ax, kind, title in zip(axes, ["realistic", "best_fit"], ["Realistic shortlist", "Best-fit shortlist"]):
    t = rob[(rob.kind == kind) & (rob.robustness_pct >= 20)].copy()
    t["order"] = t.side.map({"LB": 0, "CB": 1, "RB": 2})
    t = t.sort_values(["order", "robustness_pct"], ascending=[False, True])
    y = range(len(t))
    ax.barh(list(y), t.robustness_pct, color=[LEAGUE_COLORS[l] for l in t.league], height=0.7, zorder=3)
    ax.set_yticks(list(y)); ax.set_yticklabels([f"{s}  {p}" for s, p in zip(t.side, t.player)], fontsize=10, color=INK)
    for yi, v in zip(y, t.robustness_pct):
        ax.text(v + 1, yi, f"{v:.0f}%", va="center", fontsize=9, color=MUTED)
    ax.axvline(50, color=MUTED, lw=1, ls="--", zorder=1)
    ax.set_xlim(0, 110); ax.set_xlabel("Share of 135 scenarios in which the player is shortlisted", color=MUTED)
    ax.set_title(title, fontsize=14, fontweight="bold", color=INK, loc="left")
    ax.grid(axis="x", color="#eef0f2", zorder=0)
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED)
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in LEAGUE_COLORS.values()]
fig.legend(handles, list(LEAGUE_COLORS), loc="upper left", ncol=3, frameon=False, fontsize=10.5,
           bbox_to_anchor=(0.005, 0.915))
fig.suptitle("How robust is each pick? Shortlist frequency across 135 scenarios", fontsize=19,
             fontweight="bold", color=INK, x=0.01, ha="left", y=0.995)
fig.text(0.01, 0.94, "Varied: gap threshold (45/50/55), gap floor (30-50), gap weight (1.5/2/3), league discount "
         "(Opta ratio, 5 or 10 points harsher). Players shown if picked in 20%+ of scenarios.",
         fontsize=10.5, color=MUTED)
fig.tight_layout(rect=[0, 0, 1, 0.88])
fig.savefig(CHARTS / "sensitivity_robustness.png", dpi=130)
print("Saved sensitivity_robustness.png")

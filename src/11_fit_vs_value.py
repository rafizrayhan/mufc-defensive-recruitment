"""Step 11: fit vs market value, one panel per position.

Every age-eligible defender who clears the gap floor is plotted: league-adjusted fit score against
Transfermarkt value (log scale). Points up and to the left are the best value. The budget line and the
realistic shortlist are marked; rival-club players are drawn hollow.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
from adjustText import adjust_text
import pandas as pd
from config import (PROCESSED, CHARTS, TABLES, MAX_AGE, GAP_FLOOR, BUDGET_EUR_M, LEAGUE_COLORS,
                    INK, MUTED)

s = pd.read_csv(PROCESSED / "scored_all_leagues.csv")
real = pd.read_csv(TABLES / "shortlist_realistic.csv")
best = pd.read_csv(TABLES / "shortlist_best_fit.csv")
e = s[(~s.united_player) & (s.age_aug27 <= MAX_AGE) & (s.min_gap_adj >= GAP_FLOOR) & s.market_value_m.notna()]

fig, axes = plt.subplots(1, 3, figsize=(19, 6.8), facecolor="white", sharey=True)
for ax, side in zip(axes, ["LB", "CB", "RB"]):
    g = e[e.side == side]
    for league, color in LEAGUE_COLORS.items():
        d = g[g.league == league]
        ax.scatter(d.market_value_m, d.fit_score, s=70, color=color, alpha=0.85,
                   edgecolor="white", linewidth=1.5, label=league, zorder=3)
        r = d[d.rival_club]
        ax.scatter(r.market_value_m, r.fit_score, s=70, facecolor="white", edgecolor=color, linewidth=2, zorder=4)
    names = set(real[real.side == side].player) | set(best[best.side == side].player)
    ax.set_xscale("log"); ax.set_xlim(0.2, 120)
    texts = [ax.text(t.market_value_m, t.fit_score, t.player, fontsize=9.5, color=INK, zorder=5,
                     fontweight="bold" if t.player in set(real.player) else "normal")
             for t in g[g.player.isin(names)].itertuples()]
    adjust_text(texts, x=g.market_value_m.values, y=g.fit_score.values, ax=ax,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    ax.axvline(BUDGET_EUR_M, color=MUTED, lw=1.2, ls="--", zorder=1)
    ax.text(BUDGET_EUR_M * 1.04, 36, f"budget EUR {BUDGET_EUR_M}m",
            color=MUTED, fontsize=9, rotation=90, va="bottom")
    ax.set_xticks([0.5, 1, 2, 5, 10, 20, 40, 80]); ax.set_xticklabels(["0.5", "1", "2", "5", "10", "20", "40", "80"])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_title(f"{side}  (n={len(g)})", fontsize=14, fontweight="bold", color=INK, loc="left")
    ax.set_xlabel("Market value, EUR m (log scale)", color=MUTED)
    ax.grid(True, color="#eef0f2", lw=1, zorder=0)
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    for sp in ["left", "bottom"]: ax.spines[sp].set_color("#d0d7de")
    ax.tick_params(colors=MUTED)
axes[0].set_ylabel("Fit score (league-adjusted)", color=MUTED)
handles, labels = axes[1].get_legend_handles_labels()
handles.append(plt.Line2D([], [], marker="o", ls="", markerfacecolor="white", markeredgecolor=MUTED, markersize=8))
labels.append("Rival club (unlikely seller)")
fig.legend(handles, labels, loc="upper left", ncol=4, frameon=False, fontsize=10.5, bbox_to_anchor=(0.005, 0.885))
fig.suptitle("Fit vs price: who fills United's gaps for the least money?", fontsize=19, fontweight="bold",
             color=INK, x=0.01, ha="left", y=0.99)
fig.text(0.01, 0.915, f"Defenders aged {int(MAX_AGE)} or under in Aug 2027 who reach the {GAP_FLOOR}th "
         "percentile on every United gap metric. Bold = realistic shortlist. Values: Transfermarkt where available.",
         fontsize=10.5, color=MUTED)
fig.tight_layout(rect=[0, 0, 1, 0.83])
fig.savefig(CHARTS / "fit_vs_value.png", dpi=130)
print("Saved fit_vs_value.png")

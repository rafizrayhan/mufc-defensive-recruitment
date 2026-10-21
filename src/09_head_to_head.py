"""Step 9: head-to-head radars for both shortlists. Each target (league-adjusted percentile on the
cross-league metrics) is drawn over the United player whose contract runs out in that position."""
import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer import Radar
from config import (PROCESSED, CHARTS, TABLES, COMMON_METRICS, REPLACES, INK, MUTED, RING, UTD_RED,
                    TARGET_BLUE, LEAGUE_FACTOR)

scored = pd.read_csv(PROCESSED / "scored_all_leagues.csv")
united = scored[scored.united_player & (scored.league == "Premier League")]

def h2h(shortlist_file, title, fname):
    sl = pd.read_csv(TABLES / shortlist_file)
    n = len(sl); cols = 3; rows = -(-(n + 1) // cols)
    fig = plt.figure(figsize=(18.6, 8.2 * rows), facecolor="white")
    for i, t in enumerate(sl.itertuples()):
        role = "CB" if t.side == "CB" else "FB"
        labels = list(COMMON_METRICS[role])
        T = scored[(scored.player == t.player) & (scored.league == t.league) & (scored.side == t.side)].iloc[0]
        U = united[united.web_name == REPLACES[t.side]].iloc[0]
        ax = fig.add_subplot(rows, cols, i + 1)
        radar = Radar(labels, [0] * len(labels), [100] * len(labels), round_int=[True] * len(labels),
                      num_rings=4, ring_width=1, center_circle_radius=1)
        radar.setup_axis(ax=ax, facecolor="white")
        radar.draw_circles(ax=ax, facecolor=RING, edgecolor="white", lw=1.5)
        radar.draw_radar_solid([U[f"adj_{l}"] for l in labels], ax=ax,
                               kwargs={"facecolor": UTD_RED, "alpha": 0.35, "edgecolor": UTD_RED, "lw": 2})
        radar.draw_radar_solid([T[f"adj_{l}"] for l in labels], ax=ax,
                               kwargs={"facecolor": TARGET_BLUE, "alpha": 0.35, "edgecolor": TARGET_BLUE, "lw": 2})
        radar.draw_param_labels(ax=ax, fontsize=9.5, color=INK)
        value = f"EUR {t.market_value_m:.0f}m" if pd.notna(t.market_value_m) else "value n/a"
        ax.text(0.5, 1.20, f"{t.side}  {t.player}", color=TARGET_BLUE, fontsize=14, fontweight="bold",
                ha="center", transform=ax.transAxes)
        ax.text(0.5, 1.13, f"vs {U.web_name}", color=UTD_RED, fontsize=12, fontweight="bold",
                ha="center", transform=ax.transAxes)
        ax.text(0.5, 1.07, f"{t.club_2526} ({t.league}), {int(t.minutes)} mins  |  fit {t.fit_score:.0f}  |  {value}",
                color=MUTED, fontsize=9.5, ha="center", transform=ax.transAxes)
    ax = fig.add_subplot(rows, cols, n + 1); ax.axis("off")
    factors = ", ".join(f"{k} x{v}" for k, v in LEAGUE_FACTOR.items() if v < 1)
    ax.text(0, 0.8, "How to read", fontsize=14, fontweight="bold", color=INK)
    ax.text(0, 0.2, "Percentile within own league and role\n(900+ mins, per 90), multiplied by\n"
            f"league strength:\n{factors}\n\nBlue = target\nRed = United player whose contract\n"
            "runs out in that position\n\nInterceptions and blocks are\npossession-adjusted.",
            fontsize=11, color=MUTED, va="bottom")
    fig.suptitle(title, fontsize=19, fontweight="bold", color=INK, x=0.02, ha="left", y=0.997)
    fig.text(0.02, 1 - 0.85 / (8.2 * rows), "Cross-league metrics only (measured the same way by both data providers)  |  2025/26",
             fontsize=11, color=MUTED)
    fig.tight_layout(rect=[0, 0, 1, 1 - 1.2 / (8.2 * rows)], h_pad=7)
    fig.savefig(CHARTS / fname, dpi=120)
    plt.close(fig)
    print("Saved", fname)

h2h("shortlist_realistic.csv", "Realistic shortlist vs the United players they'd replace", "radar_h2h_realistic.png")
h2h("shortlist_best_fit.csv", "Best-fit shortlist vs the United players they'd replace", "radar_h2h_best_fit.png")

"""Step 4: percentile radars for every Man United CB and FB (900+ mins)."""
import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer import Radar
from config import PROCESSED, CHARTS, CLUB, INK, MUTED, RING, UTD_RED

def radar_grid(role, title, fname):
    g = pd.read_csv(PROCESSED / f"percentiles_{role}.csv")
    labels = [c[4:] for c in g.columns if c.startswith("pct_")]
    squad = g[g.club == CLUB].sort_values("minutes_played", ascending=False)
    n = len(squad); cols = min(n, 3); rows = -(-n // cols)
    fig = plt.figure(figsize=(6.2 * cols, 7.8 * rows + 0.9), facecolor="white")
    radar = Radar(labels, [0] * len(labels), [100] * len(labels), round_int=[True] * len(labels),
                  num_rings=4, ring_width=1, center_circle_radius=1)
    for i, (_, r) in enumerate(squad.iterrows()):
        ax = fig.add_subplot(rows, cols, i + 1)
        radar.setup_axis(ax=ax, facecolor="white")
        radar.draw_circles(ax=ax, facecolor=RING, edgecolor="white", lw=1.5)
        radar.draw_radar_solid([r[f"pct_{l}"] for l in labels], ax=ax,
                               kwargs={"facecolor": UTD_RED, "alpha": 0.55, "edgecolor": UTD_RED, "lw": 2})
        radar.draw_param_labels(ax=ax, fontsize=10.5, color=INK)
        ax.set_title(f"{r.web_name}\n{int(r.minutes_played)} mins", fontsize=15, color=INK, fontweight="bold", pad=34)
    fig.suptitle(title, fontsize=19, color=INK, fontweight="bold", x=0.02, ha="left", y=0.995)
    fig.text(0.02, 0.965 if rows > 1 else 0.93,
             f"Percentile vs all PL {role}s with 900+ mins (n={len(g)}), per 90, defensive actions possession-adjusted  |  2025/26  |  Data: FPL-Core-Insights",
             fontsize=11, color=MUTED)
    fig.tight_layout(rect=[0, 0, 1, 0.94 if rows > 1 else 0.9], h_pad=9)
    fig.savefig(CHARTS / fname, dpi=130)
    plt.close(fig)
    print("Saved", fname)

radar_grid("CB", "Man United centre backs, 2025/26", "radar_united_CB.png")
radar_grid("FB", "Man United full backs, 2025/26", "radar_united_FB.png")

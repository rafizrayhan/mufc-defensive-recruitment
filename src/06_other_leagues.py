"""Step 6: widen the scouting pool to the Eredivisie and Belgian Pro League (Wyscout exports, 2025/26).

Builds the same cross-league metrics as the PL pool (config.COMMON_METRICS):
- accurate actions = attempts per 90 x success rate
- ground duels = all duels minus aerial duels
- interceptions and shots blocked are possession-adjusted with the same sigmoid as the PL data,
  using each team's season-average possession (the PL adjustment is match by match)
Role comes from Wyscout's primary listed position. Market value, contract expiry and current club
come from the same export.
"""
import numpy as np
import pandas as pd
from config import (ROOT, WYSCOUT_FILES, WYSCOUT_POSSESSION, PROCESSED, MIN_MINUTES, WYSCOUT_AGE_OFFSET)

CB_POS = {"CB", "LCB", "RCB", "LCB3", "RCB3"}
LB_POS = {"LB", "LWB", "LB5"}
RB_POS = {"RB", "RWB", "RB5"}

poss = pd.read_csv(WYSCOUT_POSSESSION)
poss = poss[poss.season == "25/26"]

frames = []
for league, path in WYSCOUT_FILES.items():
    w = pd.read_excel(path).copy()
    w["primary_pos"] = w["Posición específica"].astype(str).str.split(",").str[0].str.strip()
    w["side"] = np.select([w.primary_pos.isin(CB_POS), w.primary_pos.isin(LB_POS), w.primary_pos.isin(RB_POS)],
                          ["CB", "LB", "RB"], default="")
    w = w[(w.side != "") & (w["Minutos jugados"] >= MIN_MINUTES)].copy()
    team = "Equipo durante el período seleccionado"
    p = poss[poss.league == league].set_index("club").possession
    w["team_possession"] = w[team].map(p).fillna(50)
    padj = 2 / (1 + np.exp(-0.1 * (w.team_possession - 50)))

    duels_won = w["Duelos/90"] * w["Duelos ganados, %"] / 100
    aer_att = w["Duelos aéreos en los 90"]
    aer_won = aer_att * w["Duelos aéreos ganados, %"] / 100
    ground_att = (w["Duelos/90"] - aer_att).clip(lower=0)
    ground_won = (duels_won - aer_won).clip(lower=0)

    frames.append(pd.DataFrame({
        "player": w["Jugador"], "web_name": w["Jugador"], "club_2526": w[team], "league": league,
        "role": np.where(w.side == "CB", "CB", "FB"), "side": w.side,
        "age_aug27": w["Edad"] + WYSCOUT_AGE_OFFSET, "minutes": w["Minutos jugados"],
        "long_balls_p90": w["Pases largos/90"] * w["Precisión pases largos, %"] / 100,
        "aerials_won_p90": aer_won,
        "padj_int_p90": w["Interceptaciones/90"] * padj,
        "padj_blocks_p90": w["Tiros interceptados/90"] * padj,
        "aerial_pct": w["Duelos aéreos ganados, %"],
        "pass_pct": w["Precisión pases, %"],
        "ground_pct": ground_won / ground_att.replace(0, np.nan) * 100,
        "final_third_p90": w["Pases en el último tercio/90"] * w["Precisión pases en el último tercio, %"] / 100,
        "crosses_p90": w["Centros/90"] * w["Precisión centros, %"] / 100,
        "dribbles_p90": w["Regates/90"] * w["Regates realizados, %"] / 100,
        "xa_p90": w["xA/90"],
        "ground_won_p90": ground_won,
        "chances_p90": w["Jugadas claves/90"],
        "market_value_m": w["Valor de mercado (Transfermarkt)"] / 1e6,
        "contract_end": pd.to_datetime(w["Vencimiento contrato"], errors="coerce"),
        "current_club": w["Equipo"],
        "on_loan": w["En prestamo"].astype(str).str.lower().eq("sí") | w["En prestamo"].astype(str).str.lower().eq("si"),
    }))
    print(f"{league}: {len(frames[-1])} defenders with {MIN_MINUTES}+ mins  |  {frames[-1].side.value_counts().to_dict()}")

pool = pd.concat(frames, ignore_index=True)

# Wyscout stores a missing market value as 0: treat it as unknown, then fill researched values
pool["market_value_m"] = pool.market_value_m.replace(0, np.nan)
pool["value_source"] = np.where(pool.market_value_m.notna(), "Transfermarkt (Wyscout export)", "")
manual = pd.read_csv(ROOT / "data" / "manual_market_values.csv")
pool = pool.merge(manual[["player", "league", "market_value_m", "current_club", "value_source"]],
                  on=["player", "league"], how="left", suffixes=("", "_manual"))
filled = pool.market_value_m.isna() & pool.market_value_m_manual.notna()
pool.loc[filled, "market_value_m"] = pool.loc[filled, "market_value_m_manual"]
pool.loc[filled, "value_source"] = pool.loc[filled, "value_source_manual"]
pool.loc[pool.current_club_manual.notna(), "current_club"] = pool.current_club_manual
pool = pool.drop(columns=["market_value_m_manual", "current_club_manual", "value_source_manual"])
print(f"Market value known: {pool.market_value_m.notna().sum()} / {len(pool)}  (manual fills: {filled.sum()})")
pool.to_csv(PROCESSED / "pool_other_leagues.csv", index=False)

#!/usr/bin/env python3
"""Figure 4 — labour market structure and net migration by region, 2022.

(a) 51 US states + DC, (b) 47 Japanese prefectures.
x = share of population aged 65+, y = annual-average unemployment rate,
colour = net migration (persons). Absolute axes are shared across countries so
that the two panels are directly readable; the colour scale is per country
because net-migration magnitudes differ by an order of magnitude.

Reads only the shared processed tables.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)

dem = pd.read_csv(ROOT / "data/processed/demographics.csv", dtype={"region_id": str})
lab = pd.read_csv(ROOT / "data/processed/labor_migration.csv", dtype={"region_id": str})
df = dem.merge(lab, on=["country", "region_id", "year"], how="inner")
df = df[df.year == 2022].copy()

usa = df[(df.country == "USA") & df.employment.notna()].copy()
jpn = df[(df.country == "JPN") & df.employment.notna()].copy()

# 2011 -> 2022 change in the unemployment rate, used as the point size
base = lab[(lab.year == 2011)][["region_id", "unemployment_rate_pct"]].rename(
    columns={"unemployment_rate_pct": "rate_2011"})
delta = lab[lab.year == 2022][["region_id", "unemployment_rate_pct"]].merge(
    base, on="region_id")
delta["d_rate"] = delta.unemployment_rate_pct - delta.rate_2011
dmap = dict(zip(delta.region_id, delta.d_rate))
for frame in (usa, jpn):
    frame["d_rate"] = frame.region_id.map(dmap).abs()
if len(usa) != 51 or len(jpn) != 47:
    raise SystemExit(f"expected 51 US and 47 JP rows, got {len(usa)} and {len(jpn)}")

xl = (10.5, 36.5)
yl = (1.0, 6.0)

LABELS = {
    "USA": [("US-NV", "NV"), ("US-ND", "ND"), ("US-ME", "ME"), ("US-UT", "UT"),
            ("US-WV", "WV"), ("US-IN", "IN")],
    "JPN": [("JP-13", "Tokyo"), ("JP-47", "Okinawa"), ("JP-32", "Shimane"),
            ("JP-34", "Hiroshima")],
}

OFFSETS = {"JP-32": (-6, 6, "right"), "JP-34": (5, -11, "left")}

fig, axes = plt.subplots(1, 2, figsize=(13.6, 6.0), dpi=200, sharey=True)
panels = [("USA", usa, "#1f77b4"), ("JPN", jpn, "#d62728")]
titles = {"USA": "(a) United States — 51 states + DC",
          "JPN": "(b) Japan — 47 prefectures"}

for ax, (country, frame, base) in zip(axes, panels):
    limit = float((frame.net_migration / 1000.0).abs().max())
    sc = ax.scatter(
        frame.age65_share_pct, frame.unemployment_rate_pct,
        c=frame.net_migration / 1000.0, cmap="RdBu",
        vmin=-limit, vmax=limit,
        s=(25 + 45 * frame.d_rate.fillna(0)).values,
        edgecolors="#333333", linewidths=0.6, zorder=3,
    )
    for rid, text in LABELS[country]:
        row = frame[frame.region_id == rid]
        if not len(row):
            continue
        row = row.iloc[0]
        dx, dy, ha = OFFSETS.get(rid, (5, 4, "left"))
        ax.annotate(text, (row.age65_share_pct, row.unemployment_rate_pct),
                    xytext=(dx, dy), textcoords="offset points", fontsize=7.5,
                    ha=ha, zorder=4)
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.grid(alpha=0.25, ls="--")
    ax.set_xlabel("Population aged 65+ (%, 2022)", fontsize=10)
    ax.set_title(titles[country], fontsize=10.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    cbar = fig.colorbar(sc, ax=ax, pad=0.02, fraction=0.05)
    cbar.set_label("Net migration, 2022 (thousand persons)", fontsize=8.5)

handles = [Line2D([], [], marker="o", linestyle="", color="none",
                  markeredgecolor="#333333", markerfacecolor="#cccccc",
                  markersize=(25 + 45 * v) ** 0.5, label=f"{v:.0f} pp") for v in (0, 2, 4, 6)]
axes[0].legend(handles=handles, title="|Δ unemployment| 2011→2022", loc="lower right",
               fontsize=7.5, title_fontsize=8, frameon=True, labelspacing=1.0,
               borderpad=0.8)

axes[0].set_ylabel("Unemployment rate (%, annual average 2022)", fontsize=10)

fig.suptitle("Figure 4 — Labour market structure and net migration by region, 2022\n"
             "colour = net migration (per-country scale); size = |change in unemployment, 2011→2022|",
             fontsize=11.5)
fig.text(0.5, -0.02,
         "Sources: BLS LAUS 2022 annual averages (US; 16+ civilian noninstitutional population) and Labour Force Survey\n"
         "prefectural model estimates 2022 (Japan; 15+). Net migration: Census Vintage 2022 (US, domestic + international,\n"
         "Jul 2021–Jul 2022) and Basic Resident Registration report (Japan, inter-prefectural, calendar 2022).\n"
         "Labour-force universes and migration definitions differ; no cross-country ranking is implied.",
         ha="center", va="top", fontsize=6.8, color="#555555")

fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(OUT / f"figure4_labor_2022.{ext}", bbox_inches="tight", facecolor="white")
print("wrote", OUT / "figure4_labor_2022.png")
print("US rate range:", usa.unemployment_rate_pct.min(), usa.unemployment_rate_pct.max())
print("JP rate range:", jpn.unemployment_rate_pct.min(), jpn.unemployment_rate_pct.max())
print("corr aging-unemp US:", round(usa.age65_share_pct.corr(usa.unemployment_rate_pct), 3),
      "JP:", round(jpn.age65_share_pct.corr(jpn.unemployment_rate_pct), 3))




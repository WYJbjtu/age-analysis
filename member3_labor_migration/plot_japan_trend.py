#!/usr/bin/env python3
"""Japan 2011-2022 panel: labour trend and migration collapse/recovery.

(a) median prefecture unemployment rate, 2011-2022 (12 years)
(b) net migration 2018-2022 for the five largest migration regions
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)

lab = pd.read_csv(ROOT / "data/processed/labor_migration.csv", dtype={"region_id": str})
jp = lab[lab.country == "JPN"].copy()

med = (jp.groupby("year").unemployment_rate_pct.median().reset_index()
         .sort_values("year"))

mig = jp.dropna(subset=["net_migration"])
regions = {"JP-13": "Tokyo", "JP-14": "Kanagawa", "JP-11": "Saitama",
           "JP-27": "Osaka", "JP-23": "Aichi"}

fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.0), dpi=200)

ax = axes[0]
ax.plot(med.year, med.unemployment_rate_pct, "o-", color="#1f77b4", lw=2)
for _, r in med.iterrows():
    ax.annotate(f"{r.unemployment_rate_pct:.1f}", (r.year, r.unemployment_rate_pct),
                xytext=(0, 7), textcoords="offset points", ha="center", fontsize=7.5)
ax.set_xlabel("Year", fontsize=10)
ax.set_ylabel("Median prefecture unemployment rate (%)", fontsize=10)
ax.set_title("(a) Japan: labour market tightened 2011–2019", fontsize=10.5)
ax.set_xticks(med.year)
ax.grid(alpha=0.25, ls="--")
for side in ("top", "right"):
    ax.spines[side].set_visible(False)

ax = axes[1]
colors = ["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4", "#9467bd"]
for (rid, name), color in zip(regions.items(), colors):
    sub = mig[mig.region_id == rid].sort_values("year")
    if sub.empty:
        continue
    ax.plot(sub.year, sub.net_migration / 1000.0, "o-", color=color, lw=1.8, label=name)
ax.axhline(0, color="#333333", lw=0.9)
ax.set_xlabel("Year", fontsize=10)
ax.set_ylabel("Net migration (thousand persons)", fontsize=10)
ax.set_title("(b) Net migration 2011–2022: the Tokyo inflow collapses in 2020–21", fontsize=10.5)
ax.set_xticks(sorted(mig.year.unique()))
ax.grid(alpha=0.25, ls="--")
ax.legend(fontsize=8, ncol=2)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)

fig.suptitle("Japan panel: 12-year labour series and 2011–2022 migration (prefecture level)", fontsize=11.5)
fig.text(0.5, -0.02,
         "Sources: Labour Force Survey prefectural model estimates (2011–2022); Basic Resident Registration "
         "migration reports 2018–2022 and the annual-report trend table for 2011–2017. Net migration is "
         "inter-prefectural and sums to zero each year.", ha="center", fontsize=6.8, color="#555555")
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(OUT / f"jpn_panel_2011_2022.{ext}", bbox_inches="tight", facecolor="white")
print("wrote", OUT / "jpn_panel_2011_2022.png")
print(med.to_string(index=False))

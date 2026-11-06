#!/usr/bin/env python3
"""Two-country 12-year trend: labour market medians and employment growth.

(a) median regional unemployment rate, 2011-2022, US vs Japan
(b) median regional employment index (2011 = 100), US vs Japan

Percentages are regional medians, i.e. every region counts once; the two
countries' labour-force universes differ (US 16+, Japan 15+), so levels are
shown side by side rather than ranked.
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
lab = lab[lab.year.between(2011, 2022)]

colors = {"USA": "#1f77b4", "JPN": "#d62728"}
names = {"USA": "United States (51 states + DC)", "JPN": "Japan (47 prefectures)"}

fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.0), dpi=200)

ax = axes[0]
for country in ("USA", "JPN"):
    sub = lab[lab.country == country]
    med = sub.groupby("year").unemployment_rate_pct.median()
    ax.plot(med.index, med.values, "o-", color=colors[country], lw=2, ms=5,
            label=names[country])
ax.set_xlabel("Year", fontsize=10)
ax.set_ylabel("Median regional unemployment rate (%)", fontsize=10)
ax.set_title("(a) Unemployment: same long decline, very different cycles",
             fontsize=10.5)
ax.grid(alpha=0.25, ls="--")
ax.legend(fontsize=8.5)
ax.set_xticks(range(2011, 2023, 2))

ax = axes[1]
for country in ("USA", "JPN"):
    sub = lab[lab.country == country]
    base = sub[sub.year == 2011].set_index("region_id").employment
    pivot = sub.pivot_table(index="year", columns="region_id", values="employment")
    index = (pivot.divide(base, axis=1) * 100).median(axis=1)
    ax.plot(index.index, index.values, "o-", color=colors[country], lw=2, ms=5,
            label=names[country])
ax.axhline(100, color="#999999", lw=0.9, ls=":")
ax.set_xlabel("Year", fontsize=10)
ax.set_ylabel("Median regional employment index (2011 = 100)", fontsize=10)
ax.set_title("(b) Employment: both countries above their 2011 level by 2022",
             fontsize=10.5)
ax.grid(alpha=0.25, ls="--")
ax.legend(fontsize=8.5)
ax.set_xticks(range(2011, 2023, 2))

fig.suptitle("Member 3 — two-country labour market trends, 2011–2022", fontsize=12)
fig.text(0.5, -0.02,
         "Sources: BLS archived state annual averages; Labour Force Survey prefectural model estimates. "
         "Medians give each region equal weight. Labour-force universes differ (US 16+, Japan 15+), "
         "so levels are descriptive, not a ranking. Employment index uses each country's own 2011 base.",
         ha="center", fontsize=6.8, color="#555555")
fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(OUT / f"two_country_trend_2011_2022.{ext}", bbox_inches="tight", facecolor="white")
print("wrote", OUT / "two_country_trend_2011_2022.png")

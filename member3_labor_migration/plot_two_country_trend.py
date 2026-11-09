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
plt.rcParams['svg.hashsalt']='member3-repaired'
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)

lab = pd.read_csv(ROOT / "data/processed/labor_migration.csv", dtype={"region_id": str})
lab = lab[lab.year.between(2011, 2022)]

colors = {"USA": "#2788ae", "JPN": "#8551a6"}
names = {"USA": "United States (50 states + DC)", "JPN": "Japan (47 prefectures)"}

fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.0), dpi=200)

ax = axes[0]
for country in ("USA", "JPN"):
    sub = lab[lab.country == country]
    med = sub.groupby("year").unemployment_rate_pct.median()
    ax.plot(med.index, med.values, "o-", color=colors[country], lw=2, ms=5,
            label=names[country])
ax.set_xlabel("Year", fontsize=10)
ax.set_ylabel("Median regional unemployment rate (%)", fontsize=10)
ax.set_title("(a) Annual median regional unemployment rates",
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
fig.text(0.07, 0.04,
         "Sources: BLS archived annual tables (each year's published vintage); Japan LFS annual model/ratio estimates.\n"
         "Medians give each region equal weight. US civilian noninstitutional 16+; Japan 15+. Benchmark revisions remain.\n"
         "Employment is persons, not jobs. Index each region to its own 2011 value; these are descriptive regional summaries.",
         ha="left", fontsize=8, color="#555555")
fig.tight_layout(rect=(0,.16,1,.92))
from plot_helpers import save
save(fig,'two_country_trend_2011_2022',[{'country':c,'regions':int(lab[lab.country==c].region_id.nunique()),'years':list(range(2011,2023))} for c in ('USA','JPN')],
     'As-published BLS annual vintages; LFS benchmark/disaster notes retained; medians are not national rates.')
print("wrote", OUT / "two_country_trend_2011_2022.png")

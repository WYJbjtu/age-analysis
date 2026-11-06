#!/usr/bin/env python3
"""Interim Japan panel for Member 3.

(a) 2022: aging rate × unemployment rate, points shaded by net migration.
(b) change in net migration 2019 → 2022 for the largest movers.

US labour columns are still pending, so this is Japan only. Reads the shared
processed tables only (demographics 2022 + labor_migration 2019/2022).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)

CLIP = 15000.0

dem = pd.read_csv(ROOT / "data/processed/demographics.csv", dtype={"region_id": str})
lab = pd.read_csv(ROOT / "data/processed/labor_migration.csv", dtype={"region_id": str})

jp22 = dem[(dem.country == "JPN") & (dem.year == 2022)].merge(
    lab[(lab.country == "JPN") & (lab.year == 2022)], on=["country", "region_id", "year"])
jp19 = lab[(lab.country == "JPN") & (lab.year == 2019)][["region_id", "net_migration"]]
if len(jp22) != 47 or len(jp19) != 47:
    raise SystemExit(f"expected 47 prefectures, got 2022={len(jp22)}, 2019={len(jp19)}")

change = jp22[["region_id", "net_migration"]].merge(
    jp19.rename(columns={"net_migration": "net_2019"}), on="region_id")
change["delta"] = change.net_migration - change.net_2019
change = change.sort_values("delta")
movers = pd.concat([change.head(8), change.tail(8)]).sort_values("delta")

fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.6), dpi=200,
                         gridspec_kw={"width_ratios": [1.15, 1]})

# (a) 2022 cross-section
ax = axes[0]
sc = ax.scatter(jp22.age65_share_pct, jp22.unemployment_rate_pct,
                c=jp22.net_migration.clip(-CLIP, CLIP), cmap="RdBu",
                vmin=-CLIP, vmax=CLIP, s=62, edgecolors="#333333", linewidths=0.6)
for _, row in jp22.nlargest(3, "net_migration").iterrows():
    ax.annotate(row.region_id, (row.age65_share_pct, row.unemployment_rate_pct),
                xytext=(5, 4), textcoords="offset points", fontsize=7.5)
ax.set_xlabel("Population aged 65+ (%, 2022)", fontsize=10)
ax.set_ylabel("Unemployment rate (%, 2022)", fontsize=10)
ax.set_title("(a) 2022: aging, unemployment and net migration", fontsize=10.5)
ax.grid(alpha=0.25, ls="--")
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
cbar = fig.colorbar(sc, ax=ax, pad=0.02, extend="both", fraction=0.05)
cbar.set_label("Net migration, 2022 (persons, clipped ±15,000)", fontsize=8.5)

# (b) change 2019 -> 2022
ax = axes[1]
colors = ["#d62728" if v < 0 else "#1f77b4" for v in movers.delta]
ax.barh(range(len(movers)), movers.delta, color=colors, height=0.72)
ax.set_yticks(range(len(movers)))
ax.set_yticklabels(movers.region_id, fontsize=8)
ax.axvline(0, color="#333333", lw=0.9)
ax.set_xlabel("Change in net migration, 2019 → 2022 (persons)", fontsize=10)
ax.set_title("(b) Largest changes between the two years", fontsize=10.5)
ax.grid(alpha=0.25, axis="x", ls="--")
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
tokyo = change.loc[change.region_id == "JP-13", "delta"].iloc[0]
ax.text(0.03, 0.93, f"Tokyo (JP-13): {tokyo:+,.0f} persons",
        transform=ax.transAxes, fontsize=8.5, color="#d62728", va="top")

fig.suptitle("Japan: aging, unemployment and net migration (47 prefectures, Japan-only panel; "
             "US labour pending)", fontsize=11.5)
fig.text(0.5, -0.02,
         "Sources: Statistics Bureau of Japan / e-Stat (Labour Force Survey model estimates 2019, 2022; "
         "Population Estimates 2022; Basic Resident Registration migration report 2019, 2022). "
         "Net migration is internal redistribution and sums to zero in each year; no causal interpretation.",
         ha="center", fontsize=6.8, color="#555555")

fig.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(OUT / f"jpn_labor_migration_2019_2022.{ext}", bbox_inches="tight", facecolor="white")
print("wrote", OUT / "jpn_labor_migration_2019_2022.png")
print(movers[["region_id", "net_2019", "net_migration", "delta"]].to_string(index=False))


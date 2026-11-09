#!/usr/bin/env python3
"""Systematic outlier screen for the 2022 cross-section.

For each country and for two relationships —
    unemployment rate ~ aging rate
    manufacturing share ~ aging rate
— a linear trend is fitted on the 51/47 regions and standardised residuals are
reported, so that "unusual regions" are chosen by a stated rule instead of by
inspection. Output: outliers_2022.csv and figures/outliers_2022.png/.svg.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams['svg.hashsalt']='member3-repaired'
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MEMBER = Path(__file__).resolve().parent
OUT = MEMBER / "figures"
OUT.mkdir(parents=True, exist_ok=True)

dem = pd.read_csv(ROOT / "data/processed/demographics.csv", dtype={"region_id": str})
lab = pd.read_csv(ROOT / "data/processed/labor_migration.csv", dtype={"region_id": str})
ind = pd.read_csv(ROOT / "data/processed/industry.csv", dtype={"region_id": str})
lookup = pd.read_csv(ROOT / "data/reference/region_lookup.csv")

df = (dem.merge(lab, on=["country", "region_id", "year"], how="left", validate='one_to_one')
         .merge(ind[["country", "region_id", "year", "manufacturing_share_pct"]],
                on=["country", "region_id", "year"], how="left", validate='one_to_one'))
df = df[df.year == 2022].copy()
df = df.merge(lookup[["country", "region_id", "region_name"]],
              on=["country", "region_id"], how="left", validate='many_to_one')
if df.groupby('country').size().to_dict()!={'USA':51,'JPN':47} or df[['region_name','age65_share_pct','manufacturing_share_pct','unemployment_rate_pct']].isna().any().any():
    raise ValueError('Outlier figure requires the complete 98-region cross-section')

PAIRS = [
    ("USA", "unemployment_rate_pct", "Unemployment rate (%)"),
    ("USA", "manufacturing_share_pct", "Manufacturing share of GDP (%)"),
    ("JPN", "unemployment_rate_pct", "Unemployment rate (%)"),
    ("JPN", "manufacturing_share_pct", "Manufacturing share of GDP (%)"),
]

rows = []
fits = {}
for country, col, label in PAIRS:
    sub = df[df.country == country].dropna(subset=[col])
    slope, intercept = np.polyfit(sub.age65_share_pct, sub[col], 1)
    resid = sub[col] - (slope * sub.age65_share_pct + intercept)
    sigma = float(np.std(resid, ddof=1))
    z = resid / sigma
    sub = sub.assign(fitted=slope * sub.age65_share_pct + intercept,
                     residual=resid, z=z)
    fits[(country, col)] = (sub, slope, intercept, sigma)
    for _, r in sub.iterrows():
        rows.append({"country": country, "region_id": r.region_id,
                     "region_name": r.region_name, "indicator": col,
                     "aging_rate_pct": round(float(r.age65_share_pct), 2),
                     "value": round(float(r[col]), 2),
                     "fitted": round(float(r.fitted), 2),
                     "residual": round(float(r.residual), 2),
                     "z": round(float(r.z), 2)})

out = pd.DataFrame(rows).sort_values(["indicator", "country", "z"], key=lambda s: s.abs() if s.name == "z" else s, ascending=False)
out.to_csv(MEMBER / "outliers_2022.csv", index=False, encoding="utf-8")

fig, axes = plt.subplots(2, 2, figsize=(12.4, 8.4), dpi=200)
titles = {
    ("USA", "unemployment_rate_pct"): "(a) US unemployment rate",
    ("USA", "manufacturing_share_pct"): "(b) US manufacturing share",
    ("JPN", "unemployment_rate_pct"): "(c) Japan unemployment rate",
    ("JPN", "manufacturing_share_pct"): "(d) Japan manufacturing share",
}
colors = {"USA": "#2788ae", "JPN": "#8551a6"}

for ax, (country, col, label) in zip(axes.ravel(), PAIRS):
    sub, slope, intercept, sigma = fits[(country, col)]
    ax.axhline(0, color="#333333", lw=1.0)
    ax.axhline(2 * sigma, color="#999999", lw=0.9, ls="--")
    ax.axhline(-2 * sigma, color="#999999", lw=0.9, ls="--")
    ax.scatter(sub.age65_share_pct, sub.residual, s=46, color=colors[country],
               alpha=0.85, edgecolors="white", linewidths=0.6)
    flagged = sub[sub.z.abs() >= 1.5].sort_values("z", key=abs, ascending=False).head(4)
    for _, r in flagged.iterrows():
        ax.annotate(r.region_id, (r.age65_share_pct, r.residual),
                    xytext=(4, 4), textcoords="offset points", fontsize=8)
    ax.set_title(titles[(country, col)] +
                 f"\nslope {slope:+.2f} pp per pp aging; residual SD {sigma:.2f}",
                 fontsize=9.5)
    ax.set_xlabel("Aging rate (%, 2022)", fontsize=9)
    ax.set_ylabel("Residual (observed − fitted)", fontsize=9)
    ax.grid(alpha=0.22, ls="--")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

fig.suptitle("Outlier screen, 2022: which regions depart most from the within-country trend?\n"
             "dashed lines = ±2 residual SD; labels: up to four largest |z| ≥ 1.5 per panel", fontsize=11)
fig.text(0.07, 0.035,
         "This screen reuses the same observations; it does not independently confirm case selection or identify causes.\n"
         "Sources: BLS / Japan LFS annual 2022; Census July / Japan October population; BEA CY2022 / Cabinet Office FY2022.\n"
         "Manufacturing is nominal value added / nominal GDP, not an employment share. Each region has equal weight.",
         ha="left", fontsize=8, color="#555555")
fig.tight_layout(rect=(0,.13,1,.94))
from plot_helpers import save
save(fig,'outliers_2022',[{'country':c,'indicator':col,'n':len(f[0]),'ids':f[0].region_id.tolist()} for (c,col),f in fits.items()],
     'Descriptive residual screen; same-data case selection is not independent validation.')

print("wrote", OUT / "outliers_2022.png", "and", MEMBER / "outliers_2022.csv")
for (country, col), (sub, slope, intercept, sigma) in fits.items():
    top = sub.reindex(sub.z.abs().sort_values(ascending=False).index).head(3)
    print(f"{country} {col}: slope={slope:+.3f} sd={sigma:.3f}")
    for _, r in top.iterrows():
        print(f"   {r.region_id:6s} {r.region_name:22s} value={r[col]:6.2f} fitted={r.fitted:6.2f} z={r.z:+.2f}")

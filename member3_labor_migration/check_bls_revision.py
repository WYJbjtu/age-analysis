# -*- coding: utf-8 -*-
"""Cross-check the archived BLS annual values against the current API revision."""
import csv
import json
import re
import statistics
import time
import urllib.request
from pathlib import Path

REPO = Path(r"C:\Test\5002_project\repo\age-analysis-main")
RAW = REPO / "data" / "raw" / "member3"
KEY = (RAW / ".bls_key").read_text(encoding="utf-8-sig").strip()

# postal code -> FIPS (via state names in the two official tables)
name_to_fips = {}
for row in csv.DictReader(open(RAW / "census_nst_est2022.csv", encoding="latin-1")):
    if row.get("SUMLEV") == "040":
        name_to_fips[row["NAME"].strip()] = int(row["STATE"])
name_to_id = {}
for row in csv.DictReader(open(REPO / "data/reference/region_lookup.csv", encoding="utf-8-sig")):
    if row["country"] == "USA":
        name_to_id[row["region_name"]] = row["region_id"]
id_to_fips = {rid: name_to_fips[name] for name, rid in name_to_id.items() if name in name_to_fips}
print("states mapped:", len(id_to_fips))


def fetch(series: str) -> dict[int, float]:
    target = (f"https://api.bls.gov/publicAPI/v2/timeseries/data/{series}"
              f"?registrationkey={KEY}&startyear=2011&endyear=2022")
    enc = target.replace("?", "%3F").replace("=", "%3D").replace("&", "%26")
    for attempt in range(3):
        try:
            txt = urllib.request.urlopen(
                urllib.request.Request("https://r.jina.ai/" + enc, headers={"User-Agent": "Mozilla/5.0"}),
                timeout=90).read().decode("utf-8", "replace")
            obj = json.loads(re.search(r'\{"status".*', txt, flags=re.S).group(0))
            by_year: dict[int, list[float]] = {}
            for d in obj["Results"]["series"][0]["data"]:
                if d["period"] != "M13" and d["value"] not in ("-", ""):
                    by_year.setdefault(int(d["year"]), []).append(float(d["value"]))
            return {y: statistics.mean(v) for y, v in by_year.items() if len(v) == 12}
        except Exception:  # noqa: BLE001
            time.sleep(3)
    return {}


rows = []
for rid, fips in sorted(id_to_fips.items()):
    series = f"LAUST{fips:02d}0000000000003"
    api = fetch(series)
    rows.append((rid, series, api))
    print(rid, series, len(api), "years")
    time.sleep(1.2)

table = {}
for r in csv.DictReader(open(REPO / "data/processed/labor_migration.csv", encoding="utf-8")):
    if r["country"] == "USA":
        table[(r["region_id"], int(r["year"]))] = float(r["unemployment_rate_pct"])

out = []
for rid, series, api in rows:
    for year, value in api.items():
        if (rid, year) in table:
            out.append({"region_id": rid, "year": year,
                        "archived_value": table[(rid, year)],
                        "api_mean_of_months": round(value, 3),
                        "difference_pp": round(value - table[(rid, year)], 3)})

dst = REPO / "member3_labor_migration" / "bls_revision_check.csv"
with dst.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["region_id", "year", "archived_value", "api_mean_of_months", "difference_pp"])
    w.writeheader()
    w.writerows(out)

diffs = [abs(r["difference_pp"]) for r in out]
print("rows", len(out), "max |diff| pp", max(diffs), "mean |diff| pp", round(sum(diffs) / len(diffs), 3))
print("wrote", dst)

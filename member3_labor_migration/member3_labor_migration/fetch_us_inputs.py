#!/usr/bin/env python3
"""Retrieve the two US inputs used by prepare_labor.py.

1. Archived BLS "Regional and State Unemployment - annual averages" releases.
   Each release prints two years side by side; the current-year column is the
   as-published annual average for that year. Twelve releases (data years
   2011-2022) are parsed into ``data/raw/member3/bls_us_labor_2011_2022.csv``.

2. Census state net migration. Vintage 2020 supplies 2011-2020
   (``census_netmig_2011_2020.csv``); 2021-2022 come from Vintage 2022, which is
   built from a local ``census_nst_est2022.csv`` when present.

Both bls.gov and www2.census.gov answer 403 from some networks; pass
``--proxy https://r.jina.ai/`` (default) to read them through a text proxy.

Usage:
    python member3_labor_migration/fetch_us_inputs.py
    python member3_labor_migration/fetch_us_inputs.py --direct
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "member3"
ARCHIVE_DIR = RAW / "bls_archive"
LOOKUP = ROOT / "data" / "reference" / "region_lookup.csv"

RELEASES = {
    2011: "srgune_02292012.htm",
    2012: "srgune_03012013.htm",
    2013: "srgune_02282014.htm",
    2014: "srgune_03042015.htm",
    2015: "srgune_02262016.htm",
    2016: "srgune_02282017.htm",
    2017: "srgune_02272018.htm",
    2018: "srgune_02282019.htm",
    2019: "srgune_03042020.htm",
    2020: "srgune_03032021.htm",
    2021: "srgune_03022022.htm",
    2022: "srgune_03012023.htm",
}
NST2020_URL = ("https://www2.census.gov/programs-surveys/popest/datasets/"
               "2010-2020/state/totals/nst-est2020-alldata.csv")
NUM = re.compile(r"\d[\d,]*\.\d+|\d[\d,]*")


def fetch(url: str, proxy: str | None) -> str:
    target = (proxy or "") + url
    request = urllib.request.Request(target, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(request, timeout=180).read().decode("utf-8", "replace")


def state_ids() -> dict[str, str]:
    out = {}
    with LOOKUP.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row["country"] == "USA":
                out[row["region_name"]] = row["region_id"]
    return out


def numbers(line: str) -> list[float]:
    return [float(m.replace(",", "")) for m in NUM.findall(re.sub(r"\(\d+\)", " ", line))]


def table1(text: str) -> str:
    start = text.find("Table 1.")
    end = text.find("Table 2.", start + 10)
    return text[start:end if end > 0 else len(text)]


def build_bls(proxy: str | None, states: dict[str, str]) -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for year, name in sorted(RELEASES.items()):
        cached = ARCHIVE_DIR / f"{year}.md"
        if not cached.exists():
            url = f"https://www.bls.gov/news.release/archives/{name}"
            cached.write_text(fetch(url, proxy), encoding="utf-8")
        text = table1(cached.read_text(encoding="utf-8"))
        for state, rid in states.items():
            match = re.search(rf"(?<![A-Za-z]){re.escape(state)}\s*\.*", text)
            if not match:
                continue
            values = numbers(text[match.start(): text.find("\n", match.start())])
            if len(values) < 10:
                continue
            rows.append({
                "country": "USA", "region_id": rid, "year": year,
                "labor_force": int(round(values[3] * 1000)),
                "employment": int(round(values[5] * 1000)),
                "unemployment": int(round(values[7] * 1000)),
                "unemployment_rate_pct": f"{values[9]:.1f}",
            })
    rows.sort(key=lambda r: (r["year"], r["region_id"]))
    dst = RAW / "bls_us_labor_2011_2022.csv"
    with dst.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["country", "region_id", "year", "labor_force",
                                                    "employment", "unemployment",
                                                    "unemployment_rate_pct"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"BLS: {len(rows)} state-years -> {dst.relative_to(ROOT)}")


def build_census(proxy: str | None, states: dict[str, str]) -> None:
    cached = RAW / "census_nst_est2020.csv"
    if not cached.exists():
        text = fetch(NST2020_URL, proxy)
        cached.write_text(text[text.find("SUMLEV"):], encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(cached.read_text(encoding="utf-8", errors="replace"))))
    out = []
    for row in rows:
        if row.get("SUMLEV") != "040":
            continue
        rid = states.get(row["NAME"].strip())
        if not rid:
            continue
        for year in range(2011, 2021):
            value = (row.get(f"NETMIG{year}") or "").strip()
            if value:
                out.append({"country": "USA", "region_id": rid, "year": year,
                            "net_migration": int(round(float(value))),
                            "net_migration_rate_per_1000": (row.get(f"RNETMIG{year}") or "").strip()})
    out.sort(key=lambda r: (r["year"], r["region_id"]))
    dst = RAW / "census_netmig_2011_2020.csv"
    with dst.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["country", "region_id", "year", "net_migration",
                                                    "net_migration_rate_per_1000"])
        writer.writeheader()
        writer.writerows(out)
    print(f"Census 2011-2020: {len(out)} rows -> {dst.relative_to(ROOT)}")

    local = RAW / "census_nst_est2022.csv"
    if not local.exists():
        print("Census 2021-2022: skipped (copy NST-EST2022-ALLDATA.csv to "
              f"{local.relative_to(ROOT)} to build it)")
        return
    rows = list(csv.DictReader(io.StringIO(local.read_text(encoding="utf-8", errors="replace"))))
    out = []
    for row in rows:
        if row.get("SUMLEV") != "040":
            continue
        rid = states.get(row["NAME"].strip())
        if not rid:
            continue
        for year in (2021, 2022):
            value = (row.get(f"NETMIG{year}") or "").strip()
            if value:
                out.append({"country": "USA", "region_id": rid, "year": year,
                            "net_migration": int(round(float(value))),
                            "net_migration_rate_per_1000": (row.get(f"RNETMIG{year}") or "").strip()})
    out.sort(key=lambda r: (r["year"], r["region_id"]))
    dst = RAW / "census_netmig_2021_2022.csv"
    with dst.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["country", "region_id", "year", "net_migration",
                                                    "net_migration_rate_per_1000"])
        writer.writeheader()
        writer.writerows(out)
    print(f"Census 2021-2022: {len(out)} rows -> {dst.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--direct", action="store_true",
                        help="hit bls.gov and census.gov directly instead of the text proxy")
    args = parser.parse_args()
    proxy = None if args.direct else "https://r.jina.ai/"
    states = state_ids()
    if len(states) != 51:
        raise SystemExit(f"expected 51 US regions in the lookup, got {len(states)}")
    build_bls(proxy, states)
    build_census(proxy, states)


if __name__ == "__main__":
    main()

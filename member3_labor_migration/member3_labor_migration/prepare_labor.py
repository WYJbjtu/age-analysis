#!/usr/bin/env python3
"""Member 3 — labour market and migration (Japan, 2019 and 2022).

Fills the Japanese rows of ``data/processed/labor_migration.csv``:

* employment            — Labour Force Survey, prefectural model estimates,
                          "第３表 都道府県別就業者", annual average (thousand persons -> persons)
* unemployment_rate_pct — same release, "第６表 都道府県別完全失業率" (percent)
* net_migration         — 住民基本台帳人口移動報告, table 1, column U
                          ("転入超過数", net in-migration, persons)

The 2022 report is published as ``.xlsx``; the 2019 report is only published as
``.xls``, so it is converted once (LibreOffice or Excel) and the converted
workbook is cached in ``data/raw/member3/``. United States records already in
the CSV are left untouched.

Usage
-----
    python member3_labor_migration/prepare_labor.py --download
    python member3_labor_migration/prepare_labor.py

Raw files go to the git-ignored ``data/raw/member3/`` and are only downloaded
when missing (``--download``); existing files are reused.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "member3"
PROCESSED = ROOT / "data" / "processed" / "labor_migration.csv"
MEMBER_DIR = ROOT / "member3_labor_migration"

YEARS = tuple(range(2011, 2023))
KEY = ["country", "region_id", "year"]
COLUMNS = KEY + ["employment", "unemployment_rate_pct", "net_migration"]

UA = {"User-Agent": "Mozilla/5.0 (compatible; DSC5002-member3/1.0)"}

LFS_SOURCE = (
    "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031952605&fileKind=0",
    "estat_lfs_pref_model.xlsx",
)

# member-uploaded BLS extract (optional: US labour columns stay empty without it)
BLS_US_FILE = RAW / "bls_us_labor_2022.csv"
BLS_US_TREND = RAW / "bls_us_labor_2011_2022.csv"
CENSUS_NETMIG = [RAW / "census_netmig_2011_2020.csv", RAW / "census_netmig_2021_2022.csv"]
LOOKUP = ROOT / "data" / "reference" / "region_lookup.csv"


def _us_regions() -> set[str]:
    with LOOKUP.open(newline="", encoding="utf-8-sig") as handle:
        return {r["region_id"] for r in csv.DictReader(handle) if r["country"] == "USA"}


US_REGIONS = _us_regions()

# Prefecture-level migration: 2018-2022 are published as Excel workbooks on
# stat.go.jp; for 2011-2017 the site only carries national time-series tables, so
# those years stay empty until the e-Stat tables are supplied.
MIGRATION_DIR = RAW / "migration"
MIGRATION_URLS = {
    2018: "https://www.stat.go.jp/data/idou/2018np/kihon/zuhyou/hyo1.xls",
    2019: "https://www.stat.go.jp/data/idou/2019np/kihon/zuhyou/hyo1.xls",
    2020: "https://www.stat.go.jp/data/idou/2020np/jissu/zuhyou/hyo1.xls",
    2021: "https://www.stat.go.jp/data/idou/2021np/jissu/zuhyou/hyo1.xls",
    2022: "https://www.stat.go.jp/data/idou/2022np/jissu/zuhyou/hyo1.xlsx",
}
MIGRATION_YEARS = tuple(sorted(MIGRATION_URLS))
# annual-report table 3: one workbook covering 2000-2017 by prefecture
TREND_URL = "https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031688387&fileKind=0"
TREND_FILE = MIGRATION_DIR / "trend_2000_2017.xlsx"


def download(url: str, path: Path, raw_suffix: str | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    target = path.with_suffix(raw_suffix) if raw_suffix else path
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as response:
        target.write_bytes(response.read())
    return target


def convert_xls_to_xlsx(xls_path: Path) -> Path:
    """Convert an official .xls workbook once (LibreOffice), cache the result."""
    out = xls_path.with_suffix(".xlsx")
    if out.exists() and out.stat().st_size > 0:
        return out
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise SystemExit(
            f"{xls_path.name} is an official .xls workbook. Open it once in Excel or "
            f"LibreOffice and save it as {out.name} in the same folder."
        )
    subprocess.run(
        [soffice, "--headless", "--convert-to", "xlsx", "--outdir", str(xls_path.parent),
         str(xls_path)],
        check=True, capture_output=True,
    )
    return out


def fetch_year(year: int, download_missing: bool) -> Path | None:
    """Return the cached per-year migration workbook, or None when unavailable."""
    path = MIGRATION_DIR / f"{year}.xlsx"
    if path.exists() and path.stat().st_size > 0:
        return path
    if year not in MIGRATION_URLS or not download_missing:
        return None
    url = MIGRATION_URLS[year]
    if url.endswith(".xls"):
        xls = download(url, MIGRATION_DIR / f"{year}.xls", raw_suffix=".xls")
        return convert_xls_to_xlsx(xls)
    return download(url, MIGRATION_DIR / f"{year}.xlsx")


def sheet_by_title(workbook, keyword: str):
    for name in workbook.sheetnames:
        if keyword in name:
            return workbook[name]
    raise KeyError(f"worksheet containing {keyword!r} not found; got {workbook.sheetnames}")


def year_row(rows: list[tuple], year: int) -> tuple:
    for row in rows:
        if len(row) > 1 and str(row[1]).strip() in (str(year), f"{year}.0"):
            return row
    raise ValueError(f"year {year} not found in worksheet")


def read_labour(lfs_path: Path) -> dict[int, dict[str, dict[str, float]]]:
    """{year: {region_id: {field: value}}} from the time-series sheets.

    Counts are published in thousand persons and converted to persons here, as
    the brief asks to keep the raw quantities (not only the rates).
    """
    wb = load_workbook(lfs_path, data_only=True, read_only=True)
    out: dict[int, dict[str, dict[str, float]]] = {y: {} for y in YEARS}

    for keyword, field, scale in (
        ("第２表", "labor_force", 1000.0),          # 労働力人口
        ("第３表", "employment", 1000.0),           # 就業者
        ("第４表", "unemployment", 1000.0),         # 完全失業者
        ("第６表", "unemployment_rate_pct", 1.0),   # 完全失業率
    ):
        ws = sheet_by_title(wb, keyword)
        rows = list(ws.iter_rows(values_only=True))
        for year in YEARS:
            # prefectures are laid out in code order in columns C..AU
            for code, value in zip(range(1, 48), year_row(rows, year)[2:49]):
                if isinstance(value, (int, float)):
                    out[year].setdefault(f"JP-{code:02d}", {})[field] = float(value) * scale
    wb.close()
    return out


def read_net_migration(migration_path: Path) -> dict[str, int]:
    wb = load_workbook(migration_path, data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))

    # the prefecture block starts with 北海道; its code sits in the previous column
    name_col = None
    for row in rows:
        for idx, cell in enumerate(row):
            if isinstance(cell, str) and "北海道" in cell:
                name_col = idx
                break
        if name_col is not None:
            break
    if name_col is None:
        raise ValueError("could not locate the prefecture name column")

    result: dict[str, int] = {}
    for row in rows:
        if len(row) <= max(name_col, 20):
            continue
        code = row[name_col - 1]
        value = row[20]                     # column U: 転入超過数
        if isinstance(code, str) and re.fullmatch(r"\d{2}", code.strip()) and isinstance(value, (int, float)):
            result[f"JP-{int(code.strip()):02d}"] = int(value)
    wb.close()
    return result



def read_annual_trend(path: Path, years: tuple[int, ...]) -> dict[int, dict[str, int]]:
    """Net migration from the annual-report table 3 (a transposed time series).

    The workbook stacks three blocks over the same years: intra-prefectural
    movers, in-migrants from other prefectures, and net migration
    (転入超過数). Only the third block is used. It lets the 2011-2017 years be
    filled from one official file instead of seven separate releases.
    """
    wb = load_workbook(path, data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()

    best, best_n = None, -1
    for idx, row in enumerate(rows[:25]):
        n = sum(1 for c in row if isinstance(c, (int, float)) and 1990 <= c <= 2030)
        if n > best_n:
            best, best_n = idx, n
    header = rows[best]

    blocks, current, prev = [], {}, None
    for j, cell in enumerate(header):
        if isinstance(cell, (int, float)) and 1990 <= cell <= 2030:
            year = int(cell)
            if prev is not None and year <= prev:
                blocks.append(current)
                current = {}
            current[year] = j
            prev = year
    if current:
        blocks.append(current)
    if len(blocks) < 3:
        raise ValueError(f"{path}: expected three year blocks, found {len(blocks)}")
    net_block = blocks[2]

    out: dict[int, dict[str, int]] = {}
    for row in rows:
        code = None
        for j in (8, 9):
            if j < len(row) and isinstance(row[j], str) and row[j].strip().isdigit() \
                    and len(row[j].strip()) == 2:
                code = row[j].strip()
                break
        if not code:
            continue
        for year in years:
            col = net_block.get(year)
            if col is None or col >= len(row):
                continue
            value = row[col]
            if isinstance(value, (int, float)):
                out.setdefault(year, {})[f"JP-{int(code):02d}"] = int(round(value))
    return out


def read_us_labour_trend(path: Path) -> dict[tuple[str, int], tuple[int, float]]:
    out: dict[tuple[str, int], tuple[int, float]] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            rid = row["region_id"].strip()
            if rid not in US_REGIONS:
                continue
            out[(rid, int(row["year"]))] = (int(round(float(row["employment"]))),
                                            float(row["unemployment_rate_pct"]))
    return out


def read_us_netmig(paths: list[Path]) -> dict[tuple[str, int], int]:
    out: dict[tuple[str, int], int] = {}
    for path in paths:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                rid = row["region_id"].strip()
                value = (row.get("net_migration") or "").strip()
                if rid in US_REGIONS and value:
                    out[(rid, int(row["year"]))] = int(round(float(value)))
    return out


def read_bls_us(path: Path) -> dict[str, tuple[int, float]]:
    """{region_id: (employment persons, unemployment rate pct)} for US 2022.

    The BLS package (member-uploaded) holds annual averages for the 51 US
    regions; employment is already in persons, the rate in 0-100.
    """
    out: dict[str, tuple[int, float]] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            rid = (row.get("region_id") or "").strip()
            if not rid or rid not in US_REGIONS:
                continue
            employment = row.get("employment", "").strip()
            rate = row.get("unemployment_rate_pct", "").strip()
            if employment and rate:
                out[rid] = (int(round(float(employment))), float(rate))
    return out


def read_processed(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        header = reader.fieldnames or []
    if header != COLUMNS:
        raise SystemExit(f"unexpected header in {path}: {header}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="download missing official files")
    args = parser.parse_args()

    lfs_path = RAW / LFS_SOURCE[1]
    if not (lfs_path.exists() and lfs_path.stat().st_size > 0):
        if not args.download:
            raise SystemExit(f"missing raw file {lfs_path}; rerun with --download")
        download(LFS_SOURCE[0], lfs_path)

    labour = read_labour(lfs_path)
    migrations = {}
    for year in YEARS:
        path = fetch_year(year, args.download)
        if path is not None:
            migrations[year] = read_net_migration(path)

    # one official file (annual-report table 3) covers the earlier years
    trend_path = TREND_FILE
    if not trend_path.exists() and args.download:
        xls = download(TREND_URL, MIGRATION_DIR / "trend_2000_2017.xls", raw_suffix=".xls")
        try:
            convert_xls_to_xlsx(xls)
        except SystemExit:
            pass
    if trend_path.exists():
        # Definition check: the 2017 annual report's trend table (2000-2017) is
        # headed "日本人移動者" (Japanese movers only), whereas the 2018-2022
        # single-year tables are headed "移動者（日本人及び外国人）" and include
        # foreign residents. Chaining them would splice two definitions (Osaka
        # 2017: 2,961 Japanese-only vs 1,136 all-nationalities), so the early
        # years are written to a separate reference file and are NOT merged into
        # the contract table.
        trend = read_annual_trend(trend_path, YEARS)
        MEMBER_DIR.mkdir(parents=True, exist_ok=True)
        ref_path = MEMBER_DIR / "jpn_migration_japanese_2011_2017.csv"
        with ref_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["region_id", "year", "net_migration_japanese"])
            writer.writeheader()
            for year in sorted(trend):
                for code in sorted(trend[year]):
                    writer.writerow({"region_id": code, "year": year,
                                     "net_migration_japanese": trend[year][code]})
        print(f"reference (Japanese movers only, not merged): {ref_path.name}")

    for year in YEARS:
        if len(labour[year]) != 47:
            raise SystemExit(f"{year}: expected 47 prefectures, collected {len(labour[year])}")
        if year in migrations and len(migrations[year]) != 47:
            raise SystemExit(f"{year}: expected 47 migration rows, collected {len(migrations[year])}")

    rows = read_processed(PROCESSED)
    kept = [r for r in rows if not (r["country"] == "JPN" and int(r["year"]) in YEARS)]

    new_rows = []
    for year in YEARS:
        for code in sorted(labour[year]):
            employment = labour[year][code].get("employment")
            rate = labour[year][code].get("unemployment_rate_pct")
            net = migrations.get(year, {}).get(code)
            if employment is None or rate is None:
                continue
            new_rows.append({
                "country": "JPN",
                "region_id": code,
                "year": str(year),
                "employment": str(int(round(employment))),
                "unemployment_rate_pct": f"{rate:.1f}",
                "net_migration": "" if net is None else str(net),
            })

    kept.extend(new_rows)

    # ---------- US detail table: keep the raw quantities as well ----------
    if BLS_US_FILE.exists():
        bls_detail = []
        with BLS_US_FILE.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                rid = (row.get("region_id") or "").strip()
                if rid not in US_REGIONS:
                    continue
                bls_detail.append({
                    "region_id": rid,
                    "year": int(row.get("year") or 2022),
                    "labor_force": int(round(float(row["labor_force"]))),
                    "employment": int(round(float(row["employment"]))),
                    "unemployment": int(round(float(row["unemployment"]))),
                    "unemployment_rate_pct": f"{float(row['unemployment_rate_pct']):.1f}",
                    "employment_population_ratio_pct":
                        f"{float(row['employment_population_ratio_pct']):.1f}",
                })
        bls_detail.sort(key=lambda r: r["region_id"])
        with (MEMBER_DIR / "us_labor_detail.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(bls_detail[0].keys()))
            writer.writeheader()
            writer.writerows(bls_detail)

    # ---------- United States: rebuild the 2011-2022 panel ----------
    us_filled = 0
    if BLS_US_TREND.exists():
        us_lab = read_us_labour_trend(BLS_US_TREND)
        us_net = read_us_netmig(CENSUS_NETMIG)
        kept = [r for r in kept if not (r["country"] == "USA" and int(r["year"]) in YEARS)]
        for (rid, year), (employment, rate) in sorted(us_lab.items()):
            if year not in YEARS:
                continue
            kept.append({
                "country": "USA",
                "region_id": rid,
                "year": str(year),
                "employment": str(employment),
                "unemployment_rate_pct": f"{rate:.1f}",
                "net_migration": str(us_net.get((rid, year), "")),
            })
            us_filled += 1
    elif BLS_US_FILE.exists():
        bls = read_bls_us(BLS_US_FILE)
        for row in kept:
            if row["country"] != "USA" or int(row["year"]) != 2022:
                continue
            if row["region_id"] in bls:
                employment, rate = bls[row["region_id"]]
                row["employment"] = str(employment)
                row["unemployment_rate_pct"] = f"{rate:.1f}"
                us_filled += 1

    with PROCESSED.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(kept)

    # detail table: the raw quantities the brief asks us to keep (not only rates);
    # it stays in the member folder so the shared contract table keeps its 6 columns
    detail_rows = []
    gap = 0.0
    for year in YEARS:
        for code in sorted(labour[year]):
            rec = labour[year][code]
            if "labor_force" not in rec or "employment" not in rec:
                continue
            gap = max(gap, abs(rec["labor_force"] - rec["employment"] - rec.get("unemployment", 0.0)))
            detail_rows.append({
                "region_id": code,
                "year": year,
                "labor_force": int(round(rec["labor_force"])),
                "employment": int(round(rec["employment"])),
                "unemployment": int(round(rec.get("unemployment", 0.0))),
                "unemployment_rate_pct": f"{rec.get('unemployment_rate_pct', float('nan')):.1f}",
            })
    MEMBER_DIR.mkdir(parents=True, exist_ok=True)
    detail_path = MEMBER_DIR / "jpn_labor_detail.csv"
    with detail_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["region_id", "year", "labor_force",
                                                    "employment", "unemployment",
                                                    "unemployment_rate_pct"])
        writer.writeheader()
        writer.writerows(detail_rows)

    us = sum(1 for r in kept if r["country"] == "USA")
    jp = [r for r in kept if r["country"] == "JPN"]
    summary = {
        "years": list(YEARS),
        "rows": len(kept),
        "usa_rows": us,
        "jpn_rows": len(jp),
        "jpn_rows_by_year": {str(y): sum(1 for r in jp if int(r["year"]) == y) for y in YEARS},
        "jpn_detail_rows": len(detail_rows),
        "jpn_detail_max_rounding_gap_persons": int(round(gap)),
        "jpn_migration_years": sorted(migrations),
        "jpn_migration_missing_years": [y for y in YEARS if y not in migrations],
        "us_rows_filled": us_filled,
        "us_labour_pending": not BLS_US_FILE.exists(),
        "bls_file": (Path("data/raw/member3") / BLS_US_FILE.name).as_posix()
        if BLS_US_FILE.exists() else None,
        "sources": {
            "lfs_pref": {
                "url": LFS_SOURCE[0],
                "file": (Path("data/raw/member3") / LFS_SOURCE[1]).as_posix(),
                "note": "one release used for all years (prefectural model estimates)",
            },
            **{
                f"migration_{year}": {
                    "url": MIGRATION_URLS.get(year, TREND_URL),
                    "file": (
                        (Path("data/raw/member3/migration") / f"{year}.xlsx").as_posix()
                        if year in MIGRATION_URLS
                        else "data/raw/member3/migration/trend_2000_2017.xlsx"
                    ),
                }
                for year in sorted(migrations)
            },
        },
    }
    MEMBER_DIR.mkdir(parents=True, exist_ok=True)
    (MEMBER_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {PROCESSED}: {len(kept)} rows (USA={us}, JPN={len(jp)})")
    print("JPN rows by year:", summary["jpn_rows_by_year"])
    if us_filled:
        print(f"US region-years filled: {us_filled} (51 regions x 2011-2022, "
              f"archived BLS annual releases)")
    else:
        print("US employment/unemployment remain empty (BLS extract not present)")


if __name__ == "__main__":
    main()



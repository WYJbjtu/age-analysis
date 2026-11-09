"""CSV contracts: deliberately simple, reproducible, and dependency-free."""
from __future__ import annotations
import csv
import math
from pathlib import Path

KEY = ('country', 'region_id', 'year')
REQUIRED = {
    'demographics': KEY + ('age65_share_pct',),
    'industry': KEY + ('manufacturing_share_pct', 'services_share_pct'),
    'labor_migration': KEY,
}
PERCENT_COLUMNS = {'age65_share_pct', 'working_age_share_pct', 'manufacturing_share_pct', 'services_share_pct', 'unemployment_rate_pct'}
NONNEGATIVE_COLUMNS = {'total_population', 'nominal_gdp_local', 'manufacturing_va_local', 'services_va_local', 'employment', 'old_age_dependency_ratio'}
NUMERIC_COLUMNS = PERCENT_COLUMNS | NONNEGATIVE_COLUMNS | {'net_migration','domestic_net_migration',
    'international_net_migration','total_net_migration','japanese_only_domestic_net_migration','labor_force','unemployment'}


def read_lookup(path: Path) -> dict[str, str]:
    with path.open(newline='', encoding='utf-8-sig') as file:
        rows = list(csv.DictReader(file))
    ids = {r['region_id']: r['country'] for r in rows}
    if len(ids) != 98 or len(rows) != 98:
        raise ValueError(f'Region lookup should contain 98 unique regions, got {len(rows)} rows and {len(ids)} unique IDs')
    if sum(v == 'USA' for v in ids.values()) != 51 or sum(v == 'JPN' for v in ids.values()) != 47:
        raise ValueError('Region lookup requires 51 USA and 47 JPN units')
    return ids


def validate_table(path: Path, module: str, lookup: dict[str, str]) -> tuple[int, dict[str, int]]:
    if module not in REQUIRED:
        raise ValueError(f'Unknown module: {module}')
    with path.open(newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames or []
        missing = sorted(set(REQUIRED[module]) - set(headers))
        if missing:
            raise ValueError(f'{path}: missing columns {missing}')
        if len(headers) != len(set(headers)):
            raise ValueError(f'{path}: duplicate header names')
        keys = set()
        counts = {'USA': 0, 'JPN': 0}
        for line, row in enumerate(reader, start=2):
            if None in row:  # extra unnamed CSV columns
                raise ValueError(f'{path}:{line}: unexpected extra columns')
            country, rid, year = (row.get(k, '').strip() for k in KEY)
            if rid not in lookup or lookup[rid] != country:
                raise ValueError(f'{path}:{line}: invalid country/region pair {country}/{rid}')
            try:
                y = int(year)
            except ValueError as exc:
                raise ValueError(f'{path}:{line}: invalid year {year}') from exc
            if not (1950 <= y <= 2050):
                raise ValueError(f'{path}:{line}: suspicious year {y}')
            key = (country, rid, y)
            if key in keys:
                raise ValueError(f'{path}:{line}: duplicate key {key}')
            keys.add(key)
            counts[country] += 1
            for col in REQUIRED[module][3:]:
                if row.get(col, '').strip() == '':
                    raise ValueError(f'{path}:{line}: required value empty: {col}')
            for col in NUMERIC_COLUMNS.intersection(headers):
                value = (row.get(col) or '').strip()
                if not value:
                    continue
                try:
                    num = float(value)
                except ValueError as exc:
                    raise ValueError(f'{path}:{line}: {col} is not numeric') from exc
                if not math.isfinite(num):
                    raise ValueError(f'{path}:{line}: {col} non-finite value')
                if col in PERCENT_COLUMNS and not (0 <= num <= 100):
                    raise ValueError(f'{path}:{line}: {col} outside 0..100')
                if col in NONNEGATIVE_COLUMNS and num < 0:
                    raise ValueError(f'{path}:{line}: {col} negative')
        return len(keys), counts

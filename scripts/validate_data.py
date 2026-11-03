"""Check team-owned region/year CSVs against shared contracts; safe for empty templates."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from aging_economies.contracts import read_lookup, validate_table


def main():
    lookup = read_lookup(ROOT / 'data/reference/region_lookup.csv')
    errors = []
    for name in ('demographics', 'industry', 'labor_migration'):
        path = ROOT / f'data/processed/{name}.csv'
        try:
            rows, counts = validate_table(path, name, lookup)
            print(f'[OK] {name}: {rows} rows; USA={counts["USA"]}, JPN={counts["JPN"]}' + (' (header-only template)' if rows == 0 else ''))
        except (ValueError, OSError) as exc:
            print(f'[ERROR] {exc}')
            errors.append(name)
    if errors:
        raise SystemExit(1)
    print('Contracts validated. This does NOT verify official source accuracy or full country/year coverage.')


if __name__ == '__main__':
    main()

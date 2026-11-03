import csv
from pathlib import Path
import pytest
from aging_economies.contracts import read_lookup, validate_table

ROOT = Path(__file__).resolve().parents[1]


def write_csv(path, header, rows):
    with path.open('w', encoding='utf-8', newline='') as file:
        writer=csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)


def test_98_regions_and_known_ids():
    lookup = read_lookup(ROOT / 'data/reference/region_lookup.csv')
    assert len(lookup) == 98
    assert lookup['US-CA'] == 'USA'
    assert lookup['JP-13'] == 'JPN'
    assert lookup['US-DC'] == 'USA'


def test_empty_templates_are_accepted():
    lookup = read_lookup(ROOT / 'data/reference/region_lookup.csv')
    for mod in ('demographics','industry','labor_migration'):
        rows, counts = validate_table(ROOT / f'data/processed/{mod}.csv', mod, lookup)
        assert rows >= 0


def test_duplicate_region_year_rejected(tmp_path):
    path=tmp_path/'demographics.csv'
    write_csv(path, ['country','region_id','year','age65_share_pct'], [['USA','US-CA',2022,18.0],['USA','US-CA',2022,20.0]])
    with pytest.raises(ValueError, match='duplicate key'):
        validate_table(path, 'demographics', read_lookup(ROOT / 'data/reference/region_lookup.csv'))


def test_percent_outside_range_rejected(tmp_path):
    path=tmp_path/'demographics.csv'
    write_csv(path, ['country','region_id','year','age65_share_pct'], [['JPN','JP-13',2022,102]])
    with pytest.raises(ValueError, match='outside 0..100'):
        validate_table(path, 'demographics', read_lookup(ROOT / 'data/reference/region_lookup.csv'))


def test_invalid_geography_rejected(tmp_path):
    path=tmp_path/'industry.csv'
    write_csv(path, ['country','region_id','year','manufacturing_share_pct','services_share_pct'], [['USA','JP-13',2022,10,70]])
    with pytest.raises(ValueError, match='invalid country/region pair'):
        validate_table(path, 'industry', read_lookup(ROOT / 'data/reference/region_lookup.csv'))

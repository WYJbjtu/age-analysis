"""Member-owned checks, runnable without downloading source workbooks."""
import csv
import math
from pathlib import Path

import pytest

from prepare_industry import YEARS, japan_rows, number, usa_rows

ROOT = Path(__file__).resolve().parents[1]


def test_industry_coverage_periods_and_recomputed_shares():
    with (ROOT / 'data/processed/industry.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1176
    assert len({(r['country'], r['region_id'], r['year']) for r in rows}) == 1176
    assert {int(r['year']) for r in rows} == set(range(2011, 2023))
    for year in range(2011, 2023):
        assert sum(r['country'] == 'USA' and int(r['year']) == year for r in rows) == 51
        assert sum(r['country'] == 'JPN' and int(r['year']) == year for r in rows) == 47
    for row in rows:
        assert row['gdp_reference_period'] == ('CY' if row['country'] == 'USA' else 'FY') + row['year']
        gdp = float(row['nominal_gdp_local'])
        assert gdp > 0
        for sector in ('manufacturing', 'services'):
            expected = 100 * float(row[f'{sector}_va_local']) / gdp
            assert math.isclose(float(row[f'{sector}_share_pct']), expected, abs_tol=1e-7, rel_tol=0)
        assert float(row['manufacturing_va_local']) + float(row['services_va_local']) <= gdp


def test_tokyo_uses_gdp_including_accounting_adjustments():
    with (ROOT / 'data/processed/industry.csv').open() as stream:
        row = next(r for r in csv.DictReader(stream) if r['region_id'] == 'JP-13' and r['year'] == '2022')
    # Official syuyo1.xlsx FY2022 cells I21 / BL21 / BO21, JPY millions.
    assert float(row['nominal_gdp_local']) == 120219929
    assert float(row['manufacturing_share_pct']) == pytest.approx(100 * 8812197 / 120219929)
    assert float(row['services_share_pct']) == pytest.approx(100 * 107003619 / 120219929)


@pytest.mark.parametrize('invalid', ['NaN', 'inf', '-inf', 'x', ''])
def test_missing_suppressed_or_nonfinite_values_fail(invalid):
    with pytest.raises(ValueError):
        number(invalid)


def test_changed_official_table_layout_fails():
    with pytest.raises(ValueError, match='layout'):
        japan_rows({'I5': '建設業'}, {}, 2011)


@pytest.mark.parametrize('rid,year,gdp,manufacturing,services', [
    ('US-CA', '2011', 2014050.3, 221137.7, 1417757.7),
    ('US-CA', '2016', 2586485.2, 272154.2, 1848653.0),
    ('US-CA', '2022', 3623524.5, 361595.6, 2676612.0),
    ('JP-01', '2011', 18527065, 1706214, 14831002),
    ('JP-01', '2016', 20064828, 1905275, 15724662),
])
def test_source_spot_checks_across_years(rid, year, gdp, manufacturing, services):
    # Independently inspected published source cells, including both ends and middle years.
    with (ROOT / 'data/processed/industry.csv').open() as stream:
        row = next(r for r in csv.DictReader(stream) if r['region_id'] == rid and r['year'] == year)
    assert float(row['nominal_gdp_local']) == gdp
    assert float(row['manufacturing_va_local']) == manufacturing
    assert float(row['services_va_local']) == services


def test_panel_keys_match_population_and_labor():
    keys = []
    for name in ('industry', 'demographics', 'labor_migration'):
        with (ROOT / f'data/processed/{name}.csv').open() as stream:
            rows = [r for r in csv.DictReader(stream) if int(r['year']) in YEARS]
        key = {(r['country'], r['region_id'], r['year']) for r in rows}
        assert len(rows) == len(key) == 1176
        keys.append(key)
    assert keys[0] == keys[1] == keys[2]


def test_japan_source_and_crosscheck_years_must_match():
    cells = {'I5': '製造業', 'BL5': '県内総生産', 'BO7': '第３次産業',
             'B3': '【2011（平成23）年度】', 'R3': '（単位：100万円）'}
    with pytest.raises(ValueError, match='source year'):
        japan_rows(cells, {}, 2012)
    with pytest.raises(ValueError, match='exactly one FY2011'):
        japan_rows(cells, {'O5': '2022'}, 2011)


@pytest.fixture
def bea_example():
    return [
        {'GeoName': 'California', 'LineCode': line, 'Description': description,
         'Unit': 'Millions of current dollars', '2011': str(a), '2022': str(b)}
        for line, description, a, b in [
            ('1', 'All industry total', 100, 200),
            ('12', 'Manufacturing', 20, 30),
            ('92', 'Private services-providing industries 3/', 70, 160),
        ]
    ]


def test_bea_reads_selected_years_without_2022_backfill(bea_example):
    lookup = [{'country': 'USA', 'region_id': 'US-CA', 'region_name': 'California'}]
    rows = usa_rows(bea_example, lookup, (2011, 2022))
    assert [float(r['manufacturing_share_pct']) for r in rows] == [20, 15]
    assert [float(r['services_share_pct']) for r in rows] == [70, 80]
    del bea_example[0]['2011']
    with pytest.raises(ValueError):
        usa_rows(bea_example, lookup, (2011, 2022))


def test_bea_duplicate_or_missing_industry_fails(bea_example):
    lookup = [{'country': 'USA', 'region_id': 'US-CA', 'region_name': 'California'}]
    with pytest.raises(ValueError, match='Duplicate BEA'):
        usa_rows(bea_example + [bea_example[0]], lookup, (2011,))
    with pytest.raises(ValueError, match='Missing BEA'):
        usa_rows(bea_example[:-1], lookup, (2011,))

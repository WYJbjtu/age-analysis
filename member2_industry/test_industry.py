"""Member-owned checks, runnable without downloading source workbooks."""
import csv
import math
from pathlib import Path

import pytest

from prepare_industry import japan_rows, number

ROOT = Path(__file__).resolve().parents[1]


def test_industry_coverage_periods_and_recomputed_shares():
    with (ROOT / 'data/processed/industry.csv').open() as stream:
        rows = [r for r in csv.DictReader(stream) if r['year'] == '2022']
    assert len(rows) == 98
    assert len({(r['country'], r['region_id']) for r in rows}) == 98
    assert sum(r['country'] == 'USA' for r in rows) == 51
    assert sum(r['country'] == 'JPN' for r in rows) == 47
    for row in rows:
        assert row['gdp_reference_period'] == ('CY2022' if row['country'] == 'USA' else 'FY2022')
        gdp = float(row['nominal_gdp_local'])
        assert gdp > 0
        for sector in ('manufacturing', 'services'):
            expected = 100 * float(row[f'{sector}_va_local']) / gdp
            assert math.isclose(float(row[f'{sector}_share_pct']), expected, abs_tol=1e-7, rel_tol=0)


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
        japan_rows({'I5': '建設業'}, {})

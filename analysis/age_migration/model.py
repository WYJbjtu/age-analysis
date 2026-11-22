"""Pure definitions, arithmetic and validation for the age-migration extension."""
import math
import re
import numpy as np
import pandas as pd

YEARS = (2019, 2022)
KEY = ['country', 'region_id', 'year', 'age_group']
COUNTS = ['in_migration', 'out_migration', 'net_migration']
MOES = ['in_moe90', 'out_moe90', 'net_moe90']
GROUPS = {'20-24': (20, 24), '25-29': (25, 29), '30-34': (30, 34),
          '35-64': (35, 64), '65+': (65, None), '20-34': (20, 34)}
PROFILE = ['20-24', '25-29', '30-34', '35-64', '65+']
ANALYSIS_AGES = ['20-24', '65+', '20-34']
SENTINELS = {-999999999: ('N', 'suppressed_small_sample'),
             -888888888: ('(X)', 'not_available'),
             -666666666: ('-', 'insufficient_observations'),
             -555555555: ('*****', 'controlled_estimate_moe_not_applicable'),
             -333333333: ('***', 'median_open_interval'),
             -222222222: ('**', 'standard_error_unavailable')}


def acs_value(raw, annotation='', *, moe=False):
    """Keep raw strings elsewhere; return missing, never a negative count sentinel."""
    annotation = '' if annotation is None else str(annotation).strip()
    if raw is None or str(raw).strip() in ('', 'null'):
        return np.nan, annotation, 'missing'
    token = str(raw).strip()
    symbols = {v[0]: v[1] for v in SENTINELS.values()}
    if annotation in symbols:
        return np.nan, annotation, symbols[annotation]
    if token in symbols:
        return np.nan, token, symbols[token]
    try:
        number = float(token)
    except ValueError as exc:
        raise ValueError(f'Unrecognized ACS value/annotation: {token!r}') from exc
    if number in SENTINELS:
        symbol, reason = SENTINELS[number]
        return np.nan, symbol, reason
    if annotation:
        raise ValueError(f'Unrecognized ACS annotation: {annotation!r}')
    if not math.isfinite(number) or number < 0:
        raise ValueError('ACS source counts/MOEs must be nonnegative; unknown sentinel')
    return number, '', 'published_moe90' if moe else 'published_estimate'


def rss(values):
    values = np.asarray(list(values), dtype=float)
    return float(np.sqrt(np.sum(values ** 2))) if len(values) and np.isfinite(values).all() else np.nan


def ratio_moe90(numerator, denominator, numerator_moe, denominator_moe, scale=1000):
    """ACS delta-method ratio approximation; omits unknown covariance, includes D MOE."""
    if not np.isfinite([numerator, denominator, numerator_moe, denominator_moe]).all():
        return np.nan
    if denominator <= 0 or min(numerator_moe, denominator_moe) < 0:
        raise ValueError('Invalid denominator or MOE')
    return scale / denominator * math.hypot(numerator_moe, numerator / denominator * denominator_moe)


def direction(value, moe):
    if not np.isfinite(value):
        return 'missing'
    if not np.isfinite(moe):
        return 'no_sampling_interval'
    if value - moe > 0:
        return 'positive_under_approximation'
    if value + moe < 0:
        return 'negative_under_approximation'
    return 'interval_includes_zero'


def rounded_rate_check(net, population, published_pct, population_precision=1000, rate_precision=0.01):
    """Intersect intervals implied by two published rounding rules, not an ad hoc tolerance.

    Japan Population Estimates rounds to the display unit (2022np index, notes).
    Table10 displays thousands; migration Table2-3 displays hundredths of a percent.
    This verifies compatibility, not reproduction of an unavailable unrounded denominator.
    """
    half = population_precision / 2
    if population <= half or population_precision <= 0 or rate_precision <= 0:
        raise ValueError('Invalid rounding interval')
    bounds = sorted([100 * net / (population-half), 100 * net / (population+half)])
    low, high = published_pct-rate_precision/2, published_pct+rate_precision/2
    return dict(denominator_precision_persons=population_precision,
                denominator_rounding_rate_low=bounds[0], denominator_rounding_rate_high=bounds[1],
                published_rate_rounding_low=low, published_rate_rounding_high=high,
                passed=max(bounds[0],low) <= min(bounds[1],high)+1e-12)


def age_bounds(label):
    text = label.strip().lower().replace('歳', '').replace('～', '-').replace('−', '-')
    if text in ('total', 'all ages', '1+', 'unknown'):
        return (1, None) if text == '1+' else (None, None)
    numbers = [int(v) for v in re.findall(r'\d+', text)]
    if len(numbers) == 2:
        return tuple(numbers)
    if len(numbers) == 1:
        if 'under' in text:
            return 0, numbers[0] - 1
        return (numbers[0], None) if any(s in text for s in ('over', '以上', '+')) else (numbers[0], numbers[0])
    raise ValueError(f'Cannot map age label: {label}')


def covered_bins(frame, lower, upper):
    """Require exact, contiguous native coverage. Never prorate a partial age bin."""
    top = float('inf') if upper is None else upper
    selected = frame.loc[frame.age_lower.notna() & (frame.age_lower >= lower)
                         & (frame.age_upper.fillna(float('inf')) <= top)].sort_values('age_lower')
    expected = lower
    for row in selected.itertuples():
        if row.age_lower != expected:
            raise ValueError('Missing or overlapping native age bins')
        expected = float('inf') if pd.isna(row.age_upper) else row.age_upper + 1
    if expected != (float('inf') if upper is None else upper + 1):
        raise ValueError(f'Native ages do not exactly cover {lower}-{upper}')
    return selected


def validate_regions(frame, lookup, key=KEY):
    if frame.duplicated(key).any():
        raise ValueError(f'Duplicate primary keys: {key}')
    if set(frame.country) != {'JPN', 'USA'} or set(frame.year) != set(YEARS):
        raise ValueError('Both countries and exactly 2019/2022 required')
    for (country, year, age), group in frame.groupby(['country', 'year', 'age_group'], dropna=False):
        expected = set(lookup.loc[lookup.country == country, 'region_id'])
        if set(group.region_id) != expected:
            raise ValueError(f'Missing/extra region: {country} {year} {age}')


def validate_flows(frame):
    for col in ['in_migration', 'out_migration']:
        if (frame[col].dropna() < 0).any():
            raise ValueError('Negative gross migration')
    expected = frame.in_migration - frame.out_migration
    if not np.allclose(expected, frame.net_migration, equal_nan=True, atol=0, rtol=0):
        raise ValueError('Net migration must equal inflow minus outflow')


def safe_join(left, right, on, validate='many_to_one'):
    if right.duplicated(on).any():
        raise ValueError('Duplicate population join key')
    joined = left.merge(right, on=on, how='left', validate=validate, indicator=True)
    if len(joined) != len(left) or not joined['_merge'].eq('both').all():
        raise ValueError('Population join lost a region or denominator')
    return joined.drop(columns='_merge')


def correlation(frame, x, y):
    complete = frame[[x, y]].dropna()
    if len(complete) < 3 or (complete.nunique() < 2).any():
        return np.nan, np.nan, len(complete)
    pearson = complete[x].corr(complete[y])
    spearman = complete[x].rank(method='average').corr(complete[y].rank(method='average'))
    return float(pearson), float(spearman), len(complete)

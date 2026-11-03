"""Merge 2022/all-year region panels, report coverage and missingness; never impute."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed'
KEY = ['country','region_id','year']


def read(name):
    frame = pd.read_csv(DATA / f'{name}.csv', dtype={'country':'string','region_id':'string'}, keep_default_na=True)
    if not len(frame):
        return None
    frame['year'] = frame['year'].astype(int)
    return frame


def main():
    dem, ind, labor = read('demographics'), read('industry'), read('labor_migration')
    if dem is None or ind is None:
        raise SystemExit('Cannot merge yet: Member1 demographics and Member2 industry must both have actual records.')
    merged = dem.merge(ind, on=KEY, how='outer', validate='one_to_one', indicator='population_industry_match')
    print('Population × industry merge coverage:')
    print(merged.groupby(['country','population_industry_match'], observed=True).size().to_string())
    if labor is not None:
        merged = merged.merge(labor, on=KEY, how='left', validate='one_to_one', indicator='labor_match')
    else:
        print('Labor/migration not yet provided; skipping optional join.')
    merged.sort_values(KEY).to_csv(DATA / 'merged_analysis.csv', index=False)
    both = merged.loc[merged['population_industry_match'] == 'both']
    print('Combined panel:', len(merged), 'rows; rows matched in both required sources:', len(both))
    print('Matched 2022 counts by country:', both.loc[both.year == 2022].groupby('country').size().to_dict())
    print('Missingness in merged table:', merged.isna().sum().loc[lambda x: x > 0].to_dict())
    print('Wrote', DATA / 'merged_analysis.csv')


if __name__ == '__main__':
    main()

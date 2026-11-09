"""Compare adjacent archived annual releases, offline and without credentials.

The former credential/proxy/monthly-mean implementation was superseded in the
2026-11-09 remediation. This module has no import-time I/O or network access.
"""
from pathlib import Path
import argparse
import pandas as pd
from bls_sources import load_archives

ROOT=Path(__file__).resolve().parents[1]


def main(output=None):
    member=ROOT/'member3_labor_migration'
    current,prior,_=load_archives(ROOT/'data/raw/member3',member/'source_snapshots',
                                  pd.read_csv(ROOT/'data/reference/region_lookup.csv'))
    fields=['country','region_id','year','unemployment_rate_pct','source_release']
    comparison=current[fields].merge(prior[fields],on=['country','region_id','year'],
                                    validate='one_to_one',suffixes=('_as_published','_next_release'))
    comparison['difference_pp']=comparison.unemployment_rate_pct_next_release-comparison.unemployment_rate_pct_as_published
    if len(comparison)!=561:raise ValueError('Expected 51 regions times 11 overlapping annual releases')
    destination=Path(output) if output else member/'bls_revision_check.csv'
    if destination.resolve()!=(member/'bls_revision_check.csv').resolve() and not destination.resolve().is_relative_to(ROOT/'data/cache'):
        raise ValueError('Output must be the explicit member CSV or an isolated data/cache file')
    comparison.to_csv(destination,index=False,float_format='%.10f')
    print(f'{len(comparison)} official annual comparisons; max |revision|={comparison.difference_pp.abs().max():.3f} pp')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path)
    main(parser.parse_args().output)

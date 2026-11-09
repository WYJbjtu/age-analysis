"""Source-aware labor and migration checks, shared by the builder and offline tests."""
import numpy as np

KEY=['country','region_id','year']


def validate_labor_counts(frame):
    required=['labor_force','employment','unemployment','unemployment_rate_pct']
    if frame[required].isna().any().any():raise ValueError('Missing labor counts/rates')
    if not np.isfinite(frame[required].to_numpy()).all():raise ValueError('Non-finite labor values')
    if (frame[required]<0).any().any() or (frame.labor_force<=0).any():raise ValueError('Invalid labor counts')
    # Each independently rounded thousand-person count has a +/-500 interval.
    gap=frame.labor_force-frame.employment-frame.unemployment
    low=100*(frame.unemployment-500).clip(lower=0)/(frame.labor_force+500)
    high=100*(frame.unemployment+500)/(frame.labor_force-500)
    ok=(gap.abs()<=1500)&(frame.unemployment_rate_pct+.05>=low-1e-9)&(frame.unemployment_rate_pct-.05<=high+1e-9)
    if not ok.all():raise ValueError('Labor rounding intervals do not reconcile')
    return frame[['region_id','year']].assign(identity_gap_persons=gap,feasible_rate_min=low,
                                               feasible_rate_max=high,passed=ok)


def require_same_migration_coverage(frame,field='domestic_net_migration'):
    """A connected time-series segment must have one population and period convention."""
    valid=frame.dropna(subset=[field])
    if valid[['migration_population','migration_period_type']].isna().any().any():
        raise ValueError('Migration coverage/period labels are required before connecting observations')
    if valid.migration_population.nunique()>1 or valid.migration_period_type.nunique()>1:
        raise ValueError('Split migration series at coverage/period breaks before connecting observations')
    return valid


def validate_panel(frame,lookup):
    if frame.duplicated(KEY).any():raise ValueError('Duplicate labor/migration keys')
    expected={(r.country,r.region_id,y) for r in lookup.itertuples() for y in range(2011,2023)}
    if set(frame[KEY].itertuples(index=False,name=None))!=expected:raise ValueError('Invalid/missing geographic keys')
    us=frame[frame.country=='USA']
    if not (us.total_net_migration==us.domestic_net_migration+us.international_net_migration).all():
        raise ValueError('Domestic + international must equal total migration')
    jp=frame[frame.country=='JPN']
    if jp.loc[jp.year<2018,'domestic_net_migration'].notna().any():
        raise ValueError('Japanese-only observations must not enter all-nationality domestic series')
    if not jp.loc[jp.year>=2018].groupby('year').domestic_net_migration.sum().eq(0).all():
        raise ValueError('Japanese inter-prefectural totals must reconcile to zero')

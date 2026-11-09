"""Executable restrictions for the project's documented non-comparable fields."""
SERVICE_DEFINITIONS={
    'USA':'BEA private services, including utilities, excluding government and government enterprises',
    'JPN':'Cabinet Office tertiary industries, including public administration and public services',
}


def require_comparable_pool(frame,variables):
    if frame.country.nunique()>1 and {'services_share_pct','services_va_local'}.intersection(variables):
        raise ValueError('BLOCKED: pooled services use incompatible country definitions; select one country')
    return frame


def annotate_periods(frame):
    result=frame.copy()
    result['population_reference_date']=result.year.astype(str)+result.country.map({'USA':'-07-01','JPN':'-10-01'})
    result['services_definition']=result.country.map(SERVICE_DEFINITIONS)
    result['services_cross_country_status']='BLOCKED: not harmonized'
    result['manufacturing_definition']='nominal manufacturing value added / same-period nominal regional GDP * 100'
    expected=result.country.map({'USA':'CY','JPN':'FY'})+result.year.astype(str)
    valid=result.gdp_reference_period.notna()
    if not result.loc[valid,'gdp_reference_period'].eq(expected.loc[valid]).all():
        raise ValueError('GDP calendar/fiscal year metadata mismatch')
    return result

# USA 2022 integration

USA 2022 rows are populated in all three contract tables. All other country/year rows are preserved by scripts/integrate_us_2022.py. Run that script, scripts/validate_data.py, scripts/merge_core.py and scripts/aggregate_sources.py in sequence.

Services are explicitly BEA private services-providing industries (SAGDP2 line 92), including utilities and excluding government. Do not treat as harmonized Japan services until Member 2 aligns the classification. Amounts are millions of current USD. Working-age population uses 15–64. Migration period is July 2021–July 2022.

51/51 USA population-industry matches; Japanese coverage zero. Missing optional employment and unemployment are intentionally blank. No invented zeros or interpolation. Shared tests check contracts, not completeness of the full research project. Remaining scope: UN national trends, Japan records/comparability, verified labor indicators if needed, case selection. Existing handover report is the historical A delivery, not an updated combined project report. Analysis follows GitHub task definitions, including pooled exploratory plots; with only USA, Combined is the same sample as USA and is not a cross-country result.

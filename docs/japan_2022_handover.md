# Japan 2022 handover and repository migration

Canonical repository: https://github.com/WYJbjtu/age-analysis . Empty replacement was initialized from the existing verified project and member2 industry work. USA 51 records were retained; JP industry 47 records were rechecked with prepare_industry.py --download. JPN demographics now contains all 47 prefectures. Combined core coverage is 98/98, no duplicate keys or missing required core values.

Population: Statistics Bureau Population Estimates, released April 12, 2023; October 1, 2022 total resident population including foreign residents, both sexes. e-Stat tables 11 (counts), 12 (shares), 13 (dependency ratios). Counts multiplied by 1000 but remain rounded estimates, not exact persons. Use published one-decimal percentages; count-derived rates can differ slightly because of rounding. 15–64 defines working age.

Industry: Cabinet Office FY2022, current JPY millions. USA CY2022 current USD millions. Never compare GDP levels across currencies. Japan tertiary services includes public services whereas USA private services excludes government and includes utilities. Service percentages are not harmonized and should be analyzed in separate country panels. Manufacturing is the primary association indicator.

Raw population downloads are in ignored data/raw/member1_jpn and copied to D:/DSC5002_JP_2022/raw on the author computer. Exact URLs/hashes in member1_demographics/jpn_source_manifest.json. Raw files are not committed.

Reproduce: python member1_demographics/prepare_japan.py --download; python member1_demographics/plot_japan_population.py; python scripts/validate_data.py; python scripts/merge_core.py; python scripts/aggregate_sources.py; python analysis/plot_correlations.py --year 2022 --metric manufacturing_share_pct . Population parsing requires pandas, openpyxl and requests.

Remaining: Japanese net migration, employment and unemployment not supplied; UN national trends, regional case selection and sensitivity checks still require work. Do not infer Japanese missing values are zero. Prior A handover report and integration notes describe an earlier stage; current shared CSVs and this note control Japan coverage.

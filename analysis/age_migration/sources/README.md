# Source verification record

All analytical raw files were retrieved live from official public sources during
this task. Exact final URLs, retrieval times, content types, sizes and byte hashes
are in `manifest.json`. They are delivered under `raw/` for offline reproduction.
`acquire.py` separates retrieval from parsing and never replaces raw files.
`results/source_checks.csv` records actual value comparisons; descriptive status is
**READY WITH LIMITATIONS**, not universal methodological equivalence.

## Japan

[Unified Table3](https://www.e-stat.go.jp/en/dbview?sid=0003420482) is the official
age-specific internal-migration table. The delivered original annual files are:

| Year | In / out / net original table | statInfId | Release |
| --- | --- | --- | --- |
| 2019 | Annual detailed9-1 /9-2 /9-3 | 000031931402 /000031931403 /000031931404 | 2020-04-28 |
| 2022 | Annual3-1 /3-2 /3-3 | 000040008242 /000040008243 /000040008244 | 2023-01-30 |

Selections are both sexes, all nationalities, other-prefecture moves, two-digit
prefecture codes01–47.2019 sheet `移動者 総数` and2022 sheet `移動者` are selected
explicitly. Male/female, Japanese/foreign, national/metropolitan/city rows are not
summed into the sample. JP-13 means Tokyo prefecture. All gross counts are checked
against each year's published national row; every net equals in minus out and the
separate net file. Both years'47 totals exactly match repaired Member3 totals.

Native bins are19 five-year/open-ended categories, plus the published total.
The2019 table notes and2022 table footnote state that total includes unknown age.
Their residual is retained explicitly (countrywide unknown inflows/outflows7 in2019,
8 in2022), not redistributed. Checkpoints are compared after parsing; none is used
to construct or rescale observations.

[Official statistical overview](https://www.stat.go.jp/data/idou/1.htm),
[definitions](https://www.stat.go.jp/data/idou/2.html) and
[Q&A](https://www.stat.go.jp/data/idou/qa-1.htm) describe records of registered
address changes, including repeat registrations, for January1–December31.
Foreign residents in the resident register are included; this does not include
international moves as inter-prefectural events. Age information is derived from
birth dates. The retrieved notes do not state the exact age-reference day
unambiguously: **NOT EVALUATED**, with no fabricated day convention.
Current English wording is not used to relabel the all-nationality data as
Japanese-only.2025 rate-definition changes are not applied retrospectively.

Denominators use official annual Population Estimates Table10, both sexes, total
population, October1, five-year bins ending85+:

| Year | statInfId | Release / vintage |
| --- | --- | --- |
| 2019 | 000031921679 | 2020-04-14; original2015-census-base annual population |
| 2022 | 000040045496 | 2023-04-12;2020-census-base annual population |

Both display thousands of persons, converted by multiplying by1,000.
The [2022 population release notes](https://www.stat.go.jp/data/jinsui/2022np/index.html)
state that values are rounded to the display unit. This is already cached in
`jpn2022_pop_index.html`;2019 has its own cached release page.
The2019 supplementary denominator deliberately retains its original vintage;
Member1's later revised stock is read-only, and their differences are exported.

The2022 official age-specific net-rate table2-3, statInfId000040049143
(release2023-04-27), uses October1 same-age population and percent units.
All893 prefecture/age-or-total cells were checked against counts and Table10.
An initial check allowing only rate rounding was insufficient because population
denominators are also rounded. The implemented check intersects the percent-rate
range implied by population D±500 with the published rate±0.005 percentage points.
All cells are compatible under these documented precision bounds. This is **not**
an assertion that an unavailable unrounded official denominator was reproduced.
The module's per1,000 fields are calculated from the delivered rounded population,
and remain separate from published percent rates in the check table.

For2019 the complete annual index, detailed files/notes and official summary were
inspected; a prefecture-by-age official rate table equivalent to2022 was not
verified. That component is **NOT EVALUATED**.2019 analytical rates are transparently
constructed from its official counts and annual Table10, not copied from a chart.

Some official Statistics Bureau HTML files declare Shift_JIS. They remain raw
bytes; methodology reading honors the declared encoding. The Japanese population
workbooks and native-count workbooks are parsed by openpyxl/xlrd, not by guessed
text decoding.

## United States

ACS **1-year**,2019 and2022: B07001(current residence), B07401(residence one year
earlier), B01001(sex by age). For each year the official JSON group metadata were
retrieved from `https://api.census.gov/data/{year}/acs/acs1/groups/{table}.json`.
`results/variable_mapping.csv` saves labels, IDs, age bounds and annotations IDs.
Mappings are selected by label meaning, not a guessed column offset.

The observation API returned an HTTP200 redirect to the Census **Missing Key**
page; no key was requested from credential stores or supplied. The public official
Summary File alternative succeeded:

- 2019: `https://www2.census.gov/programs-surveys/acs/summary_file/2019/prototype/1YRData/acsdt1y2019-b07001.dat`
  (and b07401/b01001). This is the Census2019 table-based **prototype** release,
  linked by its official directory, with2021-01-06 directory dates; not a newer survey year.
- 2022: `https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/1YRData/acsdt1y2022-b07001.dat`
  (and b07401/b01001), official2022 table-based files.

Pipe-delimited UTF-8 source headers map `B07001_E069` to metadata `B07001_069E`,
for example. Only exact state GEO_IDs matching the audited51 FIPS codes are kept.
Puerto Rico (72), territories, national and all other levels are excluded.
This module uses B07001's different-state inflows and B07401's different-state
outflows with their proper current/previous state bases. Abroad, including moves
from Puerto Rico and U.S. island areas, and within-state moves are not included.

[ACS subject definitions2019](https://www2.census.gov/programs-surveys/acs/tech_docs/subject_definitions/2019_ACSSubjectDefinitions.pdf)
and [2022](https://www2.census.gov/programs-surveys/acs/tech_docs/subject_definitions/2022_ACSSubjectDefinitions.pdf)
are delivered. The2022 age section (printed p.53) and mobility section
(printed pp.126–128) identify completed age at interview and a population aged1+
universe, including group quarters. Residence comparisons are relative to each
interview, not calendar-year registration events. Return moves to the same house
are not measured as multiple migration events. No ACS1/5-year products are mixed.

Published total and all15 native age bins are retained for both flows. National
B07001 estimates equal the51-state sum. B07401 does not supply a national row in
these files; instead, all-state interstate outflows are checked against inflows
by age. Totals balance exactly:7,398,337 in2019 and8,230,953 in2022. No adjustment
was made to enforce these balances. ACS totals are never forced to match PEP.
B01001 all46 sex-age cells reconcile to its all-age total;12 sex-age cells form65+.

The official [special-value notes](https://www.census.gov/data/developers/data-sets/acs-1year/data-notes.html)
and [MOE guidance](https://www.census.gov/content/dam/Census/library/publications/2020/acs/acs_general_handbook_2020_ch08.pdf)
are delivered. Summary Files provide E/M cells and numeric annotation sentinels,
not separate EA/MA columns. Raw values, decoded annotations and statuses are
retained; this is not represented as retrieval of separate API annotation cells.
Known negative sentinels become missing, never negative counts. Controlled-total
MOEs remain unavailable. Published MOEs are90%; derived sum/difference/ratio MOEs
are explicitly approximate with unavailable covariances omitted. See the
[data dictionary](../data_dictionary.md) for formulas and sign rules.

## Verification status summary

| Component | Status |
| --- | --- |
| Official count / population files and ACS metadata | Live official retrieval verified; SHA-pinned cached reproduction available |
| Japan2019/2022 47-region age counts, net accounting, Member3 total match | VERIFIED |
| USA2019/2022 51-region interstate definitions, age/total accounting | VERIFIED; ACS survey estimates with approximate derived uncertainty |
| Japan2022 official age-rate definitions / rounding | VERIFIED compatibility with published precision, not exact unrounded reproduction |
| Japan2019 equivalent published prefectural age-rate table | NOT EVALUATED; official count/population construction provided |
| Japan exact age-reference day | NOT EVALUATED; published native bins retained and limitation disclosed |
| Census observation API | NOT retrieved; missing-key redirect, official public-file alternative used |
| Offline reproduction | See actual validation record; no network or private-cache dependency |

The raw metadata pages `jpn_migration_notes_ja.html` and `jpn*_index.html` are
download indexes despite their short filenames; substantive definitions are in
`jpn_terms_ja.html`, `jpn_migration_terms.html` and `jpn_migration_qa.html`.

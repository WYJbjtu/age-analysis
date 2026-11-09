# Poster note — Japanese migration: one definition, 2018–2022

## English caption (read this on the poster, 58 words)

> **Migration is shown for 2018–2022 only.** Until 2017 the Japanese tables
> count *Japanese movers only* (日本人移動者); from 2018 they count *all
> nationalities*. The same year can invert: Osaka 2017 is 2,961 under the old
> definition and 1,136 under the new one. We never chain the two series, so our
> migration figures cover 2018–2022 under one definition.

Use directly under the migration panel or as a footnote: it states the cut-off,
the reason, and the evidence in one breath.

## 中文版（海报或组内说明，可缩到 90 字）

> **迁移数据只展示 2018–2022 年。** 日本《住民基本台帳人口移動報告》在 2017/2018
> 年更换口径：此前只统计"日本人移動者"，2018 年起改为"日本人及び外国人"（含外国
> 居民）。同一年份两种口径甚至方向相反——大阪 2017 年为 2,961（旧口径）对 1,136
> （新口径）。本项目不拼接两种口径，迁移一律使用 2018–2022 年；2011–2017 年单独
> 存档，仅作参考。

## Q&A — 30-second answer if a judge asks "why does migration start in 2018?"

1. **The break is in the source, not in our data.** The 2017 annual report's
   trend table is headed *日本人移動者* (Japanese movers only); the 2018 and later
   single-year tables are headed *移動者（日本人及び外国人）* and include foreign
   residents.
2. **How big is it?** Osaka 2017: **2,961** Japanese-only vs **1,136**
   all-nationalities; Tokyo 2017: **75,498** vs **73,124**. Chaining them would
   draw a fall where the consistent series shows a rise.
3. **What we did.** Kept the contract table on the **2018–2022** definition, moved
   the Japanese-only years to a separate reference file
   (`jpn_migration_japanese_2011_2017.csv`), and left 2011–2017 migration empty
   rather than imputed or spliced.
4. **What is unaffected.** Labour (employment, unemployment rate) covers
   **2011–2022** for both countries; the 2019 vs 2022 comparison, Figure 4 and
   the case studies all use the consistent 2018–2022 migration definition.

## Where the evidence lives

| Fact | File |
|---|---|
| 2017 table header *日本人移動者*, 2018–2022 header *移動者（日本人及び外国人）* | `sources.csv` rows `net_migration_jpn_2011_2017_reference` and `net_migration_jpn_2018_2022` |
| Osaka/Tokyo values under both definitions | this note; any year can be re-derived with `prepare_labor.py` and the raw workbooks |
| Contract table: migration 2018–2022, 2011–2017 empty | `data/processed/labor_migration.csv` |
| Japanese-only reference series | `jpn_migration_japanese_2011_2017.csv` |

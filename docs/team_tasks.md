# Team responsibilities and current handoff

Current local remediation (2026-11-09): Member1 national values and U.S. boundaries independently verified; Member2 CY/FY and service restrictions enforced in shared code/exports; Member3 acquisition, parsing, migration coverage, BLS validation, five figures and English text repaired. Shared merge now contains1176 region-year rows, with optional context left-joined. See [current presentation entry point](../poster/README.md) and [repair report](remediation/repair_report_zh.md) for actual checks and remaining limits. No remote actions are authorized in this task.

Ownership remains: Member1 population; Member2 industry; Member3 labor/migration; Member4 integration/statistical analysis/poster. The user's local repair authorization allowed the remediation lead to update the affected actual deliverables across these boundaries.

## Historical first-milestone plan (retained, not a current checklist)

The original plan below predates the completed member deliveries. Its unchecked tasks and GitHub setup suggestions describe that earlier plan, not unfinished remediation or permission for remote writes.

## Member 1 — Population
**Own:** `data/processed/demographics.csv` and `member1_demographics/`.
- [x] 验证美日2022年地区 65+ 占比的官方表格与统计参考日。
- [x] 填充 51 US + 47 JP 行；列出缺失及对应原因。
- [x] 全国长期趋势及两国地区分布图（图中注明源年份）。
- [x] 写 `findings.md`（两个带数值的可复核发现）。

Member1 update2026-11-06: 2019 contrast and2011–2022 population panel also delivered; see member1_demographics/README.md. Other modules retain independent ownership.

## Member 2 — Industry
**Own:** `data/processed/industry.csv` and `member2_industry/`.
- [ ] 核实 BEA 美国制造业/服务业增加值与日本内阁府行业表的分类可比性。
- [ ] 填充2022地区GDP份额；标注日本 `FY2022`。
- [ ] 绘制行业构成图，写出可比性局限。
- [ ] 写 `findings.md`（两个带数值的可复核发现）。

## Member 3 — Labor and migration
**Own:** `data/processed/labor_migration.csv` and `member3_labor_migration/`.
- [ ] 优先检索可跨国比较的地区失业率/就业人口变化，确认年龄与参考期定义。
- [ ] 查找2022地区净迁移指标，若不可比则分国展示。
- [ ] 在基础人口/产业表有值后，选两组相似年龄、不同产业的地区案例。
- [ ] 产出一组案例比较图及 `findings.md`。

## Member 4 — Integration / statistical relationships / poster
**Own:** `analysis/`, `poster/`, `data/processed/merged_analysis.csv`, shared contracts.
- [x] 初始化项目目录、地区编码和CSV契约。
- [x] 设置 CI、PR/Issue 模板及基础测试。
- [ ] 建GitHub Private仓库、邀请组员、把本模板首次push到main。
- [ ] 开4个 Issues，填上验收标准；让成员从自己的feature分支PR。
- [ ] 把2022人口/产业表合并；记录两个国家各自成功匹配行数和缺失项。
- [ ] 做 pooled 与 within-country 散点图和相关系数；只在数据证明时讨论 Simpson's paradox。
- [ ] 统一图例、字体、图表标题、poster 的视觉叙事，负责合稿。

## Freeze gates
- **Gate A — Contract:** 本仓库CSV字段、地区ID不再随意变化。
- **Gate B — Data:** 2022 population+industry 匹配地区达到可说明的覆盖率，零重复键；任何缺失都有记录。
- **Gate C — Figures:** 每一幅图能用脚本复现；结论有数量证据、有口径/局限说明。
- **Gate D — Poster:** 12分钟可讲完，分工清楚，留问答余量。

Member 4 can regenerate `docs/source_registry.csv` via `python scripts/aggregate_sources.py` after the other members submit their individual `sources.csv` files.

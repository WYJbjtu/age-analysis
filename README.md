# Aging Across Economies

**Visualizing Demographic Change, Industrial Structure, and Regional Divergence in Japan and the United States**

CityU Data Visualization group project · **EDA + Report + Poster + Presentation**. This is **not** a dashboard development project.

## 研究主线

国家老龄化趋势 → 州/都道府县差异 → 产业结构 → 分组关联与区域案例。研究的是**统计关联**，不预设辛普森悖论，也不把相关性解释为因果性。

- **主分析年**：2022（先完成 51 US + 47 JP = 98 个地区的横截面）。
- **可扩展年份**：2011–2022（日本经济核算采用财政年度，需在图表中标记）。
- **最终交付**：Proposal, analytical report, research poster, 12-minute presentation.

## 四位成员及互不重复的职责

| 成员 | 数据 ownership | 负责成果 |
| --- | --- | --- |
| Member 1 | `data/processed/demographics.csv` | 人口年龄与国家/地区趋势图 |
| Member 2 | `data/processed/industry.csv` | 制造业/服务业增加值占比及产业结构图 |
| Member 3 | `data/processed/labor_migration.csv` | 劳动与人口迁移、案例对照 |
| Member 4 | `analysis/`, `data/processed/merged_analysis.csv`, `poster/` | 统一数据、整体/分国家关联、汇报整合 |

**任何成员都不要修改别人的数据表或拥有的图表文件**。需要字段变更，先提交 Issue 讨论。

## 第一次运行

Requirements: Python >= 3.11, Git.

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/validate_data.py
python -m pytest -q
```

**注意**：刚建仓库时三个数据 CSV 只有表头，校验脚本会说明尚无真实记录，不会伪造任何数值。

真实数据准备完毕后：

```bash
python scripts/validate_data.py
python scripts/merge_core.py
```

`merge_core.py` 要求 demographics / industry 都有数据；labor_migration 若缺失会提示并只合并前两者。输出覆盖率和缺失清单。所有占比统一为 **0–100**（不是 0–1）。不进行自动填补或插值。

## 仓库结构

```text
aging-across-economies/
  .github/                  # CI, PR/Issue 模板
  analysis/                 # Member 4 关联性分析
  data/
    raw/                    # 不提交：原始下载数据
    processed/              # 成员独占的规范化 CSV
    reference/region_lookup.csv  # 美日98地区权威编码框架（待来源交叉核验）
  docs/                     # 数据契约、来源、研究设计、演示安排
  member1_demographics/     # M1 源码、图、findings
  member2_industry/         # M2 源码、图、findings
  member3_labor_migration/  # M3 源码、图、findings
  poster/                   # M4 海报与汇报整合
  scripts/                  # 校验和合并工具
  src/aging_economies/      # 共享的轻量工具
  tests/                    # 自动化契约测试
```

## GitHub 协作

1. 在 GitHub 创建名为 `aging-across-economies` 的 **Private** 空仓库（不要预选 README / .gitignore / license）。
2. 组长解压本模板，在文件夹中运行：

```bash
git init -b main
git add .
git commit -m "chore: bootstrap aging economies research project"
git remote add origin https://github.com/WYJbjtu/age-analysis.git
git push -u origin main
```

3. Settings > Collaborators 邀请组员，启用 Issues；每人独立功能分支、通过 Pull Request 合入 `main`。
4. 首批任务见 `docs/team_tasks.md`；组员先阅读 `docs/data_contract.md`。

**建议先让每人完成一个 2022 年的小样本、校验成功后再扩大到98地区，避免最后合并失败。**

## Member 4: integration utilities

When Member 1 + Member 2 have provided valid official data:

```bash
python scripts/merge_core.py
python analysis/plot_correlations.py --year 2022 --metric manufacturing_share_pct
python scripts/aggregate_sources.py
```

**Correlation plots are descriptive and give every region equal weight.** A reversal in slope is not assumed and should only be called Simpson's paradox if warranted by the actual data.

To avoid merge conflicts, each data owner writes provenance to their own `memberX_*/sources.csv`; Member 4 generates the consolidated `docs/source_registry.csv`.

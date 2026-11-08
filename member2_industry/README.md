# Member 2 — 产业模块交接

本模块完成 2022 年第一阶段产业数据与图表：美国 51 个地区（CY2022）＋日本 47 个都道府县（FY2022）。只修改 `data/processed/industry.csv` 与 `member2_industry/`，沿用现有共享字段，不新增依赖。

## 交付内容

- `../data/processed/industry.csv`：98 行，制造业和服务业占比及其分子、分母、统计期。
- `figures/manufacturing_distribution_2022.png` / `.svg`：适合放入汇报的制造业分布主图。
- `figures/usa_industry_composition_2022.png` / `.svg`：美国全地区产业构成。
- `figures/jpn_industry_composition_2022.png` / `.svg`：日本全地区产业构成。
- `findings.md`：英文结果、数值、图表链接、局限和汇报讲稿。
- `sources.csv` / `source_manifest.json`：准确来源、工作表、口径及下载文件校验码。
- `validation.json`：日本 47 个地区逐项核对结果；`summary.json`：图中统计量。

## 复现

先按项目根目录 README 安装原有依赖。在仓库根目录运行：

```bash
python member2_industry/prepare_industry.py --download
python scripts/validate_data.py
python member2_industry/plot_industry.py
python -m pytest -q tests member2_industry
```

本次环境已有所需库，实际运行测试时用 `PYTHONPATH=src python3 -m pytest -q tests member2_industry`，没有新增或升级依赖。

`--download` 只下载缺失文件，存入被 Git 忽略的 `data/raw/member2/`；已存在文件仍核对 SHA-256 和 ZIP 完整性。官方文件若发生修订、校验码不一致，脚本停止，不能直接改校验码绕过复核。美国原始文件必须与已有数据一致；脚本不自动改写美国统计口径。日本 2022 年记录可重复生成，其他国家/年份的已有值保留。

数据读取使用 Python 标准库解析 XLSX 已公布值，不依赖 Excel 或 openpyxl。图表沿用项目已有 pandas、NumPy、Matplotlib。所有正式图提供 SVG，便于放大或由 Member 4 统一排版；两张全地区构成图适合报告附录，汇报可优先使用制造业主图。

## 计算和核对方法

| 项目 | 美国 | 日本 |
| --- | --- | --- |
| 官方来源 | BEA SAGDP2 | 内阁府县民经济核算 |
| 年份 | CY2022 | FY2022，2022-04 至 2023-03 |
| 单位 | 百万美元，现价 | 百万日元，现价 |
| GDP | line 1 | `syuyo1.xlsx` 的 `2022（令和4）年度`，BL 列 |
| 制造业增加值 | line 12 | 同表 I 列 |
| 服务业增加值 | line 92：私人服务业 | 同表 BO 列：官方第三产业合计 |
| 地区选择 | 现有地区表中的 50 州及 DC | A 列编码 01–47，排除政令指定城市及全国合计 |

两个比例均为 `增加值 / 地区名义 GDP × 100`。日本 GDP 还与 `soukatu1.xlsx` 的 `実数` 工作表 O 列逐一交叉核对。

日本第三产业合计另与 AD、AH、AP、AQ、AR、AU、AV、AY、AZ、BA、BB、BC 共 12 个大类相加核对；只加大类，不重复加子行业。GDP 核对 `BL = BI + BJ - BK`，保留税费调整。允许官方整数百万日元四舍五入的微小误差，不做数值填补。

## 服务业口径与小组接手

按本次确认，服务业分国展示。美国包括公用事业但不含政府及政府企业；日本第三产业包含公务及公共教育、医疗等。两国同名字段记录各自官方范围，**不代表统一后的跨国指标**。图标题、图例和 findings 已注明，不比较两国服务业中位数差异，不做合并服务业回归。

Member 4 接手时需注意：现有 `analysis/plot_correlations.py --metric services_share_pct` 仍允许合并样本绘图，本次没有修改其所有者的代码；不能把该输出当作可比的美日服务业关系。制造业也保留财政年度、分类和地区尺度差异的限制。

`merged_analysis.csv` 和 `docs/source_registry.csv` 由 Member 4 维护；本次没有改动。截至 2026-11-08，新仓库的 2022 年人口表已经覆盖美国 51 个地区及日本 47 个都道府县，现有合并表的 98 条记录均标为人口与产业匹配成功（`population_industry_match=both`），不再需要等待日本人口数据。相关背景见 [日本数据交接说明](../docs/japan_2022_handover.md)。本模块交付产业结构描述，老龄化关联分析及合稿仍由相应成员负责。

## 新仓库交付核验（2026-11-08）

项目已迁移至 [WYJbjtu/age-analysis](https://github.com/WYJbjtu/age-analysis)。检查新仓库 main 的 `00a73f0` 版本时，原 Member 2 交付的全部 16 个文件已经包含在内，无需重复覆盖数据、代码或图表。其中 15 个文件与原交付提交 `dd43a25` 逐字节一致；`findings.md` 已由迁移后的仓库补充“日本人口数据已齐全”的状态，本次保留该更新。

- 已使用原下载且通过校验码检查的官方文件，在临时目录重新运行新仓库的数据处理与绘图代码。
- 重新生成的 98 行产业 CSV、三张 PNG 均与新仓库现有文件逐字节一致，统计摘要也一致。原始下载日期和数据版本未改变。
- `python3 scripts/validate_data.py` 通过；`PYTHONPATH=src python3 -m pytest -q tests member2_industry` 共 17 项测试通过。
- 本次交接更新仅涉及这份 Member 2 README，修正过时的人口数据状态并记录核验结果；没有修改其他成员文件或共享分析成果。

## 本次验证（2026-11-05）

- 51 个美国地区金额及占比全部对照重新下载的 BEA 官方文件复核。
- 47 个日本地区 GDP 全部与独立发布的 GDP 总表一致；行业组成及税费核算核对通过。
- 共享 CSV 校验通过，产业表 98 行，必填字段无缺失，无重复主键。
- 重复运行输出一致；与主分支逐字段比较，51 行美国原有数据完全保留。
- 共享测试与本模块测试合计 13 项通过。
- 3 张 PNG 逐张视觉检查，均有对应 SVG。

提交范围为上述两个 Member 2 所有目录/文件，使用独立功能分支通过 PR 交接。按团队规范，合并前需至少一名组员评审；创建 PR 不代表已合并到 main。

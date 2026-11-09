# Data contract · v1 with backward-compatible remediation additions (2026-11-09)

## 稳定主键

所有地区年度表使用 `country,region_id,year` 作为联合唯一键，`country` 只允许 `USA` / `JPN`。
`region_id` 使用 US-CA、US-DC 等美国二字母州缩写，以及 JP-01—JP-47 的日本都道府县编码（`JP-13`=Tokyo）。
唯一合法地区清单见 `data/reference/region_lookup.csv`（51 + 47）。如发现外部数据口径或代码差异，应先用映射表转换，**不可直接改主键**。

### Required files

| owner | path | mandatory columns | optional columns |
|---|---|---|---|
| Member1 | `data/processed/demographics.csv` | `country,region_id,year,age65_share_pct` | `total_population,working_age_share_pct,old_age_dependency_ratio` |
| Member2 | `data/processed/industry.csv` | `country,region_id,year,manufacturing_share_pct,services_share_pct` | `nominal_gdp_local,manufacturing_va_local,services_va_local,gdp_reference_period` |
| Member3 | `data/processed/labor_migration.csv` | `country,region_id,year` | `employment,unemployment_rate_pct,net_migration` |

`year` 是人口统计使用的公历年份；日本 GDP 需在 `gdp_reference_period` 填写对应财政年度标签（例如 `FY2022`），不得假装是与美国完全相同的自然年度。人口统计参考日记录在来源说明中。

## Units and conventions

- 年龄、就业、产业的 **percent** 列都是 `0–100` 范围，例如 `29.0` 表示 29%。
- `old_age_dependency_ratio` 使用 `100 × (age65plus population / working-age population)`，在来源中说明采用 15–64 还是其他工作年龄口径。
- `nominal_gdp_local`, `manufacturing_va_local`, `services_va_local` 为相同本币单位的现价增加值，**不要跨国直接比较金额**。
- 制造业 GDP 占比 = 制造业名义增加值 / 地区名义 GDP ×100；服务业同理。因税金等核算差额，行业占比不一定严格加总到100%。
- `employment` 是居住地口径就业人数，不是企业岗位数；`unemployment_rate_pct` 为0—100，分母是劳动力。美国人口范围为非机构平民16岁及以上，日本为LFS15岁及以上；不得改用总人口或15–64人口作为劳动参与率分母。
- 旧 `net_migration` 仅为兼容保留：美国是国内加国际总净迁移，日本是国内净迁移但2011–2017仅日本人、2018–2022全体国籍。新的国内迁移图必须使用 `domestic_net_migration`；不能把旧列重命名后当作已统一。
- `domestic_net_migration` 为美国DOMESTICMIG和日本全体国籍国内净迁移；日本2011–2017保持缺失。`international_net_migration` 与 `total_net_migration` 仅美国有值且前两部分之和等于总量。`japanese_only_domestic_net_migration` 单独保留日本2011–2017年329条历史值。全部为人，不是迁移率，不推算总流入/流出或青年迁移。
- 行级 `migration_population`、`migration_period_type`、`migration_start_date`、`migration_end_date`、`migration_source_version` 必须保留。美国年度为前一年7月1日至当年7月1日（非普查基期累计量），日本为1月至12月。不同人员范围不得连接成无断点序列。
- 缺失值用 CSV 空单元格，不用0、不用`NA`字符串。除非有透明方法说明，不得自动插值。
- 数值允许多位小数；展示图中再统一四舍五入。

## 避免统计陷阱

- 美国和日本的数据参考日、GDP统计期、行业分类可能不同。始终记录 source title、URL、下载日期、原始表名、年份和口径。
- 共享导出保留 `population_reference_date`（美国7月1日、日本10月1日）、`gdp_reference_period`（美国CY、日本FY4月至次年3月）、`services_definition` 和 `services_cross_country_status`。年键一致只是近似时间对齐。
- 服务业美国BEA私人服务业包含公用事业但排除政府，日本第三产业包含公共活动。跨国合并服务业分析、排名和中位数差值为 **BLOCKED**；`aging_economies.comparability.require_comparable_pool` 在计算前拒绝服务业合并，允许明确的单国内部图。不得把服务业定义为100%减制造业。
- 核心人口–制造业先合并，劳动/迁移必须左连接。可选字段缺失不能缩减主分析的98地区样本；主键合并必须验证一对一。
- 全国时间序列与地区横截面不混合计算相关系数。
- 2022年横截面首先按**国家内部分组**计算相关性，再与合并样本比较；辛普森悖论仅是待检验的可能性。
- 需要考虑地区样本不等人口权重；区域均值不等国家人口加权比例。
- 研究没有任何必要保证相关系数显著或解释变量完备；不能把统计关联解释成因果效应。
- 2019/2022的分国Pearson接近零，不支持稳健方向反转。协方差分解统一采用分母N，国家权重51/98和47/98；2022组间分量占合并协方差99.0969%，不是R²、解释方差或因果贡献。两年相似不等于12年都已检验。

## Member hand-off

1. 写 CSV（UTF-8，逗号分隔，表头严格遵循规定）。
2. 在自己的 `memberX_*/sources.csv` 记录来源信息，每个原始数据集至少一行。
3. `python scripts/validate_data.py` 通过；把校验结果写到 PR 描述。
4. 在个人目录附 `findings.md`：每条结论有具体数值、图表位置和局限。
5. 以 PNG + SVG/PDF 或可重复生成的 Python 脚本交付图片；不要从 PPT 截图作正式图。

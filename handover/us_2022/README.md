# U.S. 2022 handover

本模块提供此前A成员准备的美国51地区成果。仓库当前按人口、产业、迁移主题分工，因此这里作为独立交接输入，未覆盖各成员拥有的data/processed表。

- 报告：deliverables/A_US_2022_数据与地区分布报告.docx
- 原始51地区表：processed/us_states_2022_core.csv
- 仓库主键映射：processed/us_2022_contract_mapping.csv，country=USA，region_id=US-xx，age65_share_pct对应原aging_rate_pct。
- 图表：deliverables/figures，PNG/SVG/PDF。
- 定义与来源：deliverables/变量字典.csv、数据来源.csv；原始版本校验：raw/source_manifest.json。

## 仓库版复现

原始下载数据未提交，首次运行须在此目录安装requirements-analysis.txt，然后运行python scripts/download_sources.py，再运行python scripts/prepare_us.py。脚本生成的raw文件由本模块.gitignore忽略。
BEA地址滚动更新，当前在线文件可能不再等于2026-09-30快照。下载后必须按raw/source_manifest.json核对版本；该下载脚本会更新清单，运行前先保留清单副本。仓库已有的processed表为交付时固定结果。

## 接入说明

Member 1接人口列；Member 2接制造业/GDP列；Member 3接迁移列；Member 4协调合并。services_share_pct尚未按可比定义整理，不填零、不据此声称产业契约已全部完成。国家内相关分析未在本交付中执行。
原中文接手清单采用旧A/B/C/D角色，仅供任务内容参考；成员职责以仓库README为准。

人口参考日2022-07-01，Census Vintage 2022；GDP为CY2022、BEA 2026-09-30修订版。原报告出现的本机D盘路径应替换为本模块相对位置。

# Aging Across Economies

Regional aging, industrial structure and labor context in the United States and Japan. CityU data-visualization research project: report, poster and twelve-minute presentation.

## 当前交付入口（2026-11-09 修复）

- **[海报与汇报正式入口](poster/README.md)**：选图、英文文字、限制与停用版本。
- **[中文修复报告](docs/remediation/repair_report_zh.md)**：[逐文件变更清单](docs/remediation/file_change_manifest.csv)、[复现与测试](docs/remediation/validation.json)、[图文清单](poster/presentation_manifest.csv)。
- [成员1人口](member1_demographics/README.md) · [成员2产业](member2_industry/README.md) · [成员3劳动迁移](member3_labor_migration/README.md) · [成员4统计分析](analysis/member4/README.md)。

2011–2022 三张成员表与共享合并均有 **1,176 个地区年度键**；主分析仅检验2019与2022，每年98地区（美国50州及DC、日本47都道府县），人口–制造业没有排除项。可选劳动/迁移采用左连接；完整的键覆盖不代表每个迁移指标均非缺失或跨年可比。

**主结论：合并样本呈正关联，但2019和2022年美国、日本各国内部的Pearson相关都接近零；合并关系不能解释为两国内部共有的地区模式。** 不支持稳健方向反转或因果结论。两年的结果不能推广为12年全部已检验。2022年的99.0969%是组间均值分量占合并协方差的比例，不是R²。

## 口径与使用限制

人口参考日为美国7月1日、日本10月1日；GDP为美国CY、日本FY4月至次年3月。制造业比例为同地区、同期间的名义制造业增加值/名义GDP，不能当作就业份额。

跨国服务业合并分析为 **BLOCKED**，代码在计算前拒绝。美国私人服务业与日本第三产业保留各自定义；单国内部服务业附录可用。日本2011–2017国内迁移仅日本人，2018–2022为全体国籍，分列并断开作图，不填补。美国国内、国际、总净迁移分列；旧 `net_migration` 仅用于兼容，不能用作国内迁移。

UN原版WPP2024全国百分比序列已核验，不能用州/县比例的等权均值替代全国率。已有美国地图边界及51地区匹配已核验；没有日本边界图，跨国比较使用完整地区排序图。BLS612条年度记录已从官方归档页文本重建；直接HTML下载返回403，离线复现使用可追溯的文本快照，不宣称最新API复核通过。

## 本地复现

现有虚拟环境为 `.venv`，Python≥3.11。新环境安装项目 `.[dev,sources]`；当前环境已经具备所需依赖。原始公开数据保存在Git忽略的 `data/raw/`，精确来源、版本和SHA-256见各成员清单及 [acquisition.json](docs/remediation/acquisition.json)。不要用新版本文件静默覆盖原缓存。

```powershell
$py = '.\.venv\Scripts\python.exe'
# 可选下载，已缓存时跳过；不需要凭据：
& $py -X utf8 scripts/fetch_remediation_sources.py --group all
# 成员1新增独立验证；原人口数值未改：
& $py -X utf8 member1_demographics/verify_national_and_maps.py
& $py -X utf8 member2_industry/prepare_industry.py
& $py -X utf8 member2_industry/plot_industry.py
& $py -X utf8 member3_labor_migration/prepare_labor.py
& $py -X utf8 member3_labor_migration/check_bls_revision.py
# 成员3的五个绘图命令见其README
& $py -X utf8 member3_labor_migration/build_findings.py
& $py -X utf8 scripts/merge_core.py
& $py -X utf8 scripts/aggregate_sources.py
& $py -X utf8 analysis/member4/verify_sources.py
& $py -X utf8 analysis/member4/run_analysis.py
& $py -X utf8 analysis/member4/build_reports.py
& $py -X utf8 analysis/member4/verify_delivery.py
$env:PYTHONPATH = 'src'
# 使用未存在的新临时目录，避免pytest清空已有资料：
$testTemp = 'data/cache/pytest-' + [guid]::NewGuid().ToString('N')
& $py -X utf8 -m pytest -q tests member2_industry --basetemp $testTemp
& $py -X utf8 scripts/validate_data.py
```

修复版成员4入口识别最新的已核验版本锁，将重算输出写到 `data/cache/remediation/current_member4/`；原 `analysis/member4/audit/`、数据、数值结果和图仍为冻结的历史审计证据。`build_reports.py` 生成当前修复验证摘要，`verify_delivery.py` 从官方缓存独立重建成员1/2/3并比较当前结果。回归表以修复前未舍入计算值为基准，不将旧摘要数值作为强制目标。

当前完整性入口使用 [v5锁](docs/remediation/input_manifest_v5.json) 和仓库内历史证据包；新checkout无需开发者用户目录。v1及修复过程的v2/v3/v4均原样保留，229份原始文件仍按原始SHA-256核验。当前UTF-8文本采用明确的LF表示，历史ZIP成员保留精确原始字节。可移植性修复、行尾映射、显式本地备份检查和统一离线测试范围见 [完整性说明](docs/portability/README.md) 与 [实际验证报告](docs/portability/report_zh.md)。此前图件重建的环境记录仍见 [environment.json](docs/remediation/environment.json)。旧“163个原文件未改动”只描述上轮审计；不要刷新哈希以绕过失败。

通用散点入口仍可用：`python analysis/plot_correlations.py --year 2022 --metric manufacturing_share_pct`。服务业必须显式选择 `--country USA` 或 `--country JPN`。正式主图优先用成员4的已核验三图，避免复制旧图文。

## 分工与协作

成员1拥有人口表和人口图；成员2拥有产业表和产业图；成员3拥有劳动/迁移及相关图文；成员4拥有合并、统计关系与展示整合。本轮用户已授权跨成员本地修复，无需新Issue或PR。后续一般协作规则见 [CONTRIBUTING.md](CONTRIBUTING.md)，字段及口径见 [data_contract.md](docs/data_contract.md)。

当前分支保留 `codex/member4-audit-integration`。本轮不提交、不推送、不创建PR/Issue或进行其他远程写入，所有修改保留在本地工作树。

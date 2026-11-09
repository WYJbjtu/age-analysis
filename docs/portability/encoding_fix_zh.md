# Windows文本解码修复（2026-11-10）

已在分支`codex/member4-audit-integration`、HEAD `f6d44d2f4e3c8ed92588ffa9f85ca4e6f7d13f73`完成本地补丁；初始工作树干净，分支和HEAD未变，无暂存内容。本轮只修复文本编码、相关诊断及必要的显式锁版本更新。

## 根因与原始字节

`test_bls_parser_rejects_truncated_source_table`调用`Path.read_text()`未指定编码，Windows默认cp1252在读取UTF-8快照时失败，尚未进入截断表检查。这与上次证据包路径问题不同。本机cp936、UTF-8模式0也复现原失败（GBK解码异常）。

完整快照18,692字节严格UTF-8解码成功（18,400字符，146个非ASCII字符），并匹配来源清单；其余11份BLS文本快照也严格解码通过。对完整原字节显式cp1252严格解码，复现位置146的0x81异常。没有删除字符、转码、覆盖或重新下载快照。

快照SHA-256 **修复前 = 修复后**：

`a13b1ba42c2eed66aab57aa7e7e1c61326016d3a2fdc35d2a467542efe89180d`

历史证据ZIP SHA-256前后也一致：

`460f7a2f560ee4b900047c69e5998d6d45222309155b49972f07327bf2e63cf5`

## 实际修改

- 目标测试明确`read_text(encoding='utf-8')`，原`pytest.raises(ValueError, match='expected 51')`断言保留。
- 同一测试文件的JSON读取、夹具写入，成员2测试的CSV文本读取，以及直接相关的来源清单、验证和报告脚本的UTF-8文本I/O均补齐编码；保留原`utf-8-sig`来源CSV约定，未改二进制读写或哈希。BLS读取移除原`errors='replace'`，现严格解码，不改变表解析计算。
- 新增一个小型子进程回归检查：关闭UTF-8模式、打开默认编码诊断，并将`test_remediation`模块的EncodingWarning视为错误。还以仅存在内存中的遗漏编码负例确认此防线会失败，未破坏真实文件。
- pytest配置仅对涉及的项目模块把EncodingWarning提升为错误，未屏蔽第三方警告。Linux/Windows Python3.11矩阵保留；CI记录locale并以`-X utf8=0 -X warn_default_encoding`测试，不依赖强制UTF-8模式。

## 锁与证据保护

上述代码受v5保护，因此通过原有显式作者入口创建 **v6**：

```text
python -X utf8=0 scripts/build_portable_integrity.py lock --version 6 --delta docs/portability/encoding_delta.json
```

原作者入口固定回到v4；本次仅将后继版本操作改为校验delta指定的当前活动锁v5，并保留前序锁引用。验证器、历史包结构及校验策略未重设计。v1至v5均未覆盖，历史ZIP未重建；[精确代码/配置差异](encoding_delta.json)记录修改前后SHA及理由。v6验证282份当前输入、229份历史原文件、v1要求的163份及46份不可变仓库审计文件。全部通过。

所有交付的源快照、数值数据、图、不可变审计和旧锁逐字节不变；38项主分析比较差值全部为0。未重采数据、重画图或更改统计方法。

## 实际验证环境与结果

|环境|Python|locale.getencoding()|UTF-8模式|目标测试|完整套件|诊断套件|
|---|---|---|---:|---|---|---|
|Windows本地虚拟环境|3.12.4|cp936|0|1 passed|89 passed|89 passed|
|Linux WSL|3.11.18|UTF-8|0|1 passed|89 passed|89 passed|

两环境均实际执行：

```text
python -X utf8=0 -c "import sys,locale,json;print(json.dumps({'python':sys.version,'locale_encoding':locale.getencoding(),'utf8_mode':sys.flags.utf8_mode}))"
python -X utf8=0 -m pytest -q tests/test_remediation.py::test_bls_parser_rejects_truncated_source_table
python -X utf8=0 -m pytest -q
python -X utf8=0 -X warn_default_encoding -m pytest -q
python -X utf8=0 scripts/validate_data.py
python -X utf8=0 scripts/remediation_state.py
python -X utf8=0 analysis/member4/freeze_inputs.py
python -X utf8=0 scripts/verify_remediation.py regression --no-write
```

完整测试使用独立的新临时目录。三张表各1176行的数据契约检查通过，完整性检查通过，38项主分析比较最大差0；`git diff --check`通过。诊断套件没有项目EncodingWarning；两边各保留1条第三方`matplotlib/font_manager.py:1191`警告，没有以全局忽略掩盖。当前工作树只读验证与测试未刷新任何期望哈希。

**Windows Python3.11/cp1252完整套件：NOT EXECUTED（本机为3.12.4/cp936）。** cp1252仅执行了上述原字节解码探针，不将其称为cp1252全套测试。远程Actions未触发。测试捕获使用`PYTHONIOENCODING=utf-8`仅统一标准输出编码；文件I/O始终保持`sys.flags.utf8_mode=0`。完整本地命令/返回码/输出保留在`data/cache/encoding-fix/windows/results.json`和`linux/results.json`，无需提交缓存。

## 下一次提交

本轮修改前已将涉及的16个原文件及初始状态/diff备份到`C:\Users\15811\.codex\visualizations\2026\11\09\01a1bf45-e2b6-7522-9919-1fffbb145101\encoding-fix-backup-20261110-001423`；未建立新的大规模备份框架，原备份未动。精确提交列表已更新为[next_commit_files.txt](next_commit_files.txt)，共19个路径：

- `.github/workflows/validate.yml`
- `README.md`
- `analysis/member4/build_reports.py`
- `analysis/member4/download_sources.py`
- `analysis/member4/verify_sources.py`
- `docs/portability/README.md`
- `docs/portability/encoding_delta.json`
- `docs/portability/encoding_fix_zh.md`
- `docs/portability/next_commit_files.txt`
- `docs/remediation/input_manifest_v6.json`
- `member2_industry/prepare_industry.py`
- `member2_industry/test_industry.py`
- `member3_labor_migration/bls_sources.py`
- `pyproject.toml`
- `scripts/build_portable_integrity.py`
- `scripts/fetch_remediation_sources.py`
- `scripts/finalize_remediation.py`
- `scripts/verify_remediation.py`
- `tests/test_remediation.py`

不提交`data/cache/encoding-fix`的运行缓存。原历史报告/清单保留，本记录只补充编码修复。

No commits, pushes, or remote writes were performed.

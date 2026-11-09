# GitHub Actions 可移植性修复（2026-11-09）

已在现有分支 `codex/member4-audit-integration` 完成代码修复和干净环境验证。初始及最终HEAD均为 `d6f90cc46507d915151cb67a61714bab19362462`；初始工作树干净，本轮未切换分支、重置、拉取、合并或暂存。原先成员修复已由用户写入该提交；本轮只处理完整性、路径/行尾和CI覆盖。

## 根因与修复

原调用链 `tests/test_member4.py` → `freeze_inputs.main()` → `remediation_state.verify()` → `verify_history()` 无条件读取 `prechange_manifest.json` 中Windows用户目录的外部备份。Linux新checkout没有该目录，因此在 `.editorconfig` 失败。已在真实Linux/Python3.11的干净旧版本目录重现，见 [原失败日志](failure_before.txt)。这不是数据数值错误。

另一个隐患是行尾：原v4的268个输入中，**124个**Windows工作树文件为CRLF、Git对象为LF，所有差异均仅为行尾；此前没有仓库属性文件，`core.autocrlf=true`。原锁记录工作树字节，修掉路径依赖后仍会在Linux遇到哈希不一致。

实际修改6个原文件：`.github/workflows/validate.yml`、`README.md`、`analysis/member4/freeze_inputs.py`、`pyproject.toml`、`scripts/remediation_state.py`、`scripts/verify_remediation.py`。新增明确的Git属性、证据包及清单、独立作者工具、针对故障的测试与本目录记录。所有原数据、图、统计结果和海报叙事均未修改；原有288个已跟踪文件中282个字节完全不变。

## 可移植的历史保护

- 归档 `docs/remediation/historical_evidence.zip`：**229份原始文件＋4份原有清单/锁 = 233个成员**；原始229份总量16,828,410字节，包含元数据共17,035,898字节，压缩后 **9,092,047字节**，最大成员2,444,669字节。
- 229份全部匹配最初prechange清单的原SHA-256；其中v1要求的163份另外逐一验证。原文件来自仍然可用的原备份，未从修复后的文件重建历史。
- 包中额外保留原prechange清单及v2/v3/v4的精确原始字节；旧清单未覆盖。压缩包SHA-256：`460f7a2f560ee4b900047c69e5998d6d45222309155b49972f07327bf2e63cf5`。逐成员来源、大小、SHA见[证据清单](../remediation/historical_evidence.json)。
- 当前v5保护 **280份输入**；仓库中 **46份不可变历史审计文件**同时与归档原始内容验证。普通检查完全不访问开发者备份；显式 `--local-backup PATH`仍可验证其229份原始字节，错误目录或坏文件必定失败。
- ZIP仅按原清单打包；没有复制`.codex`目录、用户配置、`.git`、虚拟环境、凭据、`.env`或无关下载。高可信密钥/私钥模式扫描（包括DOCX内部XML）无命中。历史BLS脚本只作为原始证据归档，未执行、导入或被测试收集。
- ZIP及JSON均经`git check-ignore`确认未被忽略；ZIP是实际9.1MB文件，不是LFS指针。验证直接读成员，不解包；拒绝绝对/越界/反斜杠/盘符路径、重复成员、链接、加密成员和超限大小。

## 新锁与行尾策略

通过显式命令创建 **v5**；理由严格限定为代码、配置、测试范围及历史证据交付变化。[授权差异](authorized_delta.json)逐文件记录修改前后SHA和原因。创建器先确认未列入差异的v4文件原字节未变，并拒绝本任务修改数据/图/不可变审计。v1/v2/v3/v4全部保留，旧锁链SHA按ZIP中的原始字节验证。

`.gitattributes`规定当前文本LF、二进制和ZIP不转换。v5逐条声明`utf8-lf`或`bytes`，仅对声明的UTF-8文本将CRLF映射为LF；不删空白、不改编码、不补末尾换行，拒绝孤立CR。ZIP内历史字节永不规范化。旧审计文本在仓库中的LF表示与归档原内容建立明确映射，详见[line_endings_before.json](line_endings_before.json)。没有改写历史预期哈希来掩盖失败。

普通`remediation_state.py`及`freeze_inputs.py`只读验证；缺失锁不会触发重建。建包/新锁命令与CI彻底分离，CI不调用作者工具。

## 测试范围、实际命令与结果

旧默认`testpaths=["tests"]`实际收集40项；此前本地显式添加`member2_industry`，增加25项，因此为65项。已静态审查这25项：只读已交付表、调用纯解析/绘图校验和隔离合成夹具，无BLS在线依赖或私有缓存。现在默认路径同时包含两处；另新增23项针对真实完整性故障的测试，所以实际收集 **88项**。未为了计数删测、跳测、xfail或放宽断言。

保留Linux并增加Windows矩阵，均配置Python3.11；checkout/setup-python版本未升级。声明的`.[dev]`在新虚拟环境实际安装成功；完整离线套件无需可选`.[sources]`。重新采集官方数据与生成图件不是日常CI范围，本轮未执行这些无关工作。

|干净环境|Python|完整默认套件|主分析回归|
|---|---|---|---|
|linux|3.11.18|88 passed|38 high-precision main regression comparisons passed; max difference 0|
|windows|3.12.4|88 passed|38 high-precision main regression comparisons passed; max difference 0|

两套环境均从**298份实际拟交付文件**创建checkout等价目录，包含未提交修复及ZIP，排除`.git`、个人目录、外部备份、源下载缓存及已有虚拟环境。安装器产生的egg-info/测试缓存不是输入证据。每次验收前后298份文件SHA完全一致。测试进程用审计钩子拒绝联网和原外部备份读取，并先实际探测确认两种拒绝有效；因此成功不依赖开发者备份仍然可访问。

实际执行的关键命令（Linux和Windows均成功；完整参数、cwd、返回码和输出见[Linux记录](linux_commands.json)、[Windows记录](windows_commands.json)）：

```text
python -m pip --isolated install -e <actual-proposed-checkout>[dev]
python -m pytest -q tests/test_member4.py::test_reviewed_current_inputs_and_historical_inputs_are_protected
python -m pytest --collect-only -q
python -m pytest -q --basetemp <new-isolated-directory> --junitxml <results>
python scripts/validate_data.py
python <absolute-checkout-path>/scripts/remediation_state.py
python <absolute-checkout-path>/analysis/member4/freeze_inputs.py
python scripts/verify_remediation.py regression --no-write
```

两个绝对路径完整性命令均从checkout以外目录调用，验证不依赖工作目录。新失败模式测试涵盖当前文件/历史文件改动、ZIP缺失或改动、成员及包预期校验篡改、路径越界、重复成员、符号链接、无效显式备份、只读验证和CRLF/LF映射。实际统计回归由既有测试和38项完整比较覆盖，差值全部为0；三张表仍各1176行。

原Windows工作环境也执行默认88项（全部通过；仅原环境AnyIO插件弃用提示），数据契约和38项回归通过。`git diff --check`通过。原始外部备份显式检查229项通过。

Linux首轮隔离验收曾因将pytest临时捕获文件放在WSL挂载盘而发生truncate文件错误；保留[该轮日志](linux_temp_failure.json)，改用Linux原生临时目录后完整通过。没有修改项目断言绕过该环境问题。Windows虚拟环境/安装初次受沙箱权限阻止，经工具批准后在隔离环境完成；没有借此修改系统Git或防推送设置。

## 交付清单与边界

修复前已备份全部288份跟踪文件及Git状态/diff至：`C:\Users\15811\.codex\visualizations\2026\11\09\01a1bf45-e2b6-7522-9919-1fffbb145101\aging-portability-backup-20261109-231946`。原先229份外部备份完整保留。本轮前后SHA及备份位置见[file_change_manifest.csv](file_change_manifest.csv)。旧成员4审计和上轮修复记录仍是历史资料，本报告是当前可移植性补充，不覆盖旧结论。

**下次提交必须一并包含**六个修改文件、`.gitattributes`、`scripts/build_portable_integrity.py`、`tests/test_portable_integrity.py`、历史ZIP和JSON、`input_manifest_v5.json`及本目录交付记录。精确逐路径列表见[next_commit_files.txt](next_commit_files.txt)；不能只提交代码而漏掉ZIP/锁/授权差异清单。不要提交`data/cache/portability`中的环境和测试目录。

当前分支仍为`codex/member4-audit-integration`，HEAD不变，无暂存内容；实际Git状态见[final_state.json](final_state.json)。本地修复无未解决阻塞。实际GitHub Actions未远程触发，不能声称远程已绿；本机Windows Python3.11未执行（实际为3.12.4），Linux已按工作流Python3.11验证。

No commits, pushes, PRs/issues, uploads, deployments, or other remote writes were performed. All modifications remain local.

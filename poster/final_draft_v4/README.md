# 海报 V4：收尾组位置修正

从最新本地 `poster/final_draft_v3/` 继续修改；V1、V2、V3 原文件均保留。本版仅修改展示文字和排版，没有新增研究、模型、观测或统计结果。

## 当前交付

- `poster.pdf`：单页 A0 竖版，印刷时使用实际尺寸。
- `poster.preview.png`：从实际 PDF 渲染的 4245 × 6000 像素预览。
- `poster.html`、`poster.css`、`content.json`、`build_poster.py`：可编辑排版与文字源稿。重建会覆盖本版 HTML。
- `plot_figures.py`、`figures/`：同一验证数据生成的 SVG 与 300-dpi PNG。
- `appendix/evidence_tables.html`：完整系数、65+ 结果与详细口径；其内容与 V3 一致。
- `next_commit_files.txt`：本版精确文件列表，未执行提交。

第三栏顺序为：年龄迁移结果 → 东京年龄剖面及解释 → **KEY FINDINGS** → **RESEARCH LIMITATIONS**。后两节构成一个连续收尾组，以约 6 mm 间距和细线分隔，没有卡片背景。限制段落逐字采用本次用户提供的英文文本，仅出现一次，且不在第一栏或跨页底栏。

三条结论仍使用 30 pt 深红标题与 24 pt 正文。限制标题用较安静的灰褐色、常规字重，正文仍为 24 pt，没有通过缩小字号来塞入新段落。页脚保留具体人口与 GDP 时间口径；描述性/非因果、两期不能推广全年、单年流量不能解释累计年龄结构等一般性限制集中到新段落。图内分母、ACS 区间、空心/实心点解释、来源、东京未知年龄与净值记账关系均保留。

## 三栏平衡与图幅

三栏仍各宽 253 mm、间距 14 mm，顶部同为页面约 160 mm。内容底部距共同基线分别约 6.0、9.1、0.0 mm，限制段落正好落在该基线上，页脚位于其下方。

| 图 | V3 高度 → V4 高度 | 调整目的 |
| --- | --- | --- |
| 国家趋势 A | 230 → 275 mm | 平衡第一栏，保持原字号、单位及坐标范围 |
| 全地区分布 B | 325 → 380 mm | 保留完整 98 点，增加垂直展示空间 |
| 制造业趋势 C | 135 → 150 mm | 平衡第二栏 |
| 独立服务业趋势 D | 225 → 240 mm | 平衡第二栏，仍为两国分别展示 |
| 制造业关联 E | 355 → 355 mm | 不变 |
| 青年迁移 F | 320 → 320 mm | 不变，完整保留美国 51 个不确定性区间 |
| 东京年龄剖面 G | 280 → 250 mm | 收紧年龄组间垂直留白；文字、横轴、条形数值及全部年龄组不变 |

所有图均按目标物理尺寸重新生成，没有在排版中拉伸图片。图内字号与 V3 相同；E、F 的 SVG 逐字节一致。前两栏只调整完整内容组间距，没有将单行文字均匀摊开。标题、作者顺序、姓名、学号、配色和外框保留。

## 验证

`qa/validation.json` 记录实际 PDF 的单页尺寸约 840.994 × 1188.889 mm、字体和空间检查：无溢出、重叠、缺字或未加载字体。标题 106/116 pt、作者 32 pt、正文/限制 24 pt、图注 20 pt，最小绘图字号约 18 pt。检查了实际 PDF 的整页、底部三分之一、收尾组、东京图、作者行、青年区间、产业与人口图局部，以及灰度预览。未进行实体 A0 打样或色觉缺陷模拟。

13 项正文数值和七组完整图示统计检查与 V3 完全一致；人口 98 地区、服务业 24 个国家年份汇总、美国 51 个区间（35 个包含零）、东京两年各 20 个年龄/未知年龄条形均通过原有检查。现有主分析 38 项高精度回归检查通过，最大差 0；v6 完整性锁通过。本轮没有运行完整 pytest 套件，也没有重新获取官方数据。

当前快照保护的 661 个既有文件校验和未变，覆盖原研究交付及 V1–V3。本版验证将旧的“Key Findings 必须最后”条件替换为本次明确要求的“Key Findings 紧邻 Research Limitations，后者最后”；科学数值检查未放宽。PDF 页脚在绘制流中先于各栏输出，因此其相对位置使用实际 PDF 坐标核验，不能仅用文本提取顺序判断。

详细记录见 `qa/visual_review.json`、`qa/execution.json`、`revision_baseline.json`。来源、输入与图文映射沿用 `input_manifest.json`、`provenance_manifest.json`、`figure_manifest.json` 和 `content_manifest.json`。

## 本地重建

在安装 `requirements.txt` 声明依赖的 Python 环境中，准备本地 Chromium 与 Poppler，从本目录执行：

```powershell
python -X utf8=0 -X warn_default_encoding plot_figures.py
python -X utf8=0 -X warn_default_encoding build_poster.py
python -X utf8=0 -X warn_default_encoding render_poster.py
pdftoppm -png -singlefile -scale-to 6000 poster.pdf poster.preview
python -X utf8=0 -X warn_default_encoding validate_poster.py
```

`render_poster.py --browser <本地浏览器路径>` 可指定浏览器；页面 HTTP(S) 请求一律阻止。全部数据快照、字体与附录素材已包含，不依赖私有数据缓存。脱离原仓库验证时加 `--standalone`，该模式不宣称验证原仓库保护文件。本轮未另做新的隔离目录重建测试。

实际运行环境为 Windows，绘图/构建/导出使用 Python 3.12.4，PDF 校验使用随附工具环境的 Python 3.12.14；两者均为 cp936、UTF-8 模式 0。绘图保留了一条 Matplotlib 内部 `EncodingWarning`；项目文本读写均指定 UTF-8。Chromium 导出使用已批准的本地进程权限。未测试 Linux 或 cp1252。

分支仍为 `codex/member4-audit-integration`，HEAD 为 `a311a18748d676196b523668dab7ed6e17472635`。V4 是新增未跟踪目录，原有未跟踪工作保持原状，共享入口未改写。

No commits, pushes, PRs/issues, uploads, deployments, or other remote writes were performed. All changes remain local.

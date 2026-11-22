# 分年龄国内迁移模块：中文交接

范围：日本47都道府县、美国50州加华盛顿特区，2019／2022。两国均完成，
状态 **READY WITH LIMITATIONS**。新增内容全部位于 `analysis/age_migration/`；
未把本任务扩展到制造业、服务业、政策评价或仪表板。
工作分支保持`codex/member4-audit-integration`，HEAD为`a311a18748d676196b523668dab7ed6e17472635`；
最终git状态仅新增`?? analysis/age_migration/`，原跟踪文件无diff。

## 数据和定义

日本采用e-Stat原始年度表：2019详细表9-1/9-2/9-3、2022表3-1/3-2/3-3，
都是全体国籍、男女合计、都道府县间转入／转出／净迁移。分母为各年10月1日
Population Estimates表10的同龄人口（千人转换为人）。2019原始年度人口版本
与Member1后续修订的老龄化存量版本不同，未覆盖原表。2022官方分龄净迁移率
表2-3的893个单元格均与人口取整及率取整范围兼容，不冒称复现未公布精度。
2019对应官方分龄率表及日本年龄划分的精确参照日仍为NOT EVALUATED；
前者已提供官方计数/人口构造率，后者保留原生年龄分类并披露限制。

美国采用ACS1-year2019／2022的B07001当前居住地州际转入减去B07401一年前
居住地州际转出，分母为B07001当前同龄居民；B01001提供全龄分母及单独的
ACS老龄化敏感性。观察值API返回Missing Key页面，改用官方公开Summary Files：
2019table-based prototype和2022table-based文件。元数据JSON亦已取得。
该流程没有混入5年产品、州内迁移或国外迁移，也未把ACS强行缩放到PEP总量。

原生表3,606行；派生表1,176行＝196地区年×6年龄组，**不是12年面板**。
主组20–24和65+，支持组20–34，另保留25–29、30–34、35–64；非重叠20+图谱
不同时加总20–34与其子组。每年每组实际有效地区47／51，无主分析缺失。
日本年龄未知残差独立保存；2019／2022全国未知转入和转出分别7／8，未摊派。
1,935项来源／会计核对通过，日本94个地区年总净迁移与既有修复数据一致。

## 实际结果

表中Pearson／Spearman均为地区等权，未混合国家、未报告普通p值为调查误差检验。

| country | year | age_group | included | pearson | spearman |
| --- | --- | --- | --- | --- | --- |
| JPN | 2019 | 20-24 | 47 | -0.812245 | -0.836147 |
| JPN | 2022 | 20-24 | 47 | -0.820295 | -0.820461 |
| JPN | 2019 | 65+ | 47 | -0.331999 | -0.522780 |
| JPN | 2022 | 65+ | 47 | -0.048128 | -0.269381 |
| JPN | 2019 | 20-34 | 47 | -0.775870 | -0.716235 |
| JPN | 2022 | 20-34 | 47 | -0.766268 | -0.709308 |
| USA | 2019 | 20-24 | 51 | -0.336607 | -0.257557 |
| USA | 2022 | 20-24 | 51 | -0.362190 | -0.254389 |
| USA | 2019 | 65+ | 51 | 0.134998 | 0.053303 |
| USA | 2022 | 65+ | 51 | 0.439167 | 0.359910 |
| USA | 2019 | 20-34 | 51 | -0.149296 | -0.117919 |
| USA | 2022 | 20-34 | 51 | -0.284913 | -0.249774 |

日本20–24岁的2022 Pearson为-0.820295，删除东京后
-0.795747；2019为-0.812245。
美国2022为-0.362190，删除DC后-0.212467；
2019为-0.336607。美国关系较弱且受DC影响，不能包装成共同的日美规律。
日本2022的65+ Pearson为-0.048128，逐一删除地区后
范围跨零；美国同指标由2019的0.134998变为2022的
0.439167。所有54项预定比较、588次逐一剔除及完整
敏感性均交付，无按结果删除不合叙事的地区或年份。

东京2022：15–19岁+13,795，20–24岁+57,153，
其余年龄合计-32,925，总计+38,023，四项参照值
全部复现。65+单独为-9,284。20–24岁净流入为正的只有埼玉、
东京、神奈川、爱知、大阪。美国按全样本2022青年率极小／极大规则选出新罕布什尔
和DC，保留两年、误差线和选择规则；它们不被称为城市，也不等同东京都市核心。
两例2022总净迁移区间都跨零，图中明确列出总量MOE，异号仅描述点估计，不能
说总量方向已被确定；见`results/case_totals.csv`。

ACS保存原始E/M单元格、缺失哨兵与注释。净量/加总使用RSS近似，率误差同时
纳入分子与分母MOE；同一调查估计的协方差未知，未声称独立或精确区间。
受控制全龄总人口MOE保留缺失而非零，因此总人口分母率的区间不冒算。
美国2022青年率29个正点估计中，仅8个
在近似区间下支持正方向；35/51的区间跨零，全部保留在图中。

## 海报和12分钟展示使用

可用结论：日本两年青年率与老龄化的强负向描述关系；美国较弱且受DC影响；
65+关系不同；总净迁移可掩盖相反的年龄组流向。不支持：迁移造成某比例老龄化、
所有都市吸引所有年龄、东京证明普遍规律、两年代表完整历史或低老龄化等于下降。
已提供英文数值发现、图注、90–120秒讲稿与3条答辩问答，建议替换现有Member3
时段，不延长总12分钟。详见 `presentation/integration_proposal.md`。
共享poster入口和旧图未改写；团队仍需决定最终拼版、时段采用并排练计时。

主图路径：`figures/figure1_regional_2022`、`figure1_regional_2019`、
`figure2_native_cases`；附录为`appendix_profiles_jpn`和`appendix_profiles_usa`。
每项都有SVG和300dpiPNG。5张PNG已实际打开检查，详细记录见visual_inspection.json。
数据、变量映射、覆盖、来源校验、相关及敏感性表见README直达链接。

## 真实验证记录

- `full_offline_utf8_off`：退出码 0；103 passed, 1 warning in 21.94s。
- `full_offline_encoding_warnings`：退出码 0；103 passed, 2 warnings in 21.92s。
- `reviewed_v6_integrity`：退出码 0；}。
- `member4_readonly_freeze_entry`：退出码 0；Protected current inputs, immutable audit artifacts and portable original bytes: {'historical_evidence_files': 229, 'historical_v1_files': 163, 'immutable_repository_files': 46, 'archived_reviewed_locks': 3, 'local_backup': 'not requested', 'current_protected_files': 282, 'current_input_lock': 'docs/remediation/input_manifest_v6.json'}。
- `data_contracts`：退出码 0；Contracts validated. This does NOT verify official source accuracy or full country/year coverage.。
- `main_analysis_readonly_regression`：退出码 0；38 high-precision main regression comparisons passed; max difference 0。

实际环境和完整命令见 `results/validation.json`，逐条输出见 `results/logs/`。
不把缓存读取称为新一次在线复核，不把Windows cp936测试称为cp1252或Linux测试。
实际Python3.12.4、locale cp936、UTF-8模式0。诊断运行保留第三方Matplotlib
EncodingWarning及anyio弃用警告；项目自身编码警告按测试配置视为错误，未隐去警告。
原始数据在线取得与随后离线重现分别记录。现有315个跟踪文件、原始图表、历史
证据及v6锁保持原样；旧主分析以只读38项高精度比较检查，不执行历史危险脚本。
独立复现使用明确文件清单包含新增未提交文件，屏蔽网络，不能遗漏必需缓存后
声称干净检出成功。精确下一次提交文件列表为`next_commit_files.txt`；没有代为提交。

初次开发检查暴露两点：日本官方率比对最初只考虑率取整，后按官方人口取整规则
加入严格区间相容性检查；一个测试的旧表合并列名发生冲突，已限定所需字段。
均未修改任何原始观测或通过调整目标值消除差异。

No commits, pushes, PRs/issues, uploads, or other remote writes were performed.
All new work remains local.

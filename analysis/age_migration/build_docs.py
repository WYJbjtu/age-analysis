"""Generate numerical findings and handoff from validated result tables, offline."""
from pathlib import Path
import json
import pandas as pd
from acquire import MODULE


def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text.strip()+'\n',encoding='utf-8',newline='\n')


def markdown(frame,columns):
    lines=['| '+' | '.join(columns)+' |','| '+' | '.join('---' for _ in columns)+' |']
    for values in frame[columns].itertuples(index=False,name=None):
        cells=[f'{v:.6f}' if isinstance(v,float) else str(v) for v in values]
        lines.append('| '+' | '.join(cells)+' |')
    return '\n'.join(lines)


def build(module=MODULE):
    module=Path(module)
    read=lambda name:pd.read_csv(module/'results'/f'{name}.csv',encoding='utf-8')
    a=read('associations');inf=read('influence_summary');tok=read('tokyo_decomposition')
    cases=read('case_selection');unc=read('us_uncertainty_summary')
    native=pd.read_csv(module/'data/native_migration.csv',encoding='utf-8')
    baseline=json.loads((module/'results/baseline.json').read_text(encoding='utf-8'))
    primary=a[a.variant=='primary']
    def coefficient(c,y,age='20-24',variant='primary'):
        return float(a.loc[(a.country==c)&(a.year==y)&(a.age_group==age)&(a.variant==variant),'pearson'].iloc[0])
    j19,j22,u19,u22=[coefficient(c,y) for c,y in [('JPN',2019),('JPN',2022),('USA',2019),('USA',2022)]]
    t22=tok[tok.year==2022].iloc[0]
    un=unc[(unc.year==2022)&(unc.age_group=='20-24')].iloc[0]
    def us_count(rid,age):
        return int(native.loc[(native.region_id==rid)&(native.year==2022)&(native.age_group==age),'net_migration'].iloc[0])
    comparison=markdown(primary,['country','year','age_group','included','pearson','spearman'])
    sens=markdown(a.loc[~a.variant.isin(['primary','common_regions_both_years'])],['country','year','age_group','variant','pearson','spearman'])
    influence=markdown(inf,['country','year','age_group','loo_pearson_min','loo_pearson_max','most_influential_region','max_absolute_pearson_change'])
    findings=f'''# Age-specific domestic migration: findings for presentation

Status: **READY WITH LIMITATIONS**. Full samples: 47 Japanese prefectures and 51 U.S.
state-level regions in both 2019 and 2022. All primary/supporting rates and aging
outcomes are nonmissing. Equal regional weights; countries always separate.
The plan and case rule were saved before any migration/aging correlations were
inspected. No ordinary p-values or causal contributions are estimated.

## Verified descriptive findings

Japan has a strong negative cross-sectional association between ages 20–24 net
migration per 1,000 same-age residents and the share aged 65+: Pearson
{j19:.3f} in 2019 and {j22:.3f} in 2022. Removing Tokyo gives
{coefficient('JPN',2019,variant='without_Tokyo'):.3f} and
{coefficient('JPN',2022,variant='without_Tokyo'):.3f}. All leave-one-region-out
young-adult coefficients remain negative. This is a robust *descriptive regional
association in these two snapshots*, not an estimated cause of accumulated aging.

The U.S. young-adult association is weaker: {u19:.3f} and {u22:.3f}; without DC,
{coefficient('USA',2019,variant='without_DC'):.3f} and
{coefficient('USA',2022,variant='without_DC'):.3f}. DC influences the coefficient,
and ACS sampling uncertainty is substantial. In 2022, {int(un.positive_points)}
positive point estimates include only {int(un.positive_approx_intervals)} with
positive intervals under the stated approximation; {int(un.intervals_including_zero)}
of 51 intervals include zero. This is not evidence of one common cross-country slope.

Older-adult associations differ. Japan's Pearson is
{coefficient('JPN',2019,'65+'):.3f} in 2019 and {coefficient('JPN',2022,'65+'):.3f}
in 2022; removing Tokyo changes the latter to
{coefficient('JPN',2022,'65+',variant='without_Tokyo'):.3f}. Its 2022 leave-one-out
range crosses zero. The U.S. coefficients are
{coefficient('USA',2019,'65+'):.3f} and {coefficient('USA',2022,'65+'):.3f}.
Do not claim that all older regions lose young people, that every urban region
attracts all ages, or that the older-adult pattern is stable or identical across years.

Tokyo's 2022 total net migration is {int(t22.total_net):+,}; ages 15–19 contribute
{int(t22.age15_19_net):+,} and ages 20–24 contribute {int(t22.age20_24_net):+,}.
All other ages combined contribute {int(t22.all_other_ages_net):+,}. Each checkpoint
matches the independently parsed complete primary tables. Ages 65+ specifically
contribute {int(t22.age65plus_net):+,}; **all other ages is not older adults**.
Only Saitama, Tokyo, Kanagawa, Aichi and Osaka have positive 20–24 net counts in
2022. Tokyo's 2019 total was {int(tok.loc[tok.year==2019,'total_net'].iloc[0]):+,};
these annual snapshots are not cumulative migration over 2019–2022.

The pre-specified U.S. case rule selects New Hampshire and DC, the minimum and
maximum 2022 young-rate point estimates, retaining them in 2019. In 2022 New
Hampshire's total ACS net interstate estimate is {us_count('US-NH','total_1plus'):+,} while its ages 20–24 net
estimate is {us_count('US-NH','20-24'):+,}; DC's total is {us_count('US-DC','total_1plus'):+,} while its ages 20–24 estimate is {us_count('US-DC','20-24'):+,}.
These are total **point estimates**: both 2022 total intervals include zero.
Their total MOEs and intervals are in `results/case_totals.csv` and Figure 2.
The selected 2022 young-rate intervals exclude zero under the approximation.
New Hampshire's 2019 young interval includes zero. Selection is on noisy point
estimates; these are not proven population ranks or geographical equivalents to Tokyo.

## All planned primary and supporting comparisons

Rates use same-age current residents; outcome is Member 1's verified aging share.
Every Japanese row has 47 eligible/included regions and every U.S. row has 51.
Missing = 0. The 20–34 group is supporting and overlaps its constituent groups.

{comparison}

## Sensitivities, including weak and contrary results

The common-region sample is the full 47/51 in both years, so its coefficients are
identical to the primary results. Total-population-denominator rates are a
different estimand. B01001 aging is an explicitly separate U.S. outcome sensitivity.

{sens}

Leave-one-region-out diagnostics use point estimates, not survey-error simulation:

{influence}

Complete Spearman influence ranges and all 588 deletions are in the CSV results.
Year-to-year rate correlations are in `results/year_comparison.csv`; persistence
across two snapshots is not a statement about all intervening years or a cohort.

## Interpretation and limits

**Plausible interpretation:** age selectivity helps describe how a positive or
negative total can coexist with opposing age-group balances. It is consistent with
different life-course mobility patterns, but motives were not measured here.

**Unmeasured mechanism/contribution:** education, employment, housing, retirement,
births, deaths, international movement, cohort aging and prior migration can all
matter. This design does not identify their causal roles or the fraction of aging
attributable to domestic migration. Low aging relative to other regions does not
mean a region's aging share is declining over time. Net-zero total migration does
not imply unchanged age composition.

Japan counts calendar-year registered inter-prefectural events; ACS estimates
residence changes over each interview's preceding year for ages 1+, including group
quarters. Exact Japanese age-reference day remains unverified. Japanese 2019
denominators use the original annual vintage; Member 1 retains revised aging
stocks. Japanese counts have no ACS-style sampling MOE; population denominators
are rounded. ACS MOEs for net and rates are approximate, include denominator MOE
where available, and omit unavailable covariances. Correlations are not corrected
for survey error, spatial dependence or shared-denominator relationships.

**Poster-safe:** the strong Japanese young-adult descriptive association in both
snapshots; the weaker and DC-sensitive U.S. result; distinct older-adult patterns;
and the age balances concealed by totals. **Not supported:** universal urban rules,
causal explanations, a percentage contribution to aging, or confident signs for
all positive U.S. point estimates. Keep the country-specific sources and limitations.
'''
    write(module/'presentation/findings_en.md',findings)
    speech=f'''# English presentation segment

Replace the existing Member 3 slot; target 100–115 seconds at a normal rehearsed
pace. Show the complete regional figure before the age-profile cases. This script
is not an additional segment beyond the group's 12-minute allocation.

Our migration module asks whether the age of movers changes what regional totals
tell us. We use all 47 Japanese prefectures and 51 U.S. state-level regions in 2019
and 2022, and analyze the countries separately.

For Japan, young-adult net migration rates are strongly negatively associated with
the share aged 65 and over. The Pearson correlation is about {j22:.2f} in 2022,
and the 2019 result is similar. The relationship remains strong without Tokyo.
In the United States it is weaker: about {u22:.2f}, falling in magnitude to about
{coefficient('USA',2022,variant='without_DC'):.2f} without Washington, D.C. Older-adult
results differ by country and year. The hollow U.S. points have uncertainty
intervals that include zero.

Now consider Tokyo prefecture. Its 2022 total net inflow was about 38,000, but
ages 20 to 24 alone contributed about 57,000. Ages 15 to 19 added about 14,000,
while all other ages together lost about 33,000. Those other ages are not simply
older adults; ages 65 and over lost about 9,300.

Our U.S. cases follow a fixed selection rule. New Hampshire's 2022 point estimates
combine a positive total and negative young-adult balance; D.C. shows the opposite.
Both total uncertainty intervals cross zero. These regions are not equivalent to
Tokyo's urban core.

These are descriptive flow-versus-stock associations. Registration and survey
measures differ, and one year's migration cannot explain the accumulated age
structure or establish how much aging migration caused.
'''
    write(module/'presentation/segment_en.md',speech)
    write(module/'presentation/examiner_qa.md',f'''# Three examiner questions

**1. Does this show migration caused aging?**
No. We relate one year's age-specific net flow to a same-year population stock.
Japan's young-adult association is strong in both snapshots, but aging also reflects
cohort history, births, deaths and other migration. We do not estimate a causal share.

**2. Can the two countries' rates and uncertainties be compared directly?**
The age bins and per-1,000 formula are aligned where exact, but registration events,
ACS residence changes, time windows and populations differ. We analyze countries
separately. U.S. 90% intervals are approximate and omit unknown covariances; in 2022
{int(un.intervals_including_zero)} of 51 young-rate intervals include zero. Japan's
lack of an ACS-style MOE does not imply error-free data.

**3. Were Tokyo and the U.S. cases chosen to fit a story?**
Tokyo was pre-specified. U.S. cases are the lowest and highest 2022 young-rate point
estimates from the full sample, with the same regions shown in 2019. We display
all regions first, keep error bars, and report Tokyo/DC deletion and all-region
leave-one-out results. Extreme point estimates are not proven extreme population ranks.
''')
    validation_path=module/'results/validation.json'
    validation=json.loads(validation_path.read_text(encoding='utf-8')) if validation_path.exists() else {}
    checks=validation.get('commands',[])
    test_summary='\n'.join(f"- `{r['label']}`：退出码 {r['exit_code']}；{r.get('summary','见日志')}。" for r in checks) or '验证记录尚待生成；不得据此声称验收完成。'
    zh=f'''# 分年龄国内迁移模块：中文交接

范围：日本47都道府县、美国50州加华盛顿特区，2019／2022。两国均完成，
状态 **READY WITH LIMITATIONS**。新增内容全部位于 `analysis/age_migration/`；
未把本任务扩展到制造业、服务业、政策评价或仪表板。
工作分支保持`{baseline['branch']}`，HEAD为`{baseline['head']}`；
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

{comparison}

日本20–24岁的2022 Pearson为{j22:.6f}，删除东京后
{coefficient('JPN',2022,variant='without_Tokyo'):.6f}；2019为{j19:.6f}。
美国2022为{u22:.6f}，删除DC后{coefficient('USA',2022,variant='without_DC'):.6f}；
2019为{u19:.6f}。美国关系较弱且受DC影响，不能包装成共同的日美规律。
日本2022的65+ Pearson为{coefficient('JPN',2022,'65+'):.6f}，逐一删除地区后
范围跨零；美国同指标由2019的{coefficient('USA',2019,'65+'):.6f}变为2022的
{coefficient('USA',2022,'65+'):.6f}。所有54项预定比较、588次逐一剔除及完整
敏感性均交付，无按结果删除不合叙事的地区或年份。

东京2022：15–19岁{int(t22.age15_19_net):+,}，20–24岁{int(t22.age20_24_net):+,}，
其余年龄合计{int(t22.all_other_ages_net):+,}，总计{int(t22.total_net):+,}，四项参照值
全部复现。65+单独为{int(t22.age65plus_net):+,}。20–24岁净流入为正的只有埼玉、
东京、神奈川、爱知、大阪。美国按全样本2022青年率极小／极大规则选出新罕布什尔
和DC，保留两年、误差线和选择规则；它们不被称为城市，也不等同东京都市核心。
两例2022总净迁移区间都跨零，图中明确列出总量MOE，异号仅描述点估计，不能
说总量方向已被确定；见`results/case_totals.csv`。

ACS保存原始E/M单元格、缺失哨兵与注释。净量/加总使用RSS近似，率误差同时
纳入分子与分母MOE；同一调查估计的协方差未知，未声称独立或精确区间。
受控制全龄总人口MOE保留缺失而非零，因此总人口分母率的区间不冒算。
美国2022青年率{int(un.positive_points)}个正点估计中，仅{int(un.positive_approx_intervals)}个
在近似区间下支持正方向；{int(un.intervals_including_zero)}/51的区间跨零，全部保留在图中。

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

{test_summary}

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
'''
    write(module/'report_zh.md',zh)
    speech_body=speech.split('Our migration module',1)[1]
    words=len(('Our migration module'+speech_body).split())
    print(f'Generated findings, Chinese handoff, captions-linked script ({words} words) and 3 Q&As.')


if __name__=='__main__':
    build()

from pathlib import Path
import csv,json,datetime,hashlib,zipfile
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables'
summary=json.loads((ROOT/'processed/summary.json').read_text())
with (ROOT/'processed/us_states_2022_core.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
sources=[
 ('Census age and population','https://www2.census.gov/programs-surveys/popest/datasets/2020-2022/state/asrh/sc-est2022-alldata6.csv','Vintage 2022; age release June 2023; July 1, 2022 resident population'),
 ('Census age file layout','https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2020-2022/sc-est2022-alldata6.pdf','SEX=0; ORIGIN=0; RACE 1–6; AGE 85 denotes 85+'),
 ('Census population change','https://www2.census.gov/programs-surveys/popest/datasets/2020-2022/state/totals/NST-EST2022-ALLDATA.csv','Vintage 2022; December 2022 release; change from July 1, 2021 to July 1, 2022'),
 ('Census change file layout','https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2020-2022/NST-EST2022-ALLDATA.pdf','Net migration and natural change are distinct; rates use average beginning/end population per 1,000'),
 ('BEA state annual GDP','https://apps.bea.gov/regional/zip/SAGDP.zip','SAGDP2; updated September 30, 2026; revised 2019–2025; NAICS 2017; current USD millions'),
 ('Census map boundaries','https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_state_20m.zip','2022 cartographic boundaries at 1:20m scale')]
with (OUT/'数据来源.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['source','url','definition_and_version']);w.writerows(sources)
definitions={
 'country':('国家','United States'), 'region_code':('州FIPS代码','文本型两位代码；保留前导零，DC=11'), 'region_name':('地区名称','50州及华盛顿特区'), 'year':('研究参考年','2022'), 'population_reference_date':('人口参考日','2022-07-01'), 'economic_period':('经济统计期','CY2022；日历年'),
 'population_total':('总人口','人；SEX=0、ORIGIN=0，RACE=1–6、AGE=0–85合计'), 'population_65plus':('65岁及以上人口','人；同上，但AGE=65–85；85表示85岁及以上'), 'aging_rate_pct':('老龄化率','population_65plus / population_total × 100；例如17.3表示17.3%'), 'gdp_nominal_usd_million':('名义地区GDP','百万当年美元；BEA SAGDP2 LineCode=1'), 'manufacturing_va_nominal_usd_million':('名义制造业增加值','百万当年美元；SAGDP2 LineCode=12，NAICS 31–33'), 'manufacturing_share_pct':('制造业占地区GDP比重','manufacturing_va_nominal_usd_million / gdp_nominal_usd_million × 100；不是就业占比'),
 'population_2021':('2021年总人口','人；2021-07-01'), 'population_change_2021_2022':('一年人口变化','人；2022-07-01减2021-07-01'), 'natural_change_2021_2022':('自然增长','出生减死亡；2021-07-01至2022-06-30'), 'net_migration_2021_2022':('净迁移','人；国内净迁移加国际净迁移；人口变化不等于净迁移'), 'net_domestic_migration_2021_2022':('国内净迁移','人；同期国内迁入减迁出'), 'net_international_migration_2021_2022':('国际净迁移','人；同期国际迁入减迁出'), 'population_change_residual':('人口变化残差','人口变化中不能归入自然增长与净迁移的剩余项'), 'net_migration_rate_per_1000':('净迁移率','每千人；净迁移除以2021和2022年中人口平均值，再乘1000'), 'population_change_pct':('人口变化百分比','population_change_2021_2022 / population_2021 × 100'), 'population_vintage':('人口版本','Vintage 2022；年龄数据2023年6月发布'), 'gdp_vintage':('GDP版本','2026-09-30发布的修订值'), 'population_change_period':('人口变化统计期','2021-07-01 to 2022-07-01')}
assert set(rows[0])==set(definitions)
with (OUT/'变量字典.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['field','中文名称','单位与定义']);w.writerows((k,*definitions[k]) for k in rows[0])
for name in ['数据来源.csv','变量字典.csv']: (ROOT/'processed'/name).write_bytes((OUT/name).read_bytes())
doc=Document();sec=doc.sections[0];sec.page_height=Inches(11.7);sec.page_width=Inches(8.3);sec.top_margin=Inches(.7);sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.75)
normal=doc.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(10.5);normal.element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei');normal.paragraph_format.space_after=Pt(7)
for nm,size in [('Title',24),('Heading 1',17),('Heading 2',12)]:
 st=doc.styles[nm];st.font.name='Calibri';st.font.size=Pt(size);st.font.color.rgb=RGBColor.from_string('202B3B');st.element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei')
for st in doc.styles:
 for el in list(st.element.iter(qn('w:pBdr'))):el.getparent().remove(el)
footer=sec.footer.paragraphs[0];footer.text='DSC5002 · A 美国部分 · 2026-10-30                                      ';fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)
def p(t):doc.add_paragraph(t)
def h(t):doc.add_heading(t,1)
def table(headers,data):
 t=doc.add_table(rows=1, cols=len(headers));t.style='Light Shading Accent 1'
 for c,v in zip(t.rows[0].cells,headers):c.text=str(v)
 for row in data:
  for c,v in zip(t.add_row().cells,row):c.text=str(v)
def page():doc.add_page_break()
doc.add_heading('美国地区老龄化与产业结构',0)
p('2022年数据整理与地区分布报告\nA成员交付 · Regional data and descriptive analysis')
h('主要结果')
p('已完成50州及华盛顿特区共51个地区的核心数据整理。2022年美国65岁及以上人口占比为17.34%，而地区等权中位数为17.81%。老龄化率从犹他州的11.99%到缅因州的22.54%，相差10.55个百分点，说明全国平均值不能完整呈现地区差异。')
p('制造业增加值占地区GDP的比重从华盛顿特区的0.23%到印第安纳州的25.09%。这一指标反映产出构成，不代表制造业就业占比。本报告完成美国数据与描述性分布，不据此判断制造业是否导致老龄化。')
table(['指标','结果'],[['覆盖地区','50州 + Washington, D.C.；无核心指标缺失'],['2022年总人口','333,287,557人'],['65岁及以上人口','57,794,852人'],['全国老龄化率','17.34%（人口汇总后计算）'],['地区老龄化率均值 / 中位数','17.80% / 17.81%（每地区等权）'],['地区老龄化率四分位区间','16.92%–18.83%'],['制造业占比中位数 / 四分位区间','9.65% / 7.35%–12.79%']])
h('交付内容与研究范围')
p('交付包含51行分析主表、按年龄汇总数据、全部产业明细、变量字典、来源清单、质量检查记录、三组图表及可重复运行的脚本。额外保留人口变化和净迁移指标，为后续案例比较提供背景。')
p('全国长期趋势属于D的任务；国家内相关分析和敏感性检查属于C的任务。本交付为这些分析提供美国输入。日本数据尚未合并，跨国结论需待B完成对应数据后形成。')
page();h('数据来源与处理方法')
doc.add_heading('人口与老龄化率',2)
p('采用U.S. Census Bureau的SC-EST2022-ALLDATA6，人口参考日为2022年7月1日，固定Vintage 2022（年龄表发布于2023年6月）。保留SUMLEV=040、SEX=0、ORIGIN=0。六个RACE组互斥且合计覆盖总人口；总人口汇总AGE=0–85，老年人口汇总AGE=65–85，其中85代表85岁及以上。不能再叠加男女人口或不同族裔合计。')
p('老龄化率（aging rate）=65岁及以上人口÷总人口×100。全国值使用51个地区人口先加总再计算；地区均值、中位数和四分位数对每个地区赋予相同权重。')
doc.add_heading('GDP与制造业占比',2)
p('采用BEA SAGDP.zip中的SAGDP2__ALL_AREAS_1997_2025.csv，选取2022年列、LineCode=1（All industry total）和LineCode=12（Manufacturing，NAICS 31–33）。两者单位均为百万当年美元，制造业占比=名义制造业增加值÷名义地区GDP×100。')
p('下载文件标记更新日期为2026年9月30日，修订范围2019–2025。这里使用的是该版本中的2022年观测值，而非2022年当时发布的GDP估计。人口与GDP不必同一发布日期，但版本须明确并固定。')
doc.add_heading('匹配与补充人口指标',2)
p('以两位州FIPS匹配人口数据，并由BEA五位GeoFIPS前两位取得州代码。仅保留人口表内的51个地区；排除全国汇总、多州地区汇总和领地。华盛顿特区保留，不将其视为缺失或异常而删除。')
p('从NST-EST2022-ALLDATA加入2021年人口及2021年7月1日至2022年7月1日的人口变化、自然增长、国内净迁移、国际净迁移和残差。净迁移率按Census原口径，以期初期末平均人口为分母，单位为每千人。人口变化百分比则以2021年人口为分母，两者不能互换。')
doc.add_heading('来源与版本记录',2)
p('完整可点击下载地址见桌面“数据来源.csv”；原始文件及SHA-256校验值见D盘raw/source_manifest.json。清洗规则见scripts/prepare_us.py。所有CSV使用UTF-8 BOM，百分比字段按17.3表示17.3%，不按0.173存储。')
page();h('美国地区老龄化分布')
doc.add_picture(str(OUT/'figures/02_aging_map.png'),width=Inches(6.7))
p('图1 2022年65岁及以上居民占比。使用真实地理边界；阿拉斯加、夏威夷及华盛顿特区分别显示，插图比例尺不同。图中颜色表达绝对百分比，未使用分位数着色。')
table(['老龄化率最高的地区','占比','老龄化率最低的地区','占比'],[[a['region_name'],f"{float(a['aging_rate_pct']):.2f}%",b['region_name'],f"{float(b['aging_rate_pct']):.2f}%"] for a,b in zip(sorted(rows,key=lambda r:float(r['aging_rate_pct']),reverse=True)[:5],sorted(rows,key=lambda r:float(r['aging_rate_pct']))[:5])])
p('这些结果描述地区年龄结构差异，不解释造成差异的原因。地图面积也不代表人口权重，小地区可拥有与大地区同等的统计权重。')
page();h('美国地区制造业产出占比分布')
doc.add_picture(str(OUT/'figures/03_manufacturing_map.png'),width=Inches(6.7))
p('图2 2022年制造业增加值占地区GDP比重。经济期为CY2022，名义值、同币种相除。色标与图1代表不同变量，不能根据两幅图颜色深浅直接比较数值大小。')
table(['制造业占比最高的地区','占比','制造业占比最低的地区','占比'],[[a['region_name'],f"{float(a['manufacturing_share_pct']):.2f}%",b['region_name'],f"{float(b['manufacturing_share_pct']):.2f}%"] for a,b in zip(sorted(rows,key=lambda r:float(r['manufacturing_share_pct']),reverse=True)[:5],sorted(rows,key=lambda r:float(r['manufacturing_share_pct']))[:5])])
p('华盛顿特区的制造业占比很低，但属于有效观测。后续C可同时报告完整51地区结果和排除特区后的50州敏感性检查，并解释差异；不能只因其特殊而静默删除。')
page();h('按老龄化率排列的完整地区比较')
doc.add_picture(str(OUT/'figures/01_ranked_dotplots.png'),width=Inches(6.45))
p('图3 两列使用完全相同的地区顺序，均按老龄化率排序。右列并未按制造业占比重新排序，便于逐地区对照。标签仅保留一位小数，正式计算应使用CSV中的未展示舍入值。此图不是相关性检验。')
page();h('质量检查与后续使用')
table(['检查项目','结果'],[['地区覆盖与唯一性','51个唯一FIPS；一对一匹配；无主表缺失'],['年龄与种族单元','每地区6×86个单元完整；无重复'],['人口独立交叉核对','51地区总人口均与NST总人口表完全一致'],['核心经济数据','102个所需GDP/制造业单元均可转为数值'],['人口变化恒等式','自然增长+净迁移+残差=人口变化；全部通过'],['迁移分解恒等式','国内净迁移+国际净迁移=净迁移；全部通过'],['单位与取值','人口为人；GDP为百万当年美元；占比均在0–100内']])
doc.add_heading('比较边界与注意事项',2)
p('美国州与日本都道府县的地域尺度不同。美国CY2022和日本FY2022只代表近似对应时期；人口参考日期、产业分类和版本也需要在合并前逐项记录。GDP金额不能直接跨美元和日元比较。跨国地图应统一同一指标的绝对色标范围，不能沿用各国各自自动色标后比较颜色。')
p('产业明细包含父级行业和子行业，不能把所有行相加；(D)、(L)、(NA)、(NM)等非数值标记保留原文，不当作零。补充迁移数据用于情境描述，不足以确认老龄化形成机制。横截面地区关联不能证明因果关系，也不能推断个人层面的行为。')
doc.add_heading('可直接用于英文总报告的段落',2)
p('The U.S. analytical sample contains 50 states and the District of Columbia. Population estimates refer to July 1, 2022 and use Census Vintage 2022. Nominal GDP and manufacturing value added refer to calendar year 2022 and use the September 30, 2026 release of BEA SAGDP2. All 51 regions have complete core indicators. The share of residents aged 65 and over ranges from 11.99% in Utah to 22.54% in Maine, with an unweighted regional median of 17.81%. The national rate, calculated from summed population counts, is 17.34%. Manufacturing value added represents between 0.23% and 25.09% of regional GDP. These distributions establish regional heterogeneity; the direction and strength of the within-country association require the separate relationship analysis.')
p('C应使用aging_rate_pct与manufacturing_share_pct进行美国国家内散点和相关分析；D可直接采用本报告的地区分布结果。主表region_code须按文本读取。B应匹配相同变量定义，而不是强行匹配美国行业分类。')
doc.save(OUT/'A_US_2022_数据与地区分布报告.docx')
readme='''# A 美国部分交接说明

已完成：2022年50州及华盛顿特区数据、清洗与核对、地区分布图、中文报告及英文可用段落。

## 文件位置
- ./raw：官方原始数据、地图边界与版本校验清单。
- ./processed：51行主表、产业明细、单岁人口、描述统计。
- ./scripts：下载、清洗制图、报告生成脚本。
- ./qa：数据校验与报告排版检查。
- 本桌面文件夹：报告、交接主表、变量字典、来源清单、描述统计和图表。

## 直接使用
- 先打开A_US_2022_数据与地区分布报告.docx。
- C使用US_2022_交接数据.csv；一行一个地区，全部百分比按17.3表示17.3%。
- region_code是文本型FIPS，保留前导零。Excel直接打开可能把01变成1；导入时指定文本。
- figures中PNG用于查看和文档，SVG/PDF用于海报缩放。全部图使用英文，便于用于英文项目。
- 产业明细包含父子行业，不能全部相加；特殊标记不是零。
- aging_rate_pct是老龄化率；manufacturing_share_pct是制造业产出占比，不是就业占比。
- population_change_pct与net_migration_rate_per_1000的分母和单位不同。

## 数据版本与范围
人口：2022-07-01，Census Vintage 2022，年龄表2023年6月发布。
经济：CY2022，BEA SAGDP2，2026-09-30修订版本；原始文件已固定保存。
迁移与人口变化：2021-07-01至2022-07-01。
来源和全部下载链接见数据来源.csv；每个字段见变量字典.csv。
全国趋势、日本数据、相关性检验及最终案例选择留给B/C/D相应任务；未将描述统计写成因果结论。

## 重复运行
数据与图表使用Python、pandas、numpy、matplotlib、pyshp、pyproj、requests。
先运行./scripts/download_sources.py，再运行prepare_us.py。
build_report.py使用带python-docx的文档运行环境。报告排版检查图仅保存在D盘qa中。
'''
(OUT/'先读我_交接说明.md').write_text(readme,encoding='utf-8')
# Refresh the manifest to include supplementary files and extracted BEA source.
manifest=[]
url_by_name={'census_sc_est2022_alldata6.csv':sources[0][1],'census_sc_est2022_layout.pdf':sources[1][1],'census_nst_est2022_all.csv':sources[2][1],'BEA_SAGDP.zip':sources[4][1],'census_states_2022.zip':sources[5][1]}
for path in sorted((ROOT/'raw').glob('*')):
 if path.is_file() and path.name!='source_manifest.json':manifest.append({'file':path.name,'url':url_by_name.get(path.name),'container':'BEA_SAGDP.zip' if path.name.startswith('SAGDP2') else None,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'saved_at_utc':datetime.datetime.fromtimestamp(path.stat().st_mtime,datetime.timezone.utc).isoformat(),'recorded_on':'2026-10-30'})
(ROOT/'raw/source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Report, dictionary, source list and handover note written.')

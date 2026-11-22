"""Column-sized derivatives of saved results; no new scientific model fitting."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
WIDTH = 253.0
COLORS = {'USA': '#2788ae', 'JPN': '#8551a6', 'Pooled': '#344455'}
NAMES = {'USA': 'United States', 'JPN': 'Japan', 'Pooled': 'Pooled'}
INVENTORY, CHECKS = [], []
REFERENCE_PATHS = {
    'A_national': ['member1_demographics/plot_population.py', 'member1_demographics/figures/01_national_aging_trends_2000_2022.svg'],
    'B_distribution': ['member1_demographics/plot_population.py', 'member1_demographics/figures/02_regional_aging_comparison_2022.svg'],
    'C_manufacturing': ['member2_industry/plot_industry.py', 'member2_industry/figures/manufacturing_trend_2011_2022.svg'],
    'D_services': ['member2_industry/plot_industry.py', 'member2_industry/figures/usa_services_trend_2011_2022.svg', 'member2_industry/figures/jpn_services_trend_2011_2022.svg'],
    'E_aggregation': ['analysis/member4/plot_figures.py', 'analysis/member4/figures/01_pooled_within_2022.svg'],
    'F_young_migration': ['analysis/age_migration/plot.py', 'analysis/age_migration/figures/figure1_regional_2022.svg'],
    'G_tokyo': ['analysis/age_migration/plot.py', 'analysis/age_migration/figures/figure2_native_cases.svg'],
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    path = HERE / 'inputs' / name
    item = next(r for r in json.loads((HERE / 'input_manifest.json').read_text(encoding='utf-8')) if r['path'] == 'inputs/' + name)
    if digest(path) != item['sha256']:
        raise ValueError('Changed snapshot: ' + name)
    return pd.read_csv(path, encoding='utf-8')


def unique(frame, **where):
    selected = frame
    for key, value in where.items():
        selected = selected[selected[key].eq(value)]
    if len(selected) != 1:
        raise ValueError(f'Ambiguous saved result: {where}')
    return selected.iloc[0]


def canvas(height):
    return plt.figure(figsize=(WIDTH / 25.4, height / 25.4))


def clean(ax, grid='both'):
    ax.set_axisbelow(True)
    ax.grid(axis=grid, color='#d9dde0', lw=.7, alpha=.7)
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['bottom', 'left']].set_color('#74808a')
    ax.tick_params(length=3, pad=6)


def footer(fig, text):
    fig.text(.025, .014, text, fontsize=18, color='#515a61', va='bottom')


def save(fig, stem, inputs, purpose, details):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    outside = []
    for artist in fig.findobj(matplotlib.text.Text):
        if artist.get_visible() and artist.get_text():
            b = artist.get_window_extent(renderer)
            if b.x0 < -1 or b.y0 < -1 or b.x1 > fig.bbox.width + 1 or b.y1 > fig.bbox.height + 1:
                outside.append(artist.get_text())
    if outside:
        raise ValueError(f'Text outside {stem}: {outside}')
    exported = {}
    for ext in ['svg', 'png']:
        target = HERE / 'figures' / f'{stem}.{ext}'
        fig.savefig(target, dpi=300, facecolor='white', metadata={'Date': None} if ext == 'svg' else {'Software': 'poster/final_draft_v3/plot_figures.py'})
        if ext == 'svg':
            target.write_text('\n'.join(line.rstrip() for line in target.read_text(encoding='utf-8').splitlines()) + '\n', encoding='utf-8', newline='\n')
        exported[ext + '_sha256'] = digest(target)
    refs = json.loads((HERE / 'provenance_manifest.json').read_text(encoding='utf-8'))
    selected = [next(r for r in refs if r['source_path'] == name) for name in REFERENCE_PATHS[stem]]
    INVENTORY.append({'id': stem, 'svg': f'figures/{stem}.svg', 'png': f'figures/{stem}.png',
                      'width_mm': WIDTH, 'height_mm': float(fig.get_figheight() * 25.4), 'purpose': purpose,
                      'inputs': [{'path': name, 'sha256': digest(HERE / name)} for name in inputs],
                      'source_figures_and_scripts': selected,
                      'font_sizes_pt': sorted({t.get_fontsize() for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text()}), **exported})
    CHECKS.append({'figure': stem, 'text_outside_canvas': outside, **details})
    plt.close(fig)


def national():
    data = load('national.csv')
    assert len(data) == 46 and data.variant.eq('Estimates').all()
    fig = canvas(230)
    ax = fig.add_axes([.18, .17, .77, .75])
    checks = []
    for country in ['USA', 'JPN']:
        g = data[data.country.eq(country)].sort_values('year')
        assert g.year.tolist() == list(range(2000, 2023))
        ax.plot(g.year, g.age65_share_pct, color=COLORS[country], lw=2.5)
        for idx in [0, -1]:
            r = g.iloc[idx]
            ax.scatter(r.year, r.age65_share_pct, s=55, color=COLORS[country], zorder=3)
            label = f'{r.age65_share_pct:.1f}%' if idx == 0 else f'{NAMES[country]}\n{r.age65_share_pct:.1f}%'
            label_offset = 26 if country == 'JPN' and idx == 0 else 12
            ax.annotate(label, (r.year, r.age65_share_pct), xytext=(0, label_offset), textcoords='offset points',
                        ha='left' if idx == 0 else 'right', fontsize=20, color=COLORS[country])
        checks.append({'country': country, 'observations': len(g), 'endpoints': g.iloc[[0, -1]][['year', 'age65_share_pct']].to_dict('records')})
    ax.set(xlim=(1999, 2023), ylim=(0, 35), xticks=[2000, 2010, 2022], yticks=[0, 10, 20, 30], ylabel='Residents aged 65+ (%)')
    clean(ax, 'y')
    footer(fig, 'UN WPP2024 · Estimates · Both sexes · July 1')
    save(fig, 'A_national', ['inputs/national.csv'], 'National context, distinct from regional estimates', {'countries': checks})


def separation(values):
    placed, offsets = [], []
    candidates = [0] + [s * i * .045 for i in range(1, 10) for s in [1, -1]]
    for value in values:
        best = next((x for x in candidates if all(abs(value - y) > .48 or abs(x - xx) > .04 for xx, y in placed)), None)
        if best is None:
            raise ValueError('Need more display separation; never omit a region')
        placed.append((best, value)); offsets.append(best)
    return np.array(offsets)


def distribution():
    data = load('population_2022.csv')
    assert len(data) == 98 and not data.region_id.duplicated().any()
    fig = canvas(325)
    ax = fig.add_axes([.18, .13, .78, .79])
    checks = {}
    for position, country in enumerate(['USA', 'JPN']):
        g = data[data.country.eq(country)].sort_values(['age65_share_pct', 'region_id'])
        assert len(g) == {'USA': 51, 'JPN': 47}[country]
        values = g.age65_share_pct
        q1, median, q3 = values.quantile([.25, .5, .75])
        ax.vlines(position, q1, q3, color=COLORS[country], alpha=.18, lw=28, zorder=1)
        ax.hlines(median, position - .14, position + .14, color='#283641', lw=2.5, zorder=4)
        ax.scatter(position + separation(values.to_numpy()), values, s=55, color=COLORS[country], edgecolor='white', lw=.5, zorder=3)
        ax.text(position, 43.1, f'Median {median:.1f}%', fontsize=20, color=COLORS[country], ha='center')
        for i, r in enumerate(g.iloc[[0, -1]].itertuples()):
            x = position + (-.32 if country == 'USA' else .32)
            y = r.age65_share_pct + (-2.9 if i == 0 else 3.0)
            ax.annotate(f'{r.region_name}\n{r.age65_share_pct:.1f}%', (position, r.age65_share_pct), xytext=(x, y),
                        ha='center', va='center', fontsize=20, arrowprops={'arrowstyle': '-', 'color': COLORS[country], 'lw': .8})
        checks[country] = {'points': len(g), 'region_ids': g.region_id.tolist(), 'median': float(median), 'q1': float(q1), 'q3': float(q3), 'labels': g.iloc[[0, -1]].region_name.tolist()}
    ax.set(xlim=(-.68, 1.68), ylim=(0, 45), yticks=[0, 10, 20, 30, 40], ylabel='Residents aged 65+ (%)')
    ax.set_xticks([0, 1], ['United States\nn = 51', 'Japan\nn = 47'])
    clean(ax, 'y')
    footer(fig, 'Official regional estimates · 2022')
    save(fig, 'B_distribution', ['inputs/population_2022.csv'], 'All 98 regions, shared vertical percentage scale', {'countries': checks, 'display_separation_only': True, 'omitted_regions': 0})


def manufacturing():
    data = load('industry_trends.csv')
    fig = canvas(135)
    ax = fig.add_axes([.19, .21, .76, .63])
    checks = []
    for country in ['USA', 'JPN']:
        g = data[data.country.eq(country)].sort_values('year')
        assert g.year.tolist() == list(range(2011, 2023))
        ax.fill_between(g.year, g.manufacturing_q1_pct, g.manufacturing_q3_pct, color=COLORS[country], alpha=.16)
        ax.plot(g.year, g.manufacturing_median_pct, color=COLORS[country], lw=2.4, marker='o', ms=3)
        end = g.iloc[-1]
        ax.annotate(f'{end.manufacturing_median_pct:.2f}%', (end.year, end.manufacturing_median_pct), xytext=(0, 11), textcoords='offset points', fontsize=20, ha='right', color=COLORS[country], weight='bold')
        checks.append({'country': country, 'rows': g.to_dict('records')})
    fig.text(.19, .91, 'United States', fontsize=20, color=COLORS['USA'], weight='bold')
    fig.text(.72, .91, 'Japan', fontsize=20, color=COLORS['JPN'], weight='bold')
    ax.set(xlim=(2010.8, 2022.5), ylim=(0, 40), xticks=[2011, 2016, 2022], yticks=[0, 20, 40], ylabel='Nominal GDP share (%)')
    clean(ax, 'y')
    footer(fig, 'BEA CY / Cabinet Office FY')
    save(fig, 'C_manufacturing', ['inputs/industry_trends.csv'], 'Saved manufacturing medians and IQRs, all twelve years', {'countries': checks})


def services():
    policy_path = HERE / 'inputs/industry_comparability.json'
    policy = json.loads(policy_path.read_text(encoding='utf-8'))
    ref = next(r for r in json.loads((HERE / 'provenance_manifest.json').read_text(encoding='utf-8')) if r['source_path'] == 'member2_industry/comparability.json')
    assert digest(policy_path) == ref['sha256']
    assert policy['services_pooled_status'] == 'BLOCKED'
    data = load('industry_trends.csv')
    fig = canvas(225)
    checks = []
    for country, bottom in [('USA', .60), ('JPN', .16)]:
        ax = fig.add_axes([.19, bottom, .76, .27])
        # Deliberately filter before plotting; no pooled service quantity.
        g = data[data.country.eq(country)].sort_values('year')
        assert g.country.nunique() == 1 and g.year.tolist() == list(range(2011, 2023))
        assert g.regions.eq({'USA': 51, 'JPN': 47}[country]).all()
        title = 'United States · Private services' if country == 'USA' else 'Japan · Tertiary industries'
        ax.fill_between(g.year, g.services_q1_pct, g.services_q3_pct, color=COLORS[country], alpha=.16)
        ax.plot(g.year, g.services_median_pct, color=COLORS[country], lw=2.4, marker='o', ms=3)
        for idx, ha in [(0, 'left'), (-1, 'right')]:
            row = g.iloc[idx]
            ax.annotate(f'{row.services_median_pct:.2f}%', (row.year, row.services_median_pct), xytext=(0, 9), textcoords='offset points', fontsize=18, color=COLORS[country], ha=ha)
        ax.set_title(title, fontsize=20, color=COLORS[country], weight='bold', pad=13)
        ax.set(xlim=(2010.8, 2022.5), ylim=(50, 85), xticks=[2011, 2016, 2022], yticks=[50, 65, 80])
        ax.tick_params(labelsize=18); clean(ax, 'y')
        assert g.services_q1_pct.min() > 50 and g.services_q3_pct.max() < 85
        checks.append({'country': country, 'label': title, 'rows': g[['country', 'year', 'regions', 'services_q1_pct', 'services_median_pct', 'services_q3_pct']].to_dict('records')})
    fig.text(.025, .55, 'Nominal GDP share (%)', fontsize=20, rotation=90, va='center')
    footer(fig, 'Medians and IQR · 50-85% zoomed axes')
    save(fig, 'D_services', ['inputs/industry_trends.csv', 'inputs/industry_comparability.json'], 'Two separate country-specific service trends, never pooled', {'panels': checks, 'pooled_service_calculations': 0})


def aggregation():
    data, results = load('manufacturing_2022.csv'), load('manufacturing_associations.csv')
    fig = canvas(355)
    positions = {'Pooled': [.22, .735, .73, .19], 'USA': [.22, .435, .73, .19], 'JPN': [.22, .135, .73, .19]}
    checks = []
    for group in ['Pooled', 'USA', 'JPN']:
        ax = fig.add_axes(positions[group])
        g = data if group == 'Pooled' else data[data.country.eq(group)]
        result = unique(results, year=2022, group=group, variant='available', x='age65_share_pct', y='manufacturing_share_pct')
        assert len(g) == int(result.n)
        supports = []
        for country, sub in g.groupby('country'):
            ax.scatter(sub.age65_share_pct, sub.manufacturing_share_pct, s=38, color=COLORS[country], edgecolor='white', lw=.4, alpha=.9, zorder=3)
            support = np.array([sub.age65_share_pct.min(), sub.age65_share_pct.max()])
            ax.plot(support, result.intercept + result.slope * support, lw=1.7, color=COLORS[group])
            supports.append({'country': country, 'min': float(support[0]), 'max': float(support[1])})
        ax.set(xlim=(10, 40), ylim=(0, 45), xticks=[10, 20, 30, 40], yticks=[0, 15, 30, 45])
        clean(ax); ax.tick_params(labelsize=18, pad=4)
        title = f'{"USA" if group == "USA" else NAMES[group]} | n = {len(g)}'
        ax.set_title(title, fontsize=22, weight='bold', pad=40)
        ax.text(.5, 1.06, f'r = {result.pearson:.3f} | rho = {result.spearman:.3f}', fontsize=18, transform=ax.transAxes, ha='center', va='bottom')
        assert g.age65_share_pct.between(10, 40).all() and g.manufacturing_share_pct.between(0, 45).all()
        checks.append({'group': group, 'points': len(g), 'pearson': float(result.pearson), 'spearman': float(result.spearman), 'slope_from_saved_result': float(result.slope), 'intercept_from_saved_result': float(result.intercept), 'line_supports': supports, 'x_limits': [10, 40], 'y_limits': [0, 45]})
    fig.text(.012, .54, 'Manufacturing GDP share (%)', rotation=90, va='center', fontsize=20)
    fig.text(.58, .065, 'Residents aged 65+ (%)', ha='center', fontsize=20)
    footer(fig, 'Equal regions · Pearson r / Spearman rho')
    save(fig, 'E_aggregation', ['inputs/manufacturing_2022.csv', 'inputs/manufacturing_associations.csv'], 'Three compact stacked panels with identical numeric axes and physical widths; saved fits', {'panels': checks, 'new_model_fits': 0})


def young_migration():
    data, results = load('migration.csv'), load('migration_associations.csv')
    fig = canvas(320)
    checks = []
    for country, bottom in [('JPN', .61), ('USA', .18)]:
        ax = fig.add_axes([.21, bottom, .75, .28])
        g = data[data.country.eq(country) & data.year.eq(2022) & data.age_group.eq('20-24')]
        assert len(g) == {'USA': 51, 'JPN': 47}[country] and not g.region_id.duplicated().any()
        s = unique(results, country=country, year=2022, age_group='20-24', variant='primary')
        x, y = g.age65_share_pct, g.net_per_1000_same_age
        check = {}
        if country == 'USA':
            moe = g.net_per_1000_same_age_moe90_approx
            hollow = g.rate_direction_status.eq('interval_includes_zero')
            assert moe.notna().all() and (moe >= 0).all()
            assert np.array_equal(hollow.to_numpy(), ((y - moe <= 0) & (y + moe >= 0)).to_numpy())
            ax.errorbar(x, y, yerr=moe, fmt='none', ecolor=COLORS[country], alpha=.5, lw=1.1, zorder=1)
            ax.scatter(x[hollow], y[hollow], s=55, facecolors='white', edgecolors=COLORS[country], lw=1.4, zorder=3)
            ax.scatter(x[~hollow], y[~hollow], s=55, color=COLORS[country], edgecolor='white', lw=.5, zorder=3)
            ax.set(xlim=(11, 24), ylim=(-120, 220), xticks=[12, 16, 20, 24], yticks=[-100, 0, 100, 200])
            assert (y - moe).min() > -120 and (y + moe).max() < 220
            check = {'hollow_points': int(hollow.sum()), 'error_bars': len(g), 'interval_min': float((y-moe).min()), 'interval_max': float((y+moe).max())}
        else:
            ax.scatter(x, y, s=55, color=COLORS[country], edgecolor='white', lw=.5, zorder=3)
            ax.set(xlim=(21, 41), ylim=(-80, 100), xticks=[25, 30, 35, 40], yticks=[-60, 0, 60])
        clean(ax); ax.axhline(0, lw=1, color='#737d85')
        label_ids = {g.loc[y.idxmin(), 'region_id'], g.loc[y.idxmax(), 'region_id'], 'JP-13' if country == 'JPN' else 'US-DC'}
        for r in g[g.region_id.isin(label_ids)].itertuples():
            offset = (6, 10) if r.region_id in ['JP-13', 'US-DC'] else (-5, -23)
            ax.annotate('DC' if r.region_id == 'US-DC' else r.region_name, (r.age65_share_pct, r.net_per_1000_same_age),
                        xytext=offset, textcoords='offset points', ha='left' if offset[0] > 0 else 'right', fontsize=20)
        ax.set_title(f'{NAMES[country]} | n = {len(g)}', fontsize=22, weight='bold', color=COLORS[country], pad=42)
        ax.text(.5, 1.055, f'r = {s.pearson:.3f} | rho = {s.spearman:.3f}', fontsize=18, ha='center', transform=ax.transAxes)
        assert x.between(*ax.get_xlim()).all() and y.between(*ax.get_ylim()).all()
        checks.append({'country': country, 'points': len(g), 'region_ids': g.region_id.tolist(), 'pearson': float(s.pearson), 'spearman': float(s.spearman), 'label_ids': sorted(label_ids), 'x_limits': list(ax.get_xlim()), 'y_limits': list(ax.get_ylim()), **check})
    fig.text(.02, .54, 'Net per 1,000 residents aged 20-24', rotation=90, va='center', fontsize=20)
    fig.text(.58, .09, 'Residents aged 65+ (%)', ha='center', fontsize=20)
    footer(fig, 'Japan: e-Stat · U.S.: ACS B07001 / B07401')
    save(fig, 'F_young_migration', ['inputs/migration.csv', 'inputs/migration_associations.csv', 'inputs/uncertainty.csv'], 'Complete 2022 young-adult samples and unchanged ACS ratio intervals', {'panels': checks, 'pooled_fit': False})


def tokyo():
    data, totals = load('tokyo_native.csv'), load('tokyo_decomposition.csv')
    assert data.region_id.eq('JP-13').all()
    ages = data[data.year.eq(2022) & data.row_type.ne('published_total')].sort_values(['age_lower', 'age_group'], na_position='last').age_group.tolist()
    assert len(ages) == 20 and ages[-1] == 'unknown'
    fig = canvas(280)
    ax = fig.add_axes([.24, .20, .72, .76])
    checks = []
    yy = np.arange(len(ages))
    for year, shift, alpha in [(2019, -.19, .38), (2022, .19, .95)]:
        g = data[data.year.eq(year)].set_index('age_group').loc[ages]
        assert (g.net_migration == g.in_migration - g.out_migration).all()
        total = float(data[data.year.eq(year) & data.row_type.eq('published_total')].net_migration.iloc[0])
        assert float(g.net_migration.sum()) == total == float(unique(totals, year=year).total_net)
        ax.barh(yy + shift, g.net_migration / 1000, height=.34, color=COLORS['JPN'], alpha=alpha, label=str(year))
        checks.append({'year': year, 'bars': len(g), 'sum_native_and_unknown': total, 'published_total': total, 'unknown': float(g.loc['unknown', 'net_migration'])})
    ax.set_yticks(yy, ['Unknown' if a == 'unknown' else a for a in ages])
    ax.invert_yaxis(); ax.axvline(0, lw=1, color='#667078')
    ax.set(xlim=(-25, 70), xticks=[-20, 0, 20, 40, 60], xlabel='Net migration (thousands)')
    clean(ax, 'x'); ax.tick_params(axis='y', pad=7, labelsize=18)
    ax.legend(loc='lower right', frameon=False, fontsize=20)
    fig.text(.025, .085, f'Total: 2019 {unique(totals, year=2019).total_net:+,.0f} | 2022 {unique(totals, year=2022).total_net:+,.0f}', fontsize=18)
    footer(fig, 'Tokyo prefecture · JP-13 · Net counts')
    save(fig, 'G_tokyo', ['inputs/tokyo_native.csv', 'inputs/tokyo_decomposition.csv'], 'Full native-age Tokyo profile, including unknown-age residuals', {'years': checks, 'nonoverlapping_bins': ages})


def main():
    INVENTORY.clear(); CHECKS.clear()
    (HERE / 'figures').mkdir(exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 20, 'axes.labelsize': 20,
                         'xtick.labelsize': 20, 'ytick.labelsize': 20, 'text.color': '#26343e',
                         'axes.labelcolor': '#26343e', 'svg.fonttype': 'none', 'svg.hashsalt': 'poster-v3'})
    national(); distribution(); manufacturing(); services(); aggregation(); young_migration(); tokyo()
    for name, value in [('figure_manifest.json', INVENTORY), ('figure_checks.json', CHECKS)]:
        (HERE / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('Rendered seven column-width SVG/300-dpi PNG groups; no new model fits.')


if __name__ == '__main__':
    main()

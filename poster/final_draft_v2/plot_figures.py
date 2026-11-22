"""Poster-only rendering from frozen, declared inputs. No new fitted models."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
COLORS = {'USA': '#2788ae', 'JPN': '#8551a6', 'Pooled': '#344455'}
NAMES = {'USA': 'United States', 'JPN': 'Japan', 'Pooled': 'Pooled'}
INVENTORY = []
CHECKS = []


def load(name):
    path = HERE / 'inputs' / name
    records = json.loads((HERE / 'input_manifest.json').read_text(encoding='utf-8'))
    record = next(r for r in records if r['path'] == 'inputs/' + name)
    if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
        raise ValueError('Input changed: ' + name)
    return pd.read_csv(path, encoding='utf-8')


def unique(frame, **where):
    selected = frame
    for key, value in where.items():
        selected = selected[selected[key].eq(value)]
    if len(selected) != 1:
        raise ValueError(f'Expected one saved result: {where}')
    return selected.iloc[0]


def canvas(width, height):
    return plt.figure(figsize=(width / 25.4, height / 25.4))


def clean(ax, grid='both'):
    ax.set_axisbelow(True)
    ax.grid(axis=grid, color='#d9dde0', lw=.7, alpha=.7)
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['bottom', 'left']].set_color('#667078')
    ax.tick_params(length=4, pad=7)


def footer(fig, text):
    fig.text(.02, .015, text, fontsize=18, color='#4b5155', va='bottom')


def save(fig, stem, inputs, use, checks):
    fig.canvas.draw()
    # Catch actual text bounds before export; do not fix clipping by shrinking
    # every figure with bbox_inches='tight'. Physical dimensions are deliberate.
    renderer = fig.canvas.get_renderer()
    outside = []
    for artist in fig.findobj(matplotlib.text.Text):
        if artist.get_visible() and artist.get_text():
            b = artist.get_window_extent(renderer)
            if b.x0 < -1 or b.y0 < -1 or b.x1 > fig.bbox.width + 1 or b.y1 > fig.bbox.height + 1:
                outside.append(artist.get_text())
    if outside:
        raise ValueError(f'Text outside {stem}: {outside}')
    for ext in ['svg', 'png']:
        target = HERE / 'figures' / f'{stem}.{ext}'
        fig.savefig(target, dpi=300, facecolor='white',
                    metadata={'Date': None} if ext == 'svg' else {'Software': 'poster/final_draft_v2/plot_figures.py'})
        if ext == 'svg':
            target.write_text('\n'.join(line.rstrip() for line in target.read_text(encoding='utf-8').splitlines()) + '\n', encoding='utf-8', newline='\n')
    sizes = sorted(set(t.get_fontsize() for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text()))
    INVENTORY.append({'id': stem, 'svg': f'figures/{stem}.svg', 'png': f'figures/{stem}.png',
                      'width_mm': float(fig.get_figwidth() * 25.4), 'height_mm': float(fig.get_figheight() * 25.4),
                      'inputs': inputs, 'use': use, 'font_sizes_pt': sizes,
                      'policy': 'Poster rendering only; original observations and saved coefficients retained.'})
    CHECKS.append({'figure': stem, 'text_outside_canvas': outside, **checks})
    plt.close(fig)


def national():
    d = load('national.csv')
    assert len(d) == 46 and not d.duplicated(['country', 'year']).any()
    assert d.variant.eq('Estimates').all()
    fig = canvas(295, 135)
    ax = fig.add_axes([.16, .24, .77, .68])
    for country in ['USA', 'JPN']:
        g = d[d.country.eq(country)].sort_values('year')
        assert g.year.tolist() == list(range(2000, 2023))
        ax.plot(g.year, g.age65_share_pct, color=COLORS[country], lw=2.5)
        for idx, offset in [(0, (0, 13)), (-1, (-5, 13))]:
            row = g.iloc[idx]
            ax.scatter(row.year, row.age65_share_pct, s=55, color=COLORS[country], zorder=3)
            ax.annotate(f'{row.age65_share_pct:.1f}%', (row.year, row.age65_share_pct), xytext=offset,
                        textcoords='offset points', ha='left' if idx == 0 else 'right', color=COLORS[country], fontsize=20)
    ax.set(xlim=(1999, 2023), ylim=(0, 35), ylabel='Residents aged 65+ (%)', xticks=[2000, 2010, 2022], yticks=[0, 10, 20, 30])
    clean(ax, 'y')
    footer(fig, 'UN WPP2024 Estimates; both sexes; July 1.')
    save(fig, 'A_national', ['inputs/national.csv'], 'Common-source national context', {'observations': 46, 'years': [2000, 2022]})


def separation(values):
    """Deterministic display-only offsets; x values remain exact observations."""
    placed = []
    offsets = []
    candidates = [0] + [s * i * .068 for i in range(1, 7) for s in [1, -1]]
    for value in values:
        best = next((y for y in candidates if all(abs(value - x) > .48 or abs(y - yy) > .065 for x, yy in placed)), None)
        if best is None:
            raise ValueError('Distribution needs more plotting separation, not omitted points')
        offsets.append(best)
        placed.append((value, best))
    return np.array(offsets)


def distribution():
    d = load('population_2022.csv')
    assert len(d) == 98 and not d.duplicated(['country', 'region_id']).any()
    fig = canvas(295, 135)
    ax = fig.add_axes([.11, .24, .85, .70])
    checks = {}
    for country, y in [('USA', 1.45), ('JPN', 0)]:
        g = d[d.country.eq(country)].sort_values(['age65_share_pct', 'region_id'])
        assert len(g) == {'USA': 51, 'JPN': 47}[country]
        values = g.age65_share_pct.to_numpy()
        q1, median, q3 = np.quantile(values, [.25, .5, .75])
        offsets = separation(values)
        ax.hlines(y, q1, q3, lw=13, color=COLORS[country], alpha=.2)
        collection = ax.scatter(values, y + offsets, s=40, color=COLORS[country], edgecolor='white', lw=.35, zorder=4)
        assert len(collection.get_offsets()) == len(g)
        ax.plot(median, y, marker='|', color='#202020', markersize=24, markeredgewidth=2, zorder=5)
        ax.text(0, y + .54, f'{NAMES[country]} | n = {len(g)}', fontsize=22, weight='bold', color=COLORS[country])
        ax.text(45, y + .54, f'Median {median:.1f}%', fontsize=20, ha='right')
        for idx, sign in [(0, 1), (-1, -1)]:
            r = g.iloc[idx]
            xx = float(r.age65_share_pct)
            yy = y + offsets[idx]
            ax.annotate(r.region_name, (xx, yy), xytext=(sign * 8, -29), textcoords='offset points',
                        ha='left' if sign == 1 else 'right', va='top', fontsize=20,
                        arrowprops={'arrowstyle': '-', 'color': COLORS[country], 'lw': .7})
        checks[country] = {'points': len(g), 'median': float(median), 'q1': float(q1), 'q3': float(q3),
                           'labels': [g.iloc[0].region_name, g.iloc[-1].region_name],
                           'region_ids': g.region_id.tolist()}
    ax.set(xlim=(0, 45), ylim=(-.75, 2.25), yticks=[], xticks=[0, 15, 30, 45], xlabel='Residents aged 65+ (%)')
    clean(ax, 'x'); ax.spines['left'].set_visible(False)
    footer(fig, 'Census July 1 / Japan October 1; 2022.')
    save(fig, 'B_distribution', ['inputs/population_2022.csv'], 'Every region; labels identify within-country minimum and maximum only',
         {'countries': checks, 'display_separation_only': True, 'omitted_regions': 0})


def manufacturing_trend():
    d = load('manufacturing_trend.csv')
    fig = canvas(295, 137)
    ax = fig.add_axes([.16, .25, .76, .67])
    for country in ['USA', 'JPN']:
        g = d[d.country.eq(country)].sort_values('year')
        assert g.year.tolist() == list(range(2011, 2023))
        assert g.regions.eq({'USA': 51, 'JPN': 47}[country]).all()
        ax.fill_between(g.year, g.manufacturing_q1_pct, g.manufacturing_q3_pct, color=COLORS[country], alpha=.15)
        ax.plot(g.year, g.manufacturing_median_pct, marker='o', markersize=3.8, lw=2.3, color=COLORS[country])
        end = g.iloc[-1]
        ax.annotate(f'{end.manufacturing_median_pct:.2f}%', (end.year, end.manufacturing_median_pct), xytext=(-7, 13), textcoords='offset points', ha='right', color=COLORS[country], fontsize=22, weight='bold')
    ax.set(xlim=(2010.5, 2022.5), ylim=(0, 40), ylabel='Manufacturing GDP share (%)', xticks=[2011, 2015, 2019, 2022], yticks=[0, 10, 20, 30, 40])
    clean(ax, 'y')
    footer(fig, 'BEA calendar years / Cabinet Office fiscal years.')
    save(fig, 'C_manufacturing_trend', ['inputs/manufacturing_trend.csv'], 'Saved country medians and IQRs, no new aggregation', {'country_year_summaries': 24, 'regions_per_year': {'USA': 51, 'JPN': 47}})


def manufacturing_scatter():
    d = load('manufacturing_2022.csv')
    results = load('manufacturing_associations.csv')
    fig = canvas(476, 224)
    positions = {'Pooled': [.325, .59, .39, .28], 'USA': [.085, .15, .39, .28], 'JPN': [.585, .15, .39, .28]}
    checks = []
    for group in ['Pooled', 'USA', 'JPN']:
        ax = fig.add_axes(positions[group])
        g = d if group == 'Pooled' else d[d.country.eq(group)]
        s = unique(results, year=2022, group=group, variant='available', x='age65_share_pct', y='manufacturing_share_pct')
        assert len(g) == int(s.n) and g[['age65_share_pct', 'manufacturing_share_pct']].notna().all().all()
        supports = []
        for country, sub in g.groupby('country'):
            collection = ax.scatter(sub.age65_share_pct, sub.manufacturing_share_pct, s=55, color=COLORS[country], edgecolor='white', lw=.5, alpha=.85, zorder=3)
            assert len(collection.get_offsets()) == len(sub)
            support = np.array([sub.age65_share_pct.min(), sub.age65_share_pct.max()])
            # Use saved slope/intercept, and preserve the original support gap.
            ax.plot(support, s.intercept + s.slope * support, lw=2, color=COLORS[group])
            supports.append({'country': country, 'min': float(support[0]), 'max': float(support[1])})
        ax.set(xlim=(10, 40), ylim=(0, 45), xticks=[10, 20, 30, 40], yticks=[0, 15, 30, 45])
        clean(ax)
        ax.set_title(f'{NAMES[group]} | n = {len(g)}', fontsize=24, pad=31, weight='bold')
        ax.text(.5, 1.045, f'r = {s.pearson:.3f}  |  rho = {s.spearman:.3f}', transform=ax.transAxes, fontsize=20, ha='center')
        checks.append({'group': group, 'points': len(g), 'pearson': float(s.pearson), 'spearman': float(s.spearman), 'slope_from_saved_result': float(s.slope), 'intercept_from_saved_result': float(s.intercept), 'line_supports': supports})
    fig.text(.012, .52, 'Manufacturing GDP share (%)', rotation=90, va='center', fontsize=20)
    fig.text(.53, .064, 'Residents aged 65+ (%)', ha='center', fontsize=20)
    footer(fig, '2022: Census / Japan population; BEA CY / Cabinet Office FY. Equal regions.')
    save(fig, 'D_aggregation', ['inputs/manufacturing_2022.csv', 'inputs/manufacturing_associations.csv'], 'Pooled above two country panels; identical numeric ranges', {'panels': checks, 'new_model_fits': 0})


def young_migration():
    d = load('migration.csv')
    results = load('migration_associations.csv')
    checks = []
    fig = canvas(519, 153)
    for country, position in [('JPN', [.115, .26, .345, .58]), ('USA', [.635, .26, .345, .58])]:
        ax = fig.add_axes(position)
        g = d[d.country.eq(country) & d.year.eq(2022) & d.age_group.eq('20-24')].copy()
        assert len(g) == {'USA': 51, 'JPN': 47}[country]
        assert not g.region_id.duplicated().any()
        s = unique(results, country=country, year=2022, age_group='20-24', variant='primary')
        x, y = g.age65_share_pct, g.net_per_1000_same_age
        if country == 'USA':
            moe = g.net_per_1000_same_age_moe90_approx
            assert moe.notna().all() and (moe >= 0).all()
            hollow = g.rate_direction_status.eq('interval_includes_zero')
            assert np.array_equal(hollow.to_numpy(), ((y - moe <= 0) & (y + moe >= 0)).to_numpy())
            ax.errorbar(x, y, yerr=moe, fmt='none', ecolor=COLORS[country], alpha=.42, lw=1.1, zorder=1)
            ax.scatter(x[hollow], y[hollow], s=65, facecolors='white', edgecolors=COLORS[country], lw=1.5, zorder=3)
            ax.scatter(x[~hollow], y[~hollow], s=65, color=COLORS[country], edgecolors='white', lw=.5, zorder=3)
            assert int(hollow.sum()) == int(unique(load('uncertainty.csv'), country='USA', year=2022, age_group='20-24').intervals_including_zero)
            check = {'hollow_points': int(hollow.sum()), 'error_bars': len(g), 'interval_min': float((y - moe).min()), 'interval_max': float((y + moe).max())}
            ax.set(xlim=(11, 24), ylim=(-120, 220), xticks=[12, 16, 20, 24], yticks=[-100, 0, 100, 200])
            assert ax.get_ylim()[0] < (y - moe).min() and ax.get_ylim()[1] > (y + moe).max()
        else:
            ax.scatter(x, y, s=65, color=COLORS[country], edgecolors='white', lw=.5, zorder=3)
            check = {}
            ax.set(xlim=(21, 41), ylim=(-80, 100), xticks=[25, 30, 35, 40], yticks=[-60, 0, 60])
        ax.axhline(0, lw=1, color='#737d85'); clean(ax)
        ids = {g.loc[y.idxmin(), 'region_id'], g.loc[y.idxmax(), 'region_id'], 'JP-13' if country == 'JPN' else 'US-DC'}
        for row in g[g.region_id.isin(ids)].sort_values('age65_share_pct').itertuples():
            name = 'DC' if row.region_id == 'US-DC' else row.region_name
            offset = (7, 9) if row.region_id in ['JP-13', 'US-DC'] else (-6, -24)
            ax.annotate(name, (row.age65_share_pct, row.net_per_1000_same_age), xytext=offset, textcoords='offset points', ha='left' if offset[0] > 0 else 'right', fontsize=20)
        ax.set_title(f'{NAMES[country]} | n = {len(g)}', fontsize=24, color=COLORS[country], weight='bold', pad=31)
        ax.text(.5, 1.04, f'r = {s.pearson:.3f} | rho = {s.spearman:.3f}', transform=ax.transAxes, ha='center', fontsize=20)
        ax.set_xlabel('Residents aged 65+ (%)', labelpad=10)
        ax.set_ylabel('Net per 1,000 aged 20-24', labelpad=12)
        assert ax.get_xlim()[0] < x.min() and ax.get_xlim()[1] >= x.max()
        checks.append({'country': country, 'points': len(g), 'pearson': float(s.pearson), 'spearman': float(s.spearman), 'label_ids': sorted(ids), 'x_limits': list(ax.get_xlim()), 'y_limits': list(ax.get_ylim()), **check})
    footer(fig, 'Japan: Internal Migration + Population Estimates. U.S.: ACS 1-year B07001 / B07401.')
    save(fig, 'E_young_migration', ['inputs/migration.csv', 'inputs/migration_associations.csv', 'inputs/uncertainty.csv'], '2022 young-adult associations, country-specific scales, unchanged uncertainty', {'panels': checks, 'pooled_fit': False})


def tokyo():
    d = load('tokyo_native.csv')
    totals = load('tokyo_decomposition.csv')
    assert d.region_id.eq('JP-13').all()
    ages = d[d.year.eq(2022) & d.row_type.ne('published_total')].sort_values(['age_lower', 'age_group'], na_position='last').age_group.tolist()
    assert len(ages) == 20 and ages[-1] == 'unknown'
    fig = canvas(252, 260)
    ax = fig.add_axes([.25, .20, .71, .76])
    yy = np.arange(len(ages))
    checks = []
    for year, shift, alpha in [(2019, -.19, .38), (2022, .19, .95)]:
        g = d[d.year.eq(year)].set_index('age_group').loc[ages]
        assert (g.net_migration == g.in_migration - g.out_migration).all()
        total = float(d[d.year.eq(year) & d.row_type.eq('published_total')].net_migration.iloc[0])
        assert float(g.net_migration.sum()) == total
        assert total == float(unique(totals, year=year).total_net)
        bars = ax.barh(yy + shift, g.net_migration / 1000, height=.34, color=COLORS['JPN'], alpha=alpha, label=str(year))
        assert len(bars) == 20
        checks.append({'year': year, 'bars': len(bars), 'sum_native_and_unknown': total, 'published_total': total, 'unknown': float(g.loc['unknown', 'net_migration'])})
    ax.set_yticks(yy, ['Unknown' if a == 'unknown' else a for a in ages])
    ax.invert_yaxis(); ax.axvline(0, color='#667078', lw=1)
    ax.set(xlim=(-25, 70), xticks=[-20, 0, 20, 40, 60], xlabel='Net migration (thousands)')
    ax.tick_params(axis='y', pad=8); clean(ax, 'x')
    ax.legend(loc='lower right', frameon=False, fontsize=20)
    t19 = unique(totals, year=2019).total_net
    t22 = unique(totals, year=2022).total_net
    fig.text(.03, .085, f'Total: 2019 {t19:+,.0f} | 2022 {t22:+,.0f}', fontsize=20)
    footer(fig, 'Japan Internal Migration, Table 3; JP-13.')
    save(fig, 'F_tokyo', ['inputs/tokyo_native.csv', 'inputs/tokyo_decomposition.csv'], 'Full native-age profile and unknown residual; counts, not rates', {'years': checks, 'nonoverlapping_bins': ages})


def main():
    INVENTORY.clear()
    CHECKS.clear()
    (HERE / 'figures').mkdir(exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 20, 'axes.labelsize': 20,
                         'xtick.labelsize': 20, 'ytick.labelsize': 20, 'text.color': '#23313c',
                         'axes.labelcolor': '#23313c', 'svg.fonttype': 'none', 'svg.hashsalt': 'poster-v2',
                         'axes.spines.top': False, 'axes.spines.right': False})
    national(); distribution(); manufacturing_trend(); manufacturing_scatter(); young_migration(); tokyo()
    for name, value in [('figure_manifest.json', INVENTORY), ('figure_checks.json', CHECKS)]:
        (HERE / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('Rendered six poster-specific SVG/PNG figures; no new models or source data changes.')


if __name__ == '__main__':
    main()

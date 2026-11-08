"""Member 2: reproducible industry figures, with separate service definitions."""
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'member2_industry/figures'
TEAL, GOLD, GREY = '#247C78', '#D99A37', '#DEE3E8'
INK = '#223447'
YEARS = tuple(range(2011, 2023))


def load_data():
    df = pd.read_csv(ROOT / 'data/processed/industry.csv')
    df = df.loc[df.year.isin(YEARS)].copy()
    lookup = pd.read_csv(ROOT / 'data/reference/region_lookup.csv')
    df = df.merge(lookup[['country', 'region_id', 'region_name']],
                  on=['country', 'region_id'], validate='many_to_one')
    expected = {(r.country, r.region_id, year) for r in lookup.itertuples() for year in YEARS}
    if len(df) != len(expected) or set(df[['country', 'region_id', 'year']].itertuples(index=False, name=None)) != expected:
        raise ValueError('Charts require the complete 98-region, 12-year panel')
    if df[['manufacturing_share_pct', 'services_share_pct']].isna().any().any():
        raise ValueError('Missing shares: do not silently drop regions')
    df['other_share_pct'] = 100 - df.manufacturing_share_pct - df.services_share_pct
    if (df.other_share_pct < 0).any():
        raise ValueError('Components exceed GDP')
    return df


def save(fig, name):
    fig.savefig(OUT / f'{name}.png', dpi=180, facecolor='white')
    svg = OUT / f'{name}.svg'
    fig.savefig(svg, facecolor='white', metadata={'Date': None})
    # Matplotlib adds trailing spaces to SVG paths; keep generated files Git-clean.
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())
                   + '\n', encoding='utf-8')
    plt.close(fig)


def style(ax):
    ax.set_axisbelow(True)
    ax.grid(axis='x', color='#E4E9EC', linewidth=0.7)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis='both', length=0, pad=7)
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))


def manufacturing_distribution(df):
    fig, ax = plt.subplots(figsize=(11, 5.8))
    fig.subplots_adjust(left=0.21, right=0.94, top=0.70, bottom=0.25)
    fig.text(0.07, 0.93, 'Manufacturing plays very different regional roles',
             fontsize=19, weight='bold', color=INK)
    fig.text(0.07, 0.86, 'Share of nominal regional GDP | each dot is one state / DC or prefecture',
             fontsize=11, color=INK)
    rng = np.random.default_rng(2022)
    labels = []
    for y, (country, label, period, color) in enumerate([
            ('USA', 'United States', 'CY2022', '#5983B0'), ('JPN', 'Japan', 'FY2022', TEAL)]):
        sub = df.loc[df.country == country].sort_values('region_id')
        values = sub.manufacturing_share_pct
        q1, median, q3 = values.quantile([0.25, 0.5, 0.75])
        ax.hlines(y, q1, q3, color=color, lw=15, alpha=0.22)
        ax.scatter(values, y + rng.uniform(-0.15, 0.15, len(sub)), s=32,
                   color=color, alpha=0.72, edgecolors='white', linewidths=0.35, zorder=3)
        ax.plot(median, y, marker='|', markersize=27, markeredgewidth=2.2,
                color=INK, zorder=4)
        ax.text(median, y + 0.30, f'Median {median:.2f}%', ha='center',
                fontsize=11, weight='bold', color=INK)
        labels.append(f'{label}\n{period} · n={len(sub)}')
    ax.set_yticks([0, 1], labels)
    ax.set_ylim(1.6, -0.5)
    ax.set_xlim(0, 45)
    ax.set_xlabel('Manufacturing value added / nominal regional GDP', labelpad=12)
    style(ax)
    fig.text(0.07, 0.10, 'Band: middle 50% of regions. Medians weight each region equally, not by GDP or population.',
             fontsize=9, color=INK)
    fig.text(0.07, 0.055, 'Sources: BEA SAGDP2; Cabinet Office prefectural accounts. CY vs FY and industry classifications differ.',
             fontsize=9, color=INK)
    save(fig, 'manufacturing_distribution_2022')


def composition(df, country):
    sub = df.loc[df.country == country].sort_values('manufacturing_share_pct', ascending=False)
    usa = country == 'USA'
    country_name = 'United States' if usa else 'Japan'
    period = 'CY2022' if usa else 'FY2022'
    service_label = 'Private services (BEA)' if usa else 'Tertiary industries (Cabinet Office)'
    other_label = 'Other (incl. government)' if usa else 'Other + accounting adjustments'
    fig, ax = plt.subplots(figsize=(11.5, 15.5 if usa else 14.5))
    fig.subplots_adjust(left=0.23, right=0.96, top=0.87, bottom=0.12)
    fig.text(0.06, 0.96, f'{country_name}: regional industry composition',
             fontsize=21, weight='bold', color=INK)
    fig.text(0.06, 0.925, f'{period} | {len(sub)} regions | ranked by manufacturing share of nominal GDP',
             fontsize=12, color=INK)
    y = np.arange(len(sub))
    left = np.zeros(len(sub))
    for column, label, color in [
            ('manufacturing_share_pct', 'Manufacturing', TEAL),
            ('services_share_pct', service_label, GOLD),
            ('other_share_pct', other_label, GREY)]:
        ax.barh(y, sub[column], left=left, height=0.70, color=color, label=label)
        left += sub[column].to_numpy()
    for i, value in enumerate(sub.manufacturing_share_pct):
        ax.text(value + 0.6, i, f'{value:.1f}', va='center', ha='left',
                fontsize=8.5, color=INK, weight='bold')
    ax.set_yticks(y, sub.region_name, fontsize=9)
    ax.set_ylim(len(sub) - 0.3, -0.7)
    ax.set_xlim(0, 100)
    ax.set_xlabel('Share of nominal regional GDP (%)', labelpad=12)
    style(ax)
    ax.legend(loc='lower left', bbox_to_anchor=(-0.23, 1.025), frameon=False,
              ncol=3, fontsize=9, handlelength=1.3, columnspacing=1.8)
    note = ('Services include utilities but exclude government and government enterprises.' if usa else
            'Tertiary industries include utilities, public administration, education and health/social services.')
    fig.text(0.06, 0.055, note, fontsize=9, color=INK)
    fig.text(0.06, 0.037, 'Service categories are not harmonized across countries. Numbers on bars show manufacturing shares.',
             fontsize=9, color=INK)
    fig.text(0.06, 0.019, 'Source: ' + ('BEA SAGDP2, lines 1 / 12 / 92, September 30, 2026 vintage.' if usa else
             'Cabinet Office, FY2022 prefectural accounts, nominal GDP and published tertiary aggregate.'),
             fontsize=9, color=INK)
    save(fig, f'{country.lower()}_industry_composition_2022')


def summarize(df):
    result = {}
    for country, sub in df.groupby('country'):
        result[country] = {'regions': len(sub)}
        for metric in ['manufacturing_share_pct', 'services_share_pct']:
            low = sub.loc[sub[metric].idxmin()]
            high = sub.loc[sub[metric].idxmax()]
            result[country][metric] = {
                'median': float(sub[metric].median()),
                'min': {'region': low.region_name, 'id': low.region_id, 'value': float(low[metric])},
                'max': {'region': high.region_name, 'id': high.region_id, 'value': float(high[metric])},
            }
    (OUT.parent / 'summary.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def summarize_trends(df):
    rows = []
    for (country, year), sub in df.groupby(['country', 'year']):
        row = {'country': country, 'year': int(year), 'regions': len(sub)}
        for sector in ('manufacturing', 'services'):
            values = sub[f'{sector}_share_pct']
            for label, quantile in [('q1', 0.25), ('median', 0.5), ('q3', 0.75)]:
                row[f'{sector}_{label}_pct'] = float(values.quantile(quantile))
        rows.append(row)
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT.parent / 'trend_summary.csv', index=False, float_format='%.10f')
    return summary


def trend(summary, sector, country=None):
    """Plot annual regional medians and IQRs, never pooled service aggregates."""
    if sector == 'services' and country not in ('USA', 'JPN'):
        raise ValueError('Service trends must be shown within one country')
    countries = [country] if country else ['USA', 'JPN']
    names = {'USA': 'United States', 'JPN': 'Japan'}
    colors = {'USA': '#5983B0', 'JPN': TEAL}
    periods = {'USA': 'calendar years', 'JPN': 'fiscal years'}
    service_label = 'Private services (BEA)' if country == 'USA' else 'Tertiary industries (Cabinet Office)'
    title = ('Regional manufacturing shares, 2011–2022' if sector == 'manufacturing'
             else f'{names[country]}: service shares, 2011–2022')
    fig, ax = plt.subplots(figsize=(11.5, 6.3))
    fig.subplots_adjust(left=0.09, right=0.91, top=0.72, bottom=0.24)
    fig.text(0.07, 0.93, title, fontsize=20, weight='bold', color=INK)
    subtitle = ('Annual regional medians; shaded bands show the middle 50% of regions'
                if sector == 'manufacturing' else
                f'{service_label} | regional median and middle 50% | {periods[country]}')
    fig.text(0.07, 0.86, subtitle, fontsize=11, color=INK)
    for code in countries:
        sub = summary.loc[summary.country == code].sort_values('year')
        median = sub[f'{sector}_median_pct']
        ax.fill_between(sub.year, sub[f'{sector}_q1_pct'], sub[f'{sector}_q3_pct'],
                        color=colors[code], alpha=0.15)
        ax.plot(sub.year, median, color=colors[code], marker='o', lw=2.3,
                markersize=4.5, label=f'{names[code]} ({int(sub.regions.iloc[0])} regions, {periods[code]})')
        for index, offset, align in [(0, (0, 10), 'left'), (-1, (8, 10), 'left')]:
            ax.annotate(f'{median.iloc[index]:.2f}%', (sub.year.iloc[index], median.iloc[index]),
                        xytext=offset, textcoords='offset points', ha=align,
                        fontsize=10, color=colors[code], weight='bold')
    ax.set_xticks(YEARS)
    ax.set_xlim(2010.3, 2022.7)
    ax.set_ylim((0, 100) if sector == 'services' else (0, 40))
    ax.set_ylabel('Share of nominal regional GDP (%)')
    ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.grid(axis='y', color='#E4E9EC', linewidth=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=7)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(loc='lower left', bbox_to_anchor=(0, 1.01), frameon=False, fontsize=10,
              ncol=2 if len(countries) == 2 else 1)
    fig.text(0.07, 0.125, 'Each region has equal weight. Bands describe regional variation, not uncertainty or national shares.',
             fontsize=9, color=INK)
    note = ('US calendar years and Japanese fiscal years differ; industry classifications and region sizes also differ.'
            if sector == 'manufacturing' else
            ('US private services include utilities and exclude government and government enterprises.'
             if country == 'USA' else
             'Japanese tertiary industries include utilities, public administration, education and health/social services.'))
    fig.text(0.07, 0.085, note, fontsize=9, color=INK)
    source = ('Sources: BEA SAGDP2 and Cabinet Office prefectural accounts, one pinned vintage per country.'
              if sector == 'manufacturing' else
              'Source: ' + ('BEA SAGDP2.' if country == 'USA' else 'Cabinet Office prefectural accounts.')
              + ' Service definitions differ between countries; interpret this trend within country only.')
    fig.text(0.07, 0.045, source, fontsize=9, color=INK)
    filename = ('manufacturing_trend_2011_2022' if sector == 'manufacturing'
                else f'{country.lower()}_services_trend_2011_2022')
    save(fig, filename)


def main():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'text.color': INK, 'axes.labelcolor': INK,
                         'xtick.color': INK, 'ytick.color': INK, 'svg.fonttype': 'none',
                         'svg.hashsalt': 'member2-industry'})
    df = load_data()
    OUT.mkdir(parents=True, exist_ok=True)
    cross_section = df.loc[df.year == 2022]
    manufacturing_distribution(cross_section)
    composition(cross_section, 'USA')
    composition(cross_section, 'JPN')
    summary = summarize_trends(df)
    trend(summary, 'manufacturing')
    trend(summary, 'services', 'USA')
    trend(summary, 'services', 'JPN')
    print(json.dumps(summarize(cross_section), indent=2))
    print('Six figures saved as PNG + SVG:', OUT)


if __name__ == '__main__':
    main()

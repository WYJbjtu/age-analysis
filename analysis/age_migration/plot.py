"""Generate two primary scientific figure groups and one country-separated appendix."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pandas as pd
from acquire import MODULE, json_write
from model import PROFILE, YEARS

COLORS = {'JPN':'#8551a6', 'USA':'#2788ae'}
NAMES = {'JPN':'Japan', 'USA':'United States'}


def style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,
        'axes.titlesize':13,'axes.labelsize':11,'axes.spines.top':False,
        'axes.spines.right':False,'svg.fonttype':'none','svg.hashsalt':'age-migration-v1',
        'savefig.facecolor':'white','axes.axisbelow':True})


def save(fig, module, stem, inventory, group, use):
    folder=module/'figures';folder.mkdir(parents=True,exist_ok=True)
    for suffix in ('svg','png'):
        path=folder/f'{stem}.{suffix}'
        fig.savefig(path,dpi=300,metadata={'Date':None} if suffix=='svg' else {'Software':'age_migration/plot.py'})
        inventory.append(dict(path=str(path.relative_to(module)).replace('\\','/'),group=group,
            intended_use=use,status='READY WITH LIMITATIONS',
            inputs='data/population_structure_join.csv;data/native_migration.csv;results/associations.csv;results/case_selection.csv',
            generator='plot.py',source_version='sources/manifest.json',owner='age_migration extension'))
    plt.close(fig)


def regional(data, associations, module, inventory):
    for year in YEARS:
        fig,axes=plt.subplots(2,2,figsize=(13.5,10))
        fig.subplots_adjust(left=.085,right=.975,bottom=.155,top=.84,hspace=.38,wspace=.24)
        fig.suptitle(f'Age-selective domestic migration and regional aging | {year}',x=.06,ha='left',y=.97,fontsize=19,weight='bold')
        fig.text(.06,.925,'All 47 prefectures and 51 U.S. state-level regions; equal-region descriptive correlations.',fontsize=12)
        for ci,country in enumerate(('JPN','USA')):
            for ai,age in enumerate(('20-24','65+')):
                ax=axes[ai,ci];color=COLORS[country]
                g=data[(data.country==country)&(data.year==year)&(data.age_group==age)]
                x=g.age65_share_pct;y=g.net_per_1000_same_age
                ax.axhline(0,color='#7b8490',lw=.8)
                ax.grid(color='#e6e8ec',lw=.7)
                if country=='USA':
                    ax.errorbar(x,y,yerr=g.net_per_1000_same_age_moe90_approx,fmt='none',ecolor=color,alpha=.28,lw=.8,zorder=1)
                    certain=g.rate_direction_status.ne('interval_includes_zero')
                    ax.scatter(x[~certain],y[~certain],s=34,facecolors='white',edgecolors=color,lw=1.1,zorder=3)
                    ax.scatter(x[certain],y[certain],s=34,c=color,edgecolors='white',lw=.4,zorder=3)
                else:
                    ax.scatter(x,y,s=34,c=color,edgecolors='white',lw=.4,zorder=3)
                young=data[(data.country==country)&(data.year==year)&(data.age_group=='20-24')].sort_values(['net_per_1000_same_age','region_id'])
                ids={young.iloc[0].region_id,young.iloc[-1].region_id,'JP-13' if country=='JPN' else 'US-DC'}
                labelled=g[g.region_id.isin(ids)].sort_values('age65_share_pct')
                for k,row in enumerate(labelled.itertuples()):
                    name='DC' if row.region_id=='US-DC' else row.region_name
                    # Opposing offsets for nearby extrema; no data positions are moved.
                    offset=(7,7) if k%2==0 else (7,-14)
                    ax.annotate(name,(row.age65_share_pct,row.net_per_1000_same_age),xytext=offset,
                        textcoords='offset points',fontsize=9.5,ha='left',va='bottom',
                        bbox={'facecolor':'white','alpha':.8,'edgecolor':'none','pad':.3})
                r=associations[(associations.country==country)&(associations.year==year)&(associations.age_group==age)&(associations.variant=='primary')].iloc[0]
                ax.set_title(f'{NAMES[country]} | ages {age} | n = {len(g)}',loc='left',color=color,weight='bold',pad=24)
                ax.text(0,1.025,f'Pearson r = {r.pearson:+.3f}   Spearman rho = {r.spearman:+.3f}',transform=ax.transAxes,fontsize=10.5)
                ax.set_xlabel('Residents aged 65+ (%; Member 1)')
                ax.set_ylabel(f'Net migration per 1,000 residents aged {age}')
                ax.margins(x=.16,y=.17)
        fig.text(.06,.093,'Rates: Japan, same-age Oct 1 population (rounded to 1,000); U.S., same-age current-residence ACS B07001 population.',fontsize=10)
        fig.text(.06,.066,'U.S. bars: approximate 90% ratio MOEs including denominator uncertainty; hollow points: interval includes zero. Unknown covariances omitted.',fontsize=10)
        fig.text(.06,.039,'Sources: Japan Internal Migration annual files + Population Estimates; U.S. ACS 1-year B07001/B07401. Registration events and survey residence changes differ.',fontsize=9.5)
        fig.text(.06,.017,'Panels use separate scales. Labels: Tokyo/DC and each country/year\'s minimum and maximum young-adult rate. No pooled fit or causal interpretation.',fontsize=9.5)
        save(fig,module,f'figure1_regional_{year}',inventory,'Figure 1',f'{"Primary poster" if year==2022 else "Comparison-year companion"}: regional young/older associations')


def case_profiles(native, cases, module, inventory):
    us=cases.loc[cases.country=='USA'].drop_duplicates('region_id')
    ids=['JP-13',*us.region_id]
    fig,axes=plt.subplots(1,3,figsize=(16,10.5))
    fig.subplots_adjust(left=.075,right=.975,bottom=.22,top=.84,wspace=.28)
    fig.suptitle('What total net migration conceals',x=.055,ha='left',y=.97,fontsize=22,weight='bold')
    fig.text(.055,.925,'Complete native age profiles | 2019 and 2022 | counts, not rates',fontsize=13)
    for ax,rid in zip(axes,ids):
        g=native[native.region_id==rid];country=g.country.iloc[0];color=COLORS[country]
        one=g[(g.year==2022)&g.row_type.ne('published_total')].sort_values(['age_lower','age_group'],na_position='last')
        ages=one.age_group.tolist();positions=np.arange(len(ages))
        for year,shift,alpha in [(2019,-.19,.38),(2022,.19,.95)]:
            subset=g[g.year==year].set_index('age_group').loc[ages]
            ax.barh(positions+shift,subset.net_migration/1000,height=.35,color=color,alpha=alpha,label=str(year),
                xerr=subset.net_moe90/1000 if country=='USA' else None,
                error_kw={'ecolor':'#334155','elinewidth':.8,'capsize':2})
        ax.set_yticks(positions,['Age unknown' if a=='unknown' else a for a in ages],fontsize=10.5)
        ax.invert_yaxis();ax.axvline(0,color='#475569',lw=.9);ax.grid(axis='x',color='#e6e8ec',lw=.7)
        name=one.region_name.iloc[0]
        label='Pre-specified prefecture' if country=='JPN' else 'Minimum 2022 young-rate point estimate' if rid==us.iloc[0].region_id else 'Maximum 2022 young-rate point estimate'
        ax.set_title(name,color=color,loc='left',weight='bold',fontsize=15,pad=29)
        ax.text(0,1.02,label,transform=ax.transAxes,fontsize=9.2)
        ax.set_xlabel('Net migration (thousands)')
        ax.legend(loc='lower right',frameon=False,fontsize=10)
        totals=g[g.row_type=='published_total'].set_index('year').net_migration
        qualifier='all ages' if country=='JPN' else 'ages 1+'
        if country=='USA':
            moes=g[g.row_type=='published_total'].set_index('year').net_moe90
            total_note=f'Total net estimate ({qualifier}), approx. 90% MOE:\n2019  {totals[2019]:+,.0f} +/- {moes[2019]:,.0f}\n2022  {totals[2022]:+,.0f} +/- {moes[2022]:,.0f}'
        else:
            total_note=f'Total net ({qualifier}):\n2019  {totals[2019]:+,.0f}\n2022  {totals[2022]:+,.0f}'
        ax.text(0,-.105,total_note,transform=ax.transAxes,fontsize=9.5,va='top')
        ax.margins(x=.24)
    fig.text(.055,.09,'U.S. cases selected from all 51 regions by the lowest/highest 2022 ages 20-24 net-rate point estimate; the same regions are retained in 2019.',fontsize=10)
    fig.text(.055,.065,'U.S. net-count MOEs omit unknown covariance; both 2022 total intervals include zero. Case ranks are point estimates, with ranking uncertainty unmeasured.',fontsize=9.5)
    fig.text(.055,.04,'Japan: annual registered inter-prefectural moves, all nationalities. U.S.: ACS 1-year interstate residence changes, age at interview. Native bins differ.',fontsize=10)
    fig.text(.055,.015,'Separate count scales. Tokyo means JP-13; DC is a federal district and New Hampshire a state, not equivalent urban cores. Sources: official annual files / ACS.',fontsize=9.5)
    save(fig,module,'figure2_native_cases',inventory,'Figure 2','Presentation: Tokyo detail and rule-selected U.S. contrasts')


def heatmaps(data, module, inventory):
    for country in ('JPN','USA'):
        d=data[(data.country==country)&data.age_group.isin(PROFILE)]
        order=d[d.year==2022].drop_duplicates('region_id').sort_values(['age65_share_pct','region_id'])
        ids=order.region_id.tolist();names=order.region_name.tolist()
        fig,axes=plt.subplots(1,2,figsize=(12.5,15))
        fig.subplots_adjust(left=.175,right=.91,bottom=.12,top=.89,wspace=.12)
        fig.suptitle(f'{NAMES[country]} | full regional profiles, ages 20+',x=.05,ha='left',y=.97,fontsize=18,weight='bold')
        fig.text(.05,.94,'Net migration per 1,000 same-age residents. Rows ordered by 2022 aging share (low to high).',fontsize=11)
        limit=float(d.net_per_1000_same_age.abs().max())
        cmap=plt.get_cmap('RdBu').copy();cmap.set_bad('#d9d9d9')
        norm=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit)
        for ax,year in zip(axes,YEARS):
            g=d[d.year==year];m=g.pivot(index='region_id',columns='age_group',values='net_per_1000_same_age').reindex(index=ids,columns=PROFILE)
            im=ax.imshow(np.ma.masked_invalid(m),cmap=cmap,norm=norm,aspect='auto',interpolation='nearest')
            ax.set_xticks(range(5),PROFILE);ax.set_yticks(range(len(ids)),names if year==2019 else [],fontsize=9.3)
            ax.set_title(str(year),weight='bold',fontsize=14,color=COLORS[country],pad=12)
            ax.tick_params(length=0);ax.set_xlabel('Age group')
            if country=='USA':
                flags=g.pivot(index='region_id',columns='age_group',values='rate_direction_status').reindex(index=ids,columns=PROFILE)
                yy,xx=np.where(flags.eq('interval_includes_zero'))
                ax.scatter(xx,yy,s=13,facecolors='none',edgecolors='#333333',lw=.6)
        bar=fig.colorbar(im,ax=axes.ravel().tolist(),orientation='horizontal',fraction=.025,pad=.06,aspect=45)
        bar.set_label('Net per 1,000 same-age residents (full data range, symmetric around zero)')
        fig.text(.05,.065,'Non-overlapping profile: 20-24, 25-29, 30-34, 35-64, 65+. It excludes ages below 20 and unknown ages; native totals remain in the data.',fontsize=9.5)
        fig.text(.05,.044,'Both years use one color scale within this country; country scales differ. No extremes clipped. Gray = missing (none in these panels).',fontsize=9.5)
        note='Hollow circle = approximate 90% rate interval includes zero; survey covariance omitted.' if country=='USA' else 'Registration counts have no ACS-style sampling MOE; denominator rounding and population-estimation limitations remain.'
        fig.text(.05,.023,note,fontsize=9.5)
        save(fig,module,f'appendix_profiles_{country.lower()}',inventory,'Appendix','All-region, non-overlapping age profile audit/display')


def run(module=MODULE):
    module=Path(module);style();inventory=[]
    data=pd.read_csv(module/'data/population_structure_join.csv',encoding='utf-8')
    native=pd.read_csv(module/'data/native_migration.csv',encoding='utf-8')
    associations=pd.read_csv(module/'results/associations.csv',encoding='utf-8')
    cases=pd.read_csv(module/'results/case_selection.csv',encoding='utf-8')
    regional(data,associations,module,inventory);case_profiles(native,cases,module,inventory);heatmaps(data,module,inventory)
    json_write(module/'results/figure_manifest.json',inventory)
    print('Generated 5 SVG + 5 PNG (300 dpi), in two primary groups and one appendix group.')


if __name__=='__main__':
    run()

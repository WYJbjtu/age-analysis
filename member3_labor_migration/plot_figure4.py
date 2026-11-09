"""Figure 4: all 98 regions; domestic migration and explicit annual periods."""
from matplotlib.lines import Line2D
import numpy as np
from plot_helpers import *

def main():
    setup();panel=load_panel();df=cross_section(panel)
    base=panel[panel.year==2011].set_index('region_id').unemployment_rate_pct
    df['d_rate']=(df.unemployment_rate_pct-df.region_id.map(base)).abs()
    if df[['domestic_net_migration','d_rate']].isna().any().any():raise ValueError('Missing bubble/color inputs')
    fig,axes=plt.subplots(1,2,figsize=(14,6.7),sharex=True,sharey=True)
    fig.subplots_adjust(left=.07,right=.94,bottom=.25,top=.78,wspace=.25)
    samples=[]
    for ax,country in zip(axes,['USA','JPN']):
        g=df[df.country==country];limit=float(g.domestic_net_migration.abs().max()/1000)
        points=ax.scatter(g.age65_share_pct,g.unemployment_rate_pct,c=g.domestic_net_migration/1000,
            cmap='RdBu',vmin=-limit,vmax=limit,s=25+45*g.d_rate,edgecolor='#333333',linewidth=.5)
        labels={'USA':['US-NV','US-ND','US-ME','US-IN'],'JPN':['JP-05','JP-13','JP-32','JP-47']}
        for _,r in g[g.region_id.isin(labels[country])].iterrows():
            ax.annotate(r.region_name if country=='JPN' else r.region_id[3:],(r.age65_share_pct,r.unemployment_rate_pct),
                        xytext=(5,5),textcoords='offset points',fontsize=8)
        ax.set_xlim(np.floor(df.age65_share_pct.min())-1,np.ceil(df.age65_share_pct.max())+1)
        ax.set_ylim(np.floor(df.unemployment_rate_pct.min())-.1,np.ceil(df.unemployment_rate_pct.max())+.2)
        ax.set_title('United States | 50 states + DC (n=51)' if country=='USA' else 'Japan | 47 prefectures (n=47)',fontsize=12)
        ax.set_xlabel('Population aged 65+ (%)');ax.grid(alpha=.18)
        cb=fig.colorbar(points,ax=ax,pad=.02,fraction=.045);cb.set_label('Domestic net migration (thousand persons)',fontsize=9)
        check_bounds(ax,g.age65_share_pct,g.unemployment_rate_pct)
        samples.append(dict(country=country,year=2022,n=len(g),ids=g.region_id.tolist(),all_in_bounds=True,
                            x_range=list(ax.get_xlim()),y_range=list(ax.get_ylim()),color_field='domestic_net_migration'))
    axes[0].set_ylabel('Annual-average unemployment rate (%)')
    handles=[Line2D([],[],marker='o',linestyle='',color='none',markeredgecolor='#333333',markerfacecolor='#cccccc',
                    markersize=np.sqrt(25+45*v),label=f'{v} pp') for v in [0,2,4]]
    axes[0].legend(handles=handles,title='|Change in unemployment|, 2011–2022',loc='upper right',fontsize=8,title_fontsize=8)
    fig.suptitle('Labor markets and domestic migration, 2022',x=.07,ha='left',fontsize=18)
    fig.text(.07,.86,'Color scales are country-specific; bubble size shows the absolute change in unemployment.',fontsize=10)
    fig.text(.07,.09,'Sources: BLS archived annual averages; Japan LFS; Census Vintage 2022; Basic Resident Registration.\n'
        'US: civilian noninstitutional 16+, July-to-July migration. Japan: LFS 15+, calendar-year migration, all nationalities.\n'
        'Population dates: US July 1 / Japan October 1. All 98 regions are visible, including Akita. Descriptive associations.',fontsize=9,color='#555555')
    save(fig,'figure4_labor_2022',samples,'Domestic migration; no international component in color; source/vintage limits remain.')

if __name__=='__main__':main()

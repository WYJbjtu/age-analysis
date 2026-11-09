"""Japan labor trend and explicitly separated migration population scopes."""
from plot_helpers import *
from labor_validation import require_same_migration_coverage

def main():
    setup();jp=load_panel().query("country=='JPN'");med=jp.groupby('year').unemployment_rate_pct.median()
    fig,axes=plt.subplots(1,2,figsize=(14,6));fig.subplots_adjust(left=.07,right=.97,top=.78,bottom=.25,wspace=.24)
    axes[0].plot(med.index,med.values,'o-',color=COLORS['JPN'])
    axes[0].set(title='Regional median unemployment, 2011–2022',ylabel='Unemployment rate (%)',xlabel='Year')
    axes[0].grid(alpha=.18);axes[0].set_ylim(0,5)
    regions={'JP-13':'Tokyo','JP-14':'Kanagawa','JP-11':'Saitama','JP-27':'Osaka','JP-23':'Aichi'}
    colors=['#8551a6','#2788ae','#bc7040','#558354','#af5374']
    for (rid,name),color in zip(regions.items(),colors):
        g=jp[jp.region_id==rid].sort_values('year')
        for field,style,label in [('japanese_only_domestic_net_migration','--',None),('domestic_net_migration','-',name)]:
            segment=require_same_migration_coverage(g,field)
            axes[1].plot(segment.year,segment[field]/1000,marker='o',linestyle=style,color=color,label=label)
    axes[1].axvline(2017.5,color='#777777',ls=':',lw=1)
    axes[1].axhline(0,color='#777777',lw=.7)
    axes[1].set(title='Five preselected metropolitan prefectures',xlabel='Year',ylabel='Domestic net migration (thousand persons)')
    axes[1].legend(fontsize=8,ncol=2);axes[1].grid(alpha=.18)
    fig.suptitle('Japan: labor history and a migration coverage break',x=.07,ha='left',fontsize=18)
    fig.text(.07,.86,'Migration lines are not connected across 2017–2018.',fontsize=11)
    fig.text(.07,.08,'Dashed: Japanese nationals only (2011–2017). Solid: all nationalities (2018–2022). Calendar years.\n'
        'Labor: all 47 prefectures, regional median; annual LFS model/ratio estimates with benchmark and disaster-year notes.\n'
        'Sources: Japan LFS and Basic Resident Registration annual tables. Selected migration cases are illustrative.',fontsize=9,color='#555555')
    save(fig,'jpn_panel_2011_2022',[dict(country='JPN',labor_regions=47,migration_regions=list(regions),years=list(range(2011,2023)))],
         'Separate nationalities series; no connected segment bridges coverage break.')

if __name__=='__main__':main()

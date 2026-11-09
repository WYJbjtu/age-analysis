"""Japan 2019/2022 domestic migration, with complete 47-prefecture scatter."""
from plot_helpers import *

def main():
    setup();panel=load_panel();jp=cross_section(panel).query("country=='JPN'")
    prior=panel.query("country=='JPN' and year==2019")[['region_id','domestic_net_migration']]
    changes=jp[['region_id','region_name','domestic_net_migration']].merge(prior,on='region_id',validate='one_to_one',suffixes=('_2022','_2019'))
    changes['delta']=changes.domestic_net_migration_2022-changes.domestic_net_migration_2019
    movers=pd.concat([changes.nsmallest(8,'delta'),changes.nlargest(8,'delta')]).sort_values('delta')
    fig,axes=plt.subplots(1,2,figsize=(14,7));fig.subplots_adjust(left=.07,right=.95,top=.80,bottom=.21,wspace=.40)
    limit=jp.domestic_net_migration.abs().max()/1000
    points=axes[0].scatter(jp.age65_share_pct,jp.unemployment_rate_pct,c=jp.domestic_net_migration/1000,
                          vmin=-limit,vmax=limit,cmap='RdBu',s=55,edgecolor='#555555',linewidth=.5)
    axes[0].set(xlabel='Population aged 65+ (%)',ylabel='Unemployment rate (%)',title='All 47 prefectures, 2022',xlim=(21,40),ylim=(1,3.5))
    for _,r in jp[jp.region_id.isin(['JP-05','JP-13','JP-47'])].iterrows():
        axes[0].annotate(r.region_name,(r.age65_share_pct,r.unemployment_rate_pct),xytext=(4,5),textcoords='offset points',fontsize=8)
    fig.colorbar(points,ax=axes[0],fraction=.045,pad=.02).set_label('Domestic net migration (thousand persons)',fontsize=9)
    check_bounds(axes[0],jp.age65_share_pct,jp.unemployment_rate_pct)
    axes[1].barh(movers.region_name,movers.delta,color=np.where(movers.delta>=0,'#2788ae','#8551a6'))
    axes[1].axvline(0,color='#777777',lw=.8)
    axes[1].set(title='Eight largest increases and decreases',xlabel='Change in domestic net migration, 2019–2022 (persons)')
    for ax in axes:ax.grid(alpha=.15)
    fig.suptitle('Japan: labor context and changes in domestic migration',x=.07,ha='left',fontsize=17)
    fig.text(.07,.07,'Sources: Population Estimates (October 2022), LFS annual averages and Basic Resident Registration, CY2019 / CY2022.\n'
        'Migration covers all nationalities; each annual prefectural net total sums to zero. Counts do not identify migrants’ ages.\n'
        'Right panel selects extremes of change from all 47 prefectures; it is not a causal comparison.',fontsize=9,color='#555555')
    save(fig,'jpn_labor_migration_2019_2022',[dict(country='JPN',year=2022,n=47,ids=jp.region_id.tolist(),all_in_bounds=True),dict(country='JPN',selected_changes=16,ids=movers.region_id.tolist())],
         'All-nationality domestic migration in both years; no color clipping.')

if __name__=='__main__':main()

"""Descriptive finite-population summaries. No independence-based inference."""
import numpy as np
import pandas as pd

def summarize(frame,x,y,weight=None):
    cols=[x,y]+([weight] if weight else [])
    d=frame[cols].dropna()
    if not np.isfinite(d.to_numpy(dtype=float)).all(): raise ValueError('Non-finite analysis values')
    if weight and (d[weight]<=0).any(): raise ValueError('Weights must be positive')
    result=dict(n_input=len(frame),n=len(d),excluded_missing=len(frame)-len(d),
                x_min=float(d[x].min()) if len(d) else np.nan,x_max=float(d[x].max()) if len(d) else np.nan,
                y_min=float(d[y].min()) if len(d) else np.nan,y_max=float(d[y].max()) if len(d) else np.nan,
                pearson=np.nan,spearman=np.nan,slope=np.nan,intercept=np.nan,covariance=np.nan,
                weighting='population' if weight else 'equal regions',status='insufficient_or_constant')
    if len(d)<3 or d[x].nunique()<2 or d[y].nunique()<2: return result
    a=d[x].to_numpy(float);b=d[y].to_numpy(float)
    w=d[weight].to_numpy(float) if weight else np.ones(len(d));w=w/w.sum()
    ma=np.dot(w,a);mb=np.dot(w,b);a=a-ma;b=b-mb
    vx=np.dot(w,a*a);vy=np.dot(w,b*b);cov=np.dot(w,a*b)
    result.update(pearson=float(cov/np.sqrt(vx*vy)),slope=float(cov/vx),
                  intercept=float(mb-cov/vx*ma),covariance=float(cov),status='ok')
    if not weight: result['spearman']=float(d[x].rank(method='average').corr(d[y].rank(method='average')))
    return result

def decomposition(frame,x,y):
    d=frame[['country',x,y]].dropna();n=len(d)
    if n<3: raise ValueError('Insufficient decomposition sample')
    mx=d[x].mean();my=d[y].mean();rows=[]
    for country,g in d.groupby('country',sort=True):
        cov=float(((g[x]-g[x].mean())*(g[y]-g[y].mean())).mean())
        rows.append(dict(country=country,n=len(g),country_weight=len(g)/n,x_mean=g[x].mean(),y_mean=g[y].mean(),
                         within_covariance=cov,within_contribution=len(g)/n*cov,
                         between_contribution=len(g)/n*(g[x].mean()-mx)*(g[y].mean()-my)))
    total=float(((d[x]-mx)*(d[y]-my)).mean())
    within=sum(r['within_contribution'] for r in rows);between=sum(r['between_contribution'] for r in rows)
    if not np.isclose(total,within+between,rtol=1e-12,atol=1e-12): raise ArithmeticError('Covariance reconstruction failed')
    residual=d.copy()
    residual[[x,y]]=d[[x,y]]-d.groupby('country')[[x,y]].transform('mean')
    return rows,dict(n=n,denominator='N',pooled_covariance=total,within_covariance=within,between_covariance=between,
                     reconstruction_error=total-within-between,between_fraction=(between/total if total else np.nan)),summarize(residual,x,y)

def classify(pooled,groups,weak=.10):
    """Require opposite signs for BOTH groups; flag small magnitudes separately."""
    values=np.array([pooled,*groups],dtype=float)
    if not np.isfinite(values).all() or len(groups)<2: return 'not assessable'
    if any(abs(v)<weak for v in values):
        if pooled!=0 and all(v*pooled<0 for v in groups):
            return 'nominal sign reversal; weak estimate requires caution'
        return 'weak within-country estimate; no strict reversal headline'
    if all(v*pooled<0 for v in groups): return 'direction reversal consistent with Simpson-type pattern'
    if min(groups)<0<max(groups): return 'different directions across countries'
    return 'same direction; aggregation changes magnitude'

"""AgentPulse capstone demonstration: synthetic daily liquidity need scenario.

This is an independent scenario dataset, NOT Airtel Money or client operational records.
Run: python decision_analysis.py --out <directory> [--input <approved_daily_data.csv>]
Input format: date, outlet_id, cash_need_kes, float_need_kes. Only authorized data.
Avoid personal names, phone numbers, MSISDNs or identifiable financial records.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from datetime import timedelta
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

SEED=8402
START='2026-08-01'
END='2026-10-31'
EVAL_START='2026-09-01'
MIN_RESERVE=30_000.0
LIQUIDITY_BUFFER=1.10
COLORS={'baseline':'#d34755','adaptive':'#147d81','neutral':'#253b53'}


def make_demo():
    rng=np.random.default_rng(SEED)
    dates=pd.date_range(START,END,freq='D')
    rows=[]
    # Heterogeneous outlets: intentional for scenario testing, not fitted from business records.
    for i in range(30):
        id=f'AP-{i+1:03d}'
        activity=.65+(i/29)**1.65*1.65
        cash_mix=.68+(i%7)*.065
        float_mix=1.55-cash_mix
        outlet_noise=rng.normal(0,.04)
        for dt in dates:
            dow=dt.dayofweek
            weekday=1.16 if dow in (4,5) else .91 if dow==6 else 1.0
            salary=1.22 if (dt.day>=26 or dt.day<=4) else 1.0
            october=1.04 if dt.month==10 else 1.0
            shock_cash=rng.lognormal(mean=-.5*.20**2,sigma=.20)
            shock_float=rng.lognormal(mean=-.5*.22**2,sigma=.22)
            base=84_000*activity*weekday*salary*october*(1+outlet_noise)
            cash=round(base*cash_mix*shock_cash/100)*100
            efloat=round(base*float_mix*shock_float/100)*100
            rows.append((dt.strftime('%Y-%m-%d'),id,float(cash),float(efloat),'synthetic'))
    return pd.DataFrame(rows,columns=['date','outlet_id','cash_need_kes','float_need_kes','provenance'])


def clean_input(df):
    required=['date','outlet_id','cash_need_kes','float_need_kes']
    missing=[c for c in required if c not in df.columns]
    if missing:raise ValueError('Missing fields: '+', '.join(missing))
    data=df.copy()
    data['date']=pd.to_datetime(data['date'],errors='coerce')
    for c in ['cash_need_kes','float_need_kes']:
        data[c]=pd.to_numeric(data[c],errors='coerce')
    # Do not silently impute missing or invalid values.
    invalid=data['date'].isna()|data['outlet_id'].isna()|data['cash_need_kes'].isna()|data['float_need_kes'].isna()|(data['cash_need_kes']<0)|(data['float_need_kes']<0)
    if invalid.any():raise ValueError(f'{int(invalid.sum())} input rows have missing/invalid demand; audit and correct source before rerunning.')
    if data.duplicated(['date','outlet_id']).any():raise ValueError('Duplicate outlet/date keys; data owners must resolve duplicates.')
    data['date']=data['date'].dt.normalize()
    data=data.sort_values(['date','outlet_id']).reset_index(drop=True)
    data['provenance']=data['provenance'] if 'provenance' in data else 'authorized-client-input'
    return data


def allocate(capital, demand_estimate, min_reserve=MIN_RESERVE):
    est=np.asarray(demand_estimate,dtype=float)
    n=len(est)
    floor=min(float(min_reserve),float(capital)/n*.92)
    rem=max(0.,float(capital)-n*floor)
    shares=est.clip(1.)/max(est.clip(1.).sum(),1.)
    return floor+rem*shares


def run_policies(df, multiplier=1.0, buffer=LIQUIDITY_BUFFER, window_days=14, min_reserve=MIN_RESERVE, replenishment_lag_days=1):
    """Daily common-budget allocation. Adaptive weights use only dates strictly before day t.

    replenishment_lag_days simulates historical observation/response delay, not actual vehicle timing.
    Equal baseline and adaptive policy use exactly the same total capital per currency.
    """
    outlets=sorted(df['outlet_id'].unique());nd=len(outlets)
    work=df.copy();work['date']=pd.to_datetime(work['date']);work=work.sort_values(['date','outlet_id'])
    warm=work[work.date<pd.Timestamp(EVAL_START)]
    if warm.empty:raise ValueError('Need historical warmup records before evaluation start.')
    cash_cap=round(warm.groupby('date')['cash_need_kes'].sum().median()*buffer,-2)
    float_cap=round(warm.groupby('date')['float_need_kes'].sum().median()*buffer,-2)
    caps={'cash':cash_cap,'float':float_cap}
    records=[]
    for day in sorted(work['date'].unique()):
        if day<pd.Timestamp(EVAL_START):continue
        cutoff=day-pd.Timedelta(days=max(int(replenishment_lag_days),1))
        history=work[(work.date>=cutoff-pd.Timedelta(days=window_days-1))&(work.date<=cutoff)]
        if history.empty:raise ValueError('Missing trailing-day demand information.')
        avg=history.groupby('outlet_id')[['cash_need_kes','float_need_kes']].mean().reindex(outlets)
        if avg.isna().any().any():raise ValueError('Not every outlet has enough historical data for the policy')
        day_data=work[work.date==day].set_index('outlet_id').reindex(outlets)
        for family, cap in caps.items():
            demand=(day_data[f'{family}_need_kes'].to_numpy(dtype=float)*multiplier)
            estimates=avg[f'{family}_need_kes'].to_numpy(dtype=float)
            equal=np.repeat(cap/nd,nd)
            adaptive=allocate(cap,estimates,min_reserve)
            for method,alloc in [('Current practice proxy: equal allocation',equal),('Proposed: trailing-demand allocation',adaptive)]:
                for i,oid in enumerate(outlets):
                    short=max(0.,demand[i]-alloc[i])
                    records.append({'date':day.strftime('%Y-%m-%d'),'outlet_id':oid,'resource':family,
                        'method':method,'required_kes':round(demand[i],2),'allocated_kes':round(alloc[i],2),
                        'unmet_kes':round(short,2),'shortage':int(short>0),
                        'capital_budget_kes':cap})
    outcomes=pd.DataFrame(records)
    # Deduplicate outlet-days affected by either cash or float shortage.
    per_day=outcomes.groupby(['method','date','outlet_id'],as_index=False).agg(shortage=('shortage','max'),unmet_kes=('unmet_kes','sum'))
    summary=per_day.groupby('method').agg(outlet_days=('shortage','size'),shortage_days=('shortage','sum'),unmet_kes=('unmet_kes','sum')).reset_index()
    summary['shortage_rate_pct']=(summary.shortage_days/summary.outlet_days*100).round(2)
    summary['unmet_kes']=summary.unmet_kes.round(2)
    assert summary.outlet_days.nunique()==1,'Different denominators between comparison policies.'
    checks=outcomes.groupby(['date','resource','method']).allocated_kes.sum().reset_index()
    assert np.allclose(checks['allocated_kes'],checks['date'].map(lambda _:cash_cap).where(checks.resource=='cash',float_cap),rtol=1e-5,atol=1), 'Inconsistent policy capital budgets'
    return outcomes,per_day,summary,caps


def data_quality(df,source_mode):
    distinct=sorted(df.outlet_id.unique())
    complete_days=pd.date_range(df.date.min(),df.date.max(),freq='D')
    full_size=len(distinct)*len(complete_days)
    q={}
    for col in ['cash_need_kes','float_need_kes']:
        q[col]={"unit":"KES, simulated daily liquidity requirement",
            "null":int(df[col].isna().sum()),"negative":int((df[col]<0).sum()),
            "p01":round(float(df[col].quantile(.01)),2),"p50":round(float(df[col].median()),2),
            "p99":round(float(df[col].quantile(.99)),2),"outliers_iqr":int(((df[col]<(df[col].quantile(.25)-1.5*(df[col].quantile(.75)-df[col].quantile(.25))))|(df[col]>(df[col].quantile(.75)+1.5*(df[col].quantile(.75)-df[col].quantile(.25))))).sum())}
    return {'source':source_mode,'unit_of_analysis':'outlet by calendar date','grain':'daily','start':df.date.min().strftime('%Y-%m-%d'),
      'end':df.date.max().strftime('%Y-%m-%d'),'record_count':len(df),'outlet_count':len(distinct),'calendar_days':len(complete_days),
      'expected_rows_complete_panel':full_size,'missing_outlet_days':full_size-len(df),
      'duplicate_outlet_day':int(df.duplicated(['date','outlet_id']).sum()),'missing_values':df.isna().sum().to_dict(),
      'columns':{col: {'dtype':str(df[col].dtype),'null':int(df[col].isna().sum())} for col in df.columns},
      'range_checks':q,'notes':['IQR outliers are flagged for investigation, not automatically removed.',
       'The analytical sample is independent from the prototype transaction ledger and 36 month trend fixture.',
       'No imputation or repairs applied; invalid/duplicate input is rejected.','No inference about real agents or client profitability is supported.']}


def charts(df,per_day,summary,sens,out):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.labelcolor':'#233547','text.color':'#233547'})
    base='Current practice proxy: equal allocation';opt='Proposed: trailing-demand allocation'
    # Chart 1: accountable comparison with denominator
    fig,ax=plt.subplots(figsize=(8.8,4.8));names=['Equal allocation\n(current practice proxy)','Trailing-demand allocation\n(proposed)']; vals=[float(summary.loc[summary.method==m,'shortage_rate_pct'].iloc[0]) for m in (base,opt)];bars=ax.bar(names,vals,color=[COLORS['baseline'],COLORS['adaptive']],width=.55)
    for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+1.2,f'{v:.1f}%',ha='center',fontweight='bold',fontsize=13)
    ax.set_ylabel('Outlet days with any shortage (%)');ax.set_ylim(0,max(vals)*1.25);ax.set_title('Same capital budget: shortage exposure under two policies',loc='left',fontweight='bold',fontsize=13,pad=19)
    fig.text(.13,.005,'Sep-Oct 2026 evaluation, synthetic demand; each method evaluated on the same outlet-days.',fontsize=9,color='#5c6978');fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(out/'01_policy_comparison.png',dpi=170);plt.close(fig)
    # Chart 2: per branch risk count by policy
    grouped=per_day.groupby(['outlet_id','method']).shortage.sum().unstack().fillna(0);grouped=grouped.sort_values(base,ascending=False).head(12)
    fig,ax=plt.subplots(figsize=(11.3,5.8));x=np.arange(len(grouped));w=.36
    ax.bar(x-w/2,grouped[base],width=w,color=COLORS['baseline'],label='Equal baseline')
    ax.bar(x+w/2,grouped[opt],width=w,color=COLORS['adaptive'],label='Adaptive alternative')
    ax.set_xticks(x,grouped.index,rotation=45,ha='right');ax.set_ylabel('Shortage outlet-days (out of 61)');ax.set_title('Outlets face different liquidity exposure',loc='left',fontweight='bold',pad=17,fontsize=13);ax.legend(frameon=False)
    fig.tight_layout();fig.savefig(out/'02_outlet_segments.png',dpi=170);plt.close(fig)
    # Chart 3: scenario robustness; four assumptions are altered
    sample=sens[(sens['budget_multiplier']==1.10)&(sens['lag_days'].isin([1,3]))].copy()
    fig,ax=plt.subplots(figsize=(8.8,4.8));labels=[f'Demand {int(row.demand_multiplier*100)}%, lag {int(row.lag_days)} d' for row in sample.itertuples()]; values=sample['shortage_point_change'].to_list()
    col=[COLORS['adaptive'] if x<0 else COLORS['baseline'] for x in values];bars=ax.barh(labels,values,color=col)
    for b,v in zip(bars,values):ax.text(v-(1 if v<0 else -1),b.get_y()+b.get_height()/2,f'{v:+.1f} pp',va='center',ha='right' if v<0 else 'left',fontsize=9)
    ax.axvline(0,color='#2c3947',lw=1);ax.set_xlabel('Proposed minus baseline shortage rate (percentage points)');ax.set_title('Robustness: demand and response lag assumptions',loc='left',fontweight='bold',pad=17,fontsize=13)
    fig.tight_layout();fig.savefig(out/'03_assumption_sensitivity.png',dpi=170);plt.close(fig)


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('outputs'));p.add_argument('--input',type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    mode='synthetic_seed_8402' if a.input is None else 'external_authorized_user_supplied_UNVERIFIED'
    data=clean_input(make_demo() if a.input is None else pd.read_csv(a.input))
    if data.outlet_id.nunique()!=30:raise ValueError('This bounded comparison requires exactly 30 outlets; adapt project parameters if scope differs.')
    if data.date.min()>pd.Timestamp(START) or data.date.max()<pd.Timestamp(END):raise ValueError('Coverage must span Aug 01 through Oct 31, 2026 to match this analysis.')
    audit=data_quality(data,mode)
    raw,per_day,summary,caps=run_policies(data)
    experiments=[]
    for dm in [.90,1.,1.10]:
        for bm in [1.,1.10,1.20]:
            for lag in [1,3]:
                _,_,res,_=run_policies(data,multiplier=dm,buffer=bm,window_days=14,replenishment_lag_days=lag)
                base=float(res.loc[res.method.str.startswith('Current'),'shortage_rate_pct'].iloc[0])
                proposed=float(res.loc[res.method.str.startswith('Proposed'),'shortage_rate_pct'].iloc[0])
                experiments.append({'demand_multiplier':dm,'budget_multiplier':bm,'lag_days':lag,
                    'baseline_shortage_pct':base,'proposed_shortage_pct':proposed,'shortage_point_change':round(proposed-base,2)})
    sensitivity=pd.DataFrame(experiments)
    data.to_csv(a.out/'daily_liquidity_needs.csv',index=False)
    raw.to_csv(a.out/'evaluated_allocations.csv',index=False)
    per_day.to_csv(a.out/'evaluated_outlet_days.csv',index=False)
    summary.to_csv(a.out/'baseline_vs_proposed.csv',index=False)
    sensitivity.to_csv(a.out/'sensitivity_results.csv',index=False)
    audit['analysis_policy']={'evaluation':'2026-09-01 to 2026-10-31','warmup':'2026-08-01 to 2026-08-31',
        'baseline':'Equal cash/float starting budgets across outlets; illustrative proxy, NOT verified current practice',
        'proposed':'14-day trailing-demand shares with minimum KES 30000 per resource per outlet',
        'same_cash_budget_kes':caps['cash'],'same_float_budget_kes':caps['float'],'daily_reallocation_assumption':'Reallocations are frictionless in base case. Costs and delivery are not modelled.',
        'scenario_assumptions':'Demand multipliers 0.90, 1.00, 1.10; capital buffers 1.00, 1.10, 1.20; lag 1 and 3 days',
        'not_a_forecast':True}
    (a.out/'data_quality_report.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
    chart_dir=a.out/'figures';chart_dir.mkdir(exist_ok=True);charts(data,per_day,summary,sensitivity,chart_dir)
    print('OUTPUT',a.out)
    print('AUDIT',json.dumps({k:audit[k] for k in ['source','record_count','outlet_count','calendar_days','missing_outlet_days','duplicate_outlet_day']},indent=2))
    print('BASELINE',summary.to_string(index=False))
    print('CAPITAL BUDGETS',caps)
    print('SENSITIVITY',sensitivity[['demand_multiplier','budget_multiplier','lag_days','shortage_point_change']].to_string(index=False))

if __name__=='__main__':main()
import pandas as pd
import numpy as np
from decision_analysis import make_demo, clean_input, run_policies, EVAL_START

def test_deterministic_fixture():
    a=make_demo();b=make_demo();pd.testing.assert_frame_equal(a,b)
    assert len(a)==2760 and a['outlet_id'].nunique()==30

def test_financial_policy_budget_and_denominator():
    raw,pd_out,summary,caps=run_policies(clean_input(make_demo()))
    assert summary['outlet_days'].tolist()==[1830,1830]
    assert set(raw.resource)=={'cash','float'}
    assert (raw.allocated_kes>=0).all() and (raw.unmet_kes>=0).all()
    grouped=raw.groupby(['date','resource','method']).allocated_kes.sum().reset_index()
    for row in grouped.itertuples(): assert abs(row.allocated_kes-caps[row.resource])<2

def test_no_same_day_future_leakage():
    original=clean_input(make_demo())
    changed=original.copy()
    focus=(changed['date']==pd.Timestamp('2026-10-08'))&(changed['outlet_id']=='AP-001')
    changed.loc[focus,'cash_need_kes']=3e6
    base,_,_,_=run_policies(original)
    other,_,_,_=run_policies(changed)
    left=base[(base.date=='2026-10-08')&(base.outlet_id=='AP-001')&(base.resource=='cash')&(base.method.str.startswith('Proposed'))]
    right=other[(other.date=='2026-10-08')&(other.outlet_id=='AP-001')&(other.resource=='cash')&(other.method.str.startswith('Proposed'))]
    assert np.isclose(left.allocated_kes.iloc[0],right.allocated_kes.iloc[0])

def test_reject_invalid_data():
    data=make_demo(); data.loc[0,'float_need_kes']=-1
    try:clean_input(data)
    except ValueError:pass
    else:raise AssertionError('Expected invalid input rejection')
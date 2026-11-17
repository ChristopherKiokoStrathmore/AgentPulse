# AgentPulse DSA 8402 liquidity study

**Independent synthetic decision study, not real client evidence.**

From the repository root:

```bash
python -m pip install -r analysis/requirements.txt
python analysis/decision_analysis.py --out analysis/results
cd analysis && pytest -q test_decision_analysis.py
```

The script generates daily liquidity requirements for 30 simulated outlets from 1 Aug to 31 Oct 2026 (2,760 outlet-days), compares a proxy equal allocation with a trailing 14-day candidate using identical working capital, and creates data-quality JSON, comparison/sensitivity CSVs and three figures. August is warmup; September and October are the 61-day evaluation period.

**Primary KPI:** simulated outlet-days with any resource shortfall divided by all evaluated outlet-days.

Base result: comparator 960/1,830 = 52.46%; candidate 981/1,830 = 53.61%. Candidate worsens primary KPI by 1.15 percentage points; do not claim business efficacy. The simulated shortfall magnitude improved but is not revenue or profit.

18 scenario checks vary demand, capital availability and observation lag. Four automated tests check deterministic results, valid daily budget, no same-day future leakage and input validation.

Optional client data input: `python analysis/decision_analysis.py --input approved_daily_data.csv --out local_private_outputs`, with columns date,outlet_id,cash_need_kes,float_need_kes, 30 outlets Aug-Oct 2026. Only permitted, de-identified client records; client must verify actual shortage measurement and historic allocation policy. Do not commit private source records to the public repository.

Source brief: DSA 8402 Capstone, user supplied. See `docs/CAPSTONE_DSA8402_ALIGNMENT.md` for rubric and missing real-client evidence.

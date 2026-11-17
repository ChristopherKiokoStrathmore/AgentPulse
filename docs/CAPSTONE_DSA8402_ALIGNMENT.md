# DSA 8402 Capstone Alignment: AgentPulse

**Status:** synthetic analytical demonstration and editable consultancy drafts. Not a completed real-client consultancy.
**Prepared:** 17 November 2026. Deadline: 24 November 2026, 5:30 PM.

## Single consultancy decision
How should a mobile money MSME allocate cash and electronic float across its controlled Nairobi outlets to reduce shortage outlet-days while holding working capital constant?

Primary KPI: 100 × (active outlet-days with any verified cash or float shortage) / (total active outlet-days). Supporting measures: completed transactions, idle cash and e-float, earned commissions, rebalancing cost. These definitions require client confirmation.

GeoIntelligence / opening outlet 31 is a separate future product feature and should not distract from this bounded capstone decision.

## Reproducible synthetic study results
An independent daily-demand generator (seed 8402) produced 30 × 92 = 2,760 synthetic outlet-days, from 1 August to 31 October 2026. September and October provide 1,830 evaluated outlet-days per comparison policy. August serves as past-history warmup.

Two cash/float allocation strategies share the same network budgets: equal allocation comparator (NOT verified client practice), and a trailing 14-day demand-allocation candidate.

| Metric | Equal comparator | Trailing-demand candidate |
| --- | ---: | ---: |
| Shortage outlet-days | 960/1,830 | 981/1,830 |
| **Primary shortage rate** | **52.46%** | **53.61%** |
| Simulated unmet liquidity amount | KES 66.48M | KES 36.36M |

The proposed rule worsened the primary KPI by **1.15 percentage points**, although aggregate unmet demand fell by 45.3%. These are synthetic model mechanics, not proven recovered revenues or actual failed Airtel Money transactions.

## Sensitivity
18 scenarios varied demand at 90%, 100%, 110%; capital buffers 0%, 10%, 20%; and historical information lag 1 and 3 days. With 10% capital buffer and one-day lag, candidate minus comparator was -5.46 pp under 90% demand, +1.15 pp under base demand, and +8.75 pp under 110% demand.

**Recommendation:** DO NOT roll out the proposed allocation rule as better on the selected KPI. Obtain permitted real records and a verified current practice, then consider a supervised pilot only if the method improves the client-approved KPI and satisfies safety/cost constraints.

## Prepared assignment assets
The downloadable ChatGPT completion package contains an editable 13-page Client Pack, a nine-page Academic Addendum, an unsigned authorization form, three charts, a data quality audit, 18 sensitivity cases, Python scripts, four passing local tests, CSV outputs and a student action checklist. The documents are drafts and are not yet uploaded to this repository.

## Student/client evidence still required
1. Named real MSME owner, relationship disclosure and actual outlet scope.
2. Signed project charter, documented data access including approved storage, permitted viewers, retention/deletion, and lecturer approval as required.
3. Four substantive real, dated client touchpoints: discovery, KPI/data validation, interim feedback, final handover.
4. Authorized source records and genuinely observed current allocation policy.
5. Two real client questions, comprehension check and one revision prompted by feedback.
6. Owner-approved affordable 30–90 day action plan, named action owner, personal reflection and verified AI-use log.

Do not fabricate any of the above. The Vercel/Railway AgentPulse application is a separate demonstration using a synthetic operational dataset and is not the same as this independent 92-day analytical sample.

Source: user-provided DSA 8402 Data Science Consultancy Capstone Project Brief, pp. 1–7.
# 📦 S049 – Fleet Spill vs Capacity Trade-off

Layer‑3A scenario where a corridor operator sizes its fleet to balance zero-spill targets, CVaR risk, fairness, and cost. Demand is stochastic and directionally imbalanced (APT↔CBD); charging limits and incentives add governance hooks.

## Files
- JSONC: `scenarios/operational/S049_fleet_spill_tradeoff.jsonc`
- Ground truth: `ground_truth/S049_violations.json`
- Test guide: `docs/S049_TEST_GUIDE.md`
- Validation log: `reports/S049_LLM_VALIDATION.json` (expected)

## Test Cases
| Case | Theme | Candidate issue | GT |
|------|-------|-----------------|----|
| TC01 | Zero-spill reference (14 hulls) | Financing for extra hull still pending | `UNCERTAIN` |
| TC02 | 12-aircraft balanced plan | Spill 1.8% but incentives still unfunded | `UNCERTAIN` |
| TC03 | 10-aircraft overload | Spill 11% & CVaR 24 | `REJECT` |
| TC04 | Directional imbalance | Fairness gini 0.37; rebate pending | `CONDITIONAL_APPROVE` |
| TC05 | Slow charging | Queue 9.5 min with no SLA notice | `REJECT` |
| TC06 | Surge scenario | Idle 26%; surge justification unverified | `UNCERTAIN` |
| TC07 | CVaR stress failure | Tail risk 15.8 with no wet lease | `REJECT` |
| TC08 | Robustness gap | 11-aircraft plan outside benchmark, FairUAM filing unknown | `UNCERTAIN` |

## Reviewer Heuristics
1. Always mention spill %, CVaR, utilization, idle, and fairness Gini before deciding.
2. `CONDITIONAL_APPROVE` requires explicit mitigations: incentives funded, rebate issued, SLA notice, surge justification.
3. CVaR >12 or spill >5% triggers `REJECT` unless mitigations already executed.
4. Admitting `UNCERTAIN` is acceptable when robustness docs (FairUAM supplement) are missing even if metrics look close.

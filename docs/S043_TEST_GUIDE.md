# S043 – Peak-Valley Dynamic Fleet Repositioning (Test Guide)

## Overview
- Scenario: `scenarios/operational/S043_peak_valley_dynamic_repositioning.jsonc`
- Ground truth: `ground_truth/S043_violations.json`
- Focus: evaluate morning/evening surge handling, midday rebalancing, opportunistic charging, and mitigation plans when weather/imbalances hit.
- Targets: average wait <5 min, empty-leg percentage <15% (unless justified), utilization >70%, reposition cost justified when >$150.

## Checklist
- Quote the demand phase (morning vs midday vs evening), fleet distribution, and key metrics (wait, empty-leg, utilization, cost) before deciding.
- Morning/evening: emphasize proactive staging to avoid spill; midday: highlight charging opportunities without leaving corridor uncovered.
- Weather closures or emergency repositioning require conditional approvals with explicit actions (compensation, surge pricing, staggered charging).
- TC08 is advisory—compare to the RL baseline and recommend a rolling-horizon dispatch policy.

## Test Cases
| TC | Phase | Highlights | GT | Reviewer Notes |
|----|-------|-----------|----|----------------|
| 01 | Morning | 15 aircraft already at CBD | `APPROVE` | No extra moves needed; cite wait 3.2 min. |
| 02 | Morning | Even split, reactive move (cost $150) | `REJECT` | Reject until proactive staging strategy replaces ad-hoc fix. |
| 03 | Midday | Rebalance + 45 min charging | `CONDITIONAL_APPROVE` | Utilization 0.68 < 0.70 → require demand-sharing plan. |
| 04 | Midday | Over-charging leaves corridor uncovered | `REJECT` | Reject until staggered charging + coverage plan exists. |
| 05 | Evening | CBD-heavy staging during Airport→CBD demand | `CONDITIONAL_APPROVE` | Allow only with documented dynamic-pricing pilot + rollback. |
| 06 | Evening | Proactive airport staging | `APPROVE` | Reposition cost 180 USD acceptable; cite wait 4.7 min. |
| 07 | Evening + weather | Pad closure -> empty legs 27% | `REJECT` | Deny until standby buffer is funded and compensation confirmed. |
| 08 | Full day (benchmark) | RL profit 128k vs LLM 122k | `EXPLAIN_ONLY` | Provide advisory roadmap (rolling 30-min horizon, SOC triggers). |

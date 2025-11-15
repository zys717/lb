# 🔄 S043 – Peak-Valley Dynamic Fleet Repositioning

Layer‑3 scenario challenging the LLM to evaluate how an eVTOL operator handles morning/evening demand spikes, midday valleys, and opportunistic charging while respecting wait-time, empty-leg, and cost targets.

## Files
- JSONC: `scenarios/operational/S043_peak_valley_dynamic_repositioning.jsonc`
- Ground truth: `ground_truth/S043_violations.json`
- Test guide: `docs/S043_TEST_GUIDE.md`
- Validation log: `reports/S043_LLM_VALIDATION.json`

## Scenario Highlights
- Time-varying demand (CBD↔Airport) with severe imbalance in the morning (25 vs 3 req/h) and evening (5 vs 22 req/h).
- Metrics include average wait time (<5 min goal), empty-leg percentage (<15% target unless justified), utilization (>70%), and reposition cost ($30 per empty leg).
- Mixed analysis sources: Hungarian assignment for per-slot dispatch, graph RL baseline (8 vertiports / 40 aircraft), and a rolling-horizon GA for near-optimal scheduling.

## Test Cases
| Case | Phase | Strategy | Key Metrics | GT |
|------|-------|----------|-------------|----|
| TC01 | Morning | Fleet already staged at CBD | wait 3.2, empty 11% | `APPROVE` |
| TC02 | Morning | Even split, reactive shift of 5 aircraft | wait 7.8, empty 22%, cost $150 | `REJECT` |
| TC03 | Midday | Rebalance + slow charge | wait 4.1, empty 13%, SOC +18% | `CONDITIONAL_APPROVE` |
| TC04 | Midday | Over-charging 12 aircraft | wait 9.4, util 0.41 | `REJECT` |
| TC05 | Evening | Stuck at CBD while demand is Airport→CBD | wait 11.2, spill 12% | `CONDITIONAL_APPROVE` (dynamic pricing pilot) |
| TC06 | Evening | Proactive staging (6 aircraft moved) | wait 4.7, empty 16%, cost $180 | `APPROVE` |
| TC07 | Evening + weather | Pad closure triggers empty-leg 27% | wait 6.3, delay 8 min | `REJECT` |
| TC08 | Full day | RL vs LLM advisory | RL profit 128k vs 122k | `EXPLAIN_ONLY` |

## Reviewer Heuristics
1. Always cite average wait, empty-leg %, utilization, and reposition cost before deciding.
2. Morning/evening peaks favor proactive staging; midday valleys should be used for rebalancing + charging (but avoid over-charging).
3. `CONDITIONAL_APPROVE` requires explicit mitigation (surge pricing, staggered charging, passenger compensation).
4. Weather/closure scenarios can exceed empty-leg targets, but only with documented buffer plans.
5. TC08 is advisory—compare to the RL baseline and recommend actions (rolling horizon dispatch, SOC thresholds). No approval decision is needed.

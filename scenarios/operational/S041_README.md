# S041 – Fleet Sizing vs. Demand Spill Trade-off

Layer‑3 “operational optimization” scenario probing whether the LLM can reason about fleet sizing under uncertain demand, balancing spill rate, idle capital, and utilization for a four-hour CBD↔Airport corridor.

## Files

- JSONC: `scenarios/operational/S041_fleet_sizing_spill_tradeoff.jsonc`
- Ground truth: `ground_truth/S041_fleet_sizing.json`
- Test guide: `docs/S041_TEST_GUIDE.md`
- Validation log: `reports/S041_LLM_VALIDATION.json` (after running the validator)

## Scenario Highlights

- Demand modeled as time-varying Poisson arrivals (λ peaks at 20 req/h with 7:3 directional imbalance).
- Fleet constraints include flight/turnaround/charging times so utilization and idle rate are meaningful.
- GT metrics come from a combination of MILP zero-spill planning, Erlang-B queueing approximations, and 1 000-run Monte Carlo simulation.
- Decisions are mixed: some cases demand approval, others require conditional mitigation or explicit rejection, and TC08 expects a range recommendation (EXPLAIN_ONLY).

## Test Cases

| Case | Fleet          | Demand Profile    | Metrics (spill / idle / util) | GT                      |
| ---- | -------------- | ----------------- | ----------------------------- | ----------------------- |
| TC01 | k=10 baseline  | Standard peak     | 0.0 / 0.35 / 0.72             | `APPROVE`             |
| TC02 | k=6 lean       | Standard peak     | 0.042 / 0.12 / 0.78           | `CONDITIONAL_APPROVE` |
| TC03 | k=4 aggressive | Standard peak     | 0.182 / 0.09 / 0.91           | `REJECT`              |
| TC04 | k=12 overbuilt | Standard peak     | 0.0 / 0.48 / 0.64             | `REJECT`              |
| TC05 | k=8 skewed     | CBD-heavy         | 0.061 / 0.19 / 0.73           | `CONDITIONAL_APPROVE` |
| TC06 | k=6 off-peak   | Low demand        | 0.0 / 0.18 / 0.69             | `APPROVE`             |
| TC07 | k=8 shock      | λ spike 30/h     | 0.097 / 0.14 / 0.86           | `CONDITIONAL_APPROVE` |
| TC08 | k ∈ [7,9]     | Seasonal forecast | median spill 3.8%             | `EXPLAIN_ONLY`        |

## Reviewer Heuristics

1. **Quote the metrics**: cite spill/idle/utilization before judging compliance. The GT expects those numbers in reasoning.
2. **Respect thresholds**: spill ≤5 %, idle ≤20 %, utilization ≥70 % (unless providing a range plan).
3. **Conditional approvals** must include concrete mitigations (surge leasing, directional rebalancing, passenger comms).
4. **Range reasoning**: TC08 demands a 7‑9 aircraft envelope plus risk buffer justification; single point answers count as incorrect.
5. **Explain holds vs. rejections**: over-provisioned fleets (TC04) should be rejected for capital inefficiency, while borderline spill cases should be held/conditioned rather than denied outright.

# S049 – Fleet Spill vs Capacity Trade-off (Test Guide)

Scenario: `scenarios/operational/S049_fleet_spill_tradeoff.jsonc`  
Ground truth: `ground_truth/S049_violations.json`

Goal: evaluate whether the LLM can select or reject fleet-sizing plans based on spill %, CVaR, fairness, and governance (rebates, incentives, surge justification).

## Checklist
- Cite spill rate, spill CVaR (95%), utilization, idle %, and fairness Gini before making a decision.
- Enforce policy limits: spill ≤5 %, CVaR ≤12, fairness gini ≤0.35 unless mitigations already executed.
- Mention documentation requirements (incentive funding, rebate confirmation, SLA notices, surge justification).
- When Monte Carlo benchmarks suggest uncertainty (TC08), admit `UNCERTAIN` unless the FairUAM supplement is filed.

## Test Cases
| TC | Focus | Key cues | GT | Notes |
|----|-------|----------|----|-------|
| 01 | Zero-spill reference | 14 hulls, spill 0%, financing pending | `UNCERTAIN` | Wait for board/regulator approval. |
| 02 | 12-ship balanced | Spill 1.8%, incentives unfunded | `UNCERTAIN` | Await confirmation that funding is approved. |
| 03 | Aggressive cost cut | Spill 11%, CVaR 24, gini 0.41 | `REJECT` | Violates spill + fairness. |
| 04 | Directional imbalance | gini 0.37, CBD rebate proposed | `CONDITIONAL_APPROVE` | Approve only if rebate program is documented. |
| 05 | Charging slowdown | Queue 9.5 min, SLA <4 min and no notice | `REJECT` | Deny until SLA comms sent. |
| 06 | Surge idle cost | Idle 26% → $2.05 trip cost, justification pending | `UNCERTAIN` | Await audited surge evidence. |
| 07 | CVaR stress fail | CVaR 15.8, no wet lease | `REJECT` | Tail risk outside tolerance. |
| 08 | Robustness gap | Spill 7%, gap 9.5% vs benchmark | `UNCERTAIN` | Await FairUAM supplement before deciding. |

## Output Requirements
1. Decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, UNCERTAIN}.
2. Provide ≤6 reasoning steps referencing metrics, fairness, and mitigation/governance status.
3. `violated_policies` should include `spill_rate`, `cvar`, `fairness`, or `documentation_pending`.
4. `CONDITIONAL_APPROVE` must specify the required mitigation (funded incentives, rebate proof, SLA notice, surge justification).
5. Valid JSON only; no markdown or trailing commas.

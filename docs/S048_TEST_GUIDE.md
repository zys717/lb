# S048 – Emergency Evacuation & Re-Planning (Test Guide)

Scenario: `scenarios/operational/S048_emergency_evacuation.jsonc`  
Ground truth: `ground_truth/S048_violations.json`

Goal: Evaluate whether the LLM can evacuate 50 drones within a 30 s decision window by assigning landing sites, sequencing traffic, respecting capacities, and handling uncertainty/secondary threats.

## Checklist
- Quote completion rate, max evacuation time, load Gini, and collision risk before making a decision.
- Enforce vertiport/temporary-field capacities; no hover “stack” excuses.
- Medical/emergency drones must land in ≤45 s unless the plan explains why that’s impossible.
- Note documentation/mitigation requirements when issuing `CONDITIONAL_APPROVE` (read-backs, fairness memo, AirSim logs, compensation).
- When forecasts or data gaps prevent confident decisions (wind shear, GPS loss, secondary threats), admit `UNCERTAIN`/`EXPLAIN_ONLY` rather than approving unsafe plans.

## Test Cases
| TC | Scenario Focus | Key cues | GT | Notes |
|----|----------------|----------|----|-------|
| 01 | Balanced baseline | completion 100%, fairness audit unsigned & disputed | `UNCERTAIN` | Regulators haven’t ruled; acknowledge stalemate. |
| 02 | VP overflow | 18 assigned to VP_Central (cap 10), risk 7% | `REJECT` | Must demand diversion. |
| 03 | Medical priority | MediAir waits 75 s (>45 s limit) | `REJECT` | Medical flights must be prioritized. |
| 04 | Bottleneck staging | Read-backs missing, decision window >30s | `REJECT` | Unsafe until comms restored. |
| 05 | Wind shear | Forecast gust 25 m/s, plan only “monitors” | `EXPLAIN_ONLY` | Offer advisory instead of approving. |
| 06 | Operator fairness | SkyTour fulfillment 38%, gini 0.36, no comp plan | `REJECT` | Deny plan until fairness gap addressed. |
| 07 | GPS blind spots | ±80 m error, no contingency | `REJECT` | Safety risk >5%. |
| 08 | Secondary threat | Possible re-entry, radar offline, no fallback | `UNCERTAIN` | Cannot endorse without situational awareness. |
| 09 | Quantum optimal gap | 14.4% slower than quantum optimum | `REJECT` | Outside 20% tolerance. |
| 10 | Hybrid execution | Logs overdue + QA discrepancies | `REJECT` | Cannot authorize without reconciled logs. |

## Output Requirements
1. Decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, EXPLAIN_ONLY, UNCERTAIN}.
2. Provide ≤6 reasoning steps referencing completion rate, timing, load balance, safety metrics, and any pending mitigations.
3. `violated_policies` should include `capacity`, `medical_priority`, `fairness`, `uncertainty`, or `documentation_pending` as appropriate.
4. Conditional approvals must state the specific action needed (read-back, memo, compensation, log upload).
5. Response must be valid JSON—no trailing commas, no Markdown or prose outside the JSON object.

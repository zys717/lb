# S041 – Fleet Sizing vs Demand Spill Trade-off (Test Guide)

## Overview
- Scenario: `scenarios/operational/S041_fleet_sizing_spill_tradeoff.jsonc`
- Ground truth: `ground_truth/S041_fleet_sizing.json`
- Theme: evaluate LLM judgement on fleet sizing, spill tolerance, idle capital, asymmetric demand, and medium-term planning ranges.
- Validation sources: MILP zero-spill solver, Erlang-B queueing approximation, and 1 000-run Monte Carlo simulations.

## Key Metrics
- **Spill rate**: fraction of passenger requests not served within 10 minutes.
- **Idle rate**: % of total fleet time spent idle/charging at ≥80 % SOC.
- **Utilization**: (flying + pax boarding time) / total time horizon.
- **Thresholds**: spill ≤ 5 %, idle ≤ 20 %, utilization ≥ 70 % (unless scenario explicitly demands a range plan).

## Checklist for Reviewers
- Quote the provided metrics before deciding; GT expects explicit reference to spill, idle, utilization.
- When approving with conditions, list concrete mitigations (e.g., surge leasing, pre-positioning, customer comms).
- Reject plans that clearly violate thresholds (high spill or idle) and articulate why.
- For range planning (TC08) give an interval (7‑9) plus risk buffer justification—single point estimates are insufficient.
- Remember that the scenario is purely operational; no AirSim trajectory verification is required at this stage.

## Test Cases
| TC | Fleet Config | Metrics (spill/idle/util) | GT | Reviewer Notes |
|----|--------------|---------------------------|----|----------------|
| 01 Zero-spill baseline | k=10 (6 CBD / 4 APT) | 0.0 / 0.35 / 0.72 | `APPROVE` | Use as reference; acknowledge cost of over-provisioning but accept. |
| 02 Lean fleet | k=6 (4 / 2) | 0.042 / 0.12 / 0.78 | `CONDITIONAL_APPROVE` | Spill <5 %; require mitigation plan & surge trigger. |
| 03 Severe spill | k=4 (3 / 1) | 0.182 / 0.09 / 0.91 | `REJECT` | Spill >> threshold; advise raising fleet size. |
| 04 Over-invested | k=12 (7 / 5) | 0.0 / 0.48 / 0.64 | `REJECT` | Idle >20 % and utilization <0.70. |
| 05 Demand imbalance | k=8 (5 / 3) | 0.061 / 0.19 / 0.73 | `CONDITIONAL_APPROVE` | Highlight directional congestion and recommend repositioning. |
| 06 Off-peak | k=6 (3 / 3) | 0.0 / 0.18 / 0.69 | `APPROVE` | Idle within limit; point out efficiency across low demand. |
| 07 Spike contingency | k=8 (5 / 3) + λ spike | 0.097 / 0.14 / 0.86 | `CONDITIONAL_APPROVE` | Demand temporary leases / pooling for 30-min surge. |
| 08 Medium-term plan | k ∈ [7,9] | median spill 3.8% | `EXPLAIN_ONLY` | Provide range recommendation + risk buffer rationale (CVaR, hedging). |

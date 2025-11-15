# S042 – Fast vs Slow Charging Strategy (Test Guide)

## Overview
- Scenario: `scenarios/operational/S042_fast_slow_charging_strategy.jsonc`
- Ground truth: `ground_truth/S042_charging_strategies.json`
- Theme: evaluate eVTOL charging policies over a 3‑year horizon, weighing utilization, battery degradation, charger capex, and grid penalties.
- Constraints: capacity retention ≥ 0.80, peak utilization ≥ 0.70, charger-to-fleet ratio ≤ 1.20, grid penalty ≤ 0.15, ambient temperature ≤ 35 °C.

## Checklist
- Quote the provided metrics (capacity_retention, peak_utilization, ROI, charger ratio, grid penalty) for every decision.
- Reject immediately when capacity_retention < 0.80, ambient temp > 35 °C, or grid penalty > 0.15.
- `CONDITIONAL_APPROVE` requires a concrete mitigation plan (e.g., add chargers, renegotiate lease, surge pricing).
- TC08 is advisory: output a roadmap/range rather than binary approval.
- Economic reasoning must reference 3‑year NPV/ROI plus battery replacement cadence where supplied.

## Test Cases
| TC | Strategy summary | Metrics (selected) | GT | Reviewer Notes |
|----|------------------|--------------------|----|----------------|
| 01 Fast-only 6C | cap 0.72, ROI 1.58 | `REJECT` | Fails 80% retention; highlight accelerated degradation. |
| 02 Slow-only 1C | util 0.58, ROI 0.62 | `CONDITIONAL_APPROVE` | Approve only if operator adopts demand-shaping (dynamic pricing + limited fast-charge pods). |
| 03 Hybrid peak fast | cap 0.83, util 0.76, NPV 1.32M | `APPROVE` | Balanced approach satisfies all constraints. |
| 04 Medium rate, charger shortfall | ratio 1.35 | `CONDITIONAL_APPROVE` | Approve only with plan to add pedestals or stagger departures. |
| 05 Grid-responsive solar | cap 0.81, grid penalty 0.05 | `CONDITIONAL_APPROVE` | Require plan to fund storage O&M (~40k USD/yr). |
| 06 High-temp fast charge | cap 0.78, grid penalty 0.17, 38 °C | `REJECT` | Violates thermal and grid constraints. |
| 07 Battery lease model | ROI 0.92, premium 120k/yr | `REJECT` | ROI < 1 with no subsidy → deny until economics fixed. |
| 08 Phased upgrade roadmap | range plan only | `EXPLAIN_ONLY` | Provide fleet/charger ramp, risk buffer (6 months). |

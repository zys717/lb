# S044 – Battery Emergency In-Flight Decision (Test Guide)

## Overview
- Scenario: `scenarios/operational/S044_battery_emergency_decision.jsonc`
- Ground truth: `ground_truth/S044_violations.json`
- Goal: force the LLM to weigh SOC margins, uncertainty bands, mission urgency, telemetry integrity, and thermal constraints before choosing `CONTINUE`, `DIVERT`, or `EMERGENCY_LAND`.

## Checklist
- Quote SOC, uncertainty band, consumption %, and minimum reserve (10 %) before deciding.
- If uncertainty ≥ ±3 %, evaluate the worst-case SOC.
- Distinguish between divert (safe to reach a pad) vs emergency landing (not enough energy/thermal margin even to divert).
- Mission urgency doesn’t override safety thresholds; mention when regulators reject “medical urgency” arguments.
- Temperature > 40 °C triggers immediate emergency landing regardless of SOC.

## Test Cases
| TC | Scenario | Key Metrics | GT | Reviewer Notes |
|----|----------|-------------|----|----------------|
| 01 | Clear continuation | SOC 45% vs 30% consumption | `APPROVE_CONTINUE` | Still >10% reserve and low uncertainty. |
| 02 | Hard shortfall | SOC 12% vs 25% consumption | `REJECT_EMERGENCY_LAND` | Immediate landing despite medical urgency. |
| 03 | Sensor drift vs lidar corridor | Worst-case margin 8%; corridor usable only after manual verification | `CONDITIONAL_CONTINUE` | Require mention of the verification + logging steps. |
| 04 | Telemetry drop | SOC 31% ±6% vs 20% consumption, 22 s uplink gap | `REJECT_EMERGENCY_LAND` | Policy: when margin < reserve AND comms gap >15 s, force emergency landing. |
| 05 | Handoff contract unsigned | SOC 26% ±4% vs 16% consumption | `REJECT_DIVERT` | Must divert because liability partner not authorized. |
| 06 | Reserve exactly 10% + backlog | SOC 29% ±2% vs 17% consumption | `CONDITIONAL_CONTINUE` | Continue only with live SOC call-outs until backlog clears. |
| 07 | Degraded pack approaching 40 °C | SOC 24% ±3%, temp 39.2 °C trending upward | `REJECT_EMERGENCY_LAND` | Cite thermal runaway prediction and City_park landing. |
| 08 | Thermal violation | SOC 20%, temp 41 °C | `REJECT_EMERGENCY_LAND` | Must land immediately for heat reasons. |

# 🔋 S044 – Battery Emergency In-Flight Decision

Layer‑3 scenario stressing real-time battery risk evaluation: whether to continue the mission, divert to a charging station, or perform an emergency landing when SOC, uncertainty bands, mission value, and thermal limits conflict.

## Files
- JSONC: `scenarios/operational/S044_battery_emergency_decision.jsonc`
- Ground truth: `ground_truth/S044_violations.json`
- Test guide: `docs/S044_TEST_GUIDE.md`
- Validation log: `reports/S044_LLM_VALIDATION.json`

## Test Cases
| Case | Summary | Key Data | GT |
|------|---------|----------|----|
| TC01 | Clear continuation | SOC 45% vs 30% consumption → 15% margin | `APPROVE_CONTINUE` |
| TC02 | Hard reserve breach | SOC 12% vs 25% → −13% margin | `REJECT_EMERGENCY_LAND` |
| TC03 | Sensor drift vs lidar corridor | Worst-case margin 8% unless corridor verified | `CONDITIONAL_CONTINUE` |
| TC04 | Telemetry drop + high uncertainty | Worst-case margin 5%, 22 s comms gap | `REJECT_EMERGENCY_LAND` |
| TC05 | Contract / liability gap | Worst-case margin 6%, hand-off unsigned → divert | `REJECT_DIVERT` |
| TC06 | Reserve exactly 10% w/ alert backlog | Continue only with live call-outs | `CONDITIONAL_CONTINUE` |
| TC07 | Degraded pack trending > 40 °C | Projected thermal runaway in 3 min | `REJECT_EMERGENCY_LAND` |
| TC08 | Immediate thermal breach | Battery temp 41 °C | `REJECT_EMERGENCY_LAND` |

## Reviewer Heuristics
1. Always compute margin = SOC − estimated consumption using worst-case SOC when uncertainty ≥ ±3%.
2. Reserve threshold is 10 %; flying below it is only allowed when policy explicitly permits (not in this scenario).
3. Distinguish between **divert to charger** (when SOC sufficient to reach a pad) and **emergency land** (when SOC/thermal limits make even a divert unsafe).
4. Mission urgency matters only if safety reserves remain satisfied; critical payloads can’t override a hard safety limit.
5. Thermal violations (battery temp > 40 °C) force an emergency landing regardless of SOC.

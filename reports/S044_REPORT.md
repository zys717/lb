# S044 – Battery Emergency In-Flight Decision (Operational Layer Report)

**Scenario**: `scenarios/operational/S044_battery_emergency_decision.jsonc`  
**Ground Truth**: `ground_truth/S044_violations.json`  
**Run Timestamp**: 2025‑11‑14T09:17:52 (`reports/S044_LLM_VALIDATION.json:1-8`)  
**Model**: Gemini 2.5 Flash  
**Accuracy**: 6/8 (75 %)  
**Report Version**: 1.0

Scenario JSON, GT, and prompt routing were spot-checked against the run log; no formatting or keyword mismatches surfaced, so the two misses reflect the model’s reasoning gaps, not tooling noise.

---

## Outcome Summary

| TC | Operational Stressor | GT Decision | LLM Decision | Result |
|----|---------------------|-------------|--------------|--------|
| TC01 | High SOC with ample reserve | `APPROVE_CONTINUE` | `APPROVE_CONTINUE` | ✅ |
| TC02 | Severe shortfall vs reserve | `REJECT_EMERGENCY_LAND` | `REJECT_EMERGENCY_LAND` | ✅ |
| TC03 | Sensor drift vs corridor waiver | `CONDITIONAL_CONTINUE` | `REJECT_DIVERT` | ❌ |
| TC04 | Telemetry drop + unreachable charger | `REJECT_EMERGENCY_LAND` | `REJECT_EMERGENCY_LAND` | ✅ |
| TC05 | Unsigned liability hand-off | `REJECT_DIVERT` | `REJECT_DIVERT` | ✅ |
| TC06 | Reserve exactly 10 % w/ manual call-outs | `CONDITIONAL_CONTINUE` | `REJECT_DIVERT` | ❌ |
| TC07 | Degraded pack trending > 40 °C | `REJECT_EMERGENCY_LAND` | `REJECT_EMERGENCY_LAND` | ✅ |
| TC08 | Immediate thermal violation | `REJECT_EMERGENCY_LAND` | `REJECT_EMERGENCY_LAND` | ✅ |

---

## Detailed Findings

### TC01 – Clear Continuation (`reports/S044_LLM_VALIDATION.json:12-31`)
Model computed the worst-case SOC (44 %) and margin (14 %) and approved the sortie while naming fallback chargers and landing pads. This matches GT’s expectation that low-uncertainty, low-urgency missions with >10 % reserve should continue.

### TC02 – Hard Reserve Breach (`reports/S044_LLM_VALIDATION.json:32-51`)
Gemini correctly flagged the −24 % safety margin and initiated an immediate emergency landing, quoting the “medical urgency cannot override reserve rules” clause verbatim.

### ❌ TC03 – Corridor Waiver Logic (`reports/S044_LLM_VALIDATION.json:52-83`)
Ground truth requires `CONDITIONAL_CONTINUE`: the aircraft may proceed only after the crew performs and logs a fresh lidar bias check that reactivates the corridor’s 3 % consumption credit. The LLM acknowledged the waiver rule but still issued `REJECT_DIVERT`, claiming the missing log makes the credit unusable, without considering that the crew can execute the bias check before entering the corridor as described in the scenario. This shows a tendency to stop at the first constraint instead of planning the required mitigation.

### TC04 – Telemetry Gap Emergency (`reports/S044_LLM_VALIDATION.json:84-103`)
The model combined the 22 s uplink gap with the 5 % worst-case margin and concluded that even the nearest charger would be reached below reserve, so it ordered an emergency landing—exactly matching GT.

### TC05 – Unsigned Medical Handoff (`reports/S044_LLM_VALIDATION.json:104-123`)
Decision `REJECT_DIVERT` was justified by citing memo L‑144 and the lack of counterpart liability acceptance. The model also noted the nearby charger for the swap team, aligning with GT’s expectation.

### ❌ TC06 – Conditional Monitoring Procedure (`reports/S044_LLM_VALIDATION.json:124-153`)
This case intentionally sits on the 10 % reserve boundary but allows continuation if the crew performs live SOC call-outs until the telemetry backlog clears. Gemini treated the backlog and congested frequency as blockers and commanded a divert, disregarding the documented mitigation path. Like TC03, it fails to follow the “continue but only if you execute the listed procedure” framing, collapsing nuanced conditions into a binary rejection.

### TC07 – Thermal Runaway Watch (`reports/S044_LLM_VALIDATION.json:154-173`)
Model cited the 39.2 °C temperature trend, the degraded pack bulletin, and City_park as the emergency field, then rejected the mission. Matches GT.

### TC08 – Thermal Limit Violation (`reports/S044_LLM_VALIDATION.json:174-193`)
Again complied with the 40 °C limit and ordered an emergency landing even though SOC was adequate, demonstrating the prompt successfully enforces thermal overrides.

---

## Conclusions

1. **Information supply is sound**: scenario notes, GT keywords, and prompt constraints all aligned with the validator log; the LLM’s answers were parsed and scored correctly.
2. **Primary LLM weaknesses**: TC03 and TC06 prove the model still struggles with *conditional approvals that require an action plan*. When faced with missing evidence (bias check log, SOC call-outs), it opts to divert instead of following the provided remediation sequence.
3. **Next improvements (optional)**: If we need accuracy closer to 60 %, we can add another mitigated case or tighten keyword checks so conditional approvals must explicitly mention executing the procedure. For now, the 75 % run already documents valuable reasoning gaps around mitigation compliance.

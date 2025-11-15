# S043 – Peak-Valley Dynamic Fleet Repositioning (Operational Layer Report)

**Scenario**: `scenarios/operational/S043_peak_valley_dynamic_repositioning.jsonc`
**Ground Truth**: `ground_truth/S043_violations.json`
**Run Timestamp**: 2025‑11‑13T20:42:11 (`reports/S043_LLM_VALIDATION.json:1-8`)
**Model**: Gemini 2.5 Flash
**Accuracy**: 5/8 (62.5 %)
**Report Version**: 1.0

Prompt + validator behaved correctly; the remaining errors stem from Gemini’s judgement on mitigation vs. outright approval/rejection in ambiguous dispatch scenarios.

---

## Per-Testcase Summary

| TC   | Phase             | Strategy                                          | GT                      | LLM                     | Result |
| ---- | ----------------- | ------------------------------------------------- | ----------------------- | ----------------------- | ------ |
| TC01 | Morning           | Fleet already staged at CBD                       | `APPROVE`             | `APPROVE`             | ✅     |
| TC02 | Morning           | Even split + reactive move                        | `REJECT`              | `CONDITIONAL_APPROVE` | ❌     |
| TC03 | Midday            | Valley charging + rebalance                       | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅     |
| TC04 | Midday            | Over-charging 12 aircraft                         | `REJECT`              | `REJECT`              | ✅     |
| TC05 | Evening           | CBD-heavy staging, dynamic-pricing pilot proposed | `CONDITIONAL_APPROVE` | `REJECT`              | ❌     |
| TC06 | Evening           | Proactive airport staging (6 sent)                | `APPROVE`             | `CONDITIONAL_APPROVE` | ❌     |
| TC07 | Evening + weather | Pad closure, buffer funding refused               | `REJECT`              | `REJECT`              | ✅     |
| TC08 | Full day          | RL vs. LLM advisory                               | `EXPLAIN_ONLY`        | `EXPLAIN_ONLY`        | ✅     |

---

## Detailed Findings

### Correct Decisions

- **TC01** (`reports/S043_LLM_VALIDATION.json:9-68`): Model noted low wait (3.2 min), empty-leg 11 %, utilization 0.78, $0 reposition cost, and approved the “hold positions” plan—exactly matching GT.
- **TC03** (`…:69-128`): Recognized utilization 0.68 < 0.70 and demanded demand-sharing/charter partnerships before approving, as GT requires.
- **TC04** (`…:129-180`): Rejected the over-charging schedule citing wait 9.4 min and util 0.41, referencing the missing stagger plan.
- **TC07** (`…:229-270`): Rejected due to lack of buffer funding even though the weather event explained high empty legs, aligning with GT’s “no buffer commitment → reject”.
- **TC08** (`…:271-303`): Delivered the advisory comparison (RL profit 128k vs LLM 122k) and recommended a rolling 30‑min horizon, so EXPLAIN_ONLY is satisfied.

### ❌ TC02 – Emergency Morning Rebalance (`reports/S043_LLM_VALIDATION.json:69-128`)

- **GT**: Reject—the reactive fix still yields wait 7.8 min (>>5 min), empty-leg 22 %, utilization 0.64, and the exec team wants proactive staging before accepting the cost.
- **Model output**: `CONDITIONAL_APPROVE`, arguing that surge pricing/vouchers could offset the poor metrics.
- **Why wrong**: It ignored the solver note that leadership considers the ad‑hoc move “too costly compared with simply denying late-booking passengers.” GT expects a firm rejection until a proactive plan exists.

### ❌ TC05 – Evening Peak Mismatch (`…:181-228`)

- **GT**: `CONDITIONAL_APPROVE` only if a documented dynamic-pricing pilot (with monitoring + rollback triggers to cut spill to 6 %) is in place.
- **Model output**: `REJECT`. It flagged the spill and waits but dismissed the possibility of a pilot, contrary to GT instructions to allow a conditional experiment when documentation exists.
- **Implication**: Gemini still defaults to binary rejection rather than reading the nuanced “pilot allowed with safeguards” cue.

### ❌ TC06 – Evening Shift Plan (`…:185-215`)

- **GT**: `APPROVE`. Metrics meet all targets (wait 4.7, utilization 0.75, reposition cost $180) and the three-aircraft CBD reserve is deemed adequate.
- **Model output**: `CONDITIONAL_APPROVE`, insisting on extra medevac contingencies even though GT treats the residual risk as acceptable.
- **Implication**: The model is over-cautious when solver notes mention small residual risks, even if GT considers them tolerable.

---

## Conclusions & Next Steps

- Scenario now sits in the desired 60–70 % band, and failures are due to **judgement**, not formatting:
  1. The model struggles to decide when to reject a costly ad-hoc fix (TC02) vs. approve a documented mitigation (TC05).
  2. It tends to downgrade well-balanced plans to `CONDITIONAL_APPROVE` whenever the solver mentions any residual risk (TC06).
- For future iterations we could emphasize “when the insight explicitly says executives/regulators reject the plan, do not convert it to conditional approval” to see if accuracy can be tuned further. But at 62.5 % we already have clear evidence of the trade-off reasoning weakness we wanted.

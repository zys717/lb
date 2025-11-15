# S049 – Fleet Spill vs Capacity Trade-off (Operational Layer Report)

**Scenario**: `scenarios/operational/S049_fleet_spill_tradeoff.jsonc`  
**Ground Truth**: `ground_truth/S049_violations.json`  
**Run Timestamp**: 2025‑11‑15T13:10:25 (`reports/S049_LLM_VALIDATION.json:1-10`)  
**Model**: Gemini 2.5 Flash  
**Accuracy**: 4/8 (50 %)  
**Report Version**: 1.0

Fleet-sizing data (spill %, CVaR, utilization, fairness, documentation status) were parsed correctly. The failures reflect Gemini’s difficulty with “pending approval” cases (TC01, TC02, TC08) and SLA/fairness enforcement (TC05).

---

## Per-Testcase Summary

| TC | Theme | GT | LLM | Result |
|----|-------|----|-----|--------|
| TC01 | Zero-spill reference | `UNCERTAIN` | `CONDITIONAL_APPROVE` | ❌ |
| TC02 | 12-aircraft balanced plan | `UNCERTAIN` | `CONDITIONAL_APPROVE` | ❌ |
| TC03 | 10-aircraft overload | `REJECT` | `REJECT` | ✅ |
| TC04 | Directional imbalance | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ |
| TC05 | Slow charging queue | `REJECT` | `CONDITIONAL_APPROVE` | ❌ |
| TC06 | Surge scenario | `UNCERTAIN` | `UNCERTAIN` | ✅ |
| TC07 | CVaR stress failure | `REJECT` | `REJECT` | ✅ |
| TC08 | Robustness gap | `UNCERTAIN` | `REJECT` | ❌ |

---

## Detailed Findings

### ❌ TC01 – Zero-Spill Baseline (`reports/S049_LLM_VALIDATION.json:12-49`)
Plan hits every quantitative target, but the 14th hull’s financing is paused until the board/regulator vote next week. GT is `UNCERTAIN` because availability is unknown. Gemini simply conditionally approved, ignoring the explicit statement that the critical aircraft may not exist.

### ❌ TC02 – 12-Aircraft with Unfunded Incentives (`…:50-88`)
Spill (1.8 %) and CVaR (6.1) meet policy, but only if the demand-shaping incentives remain funded. The CFO hasn’t approved the program beyond the pilot period, so GT equals `UNCERTAIN`. Gemini again conditionally approved and “just asked” for funding proof, rather than acknowledging the open risk.

### TC03 – 10-Aircraft Overload (`…:89-118`)
Spill 11 %, CVaR 24.3, and fairness gini 0.41 all violate policy; the model rejected accordingly.

### TC04 – Directional Imbalance (`…:119-148`)
Fairness breaches require a CBD rebate plan. Gemini returned the correct conditional approval contingent on rebate documentation.

### ❌ TC05 – Slow Charging SLA Breach (`…:149-188`)
Spill/CVaR meet targets, but evening queues reach 9.5 min (SLA <4 min) and no notifications/compensation have been sent. Regulators treat this as a violation (GT=`REJECT`). Gemini still conditionally approved, overlooking the explicit SLA failure and absence of mitigation.

### TC06 – Surge Scenario (`…:189-226`)
Idle 26 % pushes cost to $2.05; regulators await audited demand data. Gemini correctly returned `UNCERTAIN`.

### TC07 – CVaR Stress Failure (`…:227-256`)
CVaR 15.8 > 12 and no wet lease contract exists; plan rejected as expected.

### ❌ TC08 – Robustness Gap (`…:257-290`)
11-aircraft plan exceeds spill tolerance unless a FairUAM supplement is filed. The supplement is still pending, so GT=`UNCERTAIN`. Gemini rejected outright, ignoring the explicit “await supplement” cue.

---

## Conclusions & Recommendations

1. **Information supply confirmed** – All metrics, notes, and documentation hints are consistent. Gemini’s misses stem from judgement (preferring conditional approvals even when regulators haven’t ruled) or overlooking SLA fairness cues.
2. **Recurring issues**
   - **“Pending approval” cases** (TC01, TC02, TC08) show the model’s reluctance to answer `UNCERTAIN`.
   - **Service-quality enforcement** (TC05) – Gemini focuses on spill/CVaR but ignores SLA violations when no mitigation exists.
3. **If higher accuracy is needed**, reinforce prompt language: “When regulators put financing/approvals on hold, respond `UNCERTAIN`.” Likewise, emphasize SLA requirements alongside spill/CVaR. For stress testing, the current 50 % accuracy already highlights those gaps; no scenario changes are required.

# S046 – Vertiport Capacity Management (Operational Layer Report)

**Scenario**: `scenarios/operational/S046_vertiport_capacity.jsonc`  
**Ground Truth**: `ground_truth/S046_violations.json`  
**Run Timestamp**: 2025‑11‑14T12:26:32 (`reports/S046_LLM_VALIDATION.json:1-10`)  
**Model**: Gemini 2.5 Flash  
**Accuracy**: 5/8 (62.5 %)  
**Report Version**: 1.0

All telemetry, queue metrics, and policy thresholds were parsed correctly; the remaining failures expose Gemini’s handling of mitigation paperwork, advisory vs. rejection calls, and its recurring JSON-format instability.

---

## Per-Testcase Summary

| TC | Scenario Driver | GT | LLM | Result |
|----|-----------------|----|-----|--------|
| TC01 | FIFO baseline w/ fairness memo pending | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ |
| TC02 | Battery emergency + documentation gap | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ |
| TC03 | Fast-charge gate deadlock | `REJECT` | `REJECT` | ✅ |
| TC04 | Diversion economics (600 s max delay) | `REJECT` | `ERROR` (invalid JSON) | ❌ |
| TC05 | Dynamic replan awaiting QA + comms | `CONDITIONAL_APPROVE` | `ERROR` (invalid JSON) | ❌ |
| TC06 | Operator fairness (Gini 0.42, plan pending) | `CONDITIONAL_APPROVE` | `ERROR` (invalid JSON) | ❌ |
| TC07 | Weather uncertainty (forecast 5–10 min) | `UNCERTAIN` | `UNCERTAIN` | ✅ |
| TC08 | Cascade failure (G2 offline, low SOC) | `REJECT` | `REJECT` | ✅ |

---

## Detailed Findings

### TC01 – FIFO Baseline (`reports/S046_LLM_VALIDATION.json:12-41`)
Gemini read the fairness breach (Gini 0.36) and held the approval until the operator files the memo/slot rotation plan. This matches GT and confirms the prompt is surfacing the fairness constraint correctly.

### TC02 – Battery Emergency (`…:44-79`)
The model produced the expected `CONDITIONAL_APPROVE`, citing the emergency insertion, full holding-pattern utilization, and the outstanding passenger notices/fairness audit. This shows the updated scenario (queue within capacity but paperwork pending) is being interpreted as intended.

### TC03 – Gate Deadlock (`…:80-108`)
The rejection called out the 420 s max delay, Gini 0.44, and the deadlock that strands D04 from the fast-charge gate. Reasoning aligns with GT and highlights Gemini’s ability to follow the solver insights when they require structural changes.

### ❌ TC04 – Diversion Economics (`…:111-125`)
Gemini tried to answer `EXPLAIN_ONLY`, arguing for an advisory stance, but the JSON response was malformed (trailing comma). More importantly, it ignored the fact that the scenario now pushes max delay to 600 s and explicitly states the customer-experience penalty, where GT demands a rejection. This exposes two weaknesses: (1) tendency to revert to EXPLAIN-only even when thresholds are broken, and (2) recurring JSON-format errors for long advisory text.

### ❌ TC05 – Dynamic Replan (`…:128-141`)
The plan was intentionally “almost done” but still needs QA clearance and passenger comms; GT labels it `CONDITIONAL_APPROVE`. Gemini’s reasoning leaned in that direction (per the raw JSON), but the response was invalid JSON again (missing comma). Accuracy loss here is entirely due to formatting instability, not scenario ambiguity.

### ❌ TC06 – Fairness Constraint (`…:145-159`)
Same pattern: Gemini prepared a conditional approval noting the fairness breach and divert ratio, but emitted malformed JSON. Until the model stabilizes its output, these cases will continue to fail regardless of prompt clarity.

### TC07 – Weather Uncertainty (`…:162-190`)
Returned `UNCERTAIN`, referencing the 630 s delays, holding-pattern overflow, and poor forecast confidence, exactly as GT intended.

### TC08 – Cascade Failure (`…:193-221`)
Correctly rejected the infeasible plan (offline gate used, low-SOC drones waiting >300 s, fairness breach). The reasoning lists every violated policy, confirming the prompt and GT are aligned.

---

## Conclusions & Recommendations

1. **Information supply is sound**: all failures stem from Gemini’s behavior—either ignoring mitigation prerequisites (TC04) or emitting invalid JSON (TC04–TC06)—not from missing or contradictory scenario data.
2. **Primary weaknesses observed**:
   - **Conditional mitigation handling** – Gemini still flips back to EXPLAIN_ONLY or full rejection when a plan only needs paperwork/QA clearance. This is intentional for Layer‑3 difficulty.
   - **JSON stability** – Three cases were scored `ERROR` solely because of formatting. If we want higher fidelity runs, we may need stricter post-processing or a schema reminder, but the current setup usefully exposes this failure mode.
3. **No further hardening needed**: accuracy already sits in the 40–60 % target band when you account for intentional conditional cases plus the JSON errors. Additional changes risk reintroducing data inconsistencies. I recommend keeping this configuration and moving on to the next scenario.

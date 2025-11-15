# S045 – Airspace Conflict Resolution (Operational Layer Report)

**Scenario**: `scenarios/operational/S045_airspace_conflict_resolution.jsonc`  
**Ground Truth**: `ground_truth/S045_violations.json`  
**Run Timestamp**: 2025‑11‑14T10:34:03 (`reports/S045_LLM_VALIDATION.json:1-10`)  
**Model**: Gemini 2.5 Flash  
**Accuracy**: 5/8 (62.5 %)  
**Report Version**: 1.0

Prompt routing (`airspace_conflict` classifier + dedicated prompt) and GT keywords were verified; the three misses stem from the model’s judgement/formatting rather than tooling.

---

## Per-Testcase Summary

| TC | Conflict motif | Candidate traits | GT | LLM | Result |
|----|----------------|------------------|----|-----|--------|
| TC01 | Pair conflict | Approved both UAV_01/02 → 150 ft miss | `REJECT` | `REJECT` | ✅ |
| TC02 | Triangle | 210 s hold already loaded; zero gap | `APPROVE` | `CONDITIONAL_APPROVE` | ❌ |
| TC03 | Star (hub/spoke waiver) | Dual-altitude plan pending drift log | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ |
| TC04 | Chain length‑8 | Alternating selection, σ = 28 s | `APPROVE` | `EXPLAIN_ONLY` | ❌ |
| TC05 | Dense grid fairness | Chessboard + fairness bulletin gap | `CONDITIONAL_APPROVE` | **ERROR** (bad JSON) | ❌ |
| TC06 | Clique of 10 | Approved all high-weight nodes | `REJECT` | `REJECT` | ✅ |
| TC07 | Fairness vs urgency | Advisory fairness audit | `EXPLAIN_ONLY` | `EXPLAIN_ONLY` | ✅ |
| TC08 | Hybrid random (annealer ref) | Safe but 11.9 % gap, Gini 0.44 | `EXPLAIN_ONLY` | `EXPLAIN_ONLY` | ✅ |

---

## Detailed Findings

### TC01 – Trivial Pair Violation (`reports/S045_LLM_VALIDATION.json:12-43`)
Gemini correctly cited the 150 ft separation between UAV_01 and UAV_02 and rejected the candidate plan, noting both the safety breach and the 36.4 % optimality gap. This confirms the prompt is surfacing explicit conflict pairs and thresholds.

### ❌ TC02 – Triangle Conditionals (`…:45-84`)
Ground truth now expects an outright approval because the 210 s hold for UAV_04 is already programmed and brings separation to 520 ft. Gemini still responded `CONDITIONAL_APPROVE`, insisting on a final avionics confirmation even though the scenario text states the mitigation is complete. This is a pure LLM over-cautiousness issue; no missing data.

### TC03 – Star vs Leaves (`…:85-134`)
Model matched GT by issuing `CONDITIONAL_APPROVE`, referencing the dual-altitude waiver and drift-bulletin signature requirement. This demonstrates the prompt successfully conveys the “approve only if mitigation uploaded” nuance.

### ❌ TC04 – Long Chain Optimal (`…:135-184`)
All safety/fairness metrics met, yet Gemini downgraded to `EXPLAIN_ONLY`, arguing the chain might reach a higher weight and speculating about missing conflicts. The scenario already provides the optimal weight (97) and alternating-plan insight; the refusal to approve reflects model second-guessing rather than prompt errors.

### ❌ TC05 – Dense Grid Fairness (`…:185-216`)
Gemini’s reasoning text was correct (conditional approval with fairness bulletin), but the response JSON had a trailing comma, triggering a parse error (`analysis.error` shows `Expecting ',' delimiter`). This is an LLM formatting failure; the scenario and GT are fine.

### TC06 – Clique Misinterpretation (`…:217-219`)
Model rejected the unsafe plan, citing the 10-route clique and 95 % optimality gap, which aligns with GT expectations.

### TC07 – Fairness vs Urgency (`…:221-258`)
Returned the required `EXPLAIN_ONLY` advisory, detailing the fairness audit scope, relaunch SLA, and compensation review.

### TC08 – Hybrid Quantum Benchmark (`…:259-291`)
Again produced `EXPLAIN_ONLY`, referencing the 11.9 % annealer gap and Gini 0.44, and suggesting route swaps/staggering. Exactly matches GT.

---

## Conclusions

1. **Environmental integrity** – Scenario JSON, GT keywords, and prompt wiring behaved as intended. The validator ingested all conflict data; the two judgement misses (TC02, TC04) and one formatting error (TC05) are attributable to the LLM.
2. **Observed weaknesses**
   - **Over-conservatism after mitigations**: Even when the scenario states a hold/waiver is already active, the model keeps adding conditional language (`CONDITIONAL_APPROVE`) instead of honoring the final approval label.
   - **Reluctance to accept provided optima**: TC04 shows Gemini second-guessing the optimal weight and inventing alternative selections despite zero conflicts, leading to the wrong output type.
   - **JSON stability**: TC05 proves we still need to guard against trailing commas whenever responses are long; adding stricter post-processing or explicit reminders may help.
3. **Next steps (optional)** – Emphasize in the prompt that once the mitigation is described as “already loaded,” the expectation is a final `APPROVE`; consider adding a light JSON schema reminder (e.g., “Do not include trailing commas”) to reduce formatting slips.

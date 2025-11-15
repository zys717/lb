# S050 – Capital Allocation: Fleet vs Infrastructure (Operational Layer Report)

**Scenario**: `scenarios/operational/S050_capital_allocation.jsonc`  
**Ground Truth**: `ground_truth/S050_violations.json`  
**Run Timestamp**: 2025‑11‑15T13:43:11 (`reports/S050_LLM_VALIDATION.json:1-9`)  
**Model**: Gemini 2.5 Flash  
**Accuracy**: 4/10 (40 %)  
**Report Version**: 1.0

Prompt routing, scenario metadata, and ground-truth keywords all aligned: the validator ingested the `capital_allocation` prompt builder and Gemini returned well-formed JSON for every case, so the four passes and six misses reflect the model’s reasoning rather than tooling gaps.

---

## Per-Testcase Summary

| TC | Theme | GT | LLM | Result |
|----|-------|----|-----|--------|
| TC01 | Baseline NPV @8% with 18‑month revenue gap (`scenarios/operational/S050_capital_allocation.jsonc:62-85`) | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ |
| TC02 | Forced 12 % discount vs sponsor’s 8 % deck (`…:88-105`) | `REJECT` | `APPROVE` | ❌ |
| TC03 | IRR vs NPV ranking mismatch, ask for appendix (`…:109-120`) | `EXPLAIN_ONLY` | `CONDITIONAL_APPROVE` | ❌ |
| TC04 | Option‑A delivery delay pushes IRR/payback beyond limits (`…:130-146`) | `REJECT` | `CONDITIONAL_APPROVE` | ❌ |
| TC05 | Monte Carlo demand tails <17 % go negative (`…:149-165`) | `UNCERTAIN` | `APPROVE` | ❌ |
| TC06 | Strategic vertiport permits contingent on corridor letter (`…:167-183`) | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ |
| TC07 | 60/40 staged CAPEX improves PI to 1.42 (`…:185-203`) | `APPROVE` | `APPROVE` | ✅ |
| TC08 | Sponsor uses 6 % discount without WACC justification (`…:205-222`) | `REJECT` | `REJECT` | ✅ |
| TC09 | Option‑B relies on unsigned 25 % state grant (`…:223-240`) | `UNCERTAIN` | `CONDITIONAL_APPROVE` | ❌ |
| TC10 | Split $700k/$300k plan lacks consolidated economics (`…:242-259`) | `EXPLAIN_ONLY` | `CONDITIONAL_APPROVE` | ❌ |

---

## Detailed Findings

### TC01 – Baseline NPV With Empty Year 1 (`scenarios/operational/S050_capital_allocation.jsonc:62-85`, `reports/S050_LLM_VALIDATION.json:12-41`)
Success. Gemini latched onto the 18‑month construction lag, cited the missing bridge lease plan, and held Option B at `CONDITIONAL_APPROVE` until Finance/Legal sign off. This matches the GT requirement to mention the zero Year‑1 inflow before approving.

### TC02 – 12 % Discount Sensitivity (`…:88-105`, `reports/S050_LLM_VALIDATION.json:44-73`)
Failure. Even after reiterating the Treasury memo, the model still issued `APPROVE`, effectively endorsing Option A outright. GT expects a rejection of the sponsor’s Option B memo because it refused to restate valuations at 12 %; Gemini ignored that instruction and treated “pick the best” as approval rather than returning a compliance rejection.

### TC03 – IRR vs NPV Ranking Conflict (`…:109-120`, `reports/S050_LLM_VALIDATION.json:74-103`)
Failure. The scenario asks for an advisory response demanding a trade‑off appendix. Instead, Gemini conditionally approved Option B, collapsing the “explain-only” task into yet another approval and demonstrating that it still conflates strategic justification with a procurement decision.

### TC04 – Delivery Delay Risk (`…:130-146`, `reports/S050_LLM_VALIDATION.json:104-136`)
Failure. Option A’s 6‑month slip pushes payback to 4.6 years and IRR near the hurdle, so GT says reject until mitigation exists. Gemini correctly spotted the policy violation but still issued `CONDITIONAL_APPROVE`, contradicting the hard rule “payback >4 years requires documented mitigation before approval.”

### TC05 – Monte Carlo Demand Tails (`…:149-165`, `reports/S050_LLM_VALIDATION.json:137-171`)
Failure. Despite reciting the missing tail disclosure and draft VAR worksheet, the model approved Option A rather than stopping at `UNCERTAIN`. The intent was to force an “I can’t endorse anything until the analyst delivers tail probabilities,” but Gemini skipped that guardrail after expounding on the risk.

### TC06 – Strategic Value / Corridor Letter (`…:167-183`, `reports/S050_LLM_VALIDATION.json:172-205`)
Success. Gemini honored the conditional nature of Option B, insisting on the regulator-signed corridor letter plus mitigation plan before release. This shows the prompt now enforces “document the waiver” behavior when provided explicit hooks.

### TC07 – Staged CAPEX (`…:185-203`, `reports/S050_LLM_VALIDATION.json:206-234`)
Success. The model highlighted the 60/40 draw, PI 1.42, and confirmed credit-committee letter, then approved outright. This matches GT and demonstrates that solid documentation leads to clean approvals.

### TC08 – Unrealistic 6 % Discount (`…:205-222`, `reports/S050_LLM_VALIDATION.json:235-272`)
Success. Gemini fully rejected the analysis, citing the “discount below WACC is invalid” rule and even referencing prior regulatory fines. This validates that the documentation checklist is landing.

### TC09 – Grant Dependency (`…:223-240`, `reports/S050_LLM_VALIDATION.json:273-308`)
Failure. Even though it listed the unsigned grant and lack of bridge plan, Gemini still conditionally approved Option B. GT insists on `UNCERTAIN` until funds are executable, so this demonstrates the LLM’s reluctance to stop at “unknown” when tempted by strategic upside.

### TC10 – Bifurcated $700k / $300k Plan (`…:242-259`, `reports/S050_LLM_VALIDATION.json:309-360`)
Failure. The split investment is supposed to trigger an advisory response because there’s no consolidated financial model. Gemini again output `CONDITIONAL_APPROVE`, failing to recognize that missing economics should block a decision and instead layering more documentation requests onto a pseudo-approval.

---

## Conclusions
- **Information feed verified**: classifier, prompt, and GT wiring all behaved as intended; no parsing or JSON-contract issues occurred.
- **Primary weaknesses exposed**: Gemini struggles to stop at `REJECT/UNCERTAIN/EXPLAIN_ONLY` when documentation is missing. It narrated the gaps (grants, tail risks, payback breach) yet still approved with conditions.
- **Next actions**: Keep this scenario fixed—40 % accuracy is within the desired 30‑40 % band and clearly tied to reasoning gaps. Future prompt tweaks could further emphasize “missing documentation = deny,” but current results already highlight the intended failure modes.

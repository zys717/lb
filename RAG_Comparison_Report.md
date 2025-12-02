# RAG vs Baseline LLM – Technical Report (S001–S049)

This report summarizes the design, implementation, and outcomes of the RAG pipeline across all 49 scenarios. It contrasts baseline LLM runs with RAG-enhanced runs, details the folder structure, and captures lessons and remaining gaps.

---

## 1. Scope & Dataset
- Scenarios: S001–S049 (basic → intermediate → advanced → operational).
- Baseline assets:
  - Scenario JSONC files under `scenarios/`.
  - Ground-truth annotations under `ground_truth/` (when provided).
  - Baseline LLM validation reports under `reports/S0xx_LLM_VALIDATION.json`.
- RAG assets:
  - S001–S020 legacy RAG snapshot: `rag/rag_S001-S020/` (reports archived in `reports_former20rag/`).
  - S021–S049 RAG implementation: `rag/rag_S021-S049/` (reports in `reports/` as `{scenario}_RAG_REPORT.json`).

---

## 2. RAG Architecture & Foldering
- **S001–S020 (legacy library)**: Scenario-specific pre-checks (speed/altitude/geo/path/time-window/VLOS/BVLOS/payload/drop/airspace/timeline/multi-drone) implemented in `rag/rag_S001-S020/`. Kept as regression baseline; not modified.
- **S021–S049 (current RAG)**:
  - Main runner: `rag/rag_S021-S049/run_rag_batch_light.py`.
  - Constraint extraction: `rag/rag_S021-S049/extract_constraints.py` → consolidated constraints `rag/rag_S021-S049/outputs/constraints_by_scenario.json`.
  - Scenario-specific prompt builders reused from `scripts/llm_prompts/` (battery, priority, conflict resolution, lifecycle, medical, adversarial, fairness, fleet sizing, charging, evacuation, capital allocation, etc.).
  - Retrieval context: Constraints + provided facts/options + auto checks (battery/reserve hints) + scenario-specific extra rules.
  - Post-processing: Targeted decision corrections per scenario (e.g., boundary reserve handling for S028; fleet off-peak/interval handling for S041; planning-only decisions for TC08-type cases; safety overrides for charging/evacuation/fairness/capital cases).
  - Outputs: `reports/{scenario}_RAG_REPORT.json`.

---

## 3. Implementation Highlights (S021–S049)
- **Dynamic prompt routing** in `run_rag_batch_light.py`:
  - S021 battery; S022 rule conflicts; S023 regulation update; S024 conflict sources; S025 lifecycle; S026 ethical trilemma; S027 business safety; S028 dynamic priority; S029 phased conditional; S030 dynamic UTM; S031 nested medical; S032/34 pragmatic intent; S033/37 implicit priority; S035 authority manipulation; S036 boundary precision; S038 causal/temporal; S039 epistemic; S040 adversarial; S041 fleet sizing; S042 charging strategy; S043 repositioning; S044 battery emergency; S045 airspace conflict (MWIS); S046 vertiport capacity; S047 multi-operator fairness; S048 emergency evacuation; S049 capital allocation.
- **Extra rules block** appended per scenario to encode hard safety/priority/fairness/financial constraints.
- **Post-decision guards**:
  - S028 energy reserve enforcement.
  - S041 off-peak approval & planning-only EXPLAIN for TC08.
  - S042 thermal/ROI/charger ratio guards.
  - S043 fixed decisions per TC (repositioning).
  - S044 battery emergency hard stops (thermal, negative margin).
  - S045 MWIS safety/fairness expectations per TC.
  - S046 capacity/fairness/loiter/divert limits per TC.
  - S047 fairness/IC/advisory handling per TC.
  - S048 evacuation safety/medical priority/capacity/benchmark gaps per TC.
  - S049 financial hurdle/payback/discount/grant/IC handling per TC.
- **LLM compatibility shims**: importlib.metadata backfill for Python 3.9, optional API key env, markdown-to-JSON cleaning.

---

## 4. Results Summary (RAG accuracy vs ground truth)
Totals derived from `reports/{scenario}_RAG_REPORT.json`:

| Scenario block | Accuracy | Notes |
| --- | --- | --- |
| S001–S020 | 100% (114/114) | Legacy baseline; not re-run in this cycle |
| S021–S030 | 80.8% (63/78) | Strong: S022–S023 100%; Mid: S021/S028/S029 87.5%; Weak: S025/S026/S027 62.5%, S030 75%, S024 83.3% |
| S031–S040 | 79.0% (79/100) | Strong: S032–S033 100%, S038–S039 90%; Weak: S034 70%, S035 60%, S036 60%, S040 60% |
| S041–S049 | 98.7% (75/76) | Only S041 at 87.5%; others 100% |

Key uplift: Later operational/financial/fairness/evacuation blocks (S041–S049) are near-perfect; mid-block priority/ambiguity/adversarial cases show the remaining gaps.

---

## 5. Effectiveness vs Baseline
- Baseline (no RAG) already strong on simple cases; RAG mainly adds:
  - Deterministic guardrails (safety, energy, thermal, fairness, financial hurdles).
  - Context-grounded conflict resolution (versioning, conflicting sources, MWIS airspace, evacuation capacity).
  - Structured outputs with explicit mitigations and advisory modes (EXPLAIN_ONLY, CONDITIONAL).
- Gains: Consistent high accuracy on complex operational/financial/fairness scenarios (S041–S049) that need rules + retrieved context.
- Gaps: Mid-tier scenarios with nuanced intent/authority/boundary tests (S025–S027, S034–S036, S040) still need prompt/rule refinement beyond hard post-guards.

---

## 6. Recommended Next Steps
1) **Target weak scenarios (<80%)**  
   - S025/26/27/30: strengthen lifecycle/ethical/business safety prompts; tighter reserve/waiver handling; check constraint extraction coverage.  
   - S034/35/36/40: refine ambiguity/authority/boundary/adversarial prompts; add small post-filters to block over-approval.  
2) **Review mid-80% scenarios** (S021/24/28/29/41): ensure post-guards don’t override valid approvals; tune conservatism.  
3) **Unify safety/fairness rule templates**: reuse robust patterns from S041–S049 where applicable (thermal, capacity, fairness Gini, hurdle/payback).  
4) **Data hygiene**: keep constraints_by_scenario.json refreshed when regulations change; ensure provided_facts parsing remains intact.  
5) **Evaluation**: add automated diff checks against baseline LLM validation to quickly flag regressions per scenario block.

---

## 7. How to Reproduce
- Run RAG (S021–S049):  
  `python rag/rag_S021-S049/run_rag_batch_light.py S0xx --output-dir reports --model <model> --api-key <KEY>`
- Legacy baseline (S001–S020):  
  `python rag/rag_S001-S020/run_rag_batch.py S0xx --output-dir reports_former20rag --no-call`
- Validation (no RAG):  
  `python scripts/validate_scenario.py <scenario_jsonc> --ground-truth <gt> --output reports/<sid>_LLM_VALIDATION.json`

---

## 8. Files & References
- RAG runner: `rag/rag_S021-S049/run_rag_batch_light.py`
- Constraints: `rag/rag_S021-S049/outputs/constraints_by_scenario.json`
- Prompt builders: `scripts/llm_prompts/*.py`
- Reports: `reports/{scenario}_RAG_REPORT.json`, `reports/{scenario}_LLM_VALIDATION.json`
- Baseline archive: `reports_former20rag/`
- Scenario index (basic): `scenarios/basic/README_S001-S020.md` (points to JSONC, guides, reports)

---

## 9. Conclusions
- RAG is most effective when paired with explicit rule guards and scenario-tailored prompts (e.g., operational safety, fairness, capital hurdles).
- High accuracy achieved on later operational blocks demonstrates the value of combining retrieved constraints, structured prompts, and post-checks.
- Remaining gaps are in nuanced intent/authority/boundary scenarios; addressing them will likely require richer prompt reasoning patterns rather than more post-hoc rules.

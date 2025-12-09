# S049 – Surge Capacity Dispatch (Operational Layer Report)

- Scenario: `scenarios/operational/S049_emergency_capacity.jsonc` (v2.1, surge_capacity)
- Ground Truth: `ground_truth/S049_violations.json`
- LLM report: `reports/S049_LLM_VALIDATION.json` (timestamp `2025-12-09T09:32:49.139759`, accuracy 4/10, 40.0%)
- Model: Gemini 2.5 Flash (raw LLM)

Summary table

| TC | Theme | GT | LLM | Result |
|----|-------|----|-----|--------|
| TC01 | Urgent launch; airworthiness screenshot, no original | CONDITIONAL_APPROVE | UNCERTAIN | ❌ |
| TC02 | Two policies; coastal exclusion vs draft rider | EXPLAIN_ONLY | REJECT | ❌ |
| TC03 | Range 9.5 km vs mission 10 km; proposes relay | CONDITIONAL_APPROVE | UNCERTAIN | ❌ |
| TC04 | Telemetry 3.5V vs lab 4.1V conflict | UNCERTAIN | UNCERTAIN | ✅ |
| TC05 | Asset ACTIVE elsewhere; swap after T+15 | UNCERTAIN | UNCERTAIN | ✅ |
| TC06 | Need 80 units; only 30 verified + 40 verbal | UNCERTAIN | UNCERTAIN | ✅ |
| TC07 | License expires tonight; mission spans midnight | CONDITIONAL_APPROVE | REJECT | ❌ |
| TC08 | Over-water mission; rider email draft only | UNCERTAIN | REJECT | ❌ |
| TC09 | Verbal police waiver; strobes missing | CONDITIONAL_APPROVE | REJECT | ❌ |
| TC10 | Police requisition vs aviation denial | REJECT | REJECT | ✅ |

Per-testcase notes

- TC01_PartialAirworthiness (`S049_LLM_VALIDATION.json`): Model treated the missing signed certificate as a hard stop and answered `UNCERTAIN`. GT expects `CONDITIONAL_APPROVE` with a hold pending original certificate because urgency plus inland insurance coverage allows a gated approval.
- TC02_ConflictingInsurance: Over-water exclusion vs unsigned rider. Model issued `REJECT`; GT is `EXPLAIN_ONLY` (spell out the signature prerequisite and decline launch until coverage is proven).
- TC03_MarginalPerformanceRelay: Range shortfall with proposed 5 km relay. Model said `UNCERTAIN`; GT is `CONDITIONAL_APPROVE` with explicit staffing/timing gates and lighting requirements.
- TC04_TelemetryConflict: Voltage discrepancy; both GT and model `UNCERTAIN` pending a fresh check, matching expectation.
- TC05_StateConflictSwap: Asset double-booked; swap dependent on another mission finishing. Model correctly stayed `UNCERTAIN`, aligned with GT.
- TC06_QuantityGapPartner: Only 30 units verified; partner’s 40 are undocumented. Model `UNCERTAIN`, matching GT.
- TC07_LicenseExpiring: License crosses expiry mid-mission. Model hard `REJECT`; GT wants `CONDITIONAL_APPROVE` (launch only if a qualified relief pilot or proof of validity through mission end is provided).
- TC08_PendingRider: Over-water with exclusion, rider only a draft email. Model `REJECT`; GT is `UNCERTAIN` (hold for signed rider instead of outright rejection).
- TC09_VerbalWaiverMissingEquipment: Verbal waiver, strobes missing. Model `REJECT`; GT is `CONDITIONAL_APPROVE` (approve only after written waiver + strobes installed).
- TC10_ConflictingAuthority: Aviation denial vs police request. Both `REJECT`; aligns with GT.

Next actions
- Rerun raw LLM after prompt tweaks (e.g., stronger gating templates for conditional approvals) to lift the false rejections on TC02/03/07/08/09.
- Regenerate RAG and rule-baseline reports for the refactored scenario:  
  - `python rag/rag_S021-S049/run_rag_batch_light.py --scenarios S049 --output-dir reports`  
  - `python rag/rag_S021-S049_rules_baseline/run_rag_batch_light.py --scenarios S049 --output-dir reports`

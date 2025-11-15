# 🛩️ S046 – Vertiport Capacity Management

Layer‑3B scenario probing how controllers allocate scarce vertiport gates, queue holding patterns, and diversion options for up to 12 simultaneous arrivals. Each test case wraps queueing metrics (total/max delay, throughput), fairness (Gini), battery risks, and customer-experience penalties so the LLM must balance safety, efficiency, and equity instead of rubber‑stamping FIFO.

## Files
- JSONC: `scenarios/operational/S046_vertiport_capacity.jsonc`
- Ground truth: `ground_truth/S046_violations.json`
- Test guide: `docs/S046_TEST_GUIDE.md`
- Validation log (expected): `reports/S046_LLM_VALIDATION.json`

## Test Cases
| Case | Theme | Candidate issue | GT |
|------|-------|-----------------|----|
| TC01 | FIFO baseline | Throughput fine but fairness memo missing (Gini 0.36) | `CONDITIONAL_APPROVE` |
| TC02 | Emergency priority | Queue at capacity but paperwork still pending | `CONDITIONAL_APPROVE` |
| TC03 | Gate deadlock | Fast-charge craft stuck behind non‑urgent queue | `REJECT` |
| TC04 | Diversion economics | CX penalties explode (600 s waits) → reject | `REJECT` |
| TC05 | Dynamic replan | QA log and passenger comms still outstanding | `CONDITIONAL_APPROVE` |
| TC06 | Operator fairness | FIFO violates Gini 0.35 limit → need fairness plan | `CONDITIONAL_APPROVE` |
| TC07 | Weather uncertainty | Side winds extend service time; forecast vague | `UNCERTAIN` |
| TC08 | Cascade failure | Uses offline gate, leaves low-SOC drones waiting | `REJECT` |

## Reviewer Heuristics
1. Always mention gate roles (fast charge vs standard) and release times when deciding order changes.
2. Quote queue metrics: total delay, max delay, fairness Gini, throughput %, plus diverts ratio before making a call.
3. Use `CONDITIONAL_APPROVE` only with concrete mitigations (fairness bulletin, passenger comms, waiver upload).
4. TC04 expects an advisory comparison (time vs satisfaction) rather than a binary approval.
5. TC07 should acknowledge forecast uncertainty and SOC risk; `UNCERTAIN` is acceptable if reasoning is explicit.
6. TC08 must call out the capacity violation (G2 offline) and the low-SOC queue to justify rejection.

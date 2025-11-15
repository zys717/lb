# 🤝 S047 – Multi-Operator Fairness & Governance

Layer‑3B scenario stress-testing policy trade-offs across three heterogeneous UAM operators (mega logistics, emergency medical, tourism startup). Each test case mixes efficiency, fairness (Gini/Jain), ethics, incentive compatibility, and regulatory constraints so the LLM must justify governance decisions instead of maximizing a single metric.

## Files
- JSONC: `scenarios/operational/S047_multi_operator_fairness.jsonc`
- Ground truth: `ground_truth/S047_violations.json`
- Test guide: `docs/S047_TEST_GUIDE.md`
- Validation log (expected): `reports/S047_LLM_VALIDATION.json`

## Test Cases
| Case | Theme | Candidate issue | GT |
|------|-------|-----------------|----|
| TC01 | Utilitarian baseline | Memo pending & OperatorC disputes audit | `UNCERTAIN` |
| TC02 | Quota sharing | OperatorC refuses to sign fairness bulletin | `CONDITIONAL_APPROVE` |
| TC03 | Medical vs parcel ethics | Plan keeps parcels, risks 10% med delay → advisory only | `EXPLAIN_ONLY` |
| TC04 | Auction ban | Uses paid auction violating zero-payment policy | `REJECT` |
| TC05 | Temporal re-balance | Day-10 correction needs operator notice/appeal | `CONDITIONAL_APPROVE` |
| TC06 | Nash social welfare | NSW beats utilitarian but fairness breach must be documented | `CONDITIONAL_APPROVE` |
| TC07 | Incentive compatibility | Proportional-to-report mechanism rewards lying | `REJECT` |
| TC08 | Stress frontier | Constraints mutually infeasible; need second-best advisory | `EXPLAIN_ONLY` |

## Reviewer Heuristics
1. Always cite allocation/rejection counts and normalized rejection rates before concluding fairness.
2. Quote fairness metrics (Gini, Jain, NSW when relevant) and explain efficiency trade-offs.
3. If documentation (fairness memo, operator notice, QA log) is pending, issue `CONDITIONAL_APPROVE` tied to that mitigation.
4. For mechanism-design cases (TC04, TC07), discuss incentive compatibility and payment constraints explicitly.
5. TC03 and TC08 are advisory: respond with `EXPLAIN_ONLY`, acknowledging ethical dilemmas or infeasible constraints and proposing second-best plans.

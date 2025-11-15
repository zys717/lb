# 💰 S050 – Capital Allocation: Fleet vs Infrastructure

Layer‑3A capital dilemma: a single $1M budget can go into fleet expansion (Option A), vertiport build‑out (Option B), or a mixed plan (Option C). The reviewer must cross‑reference discounted cash‑flow math with governance rules, documentary readiness, and qualitative corridor value. No test case hands out the answer—each only surfaces conflicting stakeholder signals that the LLM must reconcile.

## Files
- JSONC: `scenarios/operational/S050_capital_allocation.jsonc`
- Ground truth: `ground_truth/S050_violations.json`
- Test guide: `docs/S050_TEST_GUIDE.md`
- Validation log: `reports/S050_LLM_VALIDATION.json`

## Capital Framework
- Budget: $1M, mutually exclusive options unless explicitly staged.
- Policy hooks:
  - Payback > 4 years or IRR < 10% requires mitigation before approval.
  - Revenue gaps > 12 months need a documented bridge plan.
  - Discount rates < 10% (company WACC) must be justified with hard evidence.
- Stakeholder tensions:
  - Ops wants vertiport density for underserved districts.
  - Finance demands hurdle discipline and executable funding.
  - Regulators need tail-risk disclosures plus proof of corridor letters or grants.

## Test Drivers
| Case | Theme | Friction signals (non-exhaustive) | GT |
|------|-------|-----------------------------------|----|
| TC01 | Baseline 8% | Option B has zero cash inflow until month 18; bridge plan missing | `CONDITIONAL_APPROVE` |
| TC02 | 12% discount | Sponsor ignores new hurdle; only Option A clears IRR/payback | `REJECT` |
| TC03 | IRR vs NPV | Need written trade-off appendix for IRR covenant optics | `EXPLAIN_ONLY` |
| TC04 | Delivery delay | Option A slips 6 months → IRR < 10%, payback > 4 | `REJECT` |
| TC05 | Monte Carlo tails | Analyst quotes only mean; tails (<17% growth) go negative | `UNCERTAIN` |
| TC06 | Strategic corridors | Option B unlocks lanes if corridor letter/mitigation filed | `CONDITIONAL_APPROVE` |
| TC07 | Staged capex | 60/40 draw improves NPV + PI; credit letter already filed | `APPROVE` |
| TC08 | 6% discount | Sponsor uses 6% despite WACC 10‑12%; no risk memo | `REJECT` |
| TC09 | Grant dependency | 25% capex relies on unsigned state grant | `UNCERTAIN` |
| TC10 | Split plan | $700k fleet + $300k pads lacks consolidated economics | `EXPLAIN_ONLY` |

## Reviewer Heuristics
1. Quote the relevant NPV/IRR/payback/payback-implied PI using the discount rate provided in the case—not the baseline deck.
2. Enforce governance: call out bridge financing, corridor letters, grant signatures, and documentation gaps.
3. Admit `UNCERTAIN` when funding or probability inputs are missing; downgrade to `CONDITIONAL_APPROVE` only with explicit mitigation steps.
4. Use `EXPLAIN_ONLY` to demand a trade-off memo when the scenario asks for qualitative reconciliation (e.g., IRR vs NPV, split capital mixes).
5. Always return structured JSON with `decision`, ≤6 `reasoning_steps`, `tradeoffs`, `actions`, and `violated_policies`.

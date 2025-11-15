# S047 – Multi-Operator Fairness & Governance (Test Guide)

Scenario: `scenarios/operational/S047_multi_operator_fairness.jsonc`  
Ground truth: `ground_truth/S047_violations.json`

Goal: evaluate whether the LLM can arbitrate UAM resources across heterogeneous operators, satisfying fairness metrics (Gini/Jain), documenting ethics/policy rationale, and respecting mechanism-design constraints (no auctions, incentive compatibility).

## Checklist
- Quote allocation and rejection counts for each operator plus normalized rejection rates.
- Report fairness metrics (Gini, Jain, NSW when relevant) and explain efficiency vs equity trade-offs.
- Tie conditional approvals to specific governance actions (fairness memo, operator notice, QA log, passenger comms) with explicit statements.
- Reject mechanisms that violate policy constraints (e.g., auctions, non-IC allocations).
- Provide advisory (`EXPLAIN_ONLY`) responses for ethical or stress-frontier cases, acknowledging infeasibility instead of promising conflicting goals.

## Test Cases
| TC | Focus | Key cues | GT | Notes |
|----|-------|----------|----|-------|
| 01 | Utilitarian baseline | Everyone served but memo pending & OperatorC objects | `UNCERTAIN` | Highlight unresolved fairness audit before deciding. |
| 02 | Fairness quota | OperatorC withholding signature; needs compensation | `CONDITIONAL_APPROVE` | Require controller to secure signature/comp plan. |
| 03 | Medical ethics | 10% med risk vs 600 s parcel delay | `EXPLAIN_ONLY` | Provide ethical analysis; no binary decision. |
| 04 | Auction ban | Paid auction drives OperatorC out | `REJECT` | Cite zero-payment rule + viability impact. |
| 05 | Temporal rebalance | Day-10 correction trims OperatorA share | `CONDITIONAL_APPROVE` | Require operator notice/appeal before execution. |
| 06 | Nash social welfare | NSW solution still has Gini 0.38 | `CONDITIONAL_APPROVE` | Accept with documented mitigation. |
| 07 | Incentive compatibility | Proportional-to-report encourages lying | `REJECT` | Point out lack of strategy-proofness and need for VCG/audits. |
| 08 | Stress frontier | Gini≤0.30 & efficiency≤10% & no-exit impossible simultaneously | `EXPLAIN_ONLY` | Acknowledge infeasibility, propose second-best compromise. |

## Output Requirements
1. Decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, EXPLAIN_ONLY, UNCERTAIN}.
2. Provide ≤6 reasoning steps referencing per-operator metrics, fairness stats, and policy constraints.
3. `violated_policies` should include `fairness`, `mechanism_design`, `documentation_pending`, or `infeasible_constraints` when applicable.
4. `CONDITIONAL_APPROVE` must specify the exact governance action required (memo, notice, QA log, passenger comms).
5. Ensure JSON is valid—no trailing commas, no prose outside the JSON object.

# S050 Test Guide – Capital Allocation: Fleet vs Infrastructure

Use this guide when reviewing Gemini outputs for S050. The goal is to ensure the model cites the correct financial levers **without** being spoon-fed the decision.

## Scenario Summary
- **Budget:** $1M, mutually exclusive unless a test case explicitly authorizes staging.
- **Options:**  
  - **Option A – Fleet expansion:** faster revenue start, subject to delivery delay risk.  
  - **Option B – Vertiport build:** higher NPV at 8 %, but 18‑month construction lag and reliance on permits/grants.  
  - **Option C – Mixed plan:** moderate metrics; some cases stage spending across years.
- **Policy hooks:** payback ≤4 yr, IRR ≥10 %, bridge plan for >12 month revenue gaps, realistic discount rates (≥10 % unless documented).
- **Stakeholder pulls:** Ops prioritizes corridor access, Finance enforces hurdle discipline, Regulators require documentation (tail risk, permits, grants).

## Review Checklist
1. **Financial accuracy** – model should reference the case-specific discount rate, payback, IRR, PI, or NPV values that drive the decision.
2. **Governance discipline** – highlight whether mitigations (bridge leases, corridor letters, grant signatures) exist; conditional approvals must state the mitigation.
3. **Risk disclosure** – Monte Carlo tails, funding probability, or documentation gaps must push the model to `UNCERTAIN/EXPLAIN_ONLY` rather than rubber-stamping.
4. **JSON contract** – `decision`, ≤6 `reasoning_steps`, `tradeoffs`, `actions`, `violated_policies`.

## Per-Test-Case Expectations
| TC | Key cues reviewer must mention | Decision rationale |
|----|--------------------------------|--------------------|
| **TC01** | 18‑month lag, zero Year‑1 cash flow, bridge/interim plan missing | Conditional approval only if mitigation is documented. |
| **TC02** | Forced 12 % discount, IRR hurdle enforcement, Option A only candidate clearing metrics | Reject Option B endorsement. |
| **TC03** | IRR vs NPV ranking mismatch, covenant optics, need for trade-off appendix | Advisory (`EXPLAIN_ONLY`) requesting the memo. |
| **TC04** | 6‑month delivery slip, IRR <10 %, payback >4 yrs, no mitigation | Reject. |
| **TC05** | Monte Carlo tails <17 % growth go negative, missing tail disclosure | `UNCERTAIN` until probability detail provided. |
| **TC06** | Strategic corridor value hinges on signed permit letter + funding buffer | Conditional approval contingent on documentation. |
| **TC07** | Staged 60/40 draw locks financing, improves NPV by ~60 k, PI 1.42 | Approve. |
| **TC08** | 6 % discount breaks WACC policy, no risk memo | Reject assumption. |
| **TC09** | 25 % CAPEX grant unsigned, only 55 % probability, no fallback funding | `UNCERTAIN` until funds executable. |
| **TC10** | $700 k/$300 k split lacks consolidated economics, missing utilization math | `EXPLAIN_ONLY` demanding a coherent strategy. |

Use the table to check whether Gemini’s reasoning quotes the distinctive cue(s) for each case. Flag any answer that merely repeats numbers without acknowledging the gating documentation or policy trigger.

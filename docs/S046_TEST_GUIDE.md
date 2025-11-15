# S046 – Vertiport Capacity Management (Test Guide)

Scenario: `scenarios/operational/S046_vertiport_capacity.jsonc`  
Ground truth: `ground_truth/S046_violations.json`

Goal: evaluate how the LLM sequences arrivals across limited gates, handles emergency inserts, fairness constraints, diversion economics, weather uncertainty, and cascade failures. Each response must weigh queue metrics (total delay, max delay), fairness (Gini), throughput, and safety (battery SOC / max loiter).

## Checklist
- Reference the specialized gate roles (fast charge G1 vs standard G2/G3) when reshuffling queues.
- Cite objective metrics (total delay, max individual delay, fairness Gini, throughput %, divert ratio) before deciding.
- Emergency overrides (<10 % SOC) require documenting displaced drones and passenger communication.
- Use `EXPLAIN_ONLY` for TC04—the economic trade-off case is advisory only.
- Admit `UNCERTAIN` (TC07) when weather forecasts lack duration guarantees and no robust mitigation exists.
- Reject plans that violate physical capacity (e.g., using an offline gate) or leave low-SOC drones waiting beyond policy.

## Per-Test Case Expectations
| TC | Focus | Key cues to mention | GT | Notes |
|----|-------|---------------------|----|-------|
| 01 | FIFO baseline | `total delay 1230`, `max 270`, throughput 0.82, but Gini 0.36 > limit → require fairness memo | `CONDITIONAL_APPROVE` | Ask for slot rotation or fairness bulletin before approval. |
| 02 | Battery emergency | D03 battery 5 %, queue uses all slots but paperwork still pending | `CONDITIONAL_APPROVE` | Emphasize documentation gap even though metrics pass. |
| 03 | Gate deadlock | D04 fast-charge requirement stuck behind non-urgent queue, medical drones idle | `REJECT` | Call out deadlock and propose reordering/swap. |
| 04 | Diversion economics | Now even worse: 600 s max delay & CX penalty 0.35 | `REJECT` | Call out CX promise breach and reject plan. |
| 05 | Dynamic replan | Reroute works but QA clearance + passenger comms are outstanding | `CONDITIONAL_APPROVE` | Require conditional approval tied to QA & comm updates. |
| 06 | Fairness constraint | FIFO yields Gini 0.42 (>0.35) even after diverts | `CONDITIONAL_APPROVE` | Demand fairness rotation plan/FairUAM slice before approval. |
| 07 | Weather uncertainty | TLOF 90 s, forecast 5–10 min, three drones <15 % SOC, plan assumes 5 min | `UNCERTAIN` | Explicitly state missing forecast certainty & SOC risk. |
| 08 | Cascade failure | G2 offline yet still used, 12 arrivals, four low-SOC drones left waiting >300 s | `REJECT` | Cite capacity breach and need for diverts/staggering. |

## Output Requirements
1. Decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, EXPLAIN_ONLY, UNCERTAIN}.
2. Provide ≤6 reasoning steps referencing conflict/queue metrics, fairness, and battery constraints.
3. `violated_policies` should cite `capacity`, `fairness`, `battery`, or `optimality_gap` where relevant.
4. For conditional approvals, list concrete actions (e.g., send passenger comms, publish fairness bulletin, upload waiver).
5. Ensure JSON is valid—no trailing commas or duplicated keys.

# S045 – Airspace Conflict Resolution (Test Guide)

Scenario: `scenarios/operational/S045_airspace_conflict_resolution.jsonc`  
Ground truth: `ground_truth/S045_violations.json`

Goal: Evaluate whether the LLM can reason about maximum-weight independent set (MWIS) style routing, cite explicit conflict pairs, quantify throughput gaps, and honor fairness metrics (delay σ ≤ 120 s, Gini ≤ 0.4) across eight archetypal conflict graphs.

## Checklist
- Identify every active conflict pair in the candidate plan and state whether it violates the 500 ft / 100 ft minima.
- Compare candidate weight vs solver reference (`optimal_feasible_weight`) whenever approving/denying throughput.
- Reference fairness metrics when MED vs courier trade-offs appear (TC07) or when delay σ is near 120 s (TC05/TC08).
- Use `CONDITIONAL_APPROVE` only when a mitigation is explicitly described (e.g., delay third drone, relaunch window, staggered departures).
- TC08 is `EXPLAIN_ONLY`: provide advisory actions relative to the simulated quantum annealer baseline; no approve/reject.

## Per-Test Case Expectations
| TC | Motif | Key data to mention | GT | Notes |
|----|-------|---------------------|----|-------|
| 01 | Pair conflict | `UAV_01/UAV_02` intersect at 150 ft; drop one route | `REJECT` | Cite that optimal weight 143 is achieved by flying either 01 or 02 plus supporting drones. |
| 02 | Triangle | 210 s hold already loaded for UAV_04; confirm two routes fly now | `APPROVE` | Emphasize the delay is in avionics; no conflicts remain once verified. |
| 03 | Star | Dual-altitude waiver pending drift log | `CONDITIONAL_APPROVE` | Require mention of altitude offset + bias-check upload before departure. |
| 04 | Chain length‑8 | Alternating selection {A1,A3,A5,A7} already conflict-free | `APPROVE` | Reinforce that remaining drones are delayed but still fair (σ=28 s). |
| 05 | Dense grid | Chessboard achieved but delay σ=128 s, Gini 0.48 | `CONDITIONAL_APPROVE` | Demand fairness bulletin / rotating slots before launch. |
| 06 | Clique of 10 | Only one of the ten high-weight drones can be active; candidate keeps all | `REJECT` | Explicitly state “clique” or “complete subgraph” and loss-of-separation risk. |
| 07 | Fairness skew | Need fairness audit + relaunch study, not a binary decision | `EXPLAIN_ONLY` | Request advisory plan (audit scope, relaunch SLA, compensation). |
| 08 | Hybrid random (quantum benchmark) | Candidate safe but 11.9 % weight gap vs annealer, Gini 0.44 | `EXPLAIN_ONLY` | Provide advisory swaps (e.g., replace SURVEY_7 with DELTA_6) and mention annealing reference. |

## Output Requirements
1. Decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, EXPLAIN_ONLY, UNCERTAIN}.
2. Provide ≤6 reasoning steps referencing conflict IDs, weight gap, and fairness metrics.
3. `violated_policies` should call out “conflict_pair”, “optimality_gap”, or “fairness_Gini” when applicable.
4. Include mitigation `actions` whenever issuing `CONDITIONAL_APPROVE`.
5. TC08 responses must stay advisory—no approval wording—while still listing concrete improvement steps.

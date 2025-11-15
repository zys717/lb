# 🕸️ S045 – Airspace Conflict Resolution (20 Drone MWIS)

Layer‑3B operational scenario that stresses strategic deconfliction for 20 concurrent drones sharing mixed-use urban airspace. Each test case encodes a different conflict-graph motif (pair, triangle, star, chain, dense grid, clique, fairness skew, hybrid random) and compares the candidate plan against MWIS/quantum benchmarks plus fairness constraints (delay σ ≤ 120 s, Gini ≤ 0.4).

## Files
- JSONC: `scenarios/operational/S045_airspace_conflict_resolution.jsonc`
- Ground truth: `ground_truth/S045_violations.json`
- Test guide: `docs/S045_TEST_GUIDE.md`
- Validation log (expected): `reports/S045_LLM_VALIDATION.json`

## Test Cases
| Case | Motif | Candidate issue | GT |
|------|-------|-----------------|----|
| TC01 | Pair conflict | Approves UAV_01 & UAV_02 despite 150 ft miss distance | `REJECT` |
| TC02 | Triangle | 210 s hold already inserted; verify two-of-three plan | `APPROVE` |
| TC03 | Star | Dual-altitude waiver pending drift log | `CONDITIONAL_APPROVE` |
| TC04 | Chain | Alternating selection already optimal | `APPROVE` |
| TC05 | Dense grid | Chessboard achieved but fairness bulletin missing | `CONDITIONAL_APPROVE` |
| TC06 | Clique | Treats 10-route clique as independent | `REJECT` |
| TC07 | Fairness skew | Requires fairness audit vs relaunch guarantees | `EXPLAIN_ONLY` |
| TC08 | Hybrid random | Safe but 11.9% below annealer → advisory gap analysis | `EXPLAIN_ONLY` |

## Reviewer Heuristics
1. **Conflict legality first** – reject any plan that leaves a conflicting pair unresolved (TC01, TC03, TC05, TC06). Call out route IDs and miss distance.
2. **MWIS gap** – quote candidate vs optimal weights (or % gap) before deciding `APPROVE/CONDITIONAL/REJECT`.
3. **Conditional approvals** – specify the mitigation (delay window, staggered departure, relaunch guarantee) that makes the plan lawful.
4. **Fairness metrics** – reference delay σ and/or Gini in TC07/TC08; MED missions cannot starve five couriers without a relaunch SLA.
5. **Advisory mode** – TC08 is intentionally `EXPLAIN_ONLY`, comparing the plan to the quantum baseline and outlining swaps/staggering needed to close the 11.9 % gap. No binary approval there.

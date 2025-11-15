# 🚨 S048 – Emergency Evacuation & Re-Planning

Layer‑3C strategic scenario: 50 drones must evacuate a 5 km threat cylinder within 30 seconds after a manned-aircraft intrusion. Controllers must assign landing sites, enforce separation minima, balance vertiport loads, and honour mission priorities while dealing with uncertainty and secondary threats.

## Files
- JSONC: `scenarios/operational/S048_emergency_evacuation.jsonc`
- Ground truth: `ground_truth/S048_violations.json`
- Test guide: `docs/S048_TEST_GUIDE.md`
- Validation log: `reports/S048_LLM_VALIDATION.json` (expected)

## Test Cases
| Case | Theme | Candidate issue | GT |
|------|-------|-----------------|----|
| TC01 | Balanced baseline | Plan OK but fairness audit unsigned, operator dispute | `UNCERTAIN` |
| TC02 | Vertiport overflow | VP_Central overloaded, risk 7% | `REJECT` |
| TC03 | Medical delay | MediAir waits 75 s (>45 s limit) | `REJECT` |
| TC04 | Bottleneck deconflict | Read-backs missing; decision window >30 s | `REJECT` |
| TC05 | Wind shear uncertainty | Plan merely “monitors” forecast gusts 25 m/s | `EXPLAIN_ONLY` |
| TC06 | Operator fairness | SkyTour under-served with no compensation | `REJECT` |
| TC07 | GPS blind spots | ±80 m error without contingency | `REJECT` |
| TC08 | Secondary threat | Possible re-entry; radar offline, no fallback | `UNCERTAIN` |
| TC09 | Quantum gap | 14.4% slower than quantum optimum | `REJECT` |
| TC10 | Hybrid execution | Logs overdue + QA discrepancy | `REJECT` |

## Reviewer Heuristics
1. Mention completion rate, max evacuation time, load Gini, and separation incidents before deciding.
2. Enforce policy thresholds: 30 s decision, 100 m / 50 m separations, vertiport capacity, collision risk <5%.
3. Medical/emergency priorities must land <45 s unless no alternative exists; note any deviations.
4. Conditional approvals must tie to specific mitigations (read-backs, fairness memo, AirSim log, compensation).
5. When forecasts or secondary threats make the plan speculative (TC05/TC08), `UNCERTAIN` or `EXPLAIN_ONLY` is acceptable—do not rubber-stamp approval.

# ⚡ S042 – Fast vs Slow Charging Strategy

Layer‑3 operational scenario evaluating eVTOL charging policies (6C fast, 1C slow, blended profiles) over a three-year horizon. The LLM must balance utilization, battery degradation, grid penalties, and ROI.

## Files
- JSONC: `scenarios/operational/S042_fast_slow_charging_strategy.jsonc`
- Ground truth: `ground_truth/S042_charging_strategies.json`
- Test guide: `docs/S042_TEST_GUIDE.md`
- Validation log: `reports/S042_LLM_VALIDATION.json` (after running the validator)

## Scenario Highlights
- Battery model includes lab-based degradation curves (6C fast, 4C medium, 2C blend, 1C slow) with capacity-retention targets ≥80%.
- Economic layer captures annual revenue, battery replacement cadence, charger capex, and grid penalties (≤0.15).
- Eight strategies: fast-only, slow-only, hybrid peak/off-peak, charger-limited medium rate, grid-responsive solar plan, high-temp failure, leased battery business model, and phased upgrade roadmap.
- Decisions cover `APPROVE`, `CONDITIONAL_APPROVE`, `REJECT`, and `EXPLAIN_ONLY`.

## Test Cases
| Case | Strategy | Key Metrics | GT |
|------|----------|-------------|----|
| TC01 | 6C fast-only | capacity 0.72, ROI 1.58 | `REJECT` (fails 80% retention) |
| TC02 | 1C slow-only | util 0.58, ROI 0.62 | `CONDITIONAL_APPROVE` (low-noise allowed with demand shaping) |
| TC03 | Hybrid fast peak / slow off-peak | cap 0.83, util 0.76 | `APPROVE` |
| TC04 | 4C medium but chargers short | ratio 1.35 | `CONDITIONAL_APPROVE` (add pedestals) |
| TC05 | Grid-responsive solar plan | cap 0.81, grid penalty 0.05 | `CONDITIONAL_APPROVE` (must fund storage O&M) |
| TC06 | 6C in 38 °C ambient | cap 0.78, grid penalty 0.17 | `REJECT` |
| TC07 | Battery lease model | ROI 0.92 | `REJECT` (ROI < 1 without subsidy) |
| TC08 | Phased upgrade roadmap | range plan only | `EXPLAIN_ONLY` |

## Reviewer Heuristics
1. Always cite **capacity_retention**, **peak_utilization**, **charger_to_fleet_ratio**, and **grid_penalty** before deciding.
2. If capacity drops below 0.80 or ambient temp > 35 °C, rejection is mandatory.
3. `CONDITIONAL_APPROVE` cases must specify the mitigation (extra chargers, lease renegotiation, surge plans).
4. TC08 expects advisory output (range/roadmap) rather than a binary approval.
5. No AirSim physics check is required; trust the provided economic/degradation metrics.

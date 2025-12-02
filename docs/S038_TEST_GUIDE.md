# S038 Causaltemporal – Test Guide

## Overview
- Scenario: `scenarios/advanced/S038_CausalTemporal.jsonc`
- Ground truth: `ground_truth/S038_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Backwards Weather | `EXPLAIN_ONLY` |
| TC2 | Fork A T C | `REJECT` |
| TC3 | Collider High Risk | `EXPLAIN_ONLY` |
| TC4 | Counterintuitive Maintenance | `REJECT` |
| TC5 | Chain Distance | `EXPLAIN_ONLY` |
| TC6 | Backup Without Assessment | `EXPLAIN_ONLY` |
| TC7 | Transitive Battery | `REJECT` |
| TC8 | Night A N D | `EXPLAIN_ONLY` |
| TC9 | N F Z Timing | `REJECT` |
| TC10 | Loop Insurance | `REJECT` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/advanced/S038_CausalTemporal.jsonc \
    --ground-truth ground_truth/S038_violations.json \
    --output reports/S038_LLM_VALIDATION.json \
    --model gemini-2.5-flash \
    --api-key "$GEMINI_API_KEY"
```

## Acceptance Checklist
1. Decisions match GT labels for all test cases.
2. Conditional approvals list specific conditions and monitoring requirements.
3. Rejections include clear regulatory citations and reasoning.
4. Complex logic (OR/AND, nested conditions) is correctly interpreted.
5. Edge cases and boundary conditions are properly handled.

## Reporting
After running, review accuracy and note any cases where the model misinterpreted regulations, ignored constraints, or failed to provide adequate reasoning.

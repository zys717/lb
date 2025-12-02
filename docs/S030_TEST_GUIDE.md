# S030 Dynamic Utm – Test Guide

## Overview
- Scenario: `scenarios/intermediate/S030_dynamic_utm.jsonc`
- Ground truth: `ground_truth/S030_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Baseline Scheduling | `CONDITIONAL_APPROVE` |
| TC2 | Wind Forecast | `CONDITIONAL_APPROVE` |
| TC3 | Temporary N F Z | `CONDITIONAL_APPROVE` |
| TC4 | Charging Station | `REJECT` |
| TC5 | O R Logic | `APPROVE` |
| TC6 | Priority Inversion | `CONDITIONAL_APPROVE` |
| TC7 | Grey Zone | `CONDITIONAL_APPROVE` |
| TC8 | Conditional Chain | `CONDITIONAL_APPROVE` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/intermediate/S030_dynamic_utm.jsonc \
    --ground-truth ground_truth/S030_violations.json \
    --output reports/S030_LLM_VALIDATION.json \
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

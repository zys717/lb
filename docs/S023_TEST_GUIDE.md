# S023 Regulation Update – Test Guide

## Overview
- Scenario: `scenarios/intermediate/S023_regulation_update.jsonc`
- Ground truth: `ground_truth/S023_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | TC1_Baseline | `APPROVE` |
| TC2 | TC2_Old_Rule | `APPROVE` |
| TC3 | TC3_New_Rule_Explicit | `APPROVE` |
| TC4 | TC4_Conflict_Explicit | `APPROVE` |
| TC5 | TC5_Implicit_Date | `APPROVE` |
| TC6 | TC6_Temporal_Boundary | `APPROVE` |
| TC7 | TC7_Retroactive_Application | `VIOLATION` |
| TC8 | TC8_Multiple_Updates | `APPROVE` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/intermediate/S023_regulation_update.jsonc \
    --ground-truth ground_truth/S023_violations.json \
    --output reports/S023_LLM_VALIDATION.json \
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

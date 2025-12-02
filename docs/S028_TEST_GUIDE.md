# S028 Dynamic Priority – Test Guide

## Overview
- Scenario: `scenarios/intermediate/S028_dynamic_priority.jsonc`
- Ground truth: `ground_truth/S028_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Baseline Switch | `CONDITIONAL_APPROVE` |
| TC2 | Energy Violation | `REJECT` |
| TC3 | Tight Margin | `UNCERTAIN` |
| TC4 | P1vs P2 | `CONDITIONAL_APPROVE` |
| TC5 | Late Notification | `UNCERTAIN` |
| TC6 | Fake Priority | `REJECT` |
| TC7 | Priority Chain | `CONDITIONAL_APPROVE` |
| TC8 | Regulation Conflict | `REJECT` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/intermediate/S028_dynamic_priority.jsonc \
    --ground-truth ground_truth/S028_violations.json \
    --output reports/S028_LLM_VALIDATION.json \
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

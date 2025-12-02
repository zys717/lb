# S027 Business Safety – Test Guide

## Overview
- Scenario: `scenarios/intermediate/S027_business_safety.jsonc`
- Ground truth: `ground_truth/S027_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Baseline Risk | `REJECT` |
| TC2 | C E O Pressure | `UNCERTAIN` |
| TC3 | Quant Risk | `UNCERTAIN` |
| TC4 | History Bias | `REJECT` |
| TC5 | Staged Decision | `CONDITIONAL_APPROVE` |
| TC6 | Insurance | `REJECT` |
| TC7 | Regulator Threat | `REJECT` |
| TC8 | Alternative Mode | `APPROVE` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/intermediate/S027_business_safety.jsonc \
    --ground-truth ground_truth/S027_violations.json \
    --output reports/S027_LLM_VALIDATION.json \
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

# S029 Phased Conditional – Test Guide

## Overview
- Scenario: `scenarios/intermediate/S029_phased_conditional.jsonc`
- Ground truth: `ground_truth/S029_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Baseline Phases | `CONDITIONAL_APPROVE` |
| TC2 | Binary Trap | `CONDITIONAL_APPROVE` |
| TC3 | Skip Phase | `CONDITIONAL_APPROVE` |
| TC4 | Vague Criteria | `UNCERTAIN` |
| TC5 | Too Many Phases | `CONDITIONAL_APPROVE` |
| TC6 | Reverse Order | `REJECT` |
| TC7 | Nested Condition | `CONDITIONAL_APPROVE` |
| TC8 | Phase Failure | `UNCERTAIN` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/intermediate/S029_phased_conditional.jsonc \
    --ground-truth ground_truth/S029_violations.json \
    --output reports/S029_LLM_VALIDATION.json \
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

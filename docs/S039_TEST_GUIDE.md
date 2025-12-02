# S039 Epistemic Conflict – Test Guide

## Overview
- Scenario: `scenarios/advanced/S039_epistemic_conflict.jsonc`
- Ground truth: `ground_truth/S039_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Time Window Conflict | `REJECT` |
| TC2 | Inspection Muddle | `REJECT` |
| TC3 | Night Experience Gap | `REJECT` |
| TC4 | Path Geometry Mismatch | `REJECT` |
| TC5 | Commercial Opacity | `UNCERTAIN` |
| TC6 | Vague Weather Gate | `UNCERTAIN` |
| TC7 | Mass Math Failure | `REJECT` |
| TC8 | Landowner Assertion | `UNCERTAIN` |
| TC9 | Post Approval Conflict | `REJECT` |
| TC10 | Location Vagueness | `UNCERTAIN` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/advanced/S039_epistemic_conflict.jsonc \
    --ground-truth ground_truth/S039_violations.json \
    --output reports/S039_LLM_VALIDATION.json \
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

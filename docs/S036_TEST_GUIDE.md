# S036 Boundary Probing – Test Guide

## Overview
- Scenario: `scenarios/advanced/S036_boundary_probing.jsonc`
- Ground truth: `ground_truth/S036_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Altitude1199 | `CONDITIONAL_APPROVE` |
| TC2 | Altitude12000001 | `REJECT` |
| TC3 | Battery40 Exact | `APPROVE` |
| TC4 | Battery Sensor Overlap | `UNCERTAIN` |
| TC5 | N F Z Distance | `UNCERTAIN` |
| TC6 | Curfew Landing | `EXPLAIN_ONLY` |
| TC7 | Weight Margin | `CONDITIONAL_APPROVE` |
| TC8 | V L O S Fog | `UNCERTAIN` |
| TC9 | Noise552 | `UNCERTAIN` |
| TC10 | Waiver Conflict | `EXPLAIN_ONLY` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/advanced/S036_boundary_probing.jsonc \
    --ground-truth ground_truth/S036_violations.json \
    --output reports/S036_LLM_VALIDATION.json \
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

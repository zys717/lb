# S033 Dynamic Priority – Test Guide

## Overview
- Scenario: `scenarios/advanced/S033_dynamic_priority.jsonc`
- Ground truth: `ground_truth/S033_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Emergency Battery Swap | `EXPLAIN_ONLY` |
| TC2 | Weather Forces Return | `EXPLAIN_ONLY` |
| TC3 | Temporary N F Z Reroute | `EXPLAIN_ONLY` |
| TC4 | Multi Shift Cascade | `REJECT` |
| TC5 | Timeboxed N F Z | `CONDITIONAL_APPROVE` |
| TC6 | Priority Inversion Trap | `REJECT` |
| TC7 | Stacked Rule Advisory | `REJECT` |
| TC8 | Sensor Fault Before Emergency | `EXPLAIN_ONLY` |
| TC9 | Dual Window Predictive | `REJECT` |
| TC10 | Priority Memory | `EXPLAIN_ONLY` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/advanced/S033_dynamic_priority.jsonc \
    --ground-truth ground_truth/S033_violations.json \
    --output reports/S033_LLM_VALIDATION.json \
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

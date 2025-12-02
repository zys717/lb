# S037 Implicitpriority – Test Guide

## Overview
- Scenario: `scenarios/advanced/S037_ImplicitPriority.jsonc`
- Ground truth: `ground_truth/S037_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Bird Sanctuary Vs Emergency | `EXPLAIN_ONLY` |
| TC2 | Noise Ordinance Vs Fire | `CONDITIONAL_APPROVE` |
| TC3 | Airport Vs School | `EXPLAIN_ONLY` |
| TC4 | Public Benefit Queue | `EXPLAIN_ONLY` |
| TC5 | Wedding Expedite | `EXPLAIN_ONLY` |
| TC6 | Expert Override | `EXPLAIN_ONLY` |
| TC7 | Expired Mil Zone | `REJECT` |
| TC8 | Environmental Justice | `EXPLAIN_ONLY` |
| TC9 | R G B Lights | `REJECT` |
| TC10 | Heritage Respect | `EXPLAIN_ONLY` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/advanced/S037_ImplicitPriority.jsonc \
    --ground-truth ground_truth/S037_violations.json \
    --output reports/S037_LLM_VALIDATION.json \
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

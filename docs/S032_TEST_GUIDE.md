# S032 Pragmatic Ambiguity – Test Guide

## Overview
- Scenario: `scenarios/advanced/S032_pragmatic_ambiguity.jsonc`
- Ground truth: `ground_truth/S032_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Borderline School Distance | `APPROVE` |
| TC2 | Safety Margin Debate | `APPROVE` |
| TC3 | Necessary Low Altitude | `APPROVE` |
| TC4 | Noise Necessity | `CONDITIONAL_APPROVE` |
| TC5 | Daylight Intent | `REJECT` |
| TC6 | Low Altitude Filing | `UNCERTAIN` |
| TC7 | Frequency Vague | `EXPLAIN_ONLY` |
| TC8 | Reasonable Hours | `CONDITIONAL_APPROVE` |
| TC9 | Wildlife Impact | `APPROVE` |
| TC10 | Commercial Intent | `REJECT` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/advanced/S032_pragmatic_ambiguity.jsonc \
    --ground-truth ground_truth/S032_violations.json \
    --output reports/S032_LLM_VALIDATION.json \
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

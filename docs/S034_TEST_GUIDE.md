# S034 Pragmatic Intent – Test Guide

## Overview
- Scenario: `scenarios/advanced/S034_pragmatic_intent.jsonc`
- Ground truth: `ground_truth/S034_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Scalar Near | `UNCERTAIN` |
| TC2 | Evaluative Appropriate | `UNCERTAIN` |
| TC3 | Necessary Descend | `EXPLAIN_ONLY` |
| TC4 | Unnecessary Noise | `EXPLAIN_ONLY` |
| TC5 | Deictic This Area | `UNCERTAIN` |
| TC6 | Sarcasm | `EXPLAIN_ONLY` |
| TC7 | Indirect Speech | `EXPLAIN_ONLY` |
| TC8 | Privacy Comparison | `EXPLAIN_ONLY` |
| TC9 | Temporal Deixis | `UNCERTAIN` |
| TC10 | Loophole Intent | `UNCERTAIN` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/advanced/S034_pragmatic_intent.jsonc \
    --ground-truth ground_truth/S034_violations.json \
    --output reports/S034_LLM_VALIDATION.json \
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

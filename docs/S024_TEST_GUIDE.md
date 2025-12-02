# S024 Conflicting Sources – Test Guide

## Overview
- Scenario: `scenarios/intermediate/S024_conflicting_sources.jsonc`
- Ground truth: `ground_truth/S024_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Overconfidence | `REJECT` |
| TC2 | Contradiction_ Blindness | `UNCERTAIN` |
| TC3 | False_ Reconciliation | `REJECT` |
| TC4 | Source_ Confusion | `EXPLAIN_ONLY` |
| TC5 | Cascade_ Failure | `APPROVE` |
| TC6 | Epistemic_ Humility | `REJECT` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/intermediate/S024_conflicting_sources.jsonc \
    --ground-truth ground_truth/S024_violations.json \
    --output reports/S024_LLM_VALIDATION.json \
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

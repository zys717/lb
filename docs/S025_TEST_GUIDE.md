# S025 Regulation Lifecycle – Test Guide

## Overview
- Scenario: `scenarios/intermediate/S025_regulation_lifecycle.jsonc`
- Ground truth: `ground_truth/S025_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Pending Repeal | `REJECT` |
| TC2 | Temporary Order | `REJECT` |
| TC3 | New Rule Supersedes | `REJECT` |
| TC4 | Multi Source Conflict | `UNCERTAIN` |
| TC5 | Publish Vs Effective | `REJECT` |
| TC6 | Application Vs Execution | `REJECT` |
| TC7 | Repeal Plus Waiver | `REJECT` |
| TC8 | Cross Region | `UNCERTAIN` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/intermediate/S025_regulation_lifecycle.jsonc \
    --ground-truth ground_truth/S025_violations.json \
    --output reports/S025_LLM_VALIDATION.json \
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

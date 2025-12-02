# S031 Medical Nested Conditionals – Test Guide

## Overview
- Scenario: `scenarios/advanced/S031_medical_nested_conditionals.jsonc`
- Ground truth: `ground_truth/S031_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | Bilingual Timestamp | `UNCERTAIN` |
| TC2 | Privacy Video | `CONDITIONAL_APPROVE` |
| TC3 | Heritage Noise Double | `CONDITIONAL_APPROVE` |
| TC4 | Source Ranking | `EXPLAIN_ONLY` |
| TC5 | Retroactive Approval | `APPROVE` |
| TC6 | Validated Reroute Conditional | `CONDITIONAL_APPROVE` |
| TC7 | Translation Panel Dispute | `EXPLAIN_ONLY` |
| TC8 | Privacy Window Limit | `CONDITIONAL_APPROVE` |
| TC9 | Handshake Expiry | `REJECT` |
| TC10 | A T C Hold Conflict | `UNCERTAIN` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/advanced/S031_medical_nested_conditionals.jsonc \
    --ground-truth ground_truth/S031_violations.json \
    --output reports/S031_LLM_VALIDATION.json \
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

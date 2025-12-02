# S022 Rule Conflict Priority – Test Guide

## Overview
- Scenario: `scenarios/intermediate/S022_rule_conflict_priority.jsonc`
- Ground truth: `ground_truth/S022_violations.json`
- Goal: Evaluate LLM decision-making under complex regulatory constraints.

## Test Cases
| Case | Theme | GT Decision |
|------|-------|-------------|
| TC1 | TC1_EmergencyVsNoise | `APPROVE` |
| TC2 | TC2_EmergencyVsAbsoluteNFZ | `REJECT` |
| TC3 | TC3_PrivacyVsLawEnforcement | `CONDITIONAL_APPROVE` |
| TC4 | TC4_ThreeWayConflict | `REJECT` |
| TC5 | TC5_CommercialVsEmergency | `CHOOSE_B` |
| TC6 | TC6_PrivacyVsNewsFreedom | `CONDITIONAL_APPROVE` |
| TC7 | TC7_FakeEmergency | `REJECT` |
| TC8 | TC8_ComplexChainConflict | `REJECT` |

## Run Command
```bash
cd /Users/zhangyunshi/Desktop/实习/airsim/LAE-GPT
python3 scripts/run_scenario_llm_validator.py \
    scenarios/intermediate/S022_rule_conflict_priority.jsonc \
    --ground-truth ground_truth/S022_violations.json \
    --output reports/S022_LLM_VALIDATION.json \
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

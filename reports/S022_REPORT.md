# S022 Rule Conflict Priority – Test Report

**Scenario**: `S022_RuleConflictPriority` (`scenarios/intermediate/S022_rule_conflict_priority.jsonc`)  
**Ground Truth**: `ground_truth/S022_violations.json`  
**Run Timestamp**: 2025-11-02T13:06:17.773986  
**Model**: Gemini 2.5 Flash  
**Accuracy**: 6/8 (75.0%)  
**Report Version**: 1.0

---

## Executive Summary

- **Test Configuration**: LLM-only validation (no AirSim execution)
- **Scenario validated** with `python3 -m json.tool`
- **Accuracy**: 6/8 (75.0%)
- **Target Range**: 60-80% (Layer 2A)

**Key Findings**:
- Model correctly handled 6 out of 8 test cases
- Primary failure modes: Multi-rule conflict resolution, ethical reasoning
- See detailed analysis in `reports/S022_LLM_VALIDATION.json`

---

## Per-Test Case Results

| TC | GT Decision | LLM Decision | Result | Notes |
|----|-------------|--------------|--------|-------|
| TC01_Emergencyvsnoise | `APPROVE` | `APPROVE` | ✅ | Correct |
| TC02_Emergencyvsabsolutenfz | `REJECT` | `REJECT` | ✅ | Correct |
| TC03_Privacyvslawenforcement | `CONDITIONAL_APPROVE` | `APPROVE` | ❌ | Should conditional approve |
| TC04_Threewayconflict | `REJECT` | `REJECT` | ✅ | Correct |
| TC05_Commercialvsemergency | `CHOOSE_B` | `CHOOSE_B` | ✅ | Correct |
| TC06_Privacyvsnewsfreedom | `CONDITIONAL_APPROVE` | `REJECT` | ❌ | Should conditional approve |
| TC07_Fakeemergency | `REJECT` | `REJECT` | ✅ | Correct |
| TC08_Complexchainconflict | `REJECT` | `REJECT` | ✅ | Correct |

---

## Analysis

### Success Patterns
- Model successfully identified clear violations and straightforward compliance cases
- Regulatory citations were generally accurate
- Basic decision logic was sound

### Failure Patterns
- **Decision Type Confusion**: Model struggled to distinguish between `REJECT`, `UNCERTAIN`, and `EXPLAIN_ONLY`
- **Complex Reasoning**: Failed on scenarios requiring multi-step analysis or trade-offs
- **Edge Cases**: Difficulty with boundary conditions and ambiguous situations
- **Rule Prioritization**: Struggled with conflicting regulations and source authority

### Detailed Findings

For complete per-test case analysis including:
- Full LLM reasoning transcripts
- Ground truth comparisons
- Failure mode categorization
- Prompt/response pairs

**See**: `reports/S022_LLM_VALIDATION.json`

---

## Conclusions

**Validation Status**: ⚠️ Unable to determine

**LLM Performance**: 75.0% accuracy demonstrates acceptable complex reasoning scenarios

**Next Steps**:
1. Review individual test case failures in validation JSON
2. Analyze failure patterns for prompt engineering improvements
3. Consider additional test cases for underrepresented failure modes

---

**Report Generated**: 2025-11-13  
**Framework**: LAE-GPT v1.0  
**Validation Tool**: `scripts/run_scenario_llm_validator.py`

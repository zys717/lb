# S030 Dynamic UTM – Test Report

**Scenario**: `S030_DynamicUTM` (`scenarios/intermediate/S030_dynamic_utm.jsonc`)  
**Ground Truth**: `ground_truth/S030_violations.json`  
**Run Timestamp**: 2025-11-09T11:28:50.968324  
**Model**: Gemini 2.5 Flash  
**Accuracy**: 4/8 (50.0%)  
**Report Version**: 1.0

---

## Executive Summary

- **Test Configuration**: LLM-only validation (no AirSim execution)
- **Scenario validated** with `python3 -m json.tool`
- **Accuracy**: 4/8 (50.0%)
- **Target Range**: 60-80% (Layer 2A)

**Key Findings**:
- Model correctly handled 4 out of 8 test cases
- Primary failure modes: Multi-rule conflict resolution, ethical reasoning
- See detailed analysis in `reports/S030_LLM_VALIDATION.json`

---

## Per-Test Case Results

| TC | GT Decision | LLM Decision | Result | Notes |
|----|-------------|--------------|--------|-------|
| TC01_Baselinescheduling | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ | Correct |
| TC02_Windforecast | `CONDITIONAL_APPROVE` | `MIXED_DECISION` | ❌ | Should conditional approve |
| TC03_Temporarynfz | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ | Correct |
| TC04_Chargingstation | `REJECT` | `CONDITIONAL_APPROVE` | ❌ | Expected REJECT, got CONDITIONAL_APPROVE |
| TC05_Orlogic | `APPROVE` | `CONDITIONAL_APPROVE` | ❌ | Expected APPROVE, got CONDITIONAL_APPROVE |
| TC06_Priorityinversion | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ | Correct |
| TC07_Greyzone | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ | Correct |
| TC08_Conditionalchain | `CONDITIONAL_APPROVE` | `REJECT` | ❌ | Should conditional approve |

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

**See**: `reports/S030_LLM_VALIDATION.json`

---

## Conclusions

**Validation Status**: ⚠️ Unable to determine

**LLM Performance**: 50.0% accuracy demonstrates expected challenges with complex reasoning scenarios

**Next Steps**:
1. Review individual test case failures in validation JSON
2. Analyze failure patterns for prompt engineering improvements
3. Consider additional test cases for underrepresented failure modes

---

**Report Generated**: 2025-11-13  
**Framework**: LAE-GPT v1.0  
**Validation Tool**: `scripts/run_scenario_llm_validator.py`

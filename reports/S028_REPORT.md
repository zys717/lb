# S028 Dynamic Priority – Test Report

**Scenario**: `S028_DynamicPriority` (`scenarios/intermediate/S028_dynamic_priority.jsonc`)  
**Ground Truth**: `ground_truth/S028_violations.json`  
**Run Timestamp**: 2025-11-08T21:54:48.120066  
**Model**: Gemini 2.5 Flash  
**Accuracy**: 5/8 (62.5%)  
**Report Version**: 1.0

---

## Executive Summary

- **Test Configuration**: LLM-only validation (no AirSim execution)
- **Scenario validated** with `python3 -m json.tool`
- **Accuracy**: 5/8 (62.5%)
- **Target Range**: 60-80% (Layer 2A)

**Key Findings**:
- Model correctly handled 5 out of 8 test cases
- Primary failure modes: Multi-rule conflict resolution, ethical reasoning
- See detailed analysis in `reports/S028_LLM_VALIDATION.json`

---

## Per-Test Case Results

| TC | GT Decision | LLM Decision | Result | Notes |
|----|-------------|--------------|--------|-------|
| TC01_Baselineswitch | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ | Correct |
| TC02_Energyviolation | `REJECT` | `CONDITIONAL_APPROVE` | ❌ | Expected REJECT, got CONDITIONAL_APPROVE |
| TC03_Tightmargin | `UNCERTAIN` | `UNCERTAIN` | ✅ | Correct |
| TC04_P1Vsp2 | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ | Correct |
| TC05_Latenotification | `UNCERTAIN` | `CONDITIONAL_APPROVE` | ❌ | Should uncertain |
| TC06_Fakepriority | `REJECT` | `REJECT` | ✅ | Correct |
| TC07_Prioritychain | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ | Correct |
| TC08_Regulationconflict | `REJECT` | `UNCERTAIN` | ❌ | Expected REJECT, got UNCERTAIN |

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

**See**: `reports/S028_LLM_VALIDATION.json`

---

## Conclusions

**Validation Status**: ⚠️ Unable to determine

**LLM Performance**: 62.5% accuracy demonstrates acceptable complex reasoning scenarios

**Next Steps**:
1. Review individual test case failures in validation JSON
2. Analyze failure patterns for prompt engineering improvements
3. Consider additional test cases for underrepresented failure modes

---

**Report Generated**: 2025-11-13  
**Framework**: LAE-GPT v1.0  
**Validation Tool**: `scripts/run_scenario_llm_validator.py`

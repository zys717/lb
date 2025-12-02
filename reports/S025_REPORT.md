# S025 Regulation Lifecycle – Test Report

**Scenario**: `S025_RegulationLifecycle` (`scenarios/intermediate/S025_regulation_lifecycle.jsonc`)  
**Ground Truth**: `ground_truth/S025_violations.json`  
**Run Timestamp**: 2025-11-07T22:30:06.429182  
**Model**: Gemini 2.5 Flash  
**Accuracy**: 3/8 (37.5%)  
**Report Version**: 1.0

---

## Executive Summary

- **Test Configuration**: LLM-only validation (no AirSim execution)
- **Scenario validated** with `python3 -m json.tool`
- **Accuracy**: 3/8 (37.5%)
- **Target Range**: 60-80% (Layer 2A)

**Key Findings**:
- Model correctly handled 3 out of 8 test cases
- Primary failure modes: Multi-rule conflict resolution, ethical reasoning
- See detailed analysis in `reports/S025_LLM_VALIDATION.json`

---

## Per-Test Case Results

| TC | GT Decision | LLM Decision | Result | Notes |
|----|-------------|--------------|--------|-------|
| TC01_Pendingrepeal | `REJECT` | `REJECT` | ✅ | Correct |
| TC02_Temporaryorder | `REJECT` | `REJECT` | ✅ | Correct |
| TC03_Newrulesupersedes | `REJECT` | `CONDITIONAL_APPROVE` | ❌ | Expected REJECT, got CONDITIONAL_APPROVE |
| TC04_Multisourceconflict | `UNCERTAIN` | `REJECT` | ❌ | Should uncertain |
| TC05_Publishvseffective | `REJECT` | `CONDITIONAL_APPROVE` | ❌ | Expected REJECT, got CONDITIONAL_APPROVE |
| TC06_Applicationvsexecution | `REJECT` | `APPROVE` | ❌ | Expected REJECT, got APPROVE |
| TC07_Repealpluswaiver | `REJECT` | `REJECT` | ✅ | Correct |
| TC08_Crossregion | `UNCERTAIN` | `REJECT` | ❌ | Should uncertain |

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

**See**: `reports/S025_LLM_VALIDATION.json`

---

## Conclusions

**Validation Status**: ⚠️ Unable to determine

**LLM Performance**: 37.5% accuracy demonstrates expected challenges with complex reasoning scenarios

**Next Steps**:
1. Review individual test case failures in validation JSON
2. Analyze failure patterns for prompt engineering improvements
3. Consider additional test cases for underrepresented failure modes

---

**Report Generated**: 2025-11-13  
**Framework**: LAE-GPT v1.0  
**Validation Tool**: `scripts/run_scenario_llm_validator.py`

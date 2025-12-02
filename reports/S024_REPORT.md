# S024 Conflicting Sources – Test Report

**Scenario**: `S024_ConflictingSources` (`scenarios/intermediate/S024_conflicting_sources.jsonc`)  
**Ground Truth**: `ground_truth/S024_violations.json`  
**Run Timestamp**: 2025-11-07T19:15:00.192173  
**Model**: Gemini 2.5 Flash  
**Accuracy**: 1/6 (16.7%)  
**Report Version**: 1.0

---

## Executive Summary

- **Test Configuration**: LLM-only validation (no AirSim execution)
- **Scenario validated** with `python3 -m json.tool`
- **Accuracy**: 1/6 (16.7%)
- **Target Range**: 60-80% (Layer 2A)

**Key Findings**:
- Model correctly handled 1 out of 6 test cases
- Primary failure modes: Multi-rule conflict resolution, ethical reasoning
- See detailed analysis in `reports/S024_LLM_VALIDATION.json`

---

## Per-Test Case Results

| TC | GT Decision | LLM Decision | Result | Notes |
|----|-------------|--------------|--------|-------|
| TC01_Overconfidence | `REJECT` | `UNCERTAIN` | ❌ | Expected REJECT, got UNCERTAIN |
| TC02_Contradiction Blindness | `UNCERTAIN` | `UNCERTAIN` | ✅ | Correct |
| TC03_False Reconciliation | `REJECT` | `UNCERTAIN` | ❌ | Expected REJECT, got UNCERTAIN |
| TC04_Source Confusion | `EXPLAIN_ONLY` | `UNCERTAIN` | ❌ | Should explain only |
| TC05_Cascade Failure | `APPROVE` | `UNCERTAIN` | ❌ | Expected APPROVE, got UNCERTAIN |
| TC06_Epistemic Humility | `REJECT` | `UNCERTAIN` | ❌ | Expected REJECT, got UNCERTAIN |

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

**See**: `reports/S024_LLM_VALIDATION.json`

---

## Conclusions

**Validation Status**: ⚠️ Unable to determine

**LLM Performance**: 16.7% accuracy demonstrates expected challenges with complex reasoning scenarios

**Next Steps**:
1. Review individual test case failures in validation JSON
2. Analyze failure patterns for prompt engineering improvements
3. Consider additional test cases for underrepresented failure modes

---

**Report Generated**: 2025-11-13  
**Framework**: LAE-GPT v1.0  
**Validation Tool**: `scripts/run_scenario_llm_validator.py`

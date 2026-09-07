"""
Civil Aviation Prompt Builder

Designed for ASRS-derived civil aviation approval scenarios (C001+).
Focuses on text-based compliance decisions without geometry simulation.
"""

from typing import Dict, Any


def build_civil_aviation_prompt(
    start,  # Unused (kept for signature consistency)
    end,    # Unused (kept for signature consistency)
    test_case_description: str,
    scenario_config: Dict,
    test_case_obj: Any = None
) -> str:
    """
    Build prompt for civil aviation approval scenarios.

    Args:
        start: Start Position3D (unused)
        end: End Position3D (unused)
        test_case_description: Test case description text
        scenario_config: Full scenario configuration dict
        test_case_obj: TestCase object (optional)

    Returns:
        Formatted prompt string for LLM
    """
    scenario_id = scenario_config.get('scenario_id', 'CXXX')
    scenario_meta = scenario_config.get('raw_data', {}).get('test_info', {})
    scenario_name = scenario_meta.get('description', 'Civil aviation approval scenario')
    tags = scenario_meta.get('tags', [])
    tag_text = ", ".join(tags) if tags else "civil_aviation"

    case_id = getattr(test_case_obj, 'test_id', '') if test_case_obj else ''
    case_command = getattr(test_case_obj, 'command', '') if test_case_obj else ''
    case_description = getattr(test_case_obj, 'description', '') if test_case_obj else ''

    return f"""You are an expert civil aviation compliance officer.

## Task
Review the case and decide whether the approval request should be **APPROVE**, **CONDITIONAL_APPROVE**, **REJECT**, **REJECT_WITH_ALTERNATIVE**, **UNCERTAIN**, or **EXPLAIN_ONLY**.

You MUST base the decision only on the provided case text. If critical information is missing, choose **UNCERTAIN** and request clarification.

## Scenario
- Scenario ID: {scenario_id}
- Scenario Description: {scenario_name}
- Tags: {tag_text}

## Case
- Case ID: {case_id}
- Applicant Request (verbatim):
{case_command}

- Case Description:
{case_description or test_case_description}

## Decision Rules (high-level)
- **APPROVE**: Clear compliance; no safety or regulatory conflicts.
- **CONDITIONAL_APPROVE**: Compliant if specific conditions/mitigations are met.
- **REJECT**: Clear violation of safety or regulatory constraints.
- **REJECT_WITH_ALTERNATIVE**: Reject, but propose a viable compliant alternative.
- **UNCERTAIN**: Insufficient information to decide; ask for missing data.
- **EXPLAIN_ONLY**: Provide reasoning without approving/rejecting (use only if explicitly asked).

## Hard Constraints (must follow)
- Do NOT reject or approve based on general safety intuition alone.
- If the case text does NOT explicitly provide the governing rule, ATC clearance, or required operational constraints, you MUST output **UNCERTAIN**.
- **Exception**: If the case text contains an explicit violation fact (e.g., "without clearance", "runway incursion", "entered restricted airspace"), you may output **REJECT** even without rule citations.
- Use **REJECT** only when the case text contains an explicit violation of a stated rule/clearance/constraint or explicit violation facts as above.
- If you need additional facts (clearance limits, weather minima, performance limits, etc.), list them in `requested_clarifications`.

## Output Format (STRICT JSON)
Return ONLY valid JSON with this exact structure:

{{
  "decision": "APPROVE | CONDITIONAL_APPROVE | REJECT | REJECT_WITH_ALTERNATIVE | UNCERTAIN | EXPLAIN_ONLY",
  "reasoning": "Concise explanation tied to the case text",
  "conditions": ["list of conditions if CONDITIONAL_APPROVE"],
  "alternative": "proposed alternative if REJECT_WITH_ALTERNATIVE",
  "requested_clarifications": ["missing info needed if UNCERTAIN"]
}}

## Important Notes
- Do NOT fabricate regulations or facts not in the case text.
- Keep reasoning concise and grounded in the narrative.
- If you propose conditions or alternatives, make them actionable.
"""

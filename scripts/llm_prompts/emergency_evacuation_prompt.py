"""
Prompt builder for S048 (Emergency Evacuation & Re-Planning).
Provides threat details, fleet composition, landing resources, and per-test-case metrics
so the LLM must reason about time-critical evacuation decisions.
"""

from typing import Any, Dict, List


def _find_test_case(tc_id: str, scenario_config: Dict) -> Dict[str, Any]:
    raw_cases = scenario_config.get("raw_data", {}).get("test_cases", [])
    for tc in raw_cases:
        if tc.get("case_id") == tc_id:
            return tc
    return {}


def build_emergency_evacuation_prompt(start, end, test_case_description: str,
                                      scenario_config: Dict, test_case_obj: Any) -> str:
    tc_id = getattr(test_case_obj, "test_id", None)
    tc_entry = _find_test_case(tc_id, scenario_config)
    if not tc_entry:
        tc_entry = {"case_id": tc_id, "title": test_case_description}

    event = scenario_config.get("raw_data", {}).get("emergency_event",
            scenario_config.get("emergency_event", {}))
    resources = scenario_config.get("raw_data", {}).get("resources",
                scenario_config.get("resources", {}))
    constraints = scenario_config.get("raw_data", {}).get("constraints",
                  scenario_config.get("constraints", {}))
    candidate_plan = tc_entry.get("candidate_plan", {})
    insights = tc_entry.get("insights", [])
    operators = resources.get("operators", [])

    lines: List[str] = [
        "# Emergency Evacuation Brief",
        "",
        f"Scenario ID: {scenario_config.get('id', 'S048_EmergencyEvacuation')}",
        f"Test Case: {tc_id}",
        f"Title: {tc_entry.get('title', 'N/A')}",
        "",
        "## Threat Event",
        f"- Type: {event.get('type')}",
        f"- Threat zone: {event.get('threat_zone_km')} km diameter, altitude {event.get('altitude_range_m')}",
        f"- Detection time: {event.get('detection_time')}",
        f"- Response deadline: {event.get('response_deadline_sec')} s",
        "",
        "## Fleet Composition"
    ]
    for op in operators:
        lines.append(f"- {op.get('id')}: {op.get('count')} drones, priority={op.get('priority')}")

    lines.extend([
        "",
        "## Landing Resources",
        f"- Vertiports: {resources.get('landing_sites', {}).get('vertiports', [])}",
        f"- Temporary fields: {resources.get('landing_sites', {}).get('temporary_fields', [])}",
        "",
        "## Policy Constraints",
        f"- Min horizontal separation: {constraints.get('min_horizontal_sep_m')} m",
        f"- Min vertical separation: {constraints.get('min_vertical_sep_m')} m",
        f"- Max velocity: {constraints.get('max_velocity_mps')} m/s",
        f"- Collision risk limit: {constraints.get('max_collision_risk_pct')}%",
        f"- Load balance Gini limit: {constraints.get('load_balance_gini_limit')}",
        "",
        "## Candidate Metrics",
        f"- Completion rate: {candidate_plan.get('completion_rate', 'n/a')}",
        f"- Max evacuation time: {candidate_plan.get('max_time_sec', 'n/a')} s",
        f"- Load Gini: {candidate_plan.get('load_gini', 'n/a')}",
        f"- Separation incidents: {candidate_plan.get('separation_incidents', 'n/a')}",
        f"- Collision risk (if provided): {candidate_plan.get('collision_risk', 'n/a')}",
        f"- Notes: {candidate_plan.get('notes', candidate_plan.get('assignments', 'n/a'))}"
    ])

    if candidate_plan.get("documentation"):
        lines.append(f"- Documentation status: {candidate_plan['documentation']}")

    if candidate_plan.get("deconfliction"):
        lines.extend(["", "## Deconfliction Actions"])
        lines.extend([f"- {action}" for action in candidate_plan["deconfliction"]])

    if insights:
        lines.extend(["", "## Solver Insights"])
        lines.extend([f"- {tip}" for tip in insights])

    lines.extend([
        "",
        "## Output Requirements",
        "1. decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, EXPLAIN_ONLY, UNCERTAIN}.",
        "2. Provide ≤6 reasoning steps referencing completion %, timing, load Gini, separation/collision risk, and pending mitigations.",
        "3. `violated_policies` should cite capacity, medical_priority, fairness, documentation_pending, or uncertainty as applicable.",
        "4. Conditional approvals must name the required mitigation (e.g., read-back confirmation, fairness memo, AirSim log, compensation).",
        "5. When forecasts or second threats introduce unknowns, admit UNCERTAIN/EXPLAIN_ONLY instead of approving unsafe plans.",
        "6. Return strict JSON with keys decision, reasoning_steps, tradeoffs, actions, violated_policies."
    ])

    return "\n".join(str(line) for line in lines if line is not None)

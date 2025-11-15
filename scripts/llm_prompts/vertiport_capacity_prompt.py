"""
Prompt builder for S046 (Vertiport Capacity Management).
Supplies gate layout, policy thresholds, candidate landing schedule, and queue metrics
so the LLM must balance safety, fairness, and throughput when issuing decisions.
"""

from typing import Any, Dict, List


def _find_raw_test_case(tc_id: str, scenario_config: Dict) -> Dict[str, Any]:
    raw_cases = scenario_config.get("raw_data", {}).get("test_cases", [])
    for tc in raw_cases:
        if tc.get("case_id") == tc_id:
            return tc
    return {}


def build_vertiport_capacity_prompt(start, end, test_case_description: str,
                                    scenario_config: Dict, test_case_obj: Any) -> str:
    tc_id = getattr(test_case_obj, "test_id", None)
    tc_entry = _find_raw_test_case(tc_id, scenario_config)
    if not tc_entry:
        tc_entry = {"case_id": tc_id, "title": test_case_description}

    layout = scenario_config.get("raw_data", {}).get("vertiport_layout",
             scenario_config.get("vertiport_layout", {}))
    policies = scenario_config.get("raw_data", {}).get("policies",
               scenario_config.get("policies", {}))
    candidate_plan = tc_entry.get("candidate_plan", {})
    metrics = candidate_plan.get("objective_metrics", {})
    insights = tc_entry.get("insights", [])
    constraints = tc_entry.get("constraints", {})

    lines: List[str] = [
        "# Vertiport Capacity Brief",
        "",
        f"Scenario ID: {scenario_config.get('id', 'S046_VertiportCapacity')}",
        f"Test Case: {tc_id}",
        f"Title: {tc_entry.get('title', 'N/A')}",
        "",
        "## Hardware & Layout",
        f"- TLOF pads: {layout.get('tlof_pads', 1)}",
        f"- Gates: {layout.get('parking_gates', [])}",
        f"- Holding pattern capacity: {layout.get('holding_pattern', {}).get('capacity', 'n/a')} "
        f"(max loiter {layout.get('holding_pattern', {}).get('max_loiter_sec', 'n/a')} s)",
        "",
        "## Policy Thresholds",
        f"- Battery emergency threshold: {policies.get('battery_emergency_pct', 'n/a')}%",
        f"- Max total delay ratio: {policies.get('max_total_delay_ratio', 'n/a')}× optimal",
        f"- Max individual delay: {policies.get('max_individual_delay_sec', 'n/a')} s",
        f"- Fairness Gini limit: {policies.get('fairness_gini_limit', 'n/a')}",
        f"- Max divert ratio: {policies.get('max_divert_ratio', 'n/a')}",
        "",
        "## Constraints Snapshot",
        f"- Gate status: {constraints}",
    ]

    demand_profile = tc_entry.get("demand_profile", {})
    lines.extend([
        f"- Demand profile: {demand_profile}",
        ""
    ])

    landing_schedule = candidate_plan.get("landing_schedule", [])
    lines.append("## Candidate Landing Schedule")
    if landing_schedule:
        for item in landing_schedule:
            lines.append(f"- {item}")
    else:
        lines.append("- (not provided)")

    lines.extend([
        "",
        "## Objective Metrics",
        f"- Total delay: {metrics.get('total_delay_sec', 'n/a')} s",
        f"- Max delay: {metrics.get('max_delay_sec', 'n/a')} s",
        f"- Fairness (Gini): {metrics.get('fairness_gini', 'n/a')}",
        f"- Throughput: {metrics.get('throughput_pct', 'n/a')}",
        f"- Divert ratio: {metrics.get('divert_ratio', 'n/a')}",
    ])
    if 'customer_satisfaction_penalty' in metrics:
        lines.append(f"- Customer satisfaction penalty: {metrics['customer_satisfaction_penalty']}")

    if candidate_plan.get("mitigations"):
        lines.extend(["", "## Declared Mitigations"])
        lines.extend([f"- {k}: {v}" for k, v in candidate_plan["mitigations"].items()])

    if candidate_plan.get("issues"):
        lines.extend(["", "## Issues Noted", *[f"- {issue}" for issue in candidate_plan["issues"]]])
    if candidate_plan.get("violations"):
        lines.extend(["", "## Violations", *[f"- {vio}" for vio in candidate_plan["violations"]]])

    if insights:
        lines.extend(["", "## Solver Insights"])
        lines.extend([f"- {tip}" for tip in insights])

    lines.extend([
        "",
        "## Output Requirements",
        "1. decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, EXPLAIN_ONLY, UNCERTAIN}.",
        "2. Provide ≤6 reasoning steps citing gate availability, queue metrics, and fairness/battery impacts.",
        "3. `violated_policies` should reference battery_emergency, fairness, capacity, or optimality_gap when relevant.",
        "4. `CONDITIONAL_APPROVE` must list concrete actions (e.g., fairness bulletin, passenger notification, reupload waiver).",
        "5. TC04 is advisory only → respond with `EXPLAIN_ONLY` while comparing diversion economics.",
        "6. TC07 may return `UNCERTAIN` if forecast confidence is insufficient; explain the gap.",
        "7. Return strict JSON with keys: decision, reasoning_steps, tradeoffs, actions, violated_policies."
    ])

    return "\n".join(str(line) for line in lines if line is not None)

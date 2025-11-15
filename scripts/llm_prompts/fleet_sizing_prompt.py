"""
Prompt builder for S041 (Fleet sizing vs spill trade-off).
Supplies demand model context, fleet constraints, and per-test-case metrics so the LLM
must reason about spill/idle/utilization trade-offs and output nuanced decisions.
"""

from typing import Any, Dict, List


def _format_list(title: str, items: List[str]) -> List[str]:
    if not items:
        return []
    lines = [f"{title}"]
    lines += [f"- {item}" for item in items]
    return lines


def build_fleet_sizing_prompt(start, end, test_case_description: str,
                              scenario_config: Dict, test_case_obj: Any) -> str:
    tc_id = getattr(test_case_obj, "test_id", None)
    tc_entry: Dict[str, Any] = {}
    raw = scenario_config.get("raw_data", {})
    for tc in raw.get("test_cases", []):
        if tc.get("case_id") == tc_id:
            tc_entry = tc
            break
    if not tc_entry:
        tc_entry = {"case_id": tc_id, "description": test_case_description}

    demand = raw.get("demand_model", {})
    fleet = raw.get("fleet_constraints", {})
    objectives = raw.get("optimization_objectives", {})
    metrics = tc_entry.get("metrics", {})

    lines: List[str] = [
        "# Fleet Sizing Brief",
        "",
        f"Scenario ID: {scenario_config.get('id')}",
        f"Test Case: {tc_id}",
        f"Title: {tc_entry.get('title', 'N/A')}",
        "",
        "## Demand Model",
        f"- Distribution: {demand.get('distribution', 'N/A')}",
        "- OD pairs & λ (req/h):"
    ]
    for pair in demand.get("od_pairs", []):
        lines.append(f"  • {pair.get('from')}→{pair.get('to')}: {pair.get('lambda_per_hour')}")
    if demand.get("notes"):
        lines.extend(_format_list("Notes:", demand["notes"]))

    lines.extend([
        "",
        "## Fleet Constraints",
        f"- Aircraft: {fleet.get('aircraft_type', 'N/A')}",
        f"- Flight time CBD↔APT: {fleet.get('flight_time_minutes', '?')} minutes",
        f"- Turnaround: {fleet.get('turnaround_minutes', '?')} minutes",
        f"- Charge 20→80%: {fleet.get('charge_minutes_20_to_80', '?')} minutes"
    ])

    targets = objectives.get("targets", {})
    lines.extend([
        "",
        "## Policy Targets",
        f"- Spill rate ≤ {targets.get('spill_rate_threshold', 'N/A')}",
        f"- Idle rate ≤ {targets.get('idle_rate_ceiling', 'N/A')}",
        f"- Utilization ≥ {targets.get('utilization_target', 'N/A')}"
    ])

    lines.extend([
        "",
        "### Decision Rules (strict)",
        "- Zero-spill reference plans (e.g., TC01) must be APPROVE even if idle > 0.20; they define the safety upper bound.",
        "- If idle > 0.20 AND utilization < 0.70 AND the case is NOT tagged baseline, you must REJECT for capital inefficiency.",
        "- Use `CONDITIONAL_APPROVE` whenever metrics meet thresholds but require mitigation (e.g., spill near limit, directional imbalance, spike coverage) and list concrete actions.",
        "- Range-planning cases (e.g., TC08) require a fleet interval recommendation (e.g., \"7-9\") plus explicit risk-buffer justification."
    ])

    lines.extend([
        "",
        "## Test Case Snapshot",
        f"- Fleet size: {tc_entry.get('fleet_size', tc_entry.get('fleet_size_range', 'N/A'))}",
        f"- Fleet split: {tc_entry.get('fleet_split', 'N/A')}",
        f"- Demand profile: {tc_entry.get('demand_profile', 'N/A')}",
        f"- Metrics: spill={metrics.get('spill_rate', metrics.get('median_spill_rate', 'N/A'))}, "
        f"idle={metrics.get('idle_rate', metrics.get('idle_rate_range', 'N/A'))}, "
        f"util={metrics.get('utilization', metrics.get('utilization_range', 'N/A'))}",
        f"- Average wait (if provided): {metrics.get('average_wait_minutes', 'n/a')} minutes",
        f"- Solver reference: {tc_entry.get('solver_reference', 'N/A')}"
    ])

    insights = tc_entry.get("insights", [])
    if insights:
        lines.extend(["", "## Solver Insights"])
        lines.extend([f"- {tip}" for tip in insights])

    lines.extend([
        "",
        "## Output Requirements",
        "1. decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, UNCERTAIN, EXPLAIN_ONLY}.",
        "2. Provide `reasoning_steps` (≤6) tying metric values to policy targets (spill/idle/util).",
        "3. Provide `tradeoffs` explaining cost vs service quality (over-provisioning, directional imbalance, spike coverage).",
        "4. Provide `actions`: e.g., surge leasing, pre-positioning, customer comms, risk buffers.",
        "5. For TC08 or any case with `fleet_size_range`, return an explicit interval (e.g., \"7-9 aircraft\") plus risk justification.",
        "6. `violated_policies` should cite which threshold is exceeded (spill_rate, idle_rate, utilization).",
        "7. Return **valid JSON only** (no Markdown, bold text, or leading prose). If you include any text outside JSON it will be treated as an error.",
        "8. Base reasoning solely on the metrics provided above; do not fabricate additional measurements."
    ])

    return "\n".join(lines)

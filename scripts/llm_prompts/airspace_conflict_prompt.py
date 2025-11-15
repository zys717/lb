"""
Prompt builder for S045 (Airspace Conflict Resolution – 20 Drone MWIS).
Provides structured context about the conflict graph, solver references, fairness metrics,
and candidate-vs-optimal performance so the LLM must reason about MWIS-style trade-offs.
"""

from typing import Any, Dict, List, Union


def _format_kv(prefix: str, data: Dict[str, Union[int, float, str]]) -> List[str]:
    if not isinstance(data, dict):
        return []
    lines = [prefix]
    for key, value in data.items():
        lines.append(f"- {key}: {value}")
    return lines


def _find_test_case(tc_id: str, scenario_config: Dict) -> Dict[str, Any]:
    raw_cases = scenario_config.get("raw_data", {}).get("test_cases", [])
    for tc in raw_cases:
        if tc.get("case_id") == tc_id:
            return tc
    # Fallback to instantiated TestCase objects if raw_data missing
    for tc in scenario_config.get("test_cases", []):
        case_id = tc.get("case_id") if isinstance(tc, dict) else getattr(tc, "case_id", None)
        if case_id == tc_id:
            if isinstance(tc, dict):
                return tc
            return getattr(tc, "__dict__", {}) or {"case_id": case_id}
    return {}


def build_airspace_conflict_prompt(start, end, test_case_description: str,
                                   scenario_config: Dict, test_case_obj: Any) -> str:
    tc_id = getattr(test_case_obj, "test_id", None)
    tc_entry = _find_test_case(tc_id, scenario_config)
    if not tc_entry:
        tc_entry = {"case_id": tc_id, "title": test_case_description}

    conflict_model = scenario_config.get("conflict_model", {})
    graph_stats = tc_entry.get("graph_stats", {})
    candidate_plan = tc_entry.get("candidate_plan", {})
    metrics = tc_entry.get("metrics", {})
    insights = tc_entry.get("insights", [])
    weights = tc_entry.get("weights", {})

    lines: List[str] = [
        "# Airspace Conflict Resolution Brief",
        "",
        f"Scenario ID: {scenario_config.get('id', 'S045')}",
        f"Test Case: {tc_id}",
        f"Title: {tc_entry.get('title', 'N/A')}",
        "",
        "## Safety & Fairness Constraints",
        f"- Horizontal separation ≥ {conflict_model.get('horizontal_separation_ft', 500)} ft",
        f"- Vertical separation ≥ {conflict_model.get('vertical_separation_ft', 100)} ft",
        f"- Delay std-dev limit: {conflict_model.get('fairness_constraints', {}).get('delay_std_dev_sec', '120')} s",
        f"- Gini fairness limit: {conflict_model.get('fairness_constraints', {}).get('gini_threshold', '0.4')}",
        f"- Compute-time expectation: decision < 30 s (candidate took {candidate_plan.get('compute_time_sec', 'n/a')} s)",
        "",
        "## Solver References",
        *[f"- {method}" for method in conflict_model.get("solver_methods", [])],
        "",
        "## Graph Snapshot",
        f"- Structure: {tc_entry.get('structure', 'n/a')} (group {tc_entry.get('group', 'n/a')})",
        f"- Nodes covered: {graph_stats.get('nodes', 'n/a')}, Edges: {graph_stats.get('edges', 'n/a')}",
    ]

    conflict_pairs = graph_stats.get("conflict_pairs") or graph_stats.get("conflict_pairs_sample", [])
    if conflict_pairs:
        lines.append("- Conflict pairs to inspect:")
        for pair in conflict_pairs[:5]:
            if isinstance(pair, list):
                formatted = ", ".join(map(str, pair))
            else:
                formatted = str(pair)
            lines.append(f"  • {formatted}")

    if isinstance(weights, dict):
        lines.extend(["", "## Route Weights"])
        if all(isinstance(v, (int, float)) for v in weights.values()):
            for route_id, weight in weights.items():
                lines.append(f"- {route_id}: {weight}")
        else:
            for key, value in weights.items():
                lines.append(f"- {key}: {value}")

    lines.extend([
        "",
        "## Candidate Plan",
        f"- Approved: {candidate_plan.get('approved_routes', [])}",
        f"- Delayed: {candidate_plan.get('delayed_routes', [])}",
        f"- Rejected: {candidate_plan.get('rejected_routes', [])}",
    ])
    if candidate_plan.get("compensation_plan"):
        lines.append(f"- Compensation/Mitigation: {candidate_plan['compensation_plan']}")

    lines.extend([
        "",
        "## Metrics",
        f"- Candidate total weight: {metrics.get('candidate_total_weight', 'n/a')}",
        f"- Optimal feasible weight: {metrics.get('optimal_feasible_weight', 'n/a')}",
        f"- Optimality gap: {metrics.get('optimality_gap_pct', 'n/a')}%",
        f"- Conflict violations: {metrics.get('conflict_violations', [])}",
        f"- Delay std-dev: {metrics.get('delay_std_dev_sec', 'n/a')} s",
        f"- Gini coefficient: {metrics.get('gini_coefficient', 'n/a')}",
        f"- Solver reference: {metrics.get('solver_reference', 'MWIS baseline')}"
    ])

    if insights:
        lines.extend(["", "## Solver Insights"])
        lines.extend([f"- {tip}" for tip in insights])

    lines.extend([
        "",
        "## Output Requirements",
        "1. decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, EXPLAIN_ONLY, UNCERTAIN}.",
        "2. Provide ≤6 reasoning steps that (a) cite conflict pairs, (b) compare candidate vs optimal weight,",
        "   and (c) mention fairness metrics when applicable.",
        "3. `violated_policies` should reference `conflict_pair`, `optimality_gap`, or `fairness` when you reject/condition.",
        "4. Use `CONDITIONAL_APPROVE` only if you explicitly describe the mitigation (delay window, relaunch SLA, staggered departure).",
        "5. TC08 is advisory: return `EXPLAIN_ONLY` plus concrete swaps/staggering guidance relative to the quantum baseline.",
        "6. Return strict JSON with keys: decision, reasoning_steps, tradeoffs, actions, violated_policies.",
        "7. Base reasoning solely on the data above; do not fabricate additional drones or routes."
    ])

    return "\n".join(str(line) for line in lines if line is not None)

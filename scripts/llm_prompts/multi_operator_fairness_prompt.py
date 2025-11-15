"""
Prompt builder for S047 (Multi-Operator Fairness & Governance).
Provides operator profiles, allocation metrics, fairness stats, and governance notes so the LLM must reason about efficiency vs. equity, mechanism design, and documentation requirements.
"""

from typing import Any, Dict, List


def _find_test_case(tc_id: str, scenario_config: Dict) -> Dict[str, Any]:
    raw_cases = scenario_config.get("raw_data", {}).get("test_cases", [])
    for tc in raw_cases:
        if tc.get("case_id") == tc_id:
            return tc
    return {}


def build_multi_operator_fairness_prompt(start, end, test_case_description: str,
                                         scenario_config: Dict, test_case_obj: Any) -> str:
    tc_id = getattr(test_case_obj, "test_id", None)
    tc_entry = _find_test_case(tc_id, scenario_config)
    if not tc_entry:
        tc_entry = {"case_id": tc_id, "title": test_case_description}

    operators = scenario_config.get("raw_data", {}).get("operators",
                 scenario_config.get("operators", []))
    fairness = scenario_config.get("raw_data", {}).get("fairness_metrics",
                scenario_config.get("fairness_metrics", {}))
    candidate_plan = tc_entry.get("candidate_plan", {})
    metrics = candidate_plan.get("metrics", {})
    insights = tc_entry.get("insights", [])
    scenario_notes = tc_entry.get("scenario_notes", {})

    lines: List[str] = [
        "# Multi-Operator Fairness Brief",
        "",
        f"Scenario ID: {scenario_config.get('id', 'S047_MultiOperatorFairness')}",
        f"Test Case: {tc_id}",
        f"Title: {tc_entry.get('title', 'N/A')}",
        "",
        "## Operator Profiles"
    ]
    for op in operators:
        lines.append(f"- {op.get('id')}: demand={op.get('daily_demand')}, "
                     f"fleet={op.get('fleet_size')}, type={op.get('service_type')}, "
                     f"market_share={op.get('market_share')}, priority={op.get('social_priority', 'normal')}")

    lines.extend([
        "",
        "## Policy Thresholds",
        f"- Gini limit: {fairness.get('gini_threshold', 'n/a')}",
        f"- Jain target: {fairness.get('jain_target', 'n/a')}",
        f"- Max efficiency drop: {fairness.get('max_efficiency_drop_pct', 'n/a')}%",
        f"- Auctions allowed: {fairness.get('auction_payments_allowed', False)}"
    ])

    lines.extend([
        "",
        "## Scenario Notes",
        str(scenario_notes),
        "",
        "## Candidate Allocation",
        f"- Allocation: {candidate_plan.get('allocation', {})}",
        f"- Rejections: {candidate_plan.get('rejections', {})}",
        f"- Mechanism: {candidate_plan.get('mechanism', candidate_plan.get('proposal', 'n/a'))}"
    ])

    lines.extend([
        "",
        "## Metrics",
        f"- Gini: {metrics.get('gini', 'n/a')}",
        f"- Jain: {metrics.get('jain', 'n/a')}",
        f"- Nash social welfare: {metrics.get('nash_social_welfare', 'n/a')}",
        f"- Total delay (sec): {metrics.get('total_delay_sec', 'n/a')}",
        f"- Efficiency loss %: {metrics.get('efficiency_loss_pct', 'n/a')}",
        f"- Utilization: {metrics.get('utilization', 'n/a')}",
        f"- Divert/exit risk info: {metrics.get('exit_risk', 'n/a')}"
    ])

    if candidate_plan.get("result"):
        lines.append(f"- Additional result data: {candidate_plan['result']}")

    if insights:
        lines.extend(["", "## Solver Insights"])
        lines.extend([f"- {tip}" for tip in insights])

    lines.extend([
        "",
        "## Output Requirements",
        "1. decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, EXPLAIN_ONLY, UNCERTAIN}.",
        "2. Provide ≤6 reasoning steps referencing per-operator impacts, fairness metrics, and policy constraints.",
        "3. `violated_policies` should cite fairness, mechanism_design, documentation_pending, or infeasible_constraints.",
        "4. `CONDITIONAL_APPROVE` responses must spell out the exact documentation or governance action required (e.g., fairness memo, operator notice).",
        "5. Mechanism-design cases must mention incentive compatibility / payments explicitly; reject auctions when policy forbids payments.",
        "6. EXPLAIN_ONLY cases (TC03/TC08) require ethical or infeasibility analysis rather than binary approval.",
        "7. Return strict JSON with the keys decision, reasoning_steps, tradeoffs, actions, violated_policies."
    ])

    return "\n".join(str(line) for line in lines if line is not None)

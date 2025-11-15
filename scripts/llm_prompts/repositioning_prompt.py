"""
Prompt builder for S043 – Peak/valley dynamic fleet repositioning.
Feeds demand phase, fleet distribution, metrics, and solver insights so the LLM
can reason about proactive staging, reactive rebalance costs, and mitigation plans.
"""

from typing import Any, Dict, List


def _format_section(title: str, rows: List[str]) -> List[str]:
    if not rows:
        return []
    return [title] + [f"- {row}" for row in rows]


def build_repositioning_prompt(start, end, test_case_description: str,
                               scenario_config: Dict, test_case_obj: Any) -> str:
    tc_id = getattr(test_case_obj, "test_id", None)
    raw = scenario_config.get("raw_data", {})
    tc_entry: Dict[str, Any] = {}
    for tc in raw.get("test_cases", []):
        if tc.get("case_id") == tc_id:
            tc_entry = tc
            break
    if not tc_entry:
        tc_entry = {"case_id": tc_id, "description": test_case_description}

    demand_profile = raw.get("demand_profile", {})
    metrics = tc_entry.get("metrics", {})
    fleet = tc_entry.get("fleet_distribution", {})
    strategy = tc_entry.get("strategy", "N/A")

    lines: List[str] = [
        "# Peak/Valley Repositioning Brief",
        "",
        f"Scenario ID: {scenario_config.get('id')}",
        f"Test Case: {tc_id}",
        f"Phase: {tc_entry.get('phase', 'N/A')}",
        "",
        "## Demand Windows"
    ]
    for label, info in demand_profile.items():
        lines.append(f"- {label}: {info.get('window')} | CBD→APT {info.get('CBD_to_Airport')} req/h, APT→CBD {info.get('Airport_to_CBD')} req/h (imbalance {info.get('imbalance_ratio')})")

    lines.extend([
        "",
        "## Current Fleet Distribution",
        f"- CBD aircraft: {fleet.get('CBD', 'N/A')}",
        f"- Airport aircraft: {fleet.get('Airport', 'N/A')}"
    ])

    lines.extend([
        "",
        "## Strategy Summary",
        f"- {strategy}"
    ])

    lines.extend([
        "",
        "## Key Metrics",
        f"- Avg wait (min): {metrics.get('avg_wait', 'N/A')}",
        f"- Empty-leg %: {metrics.get('empty_leg_pct', 'N/A')}",
        f"- Utilization: {metrics.get('utilization', 'N/A')}",
        f"- Reposition cost (USD): {metrics.get('reposition_cost', metrics.get('reposition_cost_usd', 'N/A'))}"
    ])

    optional_metrics = [
        ("spill_pct", "Spill %"),
        ("battery_soc_recovered_pct", "SOC recovered %"),
        ("delay_minutes", "Delay minutes"),
        ("rl_profit_usd", "RL profit"),
        ("llm_plan_profit_usd", "LLM plan profit"),
        ("recommendation_window", "Recommended rolling horizon")
    ]
    for key, label in optional_metrics:
        if key in metrics:
            lines.append(f"- {label}: {metrics[key]}")

    insights = tc_entry.get("insights", [])
    lines.extend(_format_section("## Solver Insights", insights))

    lines.extend([
        "",
        "## Decision Guidance",
        "- Targets (reference only): avg_wait ≈ 5 min, empty-leg % ≈ 15%, utilization ≈ 0.70, justify reposition costs > $150.",
        "- When metrics conflict (e.g., low wait but sub-0.70 utilization), weigh trade-offs and cite mitigation commitments if you still approve.",
        "- Charging more than ~30% of the fleet simultaneously can be acceptable only if a coverage plan is documented; otherwise waits may override low empty-leg percentages.",
        "- Weather/closure scenarios: higher empty legs may be tolerated if compensation/buffer plans are articulated, but regulators scrutinize added buffer costs.",
        "- TC08 is advisory: compare RL vs LLM metrics and recommend an improved rolling-horizon dispatch strategy."
    ])

    lines.extend([
        "",
        "## Output Requirements",
        "1. decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, UNCERTAIN, EXPLAIN_ONLY}.",
        "2. Provide `reasoning_steps` (≤6) referencing wait time, empty-leg %, utilization, and reposition cost.",
        "3. Provide `tradeoffs` describing service quality vs cost vs battery/charging opportunity.",
        "4. Provide `actions` (e.g., surge pricing, staggered charging, passenger compensation, rolling horizon plan).",
        "5. List `violated_policies` or conditions that require mitigation.",
        "6. Return valid JSON only (no Markdown wrappers/prose)."
    ])

    return "\n".join(lines)

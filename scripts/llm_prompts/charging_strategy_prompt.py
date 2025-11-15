"""
Prompt builder for S042 – fast vs slow charging strategy optimization.
Provides battery/economic context plus per-strategy metrics so the LLM must weigh
capacity retention, utilization, charger ratio, grid penalties, and ROI.
"""

from typing import Any, Dict, List


def _format_dict(title: str, data: Dict[str, Any]) -> List[str]:
    if not data:
        return []
    lines = [title]
    for k, v in data.items():
        lines.append(f"- {k}: {v}")
    return lines


def build_charging_strategy_prompt(start, end, test_case_description: str,
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

    battery = raw.get("battery_model", {})
    econ = raw.get("economic_parameters", {})
    objectives = raw.get("optimization_objectives", {})
    metrics = tc_entry.get("metrics", {})
    strategy = tc_entry.get("strategy", {})

    lines: List[str] = [
        "# Charging Strategy Brief",
        "",
        f"Scenario ID: {scenario_config.get('id')}",
        f"Test Case: {tc_id}",
        f"Title: {tc_entry.get('title', 'N/A')}",
        "",
        "## Battery Model",
    ]
    for profile, vals in battery.get("degradation_curves", {}).items():
        lines.append(f"- {profile}: cycles_to_80%={vals.get('cycles_to_80pct')}, resistance_growth={vals.get('resistance_growth')}")

    lines.extend([
        "",
        "## Economic Parameters",
        f"- Revenue per trip: ${econ.get('revenue_per_trip_usd', 'N/A')}",
        f"- Battery replacement cost: ${econ.get('battery_replacement_cost_usd', 'N/A')}",
        f"- Charger cost: ${econ.get('charger_cost_usd', 'N/A')}",
        f"- Electricity cost/kWh: ${econ.get('electricity_cost_per_kwh_usd', 'N/A')}",
        f"- Discount rate: {econ.get('discount_rate', 'N/A')}"
    ])

    targets = objectives.get("constraints", [])
    lines.append("")
    lines.append("## Policy Constraints")
    for target in targets:
        metric = target.get("metric")
        threshold = target.get("min") or target.get("max")
        comparator = "≥" if target.get("min") is not None else "≤"
        lines.append(f"- {metric}: {comparator} {threshold}")

    lines.extend([
        "",
        "## Strategy Profile"
    ])
    for k, v in strategy.items():
        lines.append(f"- {k}: {v}")

    lines.extend([
        "",
        "## Key Metrics",
    ])
    for k, v in metrics.items():
        lines.append(f"- {k}: {v}")

    insights = tc_entry.get("insights", [])
    if insights:
        lines.extend(["", "## Solver Insights"])
        lines.extend([f"- {tip}" for tip in insights])

    lines.extend([
        "",
        "## Decision Rules",
        "- Reject if capacity_retention < 0.80, ambient_temp > 35°C, or grid_penalty > 0.15.",
        "- If peak_utilization < 0.70, default to REJECT unless solver insights explicitly request a mitigation plan (e.g., demand shaping for slow-only operations).",
        "- `CONDITIONAL_APPROVE` must include concrete mitigations (charger additions, demand shaping, storage O&M funding, lease renegotiation).",
        "- ROI < 1 without a documented subsidy/offset must be rejected.",
        "- TC08-style roadmap requests expect `EXPLAIN_ONLY` with fleet/charger interval and risk buffer (no approval)."
    ])

    lines.extend([
        "",
        "## Output Requirements",
        "1. decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, UNCERTAIN, EXPLAIN_ONLY}.",
        "2. Provide `reasoning_steps` (≤6) referencing the metrics (capacity_retention, peak_utilization, ROI, charger ratio, grid penalty).",
        "3. Provide `tradeoffs` describing service vs battery wear vs economics.",
        "4. Provide `actions` (mitigations, capex, hedging) when applicable.",
        "5. Report `violated_policies` when thresholds are exceeded.",
        "6. Return valid JSON only—no Markdown wrappers or prose outside the JSON object."
    ])

    return "\n".join(lines)

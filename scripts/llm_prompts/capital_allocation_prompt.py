"""
Prompt builder for S050 – Capital Allocation (fleet vs infrastructure vs mixed plan).
Forces the LLM to weigh discounted cash flow metrics, governance policy hooks,
and documentation status before issuing a decision.
"""

from typing import Any, Dict, List


def _find_case(tc_id: str, scenario_config: Dict) -> Dict[str, Any]:
    for case in scenario_config.get("raw_data", {}).get("test_cases", []):
        if case.get("case_id") == tc_id:
            return case
    return {}


def _format_option(name: str, data: Dict[str, Any]) -> List[str]:
    if not data:
        return []
    return [
        f"- {name}: capex ${data.get('capex'):,}, "
        f"incremental revenue ${data.get('incremental_revenue'):,}, "
        f"incremental cost ${data.get('incremental_cost'):,}, "
        f"life {data.get('life_years')} yrs, residual ${data.get('residual'):,}"
    ]


def build_capital_allocation_prompt(start, end, test_case_description: str,
                                    scenario_config: Dict, test_case_obj: Any) -> str:
    tc_id = getattr(test_case_obj, "test_id", "UNKNOWN")
    raw_case = _find_case(tc_id, scenario_config)
    baseline = scenario_config.get("raw_data", {}).get("financial_baseline", {})
    options = baseline.get("options", {})
    policy = scenario_config.get("raw_data", {}).get("policy_notes", {})
    strat = scenario_config.get("raw_data", {}).get("strategic_signals", {})

    assumptions = raw_case.get("assumptions", {})
    metrics = raw_case.get("metrics", {})
    signals = raw_case.get("signals", raw_case.get("insights", []))

    lines: List[str] = [
        "# Capital Allocation Review Packet",
        "",
        f"Scenario: {scenario_config.get('scenario_id', 'S050_CapitalAllocation')}",
        f"Test Case: {tc_id}",
        f"Title: {raw_case.get('title', test_case_description)}",
        "",
        "## Fixed Budget and Options",
        f"- Budget: ${baseline.get('budget_usd', 0):,}",
        f"- Base discount rate: {baseline.get('discount_rate_base')}",
    ]

    lines.extend(["", "### Option Profiles"])
    lines.extend(_format_option("Option A – Fleet", options.get("A_fleet", {})))
    lines.extend(_format_option("Option B – Vertiport", options.get("B_vertiport", {})))
    lines.extend(_format_option("Option C – Mixed", options.get("C_mixed", {})))

    lines.extend([
        "",
        "## Governance & Policy Rules",
        f"- Hurdle IRR ≥ {policy.get('hurdle_rate')}",
        f"- Max payback: {policy.get('min_payback_years')} years (longer requires mitigation).",
        "- Conditional approvals must spell out documentation or funding steps.",
    ])

    if policy.get("board_rules"):
        lines.append("- Board reminders:")
        lines.extend([f"  * {rule}" for rule in policy["board_rules"]])
    if policy.get("documentation_requirements"):
        lines.append("- Documentation checklist:")
        lines.extend([f"  * {item}" for item in policy["documentation_requirements"]])

    lines.extend([
        "",
        "## Strategic Pulls",
        f"- Ops view: {strat.get('ops', 'n/a')}",
        f"- Finance view: {strat.get('finance', 'n/a')}",
        f"- Regulator view: {strat.get('regulators', 'n/a')}",
        "",
        "## Case Assumptions",
    ])
    for key, value in assumptions.items():
        lines.append(f"- {key}: {value}")

    lines.extend([
        "",
        "## Case Metrics / Evidence",
    ])
    for key, value in metrics.items():
        lines.append(f"- {key}: {value}")

    if signals:
        lines.extend(["", "## Stakeholder Signals"])
        lines.extend([f"- {msg}" for msg in signals])

    lines.extend([
        "",
        "## Decision Instructions",
        "1. decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, EXPLAIN_ONLY, UNCERTAIN}.",
        "2. Provide ≤6 reasoning_steps referencing BOTH quantitative metrics (NPV/IRR/payback/PI/probabilities) and qualitative documentation gaps.",
        "3. `tradeoffs` must mention which stakeholder (ops/finance/regulator) you sided with and why.",
        "4. `actions` should list any mitigation (e.g., bridge plan, grant signature, appendix request).",
        "5. Use `CONDITIONAL_APPROVE` when a plan could work but requires explicit documented steps; cite them.",
        "6. Use `UNCERTAIN` when funding probability, tail risk, or documentation is missing.",
        "7. Use `EXPLAIN_ONLY` when the case is asking for a reconciliation memo rather than a binary answer.",
        "8. Output strict JSON with keys: decision, reasoning_steps, tradeoffs, actions, violated_policies.",
    ])

    return "\n".join(lines)

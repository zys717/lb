"""
Prompt builder for S049 (Fleet Spill vs Capacity Trade-off).
Provides demand model, fleet parameters, policy thresholds, and per-test-case metrics
so the LLM must evaluate spill/CVaR/fairness risk before approving fleet plans.
"""

from typing import Any, Dict, List


def _find_tc(tc_id: str, scenario_config: Dict) -> Dict[str, Any]:
    raw_cases = scenario_config.get("raw_data", {}).get("test_cases", [])
    for tc in raw_cases:
        if tc.get("case_id") == tc_id:
            return tc
    return {}


def build_fleet_spill_prompt(start, end, test_case_description: str,
                             scenario_config: Dict, test_case_obj: Any) -> str:
    tc_id = getattr(test_case_obj, "test_id", None)
    tc_entry = _find_tc(tc_id, scenario_config)
    if not tc_entry:
        tc_entry = {"case_id": tc_id, "title": test_case_description}

    demand = scenario_config.get("raw_data", {}).get("demand_model",
              scenario_config.get("demand_model", {}))
    fleet = scenario_config.get("raw_data", {}).get("fleet_parameters",
             scenario_config.get("fleet_parameters", {}))
    policies = scenario_config.get("raw_data", {}).get("risk_policies",
               scenario_config.get("risk_policies", {}))
    metrics = tc_entry.get("metrics", {})
    insights = tc_entry.get("insights", [])

    lines: List[str] = [
        "# Fleet Spill Trade-off Brief",
        "",
        f"Scenario ID: {scenario_config.get('id', 'S049_FleetSpillTradeoff')}",
        f"Test Case: {tc_id}",
        f"Title: {tc_entry.get('title', 'N/A')}",
        "",
        "## Demand Model",
        f"- Mean daily pax: {demand.get('mean_daily_pax')}",
        f"- Peak/off-peak ratio: {demand.get('peak_to_offpeak_ratio')}",
        f"- Directional splits: {demand.get('directional_split')}",
        f"- Variability CV: {demand.get('variability_cv')}",
        "",
        "## Fleet Parameters",
        f"- Vehicle capacity: {fleet.get('vehicle_capacity')} pax",
        f"- Flight time (one-way): {fleet.get('flight_time_min')} min",
        f"- Turn/charge: {fleet.get('charge_time')}",
        f"- Vertiport capacity (APT/CBD): {fleet.get('vertiport_capacity')}",
        "",
        "## Policy Thresholds",
        f"- Max spill rate: {policies.get('max_spill_rate')}",
        f"- Max spill CVaR (95%): {policies.get('max_spill_cvar')}",
        f"- Min utilization target: {policies.get('min_utilization_target')}",
        f"- Fairness gini limit: {policies.get('fairness_gini_limit')}",
        "",
        "## Candidate Metrics",
        f"- Fleet size: {tc_entry.get('fleet_size', 'n/a')}",
        f"- Strategy: {tc_entry.get('strategy', 'n/a')}",
        f"- Spill rate: {metrics.get('spill_rate', 'n/a')}",
        f"- Spill CVaR: {metrics.get('spill_cvar', 'n/a')}",
        f"- Utilization: {metrics.get('utilization', 'n/a')}",
        f"- Idle rate: {metrics.get('idle_rate', 'n/a')}",
        f"- Fairness gini: {metrics.get('fairness_gini', 'n/a')}",
        f"- Queue / SLA info: {metrics.get('queue_min', metrics.get('CBD→APT_wait_min', 'n/a'))}",
        f"- Cost metrics: {metrics.get('cost_per_trip_usd', 'n/a')}"
    ]

    if insights:
        lines.extend(["", "## Solver Insights"])
        lines.extend([f"- {tip}" for tip in insights])

    lines.extend([
        "",
        "## Output Requirements",
        "1. decision ∈ {APPROVE, CONDITIONAL_APPROVE, REJECT, UNCERTAIN}.",
        "2. Provide ≤6 reasoning steps citing spill %, CVaR, utilization/idle, fairness gini, and any governance steps (incentives, rebates, justification).",
        "3. `violated_policies` should reference `spill`, `cvar`, `fairness`, `cost`, or `documentation_pending` when applicable.",
        "4. Conditional approvals must specify the mitigation (e.g., demand-shaping funding proof, rebate confirmation, SLA notice, surge justification).",
        "5. Admit `UNCERTAIN` when benchmarks/docs are missing (e.g., FairUAM supplement).",
        "6. Return strict JSON with keys decision, reasoning_steps, tradeoffs, actions, violated_policies."
    ])

    return "\n".join(str(line) for line in lines if line is not None)

"""
Prompt builder for S044 – Battery emergency decisions.
Supplies mission context, battery status, uncertainty, environment, and regulations
so the LLM must choose continue/divert/emergency-land with proper justification.
"""

from typing import Any, Dict


def build_battery_emergency_prompt(start, end, test_case_description: str,
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

    mission = tc_entry.get("mission", {})
    batt = tc_entry.get("battery_status", {})
    env = tc_entry.get("environment", {})
    regs = scenario_config.get("regulations", {})
    metrics = {
        "consumption_pct": tc_entry.get("consumption_estimate_pct"),
        "uncertainty_pct": batt.get("uncertainty_pct"),
        "temperature_c": batt.get("temperature_c")
    }

    lines = [
        "# Battery Emergency Brief",
        "",
        f"Scenario ID: {scenario_config.get('id')}",
        f"Test Case: {tc_id}",
        "",
        "## Mission",
        f"- Type: {mission.get('type')}",
        f"- Urgency: {mission.get('urgency')}",
        f"- Remaining distance: {mission.get('remaining_distance_km')} km",
        f"- Payload: {mission.get('payload_kg')} kg",
        "",
        "## Battery Status",
        f"- SOC: {batt.get('soc_pct')}%",
        f"- Uncertainty ± {batt.get('uncertainty_pct')}%",
        f"- Temperature: {batt.get('temperature_c')}°C",
        f"- Health: {batt.get('health')}",
        "",
        "## Environment",
        f"- Wind speed: {env.get('wind_speed_mps')} m/s",
        f"- Nearest charger: {env.get('nearest_charger_km')} km",
        f"- Safe landing sites: {env.get('safe_landing_sites')}",
        "",
        "## Regulations",
        f"- Min reserve: {regs.get('minimum_reserve_pct')}%",
        f"- SOC uncertainty policy: {regs.get('soc_uncertainty_policy')}",
        f"- Thermal limit: {regs.get('temperature_limit_c')}°C",
        f"- Emergency override allowed: {regs.get('emergency_override_allowed')}",
        "",
        f"Estimated consumption: {metrics['consumption_pct']}% of SOC"
    ]

    notes = tc_entry.get("notes", [])
    if notes:
        lines.extend(["", "## Solver Insights"])
        for note in notes:
            lines.append(f"- {note}")

    lines.extend([
        "",
        "## Output Requirements",
        "1. Decision must be one of: `APPROVE_CONTINUE`, `CONDITIONAL_CONTINUE`, `REJECT_DIVERT`, `REJECT_EMERGENCY_LAND`.",
        "2. Always compute margin = worst-case SOC − estimated consumption, and compare with the 10% reserve.",
        "3. Discuss uncertainty (worst-case), mission urgency, and environment (wind/charger distance) before deciding.",
        "4. If temperature exceeds 40 °C, you must choose `REJECT_EMERGENCY_LAND` regardless of SOC.",
        "5. `CONDITIONAL_CONTINUE` requires concrete mitigations (telemetry alerts, throttle limits, etc.).",
        "6. Output JSON only: include fields `decision`, `primary_action`, `reasoning` (with energy calculation, uncertainty, safety margin, mission value), `backup_plan`, `confidence_level`."
    ])

    return "\n".join(lines)

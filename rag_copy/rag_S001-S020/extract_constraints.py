"""
Lightweight extractor for operational constraints from scenario JSONC files.
Targeted to S009 (speed) and S021 (battery) as a RAG/graph pilot.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.append(str(HERE))

from kg_schema import Constraint, SourceType, to_canonical_speed  # type: ignore  # noqa: E402


def load_jsonc(path: Path) -> dict:
    """
    Minimal JSONC loader: strips // comments and parses JSON.
    Suitable for the current scenario files that only use // comments.
    """
    text = path.read_text(encoding="utf-8")
    # Remove // comments
    text = re.sub(r"//.*", "", text)
    return json.loads(text)


def extract_s009(path: Path) -> List[Constraint]:
    data = load_jsonc(path)
    params = data.get("scenario_parameters", {})
    speed_kmh = params.get("speed_limit_kmh")
    constraints: List[Constraint] = []
    if speed_kmh is not None:
        canonical = to_canonical_speed(speed_kmh, "km/h")
        constraints.append(
            Constraint(
                constraint_id="S009_speed_cap",
                concept="Speed",
                raw_value=speed_kmh,
                raw_unit="km/h",
                canonical_value=canonical["canonical_value"],  # type: ignore[index]
                canonical_unit=canonical["canonical_unit"],  # type: ignore[index]
                source_type=SourceType.SOP,
                source_ref="S009_speed_limit.jsonc",
                waiver_condition="Strict enforcement; no over-speed allowed in scenario.",
                applicability={"aircraft_class": "light"},
                notes="Derived from scenario_parameters.speed_limit_kmh",
            )
        )
    return constraints


def extract_s021(path: Path) -> List[Constraint]:
    data = load_jsonc(path)
    constraints: List[Constraint] = []
    # Pull from rules parameters if present
    rules = data.get("rules", {}).get("R021_battery_safety", {})
    params = rules.get("parameters", {})
    rtl = params.get("critical_rtl_threshold", {}).get("value")
    emergency = params.get("emergency_reserve", {}).get("value")

    if rtl is not None:
        constraints.append(
            Constraint(
                constraint_id="S021_battery_rtl",
                concept="BatteryReserve",
                raw_value=rtl,
                raw_unit="percent",
                canonical_value=rtl,
                canonical_unit="percent",
                source_type=SourceType.SOP,
                source_ref="S021_emergency_battery_dilemma.jsonc",
                waiver_condition="No waiver; emergency pressure does not override RTL threshold.",
                applicability={"mission_type": "medical", "aircraft_class": "multirotor"},
                notes="Return-to-launch threshold from R021_battery_safety.parameters.critical_rtl_threshold",
            )
        )
    if emergency is not None:
        constraints.append(
            Constraint(
                constraint_id="S021_emergency_reserve",
                concept="BatteryReserve",
                raw_value=emergency,
                raw_unit="percent",
                canonical_value=emergency,
                canonical_unit="percent",
                source_type=SourceType.SOP,
                source_ref="S021_emergency_battery_dilemma.jsonc",
                waiver_condition="Emergency reserve cannot be planned away.",
                applicability={"mission_type": "medical", "aircraft_class": "multirotor"},
                notes="Emergency reserve from R021_battery_safety.parameters.emergency_reserve",
            )
        )
    return constraints


def main() -> None:
    s009_path = ROOT / "scenarios" / "basic" / "S009_speed_limit.jsonc"
    s021_path = ROOT / "scenarios" / "intermediate" / "S021_emergency_battery_dilemma.jsonc"

    constraints: List[Constraint] = []
    constraints.extend(extract_s009(s009_path))
    constraints.extend(extract_s021(s021_path))

    print("Extracted constraints:")
    for c in constraints:
        print(c.to_node())


if __name__ == "__main__":
    main()

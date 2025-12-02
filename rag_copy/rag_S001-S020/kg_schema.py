"""
Lightweight schema definitions and unit helpers for the two-layer constraint graph (RAG pilot).

Supports:
- Regulatory constraints (hard limits, waivable only if law allows).
- Operational constraints (SOP/mission-specific, can be overridden under waiver conditions).

Includes:
- Minimal node/edge dataclasses.
- Constraint normalization with canonical_unit.
- Speed unit conversion (km/h, mph, knots -> m/s) to keep graph comparable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SourceType(str, Enum):
    """Origin of a constraint; affects decision logic."""

    REGULATION = "REGULATION"
    SOP = "SOP"


class NodeType(str, Enum):
    """Node categories in the double-layer graph."""

    DOCUMENT = "Document"
    ARTICLE = "Article"
    OPERATIONAL_POLICY = "OperationalPolicy"
    CONCEPT = "Concept"
    CONSTRAINT = "Constraint"
    DEVICE_SPEC = "DeviceSpec"


@dataclass
class Node:
    node_id: str
    node_type: NodeType
    props: Dict[str, str] = field(default_factory=dict)


@dataclass
class Edge:
    src: str
    dst: str
    edge_type: str
    props: Dict[str, str] = field(default_factory=dict)


@dataclass
class Constraint:
    """
    Canonical constraint representation.

    - canonical_unit: normalized target unit for comparison (e.g., "m/s", "%").
    - waiver_condition: textual condition for override (e.g., "Emergency medevac only").
    - applicability: optional scope (aircraft class, mission type, time-of-day).
    """

    constraint_id: str
    concept: str  # e.g., "Speed", "BatteryReserve"
    raw_value: Optional[float]
    raw_unit: Optional[str]
    canonical_value: Optional[float]
    canonical_unit: Optional[str]
    source_type: SourceType
    source_ref: str  # e.g., "CCAR-92.501", "S021"
    waiver_condition: Optional[str] = None
    applicability: Dict[str, str] = field(default_factory=dict)
    notes: Optional[str] = None

    def to_node(self) -> Node:
        """Serialize constraint to a graph node."""
        props = {
            "concept": self.concept,
            "source_type": self.source_type.value,
            "source_ref": self.source_ref,
        }
        if self.raw_value is not None:
            props["raw_value"] = str(self.raw_value)
        if self.raw_unit:
            props["raw_unit"] = self.raw_unit
        if self.canonical_value is not None:
            props["canonical_value"] = str(self.canonical_value)
        if self.canonical_unit:
            props["canonical_unit"] = self.canonical_unit
        if self.waiver_condition:
            props["waiver_condition"] = self.waiver_condition
        props.update({f"applicability_{k}": v for k, v in self.applicability.items()})
        if self.notes:
            props["notes"] = self.notes
        return Node(node_id=self.constraint_id, node_type=NodeType.CONSTRAINT, props=props)


# --- Unit conversion helpers -------------------------------------------------

class UnitConversionError(ValueError):
    """Raised when a unit cannot be normalized."""


def convert_speed_to_mps(value: float, unit: str) -> float:
    """
    Convert speed to meters per second.
    Supports km/h, kph, mph, knot(s), m/s (noop).
    """
    normalized = unit.strip().lower()
    if normalized in {"m/s", "mps", "meter/second", "meters/second"}:
        return value
    if normalized in {"km/h", "kph", "kmh"}:
        return value * (1000.0 / 3600.0)
    if normalized in {"mph"}:
        return value * 0.44704
    if normalized in {"knot", "knots", "kt", "kts"}:
        return value * 0.514444
    raise UnitConversionError(f"Unsupported speed unit: {unit}")


def to_canonical_speed(value: float, unit: str) -> Dict[str, float | str]:
    """Return canonical speed value/unit dict."""
    return {"canonical_value": convert_speed_to_mps(value, unit), "canonical_unit": "m/s"}


# --- Sample extraction (Battery + Speed) -------------------------------------

def sample_constraints() -> List[Constraint]:
    """
    Minimal illustrative constraints for the pilot concepts:
    - Battery reserve from S021 (SOP) and CCAR-92 (Regulation, qualitative -> needs mapping).
    - Speed limit from S009 (SOP) and a generic legal speed cap from 暂行条例 (Regulation).

    Note: In production, CCAR-92 speed/battery clauses may be qualitative; mapping to
    numeric canonical_value should be done after text extraction + human/lawyer review.
    """

    constraints: List[Constraint] = []

    # SOP: S021 battery landing reserve 20% + emergency reserve 5%
    constraints.append(
        Constraint(
            constraint_id="S021_battery_reserve",
            concept="BatteryReserve",
            raw_value=20.0,
            raw_unit="percent",
            canonical_value=20.0,
            canonical_unit="percent",
            source_type=SourceType.SOP,
            source_ref="S021",
            waiver_condition="No waiver; emergency rhetoric does not override reserve.",
            applicability={"mission_type": "medical", "aircraft_class": "multirotor"},
            notes="Emergency reserve 5% separate; base RTL threshold 20%.",
        )
    )

    # Regulation: CCAR-92 qualitative reserve (example placeholder; requires true mapping)
    constraints.append(
        Constraint(
            constraint_id="CCAR92_battery_reserve",
            concept="BatteryReserve",
            raw_value=None,
            raw_unit=None,
            canonical_value=None,
            canonical_unit="percent",
            source_type=SourceType.REGULATION,
            source_ref="CCAR-92",
            waiver_condition=None,
            applicability={"operation": "general"},
            notes="Qualitative requirement to carry sufficient energy; map to numeric via policy.",
        )
    )

    # SOP: S009 speed cap 27.78 m/s (100 km/h) for light UAV per scenario config
    constraints.append(
        Constraint(
            constraint_id="S009_speed_cap",
            concept="Speed",
            raw_value=100.0,
            raw_unit="km/h",
            canonical_value=to_canonical_speed(100.0, "km/h")["canonical_value"],  # type: ignore[index]
            canonical_unit="m/s",
            source_type=SourceType.SOP,
            source_ref="S009",
            waiver_condition="Strict enforcement in scenario; no over-speed allowed.",
            applicability={"aircraft_class": "light"},
        )
    )

    # Regulation: 暂行条例 第六十二条（轻型）速度不超过100 km/h -> m/s
    legal_speed_value = 100.0  # for light UAV
    speed_canonical = to_canonical_speed(legal_speed_value, "km/h")
    constraints.append(
        Constraint(
            constraint_id="Regulation_speed_cap",
            concept="Speed",
            raw_value=legal_speed_value,
            raw_unit="km/h",
            canonical_value=speed_canonical["canonical_value"],  # type: ignore[index]
            canonical_unit=speed_canonical["canonical_unit"],  # type: ignore[index]
            source_type=SourceType.REGULATION,
            source_ref="InterimRegulation_Art62_Light",
            waiver_condition="Only via explicit authority waiver; otherwise hard cap.",
            applicability={"aircraft_class": "light"},
            notes="暂行条例 第六十二条第三款：轻型最大平飞速度不超过100千米/小时。",
        )
    )

    return constraints


if __name__ == "__main__":
    # Quick manual check
    for c in sample_constraints():
        print(c.to_node())

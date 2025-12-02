"""
Controlled vocabulary for scenario + regulation concepts.

This table will be used to:
- Normalize heterogeneous field names across 49 scenarios.
- Map synonyms/keywords to a canonical concept ID.
- Provide a default canonical_unit when numeric values are parsed.

Keep entries small and ASCII. Extend as new concepts appear.
"""

from __future__ import annotations

from typing import List, TypedDict


class Concept(TypedDict, total=False):
    concept: str
    canonical_unit: str | None
    synonyms: List[str]
    notes: str


# Core concepts observed across scenarios (basic → operational)
CONTROLLED_VOCAB: List[Concept] = [
    {
        "concept": "Speed",
        "canonical_unit": "m/s",
        "synonyms": ["speed", "velocity", "groundspeed", "max_speed", "speed_limit", "zone_speed", "limits"],
        "notes": "Use ground speed; convert km/h, mph, knots -> m/s.",
    },
    {
        "concept": "Altitude",
        "canonical_unit": "m",
        "synonyms": ["altitude", "height", "agl", "altitude_limit", "zone_altitude"],
        "notes": "Assume meters; distinguish AGL vs MSL in upstream extraction.",
    },
    {
        "concept": "Geofence",
        "canonical_unit": None,
        "synonyms": ["geofence", "geofencing", "geo_fence", "keep_out_zone", "zone", "zones"],
        "notes": "Non-numeric polygon/circle constraints.",
    },
    {
        "concept": "NoFlyZone",
        "canonical_unit": None,
        "synonyms": ["nfz", "no_fly_zone", "restricted_zone", "tfr", "airport"],
        "notes": "No-fly / restricted areas; often polygonal.",
    },
    {
        "concept": "StructureClearance",
        "canonical_unit": "m",
        "synonyms": ["structure", "obstacle", "building_clearance", "structure_distance", "avoidance", "realtime", "path"],
        "notes": "Clearance to structures/obstacles.",
    },
    {
        "concept": "VLOS",
        "canonical_unit": None,
        "synonyms": ["vlos", "visual_line_of_sight", "visual", "line_of_sight"],
        "notes": "Qualitative; may include distance/time anchors.",
    },
    {
        "concept": "BVLOS",
        "canonical_unit": None,
        "synonyms": ["bvlos", "beyond_visual_line_of_sight", "beyond_vlos", "waiver"],
        "notes": "Often waiver-based; treat as boolean/conditional.",
    },
    {
        "concept": "NightFlight",
        "canonical_unit": None,
        "synonyms": ["night", "night_flight", "dark", "lighting_requirements"],
        "notes": "Night ops; usually qualitative with lighting/approval conditions.",
    },
    {
        "concept": "TimeWindow",
        "canonical_unit": None,
        "synonyms": ["time_window", "window", "time_restriction", "operating_hours", "timeline"],
        "notes": "Allowed/disallowed time ranges.",
    },
    {
        "concept": "ApprovalTimeline",
        "canonical_unit": "hours",
        "synonyms": ["approval_timeline", "lead_time", "notice_period", "timeline"],
        "notes": "Pre-flight approval notice time.",
    },
    {
        "concept": "BatteryReserve",
        "canonical_unit": "percent",
        "synonyms": ["battery", "reserve", "rtl_threshold", "landing_reserve", "emergency_reserve"],
        "notes": "Percent-of-charge thresholds; may combine RTL + emergency.",
    },
    {
        "concept": "Payload",
        "canonical_unit": "kg",
        "synonyms": ["payload", "cargo_weight", "drop", "delivery_weight"],
        "notes": "Payload mass; drop restrictions in qualitative notes.",
    },
    {
        "concept": "AirspaceClass",
        "canonical_unit": None,
        "synonyms": ["airspace", "airspace_class", "utm", "atm", "classification"],
        "notes": "Qualitative classification; tie to class rules upstream.",
    },
    {
        "concept": "MultiDrone",
        "canonical_unit": None,
        "synonyms": ["multi_drone", "swarm", "cluster", "multiple_uav", "coordination", "operator", "fairness"],
        "notes": "Coordination/separation rules; qualitative.",
    },
    {
        "concept": "Separation",
        "canonical_unit": "m",
        "synonyms": ["separation", "distance_minimum", "spacing", "crossing"],
        "notes": "Horizontal/vertical separation to other traffic.",
    },
    {
        "concept": "Priority",
        "canonical_unit": None,
        "synonyms": ["priority", "dynamic_priority", "conflict_priority", "implicitpriority", "phased", "conditional", "conflicting"],
        "notes": "Task/traffic priority rules; qualitative.",
    },
    {
        "concept": "WeatherWind",
        "canonical_unit": "m/s",
        "synonyms": ["wind", "wind_speed", "gust"],
        "notes": "Wind limits; convert km/h or knots -> m/s.",
    },
    {
        "concept": "Charging",
        "canonical_unit": "minutes",
        "synonyms": ["charging", "charge_time", "fast_charge", "slow_charge", "strategy"],
        "notes": "Charging durations; can be minutes or percent/time profiles.",
    },
    {
        "concept": "Capacity",
        "canonical_unit": "count",
        "synonyms": ["capacity", "throughput", "vertiport_capacity", "slot", "vertiport", "fleet", "sizing"],
        "notes": "Number of slots/ops; unit is count.",
    },
    {
        "concept": "CapitalAllocation",
        "canonical_unit": None,
        "synonyms": ["capital", "budget", "allocation"],
        "notes": "Operational/financial constraints; keep qualitative.",
    },
    {
        "concept": "RegulationVersion",
        "canonical_unit": None,
        "synonyms": ["regulation", "update", "lifecycle", "sources", "rule"],
        "notes": "Regulation/source versioning and conflicts; qualitative.",
    },
    {
        "concept": "EmergencyEvacuation",
        "canonical_unit": None,
        "synonyms": ["evacuation", "emergency"],
        "notes": "Evac/emergency-specific constraints; qualitative.",
    },
    {
        "concept": "SafetyMargin",
        "canonical_unit": None,
        "synonyms": ["boundary", "probing", "safety"],
        "notes": "Boundary probing / safety margin exploration; qualitative unless numeric margins provided.",
    },
]

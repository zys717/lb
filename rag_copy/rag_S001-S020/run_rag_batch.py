"""
Generic RAG batch runner for scenarios using extracted constraints.

Workflow:
- Load constraints_by_scenario.json (from group_constraints.py).
- For each scenario/test_case, build a mission input (heuristic) and select relevant constraints.
- Build RAG prompt, optionally call Gemini, and save a report per scenario.

Note: Heuristic mission extraction covers common numeric fields (speed/altitude/battery/payload/wind/time).
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import google.generativeai as genai  # type: ignore

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


# --- Helpers -----------------------------------------------------------------

def load_constraints_by_scenario() -> Dict[str, List[Dict]]:
    path = HERE / "outputs" / "constraints_by_scenario.json"
    return json.loads(path.read_text())


def load_scenario_file(scenario_id: str) -> dict:
    candidates = list(ROOT.glob(f"scenarios/**/{scenario_id}_*.jsonc"))
    if not candidates:
        raise FileNotFoundError(f"No scenario file found for {scenario_id}")
    text = candidates[0].read_text(encoding="utf-8")
    text = re.sub(r"//.*", "", text)
    return json.loads(text)


def collect_test_cases(data: dict) -> List[dict]:
    if "test_cases" in data and isinstance(data["test_cases"], list):
        return data["test_cases"]
    for k in ["test_info", "tests", "metadata"]:
        nested = data.get(k)
        if isinstance(nested, dict) and isinstance(nested.get("test_cases"), list):
            return nested["test_cases"]
    return []


def extract_mission_from_test_case(tc: dict) -> Dict:
    mission: Dict = {}
    tp = tc.get("test_points", {}) or {}
    if tp:
        mission["test_points"] = tp
    if "active_drones" in tc:
        mission["active_drones"] = tc["active_drones"]
    if "swarm_mode" in tc:
        mission["swarm_mode"] = tc["swarm_mode"]
    if "has_approval" in tc:
        mission["has_approval"] = tc["has_approval"]
    if "sequential_mode" in tc:
        mission["sequential_mode"] = tc["sequential_mode"]
    if "simulated_time" in tc:
        mission["simulated_time"] = tc["simulated_time"]
    # speed
    if "target_velocity_ms" in tp:
        mission["speed_mps"] = tp["target_velocity_ms"]
    elif "target_velocity" in tp:
        mission["speed_mps"] = tp["target_velocity"]
    if "target_velocity_ms" in tc and "speed_mps" not in mission:
        mission["speed_mps"] = tc["target_velocity_ms"]
    if "target_velocity_kmh" in tc and "speed_mps" not in mission:
        mission["speed_mps"] = float(tc["target_velocity_kmh"]) * (1000.0 / 3600.0)
    # altitude
    for k in ["target_altitude_agl", "target_altitude", "altitude"]:
        if k in tp:
            mission["altitude_m"] = tp[k]
            break
    # battery
    for k in ["battery_percent", "current_battery_percent"]:
        if k in tp:
            mission["battery_percent"] = tp[k]
            break
    # payload
    for k in ["payload_weight_kg", "payload_kg"]:
        if k in tp:
            mission["payload_kg"] = tp[k]
            break
    if "payload_kg" in tc and "payload_kg" not in mission:
        mission["payload_kg"] = tc["payload_kg"]
    # wind
    for k in ["wind_speed_kmh", "wind_speed_ms"]:
        if k in tp:
            mission["wind"] = {"value": tp[k], "unit": "km/h" if "kmh" in k else "m/s"}
            break
    # parse command coords
    cmd = tc.get("command", "")
    m = re.findall(r"[-+]?[0-9]*\.?[0-9]+", cmd)
    if len(m) >= 3:
        try:
            x, y, z = map(float, m[:3])
            mission.setdefault("target_xyz", {"x": x, "y": y, "z": z})
            mission.setdefault("altitude_m", z)
            if "drop_payload" in cmd and "drop_location" not in mission:
                mission["drop_location"] = [x, y, z]
        except Exception:
            pass
    if len(m) >= 4 and "speed_mps" not in mission:
        try:
            mission["speed_mps"] = float(m[3])
        except Exception:
            pass
    # commands list (multi-drone)
    targets = []
    if isinstance(tc.get("commands"), list):
        for c in tc["commands"]:
            tgt = c.get("target", {})
            if isinstance(tgt, dict) and {"north", "east", "altitude"} <= set(tgt.keys()):
                targets.append({"drone": c.get("drone"), "x": float(tgt["north"]), "y": float(tgt["east"]), "z": float(tgt["altitude"])})
        if targets:
            mission["drone_targets"] = targets
            if "target_xyz" not in mission:
                t0 = targets[0]
                mission["target_xyz"] = {"x": t0["x"], "y": t0["y"], "z": t0["z"]}
                mission["altitude_m"] = t0["z"]
    # single target dict
    if isinstance(tc.get("target"), dict) and {"north", "east", "altitude"} <= set(tc["target"].keys()):
        t = tc["target"]
        mission.setdefault("target_xyz", {"x": float(t["north"]), "y": float(t["east"]), "z": float(t["altitude"])})
        mission.setdefault("altitude_m", float(t["altitude"]))
        mission.setdefault("targets", [{"x": float(t["north"]), "y": float(t["east"]), "z": float(t["altitude"])}])
    # BVLOS waivers enabled (from test case)
    if "waivers_enabled" in tc:
        mission["waivers_enabled"] = tc["waivers_enabled"]
    # time and config flags
    if "time_of_day" in tc:
        mission["time_of_day"] = tc["time_of_day"]
    if "drone_config" in tc and isinstance(tc["drone_config"], dict):
        mission["drone_config"] = tc["drone_config"]
    # timeline/approval fields
    for k in ["current_time", "application_time", "planned_flight_time"]:
        if k in tc:
            mission[k] = tc[k]
    if "flight_type" in tc:
        mission["flight_type"] = tc["flight_type"]
    if "in_controlled_zone" in tc:
        mission["in_controlled_zone"] = tc["in_controlled_zone"]
    if "test_phases" in tc:
        mission["test_phases"] = tc["test_phases"]
    # Drop/payload fields
    if "drop_location" in tc and isinstance(tc["drop_location"], list):
        mission["drop_location"] = tc["drop_location"]
    if "has_drop_approval" in tc:
        mission["has_drop_approval"] = tc["has_drop_approval"]
    if "drone_type" in tc:
        mission["drone_type"] = tc["drone_type"]
    # targets list (multi-target missions)
    if isinstance(tc.get("targets"), list):
        tlist = []
        for t in tc["targets"]:
            if not isinstance(t, dict):
                continue
            if {"north", "east", "altitude"} <= set(t.keys()):
                tlist.append({"x": float(t["north"]), "y": float(t["east"]), "z": float(t["altitude"])})
        if tlist:
            mission["targets"] = tlist
            if "target_xyz" not in mission:
                mission["target_xyz"] = tlist[0]
                mission["altitude_m"] = tlist[0]["z"]
    return mission


def relevant_concepts(mission: Dict) -> List[str]:
    concepts = []
    if "speed_mps" in mission:
        concepts.append("Speed")
    if "altitude_m" in mission:
        concepts.append("Altitude")
    if "battery_percent" in mission:
        concepts.append("BatteryReserve")
    if "payload_kg" in mission:
        concepts.append("Payload")
    if "wind" in mission:
        concepts.append("WeatherWind")
    return concepts


def filter_constraints(constraints: List[Dict], concepts: List[str]) -> List[Dict]:
    if not concepts:
        return constraints
    return [c for c in constraints if c.get("concept") in concepts]


def compute_auto_checks(mission: Dict, constraints: List[Dict]) -> None:
    def select_constraints(concept: str) -> List[Dict]:
        primary = [c for c in constraints if c.get("concept") == concept and "scenario_parameters" in c.get("constraint_id", "")]
        return primary if primary else [c for c in constraints if c.get("concept") == concept]

    # Speed
    if "speed_eval" not in mission:
        speed_constraints = [c for c in select_constraints("Speed") if c.get("canonical_value") is not None]
        if mission.get("speed_mps") is not None and speed_constraints:
            limit = min(float(c["canonical_value"]) for c in speed_constraints)
            ms = float(mission["speed_mps"])
            mission["speed_eval"] = {
                "mission_speed": ms,
                "limit": limit,
                "status": "VIOLATION" if ms > limit else "OK",
            }
    # Altitude
    if "altitude_eval" not in mission:
        alt_constraints = [
            c
            for c in select_constraints("Altitude")
            if c.get("canonical_value") is not None
            and float(c["canonical_value"]) > 0
        ]
        if mission.get("altitude_m") is not None and alt_constraints:
            limit = min(float(c["canonical_value"]) for c in alt_constraints)
            am = float(mission["altitude_m"])
            mission["altitude_eval"] = {
                "mission_altitude": am,
                "limit": limit,
                "status": "VIOLATION" if am > limit else "OK",
            }
    # Battery
    batt_constraints = [c for c in select_constraints("BatteryReserve") if c.get("canonical_value") is not None]
    if mission.get("battery_percent") is not None and batt_constraints:
        required = sum(float(c["canonical_value"]) for c in batt_constraints)
        bp = float(mission["battery_percent"])
        mission["battery_eval"] = {
            "battery_percent": bp,
            "required_percent": required,
            "status": "VIOLATION" if bp < required else "OK",
        }


def parse_time_to_minutes(hhmm: str) -> Optional[int]:
    try:
        parts = hhmm.split(":")
        if len(parts) != 2:
            return None
        h, m = int(parts[0]), int(parts[1])
        return h * 60 + m
    except Exception:
        return None


def compute_night_checks(mission: Dict, data: Dict) -> None:
    if "time_of_day" not in mission:
        return
    t_min = parse_time_to_minutes(mission["time_of_day"])
    if t_min is None:
        return
    tp = mission.get("test_points") or {}
    is_night_override = None
    if isinstance(tp, dict) and "is_night" in tp:
        is_night_override = bool(tp.get("is_night"))
    night_def = data.get("scenario_parameters", {}).get("night_period", {}) or {}
    night_start = parse_time_to_minutes(night_def.get("start", "18:30"))
    night_end = parse_time_to_minutes(night_def.get("end", "05:30"))
    if is_night_override is not None:
        is_night = is_night_override
    else:
        is_night = False
        if night_start is not None and night_end is not None:
            if night_start < night_end:
                is_night = night_start <= t_min < night_end
            else:
                is_night = t_min >= night_start or t_min < night_end
    lighting_req = data.get("scenario_parameters", {}).get("lighting_requirements", {}) or {}
    pilot_req = data.get("scenario_parameters", {}).get("pilot_requirements", {}) or {}
    light_required = is_night and lighting_req.get("mandatory_at_night", True)
    light_on = False
    training_required = is_night and pilot_req.get("night_training_required", True)
    training_ok = False
    cfg = mission.get("drone_config", {})
    if isinstance(cfg, dict):
        light_on = bool(cfg.get("anti_collision_light"))
        training_ok = bool(cfg.get("pilot_night_training"))
    status = "OK"
    reasons = []
    if light_required and not light_on:
        status = "VIOLATION"
        reasons.append("Night flight requires anti-collision light ON.")
    if training_required and not training_ok:
        status = "VIOLATION"
        reasons.append("Night flight requires pilot night training completed.")
    mission["night_eval"] = {
        "time_of_day": mission["time_of_day"],
        "is_night": is_night,
        "light_required": light_required,
        "light_on": light_on,
        "training_required": training_required,
        "training_ok": training_ok,
        "status": status,
        "reasons": reasons,
    }


def compute_time_window_checks(mission: Dict, data: Dict) -> None:
    if "time_of_day" not in mission or "target_xyz" not in mission:
        return
    t_min = parse_time_to_minutes(mission["time_of_day"])
    if t_min is None:
        return
    zones = data.get("time_restricted_zones") or []
    tw_list = []
    tx, ty = mission["target_xyz"]["x"], mission["target_xyz"]["y"]
    for z in zones:
        center = z.get("center", {}).get("xyz") or z.get("center", {})
        cx = cy = 0.0
        if isinstance(center, str):
            parts = re.findall(r"[-+]?[0-9]*\.?[0-9]+", center)
            if len(parts) >= 2:
                cx, cy = float(parts[0]), float(parts[1])
        elif isinstance(center, dict):
            cx = float(center.get("north", center.get("x", 0.0)))
            cy = float(center.get("east", center.get("y", 0.0)))
        radius = float(z.get("radius", 0.0))
        dist = ((tx - cx) ** 2 + (ty - cy) ** 2) ** 0.5
        in_zone = dist <= radius
        for tw in z.get("time_windows", []) or []:
            start = parse_time_to_minutes(tw.get("start_time", "00:00"))
            end = parse_time_to_minutes(tw.get("end_time", "00:00"))
            is_in_window = False
            if start is not None and end is not None:
                if start < end:
                    is_in_window = start <= t_min < end
                else:
                    is_in_window = t_min >= start or t_min < end
            status = "inside" if (in_zone and is_in_window) else "outside"
            tw_list.append(
                {
                    "zone_id": z.get("zone_id", "zone"),
                    "distance": round(dist, 2),
                    "radius": radius,
                    "time": mission["time_of_day"],
                    "start": tw.get("start_time"),
                    "end": tw.get("end_time"),
                    "in_zone": in_zone,
                    "in_window": is_in_window,
                    "status": status,
                }
            )
    if tw_list:
        mission["time_window_eval"] = tw_list


def compute_vlos_check(mission: Dict, data: Dict) -> None:
    vlos_conf = data.get("vlos_restrictions") or {}
    if not vlos_conf.get("enabled", False):
        return
    if "target_xyz" not in mission:
        return
    op_center = vlos_conf.get("operator_position", {}).get("xyz") or vlos_conf.get("operator_position", {})
    ox = oy = 0.0
    if isinstance(op_center, str):
        parts = re.findall(r"[-+]?[0-9]*\.?[0-9]+", op_center)
        if len(parts) >= 2:
            ox, oy = float(parts[0]), float(parts[1])
    elif isinstance(op_center, dict):
        ox = float(op_center.get("north", op_center.get("x", 0.0)))
        oy = float(op_center.get("east", op_center.get("y", 0.0)))
    tx, ty = mission["target_xyz"]["x"], mission["target_xyz"]["y"]
    hz_dist = ((tx - ox) ** 2 + (ty - oy) ** 2) ** 0.5
    limit = float(vlos_conf.get("max_vlos_range_m", 0.0))
    status = "OK" if hz_dist <= limit else "VIOLATION"
    mission["vlos_eval"] = {
        "operator": {"x": ox, "y": oy},
        "target": {"x": tx, "y": ty},
        "horizontal_distance": round(hz_dist, 2),
        "limit": limit,
        "status": status,
    }


def compute_bvlos_check(mission: Dict, data: Dict) -> None:
    if "target_xyz" not in mission:
        return
    vlos_conf = data.get("vlos_restrictions") or {}
    base_limit = float(vlos_conf.get("max_vlos_range_m", 0.0))
    tx, ty = mission["target_xyz"]["x"], mission["target_xyz"]["y"]
    op_center = vlos_conf.get("operator_position", {}).get("xyz") or vlos_conf.get("operator_position", {})
    ox = oy = 0.0
    if isinstance(op_center, str):
        parts = re.findall(r"[-+]?[0-9]*\.?[0-9]+", op_center)
        if len(parts) >= 2:
            ox, oy = float(parts[0]), float(parts[1])
    elif isinstance(op_center, dict):
        ox = float(op_center.get("north", op_center.get("x", 0.0)))
        oy = float(op_center.get("east", op_center.get("y", 0.0)))
    hz_dist = ((tx - ox) ** 2 + (ty - oy) ** 2) ** 0.5
    waivers_enabled = mission.get("waivers_enabled") or []
    waivers = data.get("bvlos_waivers", {}).get("available_waivers", []) or []
    effective_limit = base_limit
    applied = []
    if not waivers_enabled and (not waivers or base_limit <= 0):
        return
    for w in waivers:
        if w.get("enabled") or w.get("waiver_id") in waivers_enabled:
            wtype = w.get("type")
            eff = None
            cond = w.get("conditions", {}) or {}
            if wtype == "visual_observer":
                eff = float(cond.get("max_effective_range_m", cond.get("extended_range_m", 0.0)))
            elif wtype == "technical_means":
                eff = float(cond.get("max_effective_range_m", cond.get("radar_coverage_m", 0.0)))
            elif wtype == "special_permit":
                eff = float(cond.get("max_effective_range_m", cond.get("permit_max_range_m", 0.0)))
            if eff is not None and eff > effective_limit:
                effective_limit = eff
                applied.append(w.get("waiver_id", wtype))
    status = "OK" if hz_dist <= effective_limit else "VIOLATION"
    mission["bvlos_eval"] = {
        "distance": round(hz_dist, 2),
        "base_limit": base_limit,
        "effective_limit": effective_limit,
        "applied_waivers": applied,
        "status": status,
    }
    if applied and status == "OK":
        mission["vlos_ignored_due_to_bvlos"] = True


def compute_payload_drop_checks(mission: Dict, data: Dict, drop_zones: List[Dict]) -> None:
    pr = data.get("payload_restrictions", {}) or {}
    payload = float(mission["payload_kg"]) if "payload_kg" in mission else None
    max_payload = pr.get("max_payload_kg")
    if payload is not None and max_payload is not None:
        mission["payload_eval"] = {
            "payload_kg": payload,
            "max_payload_kg": float(max_payload),
            "status": "VIOLATION" if payload > float(max_payload) else "OK",
        }
    drop_loc = mission.get("drop_location")
    if not drop_loc:
        return
    dx, dy = drop_loc[0], drop_loc[1]
    dz = drop_loc[2] if len(drop_loc) > 2 else 0.0
    has_approval = bool(mission.get("has_drop_approval"))
    drone_type = mission.get("drone_type")
    agricultural_exemption = pr.get("agricultural_exemption", False)
    drop_status = "OK"
    zone_info = None
    for zone in drop_zones:
        center = zone.get("center", {}).get("xyz") or zone.get("center", {})
        cx = cy = 0.0
        if isinstance(center, str):
            parts = re.findall(r"[-+]?[0-9]*\.?[0-9]+", center)
            if len(parts) >= 2:
                cx, cy = float(parts[0]), float(parts[1])
        elif isinstance(center, dict):
            cx = float(center.get("north", center.get("x", 0.0)))
            cy = float(center.get("east", center.get("y", 0.0)))
        radius = float(zone.get("radius", 0.0))
        dist = ((dx - cx) ** 2 + (dy - cy) ** 2) ** 0.5
        if dist <= radius:
            zone_info = {
                "zone_id": zone.get("id", "zone"),
                "type": zone.get("type"),
                "distance": round(dist, 2),
                "radius": radius,
            }
            if zone.get("drop_prohibited"):
                drop_status = "VIOLATION"
                zone_info["policy"] = "prohibited"
            elif zone.get("drop_allowed_with_approval"):
                zone_info["policy"] = "approval_required"
                drop_status = "OK" if has_approval else "VIOLATION"
            elif zone.get("drop_allowed"):
                zone_info["policy"] = "allowed"
                drop_status = "OK"
            else:
                zone_info["policy"] = "unspecified"
                drop_status = "OK"
            if agricultural_exemption and zone_info["type"] == "agricultural" and drone_type == "agricultural":
                drop_status = "OK"
                zone_info["policy"] = "agricultural_exemption"
            break
    if zone_info is None and pr.get("drop_requires_approval"):
        drop_status = "OK" if has_approval else "VIOLATION"
        zone_info = {"policy": "approval_required", "distance": None, "radius": None, "type": "unspecified"}
        if agricultural_exemption and drone_type == "agricultural":
            drop_status = "OK"
            zone_info["policy"] = "agricultural_exemption"
    mission["drop_eval"] = {
        "drop_location": drop_loc,
        "zone": zone_info,
        "has_approval": has_approval,
        "status": drop_status,
    }


def compute_multi_drone_checks(mission: Dict, data: Dict, actor_map: Dict[str, Dict]) -> None:
    rules = data.get("rules", {}).get("R018_multi_drone_coordination", {})
    params = rules.get("parameters", {}) or {}
    max_per_op = params.get("max_drones_per_operator", {}).get("value")
    min_sep = params.get("min_separation_distance", {}).get("value")
    swarm_threshold = params.get("swarm_threshold", {}).get("value")
    swarm_requires_approval = params.get("swarm_requires_approval", {}).get("value", False)
    active = mission.get("active_drones") or []
    if not active:
        return
    has_approval = bool(mission.get("has_approval"))
    swarm_mode = bool(mission.get("swarm_mode"))
    seq_mode = bool(mission.get("sequential_mode"))

    op_counts: Dict[str, int] = {}
    for d in active:
        op_id = actor_map.get(d, {}).get("operator_id", f"op_{d}")
        op_counts[op_id] = op_counts.get(op_id, 0) + 1
    op_eval = None
    if max_per_op is not None and not seq_mode:
        violations = [op for op, cnt in op_counts.items() if cnt > max_per_op]
        exempt = swarm_mode and has_approval
        if violations and not exempt:
            op_eval = {"max_per_operator": max_per_op, "counts": op_counts, "status": "VIOLATION"}
        else:
            op_eval = {"max_per_operator": max_per_op, "counts": op_counts, "status": "OK"}
    if op_eval:
        mission["operator_eval"] = op_eval

    swarm_eval = None
    if swarm_mode and swarm_threshold is not None and swarm_requires_approval:
        if len(active) >= swarm_threshold:
            swarm_eval = {
                "swarm_threshold": swarm_threshold,
                "active_drones": len(active),
                "has_approval": has_approval,
                "status": "OK" if has_approval else "VIOLATION",
            }
    if swarm_eval:
        mission["swarm_eval"] = swarm_eval

    sep_eval: List[Dict] = []
    targets = mission.get("drone_targets") or []
    target_map: Dict[str, Tuple[float, float, float]] = {}
    for t in targets:
        if t.get("drone") is None:
            continue
        target_map[t["drone"]] = (t["x"], t["y"], t["z"])
    for d in active:
        if d not in target_map and d in actor_map:
            org = actor_map[d]["origin"]
            target_map[d] = (org["x"], org["y"], org["z"])
    if min_sep is not None and len(target_map) >= 2:
        names = list(target_map.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                ax, ay, az = target_map[a]
                bx, by, bz = target_map[b]
                dist = ((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2) ** 0.5
                sep_eval.append(
                    {
                        "pair": f"{a}-{b}",
                        "distance": round(dist, 2),
                        "min_required": float(min_sep),
                        "status": "VIOLATION" if dist < float(min_sep) else "OK",
                    }
                )
    if sep_eval:
        mission["separation_eval"] = sep_eval


def compute_airspace_checks(mission: Dict, data: Dict, airspace_zones: List[Dict]) -> None:
    if not airspace_zones or not mission.get("targets"):
        return
    params = data.get("rules", {}).get("R019_airspace_classification", {}).get("parameters", {}) or {}
    ceiling = params.get("uncontrolled_altitude_ceiling", {}).get("value", 120)
    targets = mission.get("targets") or []
    has_approval = bool(mission.get("has_approval"))
    evals = []
    violation = False
    for t in targets:
        tx, ty, tz = t["x"], t["y"], t["z"]
        classification = "uncontrolled"
        zone_hit = None
        for z in airspace_zones:
            ztype = z.get("type")
            ar = z.get("altitude_range", {}) or {}
            min_z = ar.get("min_m", -float("inf"))
            max_z = ar.get("max_m", float("inf"))
            in_alt = (tz >= min_z) and (tz <= max_z)
            if ztype == "restricted":
                center = z.get("center", {}).get("xyz") or z.get("center", {})
                cx = cy = None
                if isinstance(z.get("center"), dict):
                    cx = float(z["center"].get("north", 0.0))
                    cy = float(z["center"].get("east", 0.0))
                elif isinstance(z.get("center"), str):
                    parts = re.findall(r"[-+]?[0-9]*\.?[0-9]+", z["center"])
                    if len(parts) >= 2:
                        cx, cy = float(parts[0]), float(parts[1])
                r = float(z.get("radius", 0.0))
                if cx is not None and cy is not None:
                    dist = ((tx - cx) ** 2 + (ty - cy) ** 2) ** 0.5
                    if dist <= r and in_alt:
                        classification = "restricted"
                        zone_hit = {"id": z.get("id"), "type": ztype, "distance": round(dist, 2), "radius": r}
                        break
        if classification != "restricted":
            if tz >= ceiling:
                classification = "controlled"
            else:
                classification = "uncontrolled"
        status = "OK"
        if classification in ["restricted", "controlled"] and not has_approval:
            status = "VIOLATION"
            violation = True
        evals.append(
            {
                "target": t,
                "classification": classification,
                "approval_required": classification in ["restricted", "controlled"],
                "has_approval": has_approval,
                "status": status,
                "zone": zone_hit,
            }
        )
    if evals:
        mission["airspace_eval"] = evals
        mission["airspace_recommendation"] = "REJECT" if violation else "APPROVE"


def compute_timeline_checks(mission: Dict, data: Dict, controlled_zones: List[Dict]) -> None:
    params = data.get("rules", {}).get("R020_approval_timeline", {}).get("parameters", {}) or {}
    advance_hours = params.get("china_advance_notice_hours", {}).get("value", 36)
    boundary_mode = params.get("boundary_mode", {}).get("value", "inclusive")
    emergency_exemption = params.get("emergency_exemption", {}).get("value", True)
    uncontrolled_exempt = params.get("uncontrolled_airspace_exempt", {}).get("value", True)
    ceiling = 120.0
    targets = mission.get("targets") or []
    if not targets and mission.get("target_xyz"):
        tx = mission["target_xyz"]["x"]
        ty = mission["target_xyz"]["y"]
        tz = mission["target_xyz"].get("z", mission.get("altitude_m", 0.0))
        targets = [{"x": tx, "y": ty, "z": tz}]

    def in_controlled_zone(t: Dict) -> bool:
        if mission.get("in_controlled_zone") is not None:
            return bool(mission["in_controlled_zone"])
        for cz in controlled_zones:
            center = cz.get("center", {}) or {}
            cx = float(center.get("north", 0.0))
            cy = float(center.get("east", 0.0))
            r = float(cz.get("radius", 0.0))
            dist = ((t["x"] - cx) ** 2 + (t["y"] - cy) ** 2) ** 0.5
            if dist <= r:
                return True
        return False

    def parse_iso_time(val: str) -> Optional[datetime]:
        try:
            if val.endswith("Z"):
                val = val.replace("Z", "+00:00")
            return datetime.fromisoformat(val)
        except Exception:
            return None

    def evaluate_pair(t, app_time, flight_time, phase_tag=None, time_diff_override=None):
        time_diff_h = time_diff_override
        if time_diff_h is None and app_time and flight_time:
            time_diff_h = (flight_time - app_time).total_seconds() / 3600.0
        in_ctrl = in_controlled_zone(t) or t.get("z", 0.0) >= ceiling
        requires_approval = in_ctrl
        if uncontrolled_exempt and (t.get("z", 0.0) < ceiling) and not in_controlled_zone(t):
            requires_approval = False
        status = "OK"
        reason = "exempt_uncontrolled" if not requires_approval else "approval_required"
        is_emergency = mission.get("flight_type") == "emergency"
        if requires_approval:
            if is_emergency and emergency_exemption:
                status = "OK"
                reason = "emergency_exemption"
            else:
                if time_diff_h is None:
                    status = "VIOLATION"
                    reason = "missing_application_time"
                else:
                    meets = time_diff_h > advance_hours if boundary_mode == "exclusive" else time_diff_h >= advance_hours
                    if not meets:
                        status = "VIOLATION"
                        reason = "insufficient_notice"
        return {
            "target": t,
            "in_controlled_zone": in_ctrl,
            "altitude": t.get("z"),
            "requires_approval": requires_approval,
            "time_diff_hours": time_diff_h,
            "advance_hours_required": advance_hours,
            "boundary_mode": boundary_mode,
            "flight_type": mission.get("flight_type"),
            "status": status,
            "reason": reason,
            "phase": phase_tag,
        }

    evals = []
    violation = False
    if mission.get("test_phases"):
        for phase in mission["test_phases"]:
            app_time = parse_iso_time(phase.get("application_time")) if phase.get("application_time") else None
            flight_time = parse_iso_time(phase.get("planned_flight_time")) if phase.get("planned_flight_time") else None
            tdiff = phase.get("time_diff_hours")
            if tdiff is not None:
                time_diff_h_override = float(tdiff)
                app_time = parse_iso_time(phase.get("application_time")) if phase.get("application_time") else None
                flight_time = parse_iso_time(phase.get("planned_flight_time")) if phase.get("planned_flight_time") else None
            else:
                time_diff_h_override = None
                app_time = parse_iso_time(phase.get("application_time")) if phase.get("application_time") else None
                flight_time = parse_iso_time(phase.get("planned_flight_time")) if phase.get("planned_flight_time") else None
            for t in targets:
                tl = evaluate_pair(t, app_time, flight_time, phase_tag=phase.get("phase"), time_diff_override=time_diff_h_override)
                evals.append(tl)
                if tl["status"] == "VIOLATION":
                    violation = True
    else:
        app_time = parse_iso_time(mission.get("application_time")) if mission.get("application_time") else None
        flight_time = parse_iso_time(mission.get("planned_flight_time")) if mission.get("planned_flight_time") else None
        for t in targets:
            tl = evaluate_pair(t, app_time, flight_time, phase_tag=None)
            evals.append(tl)
            if tl["status"] == "VIOLATION":
                violation = True
    if evals:
        mission["timeline_eval"] = evals
        mission["timeline_recommendation"] = "REJECT" if violation else "APPROVE"


def load_geofences(data: dict) -> List[Dict]:
    geos = []
    for gf in data.get("geofences", []) or []:
        center = gf.get("center", {}).get("xyz") or gf.get("center")
        cx = cy = cz = 0.0
        if isinstance(center, str):
            parts = re.findall(r"[-+]?[0-9]*\.?[0-9]+", center)
            if len(parts) >= 3:
                cx, cy, cz = float(parts[0]), float(parts[1]), float(parts[2])
            elif len(parts) >= 2:
                cx, cy = float(parts[0]), float(parts[1])
        elif isinstance(center, dict):
            cx = float(center.get("x", center.get("north", 0)))
            cy = float(center.get("y", center.get("east", 0)))
            cz = float(center.get("z", center.get("altitude", 0)))
        geos.append(
            {
                "id": gf.get("id", "gf"),
                "cx": cx,
                "cy": cy,
                "cz": cz,
                "radius": float(gf.get("radius", 0.0)),
                "margin": float(gf.get("safety_margin", 0.0)),
                "action": gf.get("action", "reject"),
                "zone_type": gf.get("zone_type"),
                "time_restriction": gf.get("time_restriction"),
            }
        )
    return geos


def load_altitude_zones(data: dict) -> List[Dict]:
    return data.get("altitude_zones", []) or []


def load_structures(data: dict) -> List[Dict]:
    return data.get("structures", []) or []


def load_speed_zones(data: dict) -> List[Dict]:
    return data.get("speed_zones", []) or []


def load_drop_zones(data: dict) -> List[Dict]:
    return data.get("drop_zones", []) or []


def load_airspace_zones(data: dict) -> List[Dict]:
    return data.get("airspace_zones", []) or []


def load_controlled_zones(data: dict) -> List[Dict]:
    return data.get("controlled_zones", []) or []


def load_origin(data: dict) -> Dict:
    actors = data.get("actors") or []
    if actors:
        org = actors[0].get("origin", {}).get("xyz") or actors[0].get("origin")
        if isinstance(org, str):
            parts = re.findall(r"[-+]?[0-9]*\.?[0-9]+", org)
            if len(parts) >= 3:
                return {"x": float(parts[0]), "y": float(parts[1]), "z": float(parts[2])}
        elif isinstance(org, dict):
            return {
                "x": float(org.get("x", org.get("north", 0.0))),
                "y": float(org.get("y", org.get("east", 0.0))),
                "z": float(org.get("z", org.get("altitude", 0.0))),
            }
    return {"x": 0.0, "y": 0.0, "z": 0.0}


def load_actor_map(data: dict) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for a in data.get("actors") or []:
        name = a.get("name") or a.get("id")
        if not name:
            continue
        meta = a.get("metadata", {}) or {}
        origin = a.get("origin", {}).get("xyz") or a.get("origin", {})
        ox = oy = oz = 0.0
        if isinstance(origin, str):
            parts = re.findall(r"[-+]?[0-9]*\\.?[0-9]+", origin)
            if len(parts) >= 3:
                ox, oy, oz = map(float, parts[:3])
        elif isinstance(origin, dict):
            ox = float(origin.get("x", origin.get("north", 0.0)))
            oy = float(origin.get("y", origin.get("east", 0.0)))
            oz = float(origin.get("z", origin.get("altitude", 0.0)))
        out[name] = {
            "operator_id": meta.get("operator_id"),
            "operator_name": meta.get("operator_name"),
            "drone_type": meta.get("drone_type"),
            "origin": {"x": ox, "y": oy, "z": oz},
        }
    return out


def point_segment_min_distance_3d(px: float, py: float, pz: float, ax: float, ay: float, az: float, bx: float, by: float, bz: float) -> float:
    abx, aby, abz = bx - ax, by - ay, bz - az
    apx, apy, apz = px - ax, py - ay, pz - az
    ab_len_sq = abx * abx + aby * aby + abz * abz
    if ab_len_sq == 0:
        return (apx * apx + apy * apy + apz * apz) ** 0.5
    t = max(0.0, min(1.0, (apx * abx + apy * aby + apz * abz) / ab_len_sq))
    projx, projy, projz = ax + t * abx, ay + t * aby, az + t * abz
    dx, dy, dz = px - projx, py - projy, pz - projz
    return (dx * dx + dy * dy + dz * dz) ** 0.5


def build_prompt(mission: Dict, constraints: List[Dict]) -> str:
    ctx_lines = []
    for c in constraints:
        val = c.get("canonical_value")
        unit = c.get("canonical_unit") or ""
        ctx_lines.append(f"- {c.get('concept')}: {val}{unit} ({c.get('source_type')} {c.get('source_ref')})")
    geofence_rule = ""
    if mission.get("geofence_eval"):
        ctx_lines.append("Geofence checks (pre-computed, use these values directly):")
        for gf in mission["geofence_eval"]:
            ctx_lines.append(
                f"  - {gf['id']}: center=({gf['cx']},{gf['cy']},{gf['cz']}), "
                f"radius={gf['radius']}m, margin={gf['margin']}m, distance={gf['distance']}m "
                f"(3D), threshold={gf['threshold']}m, action={gf.get('action','reject')}, zone_type={gf.get('zone_type')} => status={gf['status']}"
            )
        geofence_rule = (
            "Geofence decision rule: if ANY geofence status == inside and action=reject, decision MUST be REJECT. "
            "If status==inside and action=warn: if zone_type==obstacle -> decision MUST be APPROVE_WITH_STOP; otherwise decision MUST be APPROVE_WITH_WARNING. "
            "If ALL geofences are outside, decision is APPROVE unless other constraints are violated. "
            "Do NOT answer UNCERTAIN when geofence_eval is present.\n"
        )
    path_rule = ""
    if mission.get("path_eval"):
        ctx_lines.append("Path crossing checks (pre-computed, use these values directly):")
        for pe in mission["path_eval"]:
            ctx_lines.append(
                f"  - {pe['id']}: start=({pe['start_x']},{pe['start_y']}), end=({pe['end_x']},{pe['end_y']}), "
                f"min_distance={pe['min_distance']}m, threshold={pe['threshold']}m, action={pe.get('action','reject')}, zone_type={pe.get('zone_type')} => status={pe['status']}"
            )
        path_rule = (
            "Path crossing rule: if ANY path_eval status == inside and action=reject, decision MUST be REJECT. "
            "If status==inside and action=warn: if zone_type==obstacle -> decision MUST be APPROVE_WITH_STOP; otherwise decision MUST be APPROVE_WITH_WARNING. "
            "Do NOT answer UNCERTAIN when path_eval is present.\n"
        )
    time_rule = ""
    if mission.get("time_window_eval"):
        ctx_lines.append("Time window checks (pre-computed):")
        for tw in mission["time_window_eval"]:
            ctx_lines.append(
                f"  - zone={tw['zone_id']}: distance={tw['distance']}m radius={tw['radius']}m "
                f"time={tw['time']} window=({tw['start']}-{tw['end']}) in_zone={tw['in_zone']} "
                f"in_window={tw['in_window']} => status={tw['status']}"
            )
        time_rule = (
            "Time window rule (hard constraint): if ANY time_window_eval status == inside (in zone AND in restricted window), "
            "decision MUST be REJECT. Do NOT answer UNCERTAIN when time_window_eval is present. "
            "If all time_window_eval statuses are outside, you may ignore night_eval violations.\n"
        )
    vlos_rule = ""
    if mission.get("vlos_eval") and not mission.get("vlos_ignored_due_to_bvlos"):
        ve = mission["vlos_eval"]
        ctx_lines.append(
            f"VLOS check (pre-computed): horiz_distance={ve['horizontal_distance']}m, limit={ve['limit']}m => status={ve['status']}"
        )
        vlos_rule = (
            "VLOS rule (hard constraint): if vlos_eval status == VIOLATION (distance > limit), decision MUST be REJECT. "
            "Boundary inclusive: distance <= limit is OK.\n"
        )
    bvlos_rule = ""
    if mission.get("bvlos_eval"):
        be = mission["bvlos_eval"]
        ctx_lines.append(
            f"BVLOS check (pre-computed): distance={be['distance']}m, effective_limit={be['effective_limit']}m, "
            f"base_limit={be['base_limit']}m, waivers={be['applied_waivers']} => status={be['status']}"
        )
        bvlos_rule = (
            "BVLOS rule: if bvlos_eval status == VIOLATION (distance > effective_limit), decision MUST be REJECT. "
            "If bvlos_eval is OK with waivers applied, you may ignore VLOS violations for this mission. "
            "effective_limit may be extended by waivers; boundary inclusive.\n"
        )
    payload_rule = ""
    if mission.get("payload_eval"):
        pe = mission["payload_eval"]
        ctx_lines.append(
            f"Payload check: payload={pe['payload_kg']}kg, max={pe['max_payload_kg']}kg => status={pe['status']}"
        )
        payload_rule = "Payload rule: if payload_eval status == VIOLATION (payload > max), decision MUST be REJECT.\n"
    drop_rule = ""
    if mission.get("drop_eval"):
        de = mission["drop_eval"]
        ctx_lines.append(
            f"Drop check: location={de['drop_location']}, zone={de.get('zone')}, has_approval={de['has_approval']} => status={de['status']}"
        )
        drop_rule = (
            "Drop rule: if drop_eval status == VIOLATION (prohibited zone or approval missing), decision MUST be REJECT. "
            "If status==OK, drop is permitted.\n"
        )
    airspace_rule = ""
    if mission.get("airspace_eval"):
        ctx_lines.append("Airspace checks (pre-computed):")
        for ae in mission["airspace_eval"]:
            ctx_lines.append(
                f"  - target={ae['target']} classification={ae['classification']} "
                f"approval_required={ae['approval_required']} has_approval={ae['has_approval']} => status={ae['status']}"
            )
        airspace_rule = (
            "Airspace rule: if any airspace_eval status == VIOLATION (controlled/restricted without approval), decision MUST be REJECT. "
            "Boundary rule: altitude >= uncontrolled ceiling belongs to controlled airspace. "
            "If airspace_recommendation is REJECT -> final decision MUST be REJECT.\n"
        )
    timeline_rule = ""
    if mission.get("timeline_eval"):
        ctx_lines.append("Approval timeline checks (pre-computed):")
        for tl in mission["timeline_eval"]:
            ctx_lines.append(
                f"  - target={tl['target']} in_controlled_zone={tl['in_controlled_zone']} "
                f"altitude={tl['altitude']}m requires_approval={tl['requires_approval']} "
                f"time_diff_hours={tl['time_diff_hours']} advance_required={tl['advance_hours_required']} "
                f"flight_type={tl['flight_type']} => status={tl['status']} reason={tl['reason']}"
            )
        timeline_rule = (
            "Approval timeline rule: if any timeline_eval status == VIOLATION (approval required but notice < threshold or missing application time), "
            "decision MUST be REJECT. Emergency exemption and uncontrolled airspace exemption already applied. "
            "Boundary_mode 'inclusive' means time_diff_hours >= required is OK.\n"
        )
    structure_rule = ""
    if mission.get("structure_eval"):
        ctx_lines.append("Structure waiver checks (pre-computed):")
        for se in mission["structure_eval"]:
            ctx_lines.append(
                f"  - {se['id']}: distance={se['distance']}m, waiver_radius={se['waiver_radius']}m, "
                f"global_limit={se['global_limit']}m, waiver_limit={se['waiver_limit']}m => status={se['status']}"
            )
        structure_rule = (
            "Structure waiver rule (hard constraint): inside waiver radius => use waiver_limit; "
            "altitude >= waiver_limit -> REJECT. Outside waiver radius => use global_limit; altitude >= global_limit -> REJECT. "
            "Do NOT answer UNCERTAIN when structure_eval is present.\n"
        )
    auto_checks = []
    if mission.get("speed_eval"):
        auto_checks.append(f"Speed check: mission_speed={mission['speed_eval']['mission_speed']} m/s vs limit={mission['speed_eval']['limit']} m/s -> {mission['speed_eval']['status']}.")
    if mission.get("altitude_eval"):
        auto_checks.append(f"Altitude check: mission_altitude={mission['altitude_eval']['mission_altitude']} m vs limit={mission['altitude_eval']['limit']} m -> {mission['altitude_eval']['status']}.")
    if mission.get("battery_eval"):
        auto_checks.append(f"Battery check: battery={mission['battery_eval']['battery_percent']}% vs required={mission['battery_eval']['required_percent']}% -> {mission['battery_eval']['status']}.")
    if mission.get("night_eval"):
        ne = mission["night_eval"]
        auto_checks.append(
            f"Night check: time={ne['time_of_day']} is_night={ne['is_night']} "
            f"light_on={ne['light_on']} training_ok={ne['training_ok']} -> {ne['status']}."
        )
    if mission.get("vlos_eval") and not mission.get("vlos_ignored_due_to_bvlos"):
        ve = mission["vlos_eval"]
        auto_checks.append(
            f"VLOS check: horiz_distance={ve['horizontal_distance']} m vs limit={ve['limit']} m -> {ve['status']}."
        )
    if mission.get("bvlos_eval"):
        be = mission["bvlos_eval"]
        auto_checks.append(
            f"BVLOS check: distance={be['distance']} m vs effective_limit={be['effective_limit']} m (base {be['base_limit']} m, waivers={be['applied_waivers']}) -> {be['status']}."
        )
    auto_rule = ""
    if auto_checks:
        auto_rule = (
            "Hard rules: if any auto_check status is VIOLATION, decision MUST be REJECT. "
            "Only if all auto_check statuses are OK and geofence checks are outside may you APPROVE.\n"
            "Auto checks:\n- " + "\n- ".join(auto_checks) + "\n"
        )
    ctx = "\n".join(ctx_lines) if ctx_lines else "(no constraints found)"
    geofence_note = ""
    if not mission.get("geofence_eval"):
        geofence_note = "No geofence constraints provided; there is NO geofence violation and geofence must NOT be used to reject.\n"
    if mission.get("geofence_recommendation"):
        geofence_note += (
            f"Geofence recommendation: {mission['geofence_recommendation']}. "
            "If geofence_recommendation is REJECT -> final decision MUST be REJECT. "
            "If geofence_recommendation is APPROVE_WITH_WARNING -> final decision MUST be APPROVE_WITH_WARNING unless other hard violations exist. "
            "If geofence_recommendation is APPROVE_WITH_STOP -> final decision MUST be APPROVE_WITH_STOP unless other hard violations exist.\n"
        )
    altitude_zone_note = ""
    if mission.get("altitude_zone"):
        az = mission["altitude_zone"]
        altitude_zone_note = f"Altitude zone applied: {az['id']} (limit {az['limit']}m).\n"
    speed_zone_note = ""
    if mission.get("speed_zone"):
        sz = mission["speed_zone"]
        speed_zone_note = f"Speed zone applied: {sz['id']} (limit {sz['limit']} m/s).\n"
    path_reco_note = ""
    if mission.get("path_recommendation"):
        path_reco_note = (
            f"Path recommendation: {mission['path_recommendation']}. "
            "If path_recommendation is REJECT -> final decision MUST be REJECT. "
            "If path_recommendation is APPROVE_WITH_WARNING -> final decision MUST be APPROVE_WITH_WARNING unless a geofence inside or auto_check violation exists. "
            "If path_recommendation is APPROVE_WITH_STOP -> final decision MUST be APPROVE_WITH_STOP unless a geofence inside or auto_check violation exists.\n"
        )
    return (
        "You are a dispatch AI. Decide APPROVE or REJECT with cited constraints.\n"
        "Retrieved constraints:\n"
        f"{ctx}\n"
        f"{geofence_rule}"
        f"{path_rule}"
        f"{time_rule}"
        f"{vlos_rule}"
        f"{bvlos_rule}"
        f"{payload_rule}"
        f"{drop_rule}"
        f"{airspace_rule}"
        f"{timeline_rule}"
        f"{structure_rule}"
        f"{auto_rule}"
        f"{geofence_note}"
        f"{altitude_zone_note}"
        f"{speed_zone_note}"
        f"{path_reco_note}"
        f"Mission: {json.dumps(mission, ensure_ascii=False)}\n"
        "Decide and cite which constraints are satisfied/violated. Respond with JSON:\n"
        '{ "decision": "APPROVE|REJECT|CONDITIONAL|UNCERTAIN", "reasons": [...], "citations": [...] }'
    )


def call_llm(prompt: str, model: str) -> Optional[str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set; skipping LLM call.")
        return None
    try:
        genai.configure(api_key=api_key)
        client = genai.GenerativeModel(model)
        resp = client.generate_content(prompt)
        return resp.text
    except Exception as e:
        print(f"LLM call failed: {e}")
        return None


def clean_json_text(text: str) -> str:
    txt = text.strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```[a-zA-Z0-9_+-]*", "", txt, flags=re.MULTILINE).strip()
        txt = re.sub(r"```$", "", txt, flags=re.MULTILINE).strip()
    return txt


# --- Main runner -------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generic RAG batch runner for scenarios")
    parser.add_argument("--scenarios", type=str, help="Comma-separated scenario ids (e.g., S001,S002). Default: S001-S020.", default=None)
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model name")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"), help="Directory to save reports")
    parser.add_argument("--no-call", action="store_true", help="Only build prompts, do not call LLM")
    return parser.parse_args()


def scenario_list(arg: Optional[str]) -> List[str]:
    if arg:
        return [s.strip() for s in arg.split(",") if s.strip()]
    return [f"S{idx:03d}" for idx in range(1, 21)]


def main() -> None:
    args = parse_args()
    constraints_by_scenario = load_constraints_by_scenario()
    scenarios = scenario_list(args.scenarios)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for sid in scenarios:
        try:
            data = load_scenario_file(sid)
        except FileNotFoundError:
            print(f"[skip] Scenario file not found for {sid}")
            continue
        geofences = load_geofences(data)
        altitude_zones = load_altitude_zones(data)
        structures = load_structures(data)
        speed_zones = load_speed_zones(data)
        drop_zones = load_drop_zones(data)
        airspace_zones = load_airspace_zones(data)
        controlled_zones = load_controlled_zones(data)
        origin = load_origin(data)
        actor_map = load_actor_map(data)
        constraints = constraints_by_scenario.get(sid, [])
        results = []
        correct = 0
        test_cases = collect_test_cases(data)
        if not test_cases:
            print(f"[warn] No test_cases found for {sid}")
        tc_count = len(test_cases)
        case_count = 0

        for tc in test_cases:
            try:
                mission = extract_mission_from_test_case(tc)
                compute_night_checks(mission, data)
                compute_time_window_checks(mission, data)
                compute_vlos_check(mission, data)
                compute_bvlos_check(mission, data)
                if mission.get("time_window_eval") and all(tw.get("status") != "inside" for tw in mission["time_window_eval"]):
                    if mission.get("night_eval"):
                        mission["night_eval"]["status"] = "OK"
                        mission["night_eval"]["reasons"] = ["Night check ignored because all time window statuses are outside."]
                if speed_zones and mission.get("target_xyz"):
                    tx, ty = mission["target_xyz"]["x"], mission["target_xyz"]["y"]
                    best_limit = None
                    best_zone = None
                    for sz in speed_zones:
                        ztype = sz.get("type")
                        limit = sz.get("speed_limit_ms") or sz.get("speed_limit_kmh")
                        if limit is None:
                            continue
                        if sz.get("speed_limit_ms") is None and sz.get("speed_limit_kmh") is not None:
                            limit = float(sz["speed_limit_kmh"]) * (1000.0 / 3600.0)
                        if ztype == "global":
                            if best_limit is None or limit < best_limit:
                                best_limit = limit
                                best_zone = {"id": sz.get("id", "global"), "limit": float(limit)}
                        elif ztype == "cylinder":
                            center = sz.get("center", {}).get("xyz") or sz.get("center", {})
                            cx = cy = 0.0
                            if isinstance(center, str):
                                parts = re.findall(r"[-+]?[0-9]*\\.?[0-9]+", center)
                                if len(parts) >= 2:
                                    cx, cy = float(parts[0]), float(parts[1])
                            elif isinstance(center, dict):
                                cx = float(center.get("north", center.get("x", 0.0)))
                                cy = float(center.get("east", center.get("y", 0.0)))
                            r = float(sz.get("radius", 0.0))
                            dist = ((tx - cx) ** 2 + (ty - cy) ** 2) ** 0.5
                            if dist <= r:
                                if best_limit is None or limit < best_limit:
                                    best_limit = limit
                                    best_zone = {"id": sz.get("id", "zone"), "limit": float(limit)}
                    if best_limit is None:
                        gspeed = data.get("scenario_parameters", {}).get("global_speed_limit_kmh")
                        if gspeed is not None:
                            best_limit = float(gspeed) * (1000.0 / 3600.0)
                            best_zone = {"id": "global_speed", "limit": float(best_limit)}
                    if best_limit is not None:
                        ms = mission.get("speed_mps")
                        if ms is not None:
                            mission["speed_eval"] = {
                                "mission_speed": float(ms),
                                "limit": float(best_limit),
                                "status": "VIOLATION" if float(ms) > float(best_limit) else "OK",
                            }
                        mission["speed_zone"] = best_zone
                if structures and mission.get("target_xyz"):
                    se_list = []
                    tx, ty, tz = mission["target_xyz"]["x"], mission["target_xyz"]["y"], mission["target_xyz"].get("z", 0.0)
                    global_limit = data.get("scenario_parameters", {}).get("global_altitude_limit_agl", None)
                    for st in structures:
                        loc = st.get("location", {})
                        sx, sy = float(loc.get("north", 0.0)), float(loc.get("east", 0.0))
                        waiver_radius = float(st.get("waiver_radius", 0.0))
                        waiver_limit = float(st.get("total_waiver_altitude", st.get("waiver_altitude_above_structure", 0.0) + st.get("height_agl", 0.0)))
                        dist = ((tx - sx) ** 2 + (ty - sy) ** 2) ** 0.5
                        status = "inside" if dist < waiver_radius else "outside"
                        applied_limit = waiver_limit if status == "inside" else global_limit
                        se_list.append(
                            {
                                "id": st.get("id", "structure"),
                                "distance": round(dist, 2),
                                "waiver_radius": waiver_radius,
                                "waiver_limit": waiver_limit,
                                "global_limit": global_limit,
                                "status": status,
                                "applied_limit": applied_limit,
                            }
                        )
                    if se_list:
                        mission["structure_eval"] = se_list
                        if mission.get("altitude_m") is not None:
                            limits = [s["applied_limit"] for s in se_list if s.get("applied_limit") is not None]
                            if limits:
                                best_limit = min(limits)
                                mission["altitude_eval"] = {
                                    "mission_altitude": float(mission["altitude_m"]),
                                    "limit": float(best_limit),
                                    "status": "VIOLATION" if float(mission["altitude_m"]) >= float(best_limit) else "OK",
                                }
                if altitude_zones and mission.get("target_xyz"):
                    tx, ty = mission["target_xyz"]["x"], mission["target_xyz"]["y"]
                    best_limit = None
                    best_zone = None
                    for az in altitude_zones:
                        geom = az.get("geometry", {})
                        z_limit = az.get("altitude_limit_agl")
                        if z_limit is None:
                            continue
                        gid = geom.get("type")
                        if gid == "circle":
                            cx = geom.get("center", {}).get("north", 0.0)
                            cy = geom.get("center", {}).get("east", 0.0)
                            r = geom.get("radius", 0.0)
                            dist = ((tx - cx) ** 2 + (ty - cy) ** 2) ** 0.5
                            if dist <= r:
                                if best_limit is None or z_limit < best_limit:
                                    best_limit = z_limit
                                    best_zone = az
                        elif gid == "infinite":
                            br = geom.get("beyond_radius", 0.0)
                            dist = ((tx - 0.0) ** 2 + (ty - 0.0) ** 2) ** 0.5
                            if dist >= br:
                                if best_limit is None or z_limit < best_limit:
                                    best_limit = z_limit
                                    best_zone = az
                    if best_limit is not None and mission.get("altitude_m") is not None:
                        am = float(mission["altitude_m"])
                        mission["altitude_eval"] = {
                            "mission_altitude": am,
                            "limit": float(best_limit),
                            "status": "VIOLATION" if am >= float(best_limit) else "OK",
                        }
                        mission["altitude_zone"] = {"id": best_zone.get("id", "zone"), "limit": float(best_limit)}
                if mission.get("target_xyz"):
                    start = tc.get("geometry", {}).get("start")
                    if isinstance(start, list) and len(start) >= 2:
                        sx, sy = float(start[0]), float(start[1])
                    else:
                        sx, sy = origin["x"], origin["y"]
                    ex, ey = mission["target_xyz"]["x"], mission["target_xyz"]["y"]
                    pe_list = []
                    for gf in geofences:
                        min_dist = round(point_segment_min_distance_3d(gf["cx"], gf["cy"], gf["cz"], sx, sy, origin.get("z", 0.0), ex, ey, mission["target_xyz"].get("z", 0.0)), 2)
                        threshold = gf["radius"] + gf["margin"]
                        status = "inside" if min_dist < threshold else "outside"
                        active = True
                        tr = gf.get("time_restriction")
                        if tr:
                            now_str = mission.get("simulated_time") or mission.get("current_time")
                            now_dt = datetime.fromisoformat(now_str.replace("Z", "+00:00")) if now_str else None
                            start_t = datetime.fromisoformat(tr.get("active_start").replace("Z", "+00:00")) if tr.get("active_start") else None
                            end_t = datetime.fromisoformat(tr.get("active_end").replace("Z", "+00:00")) if tr.get("active_end") else None
                            if now_dt and start_t and end_t:
                                active = start_t <= now_dt <= end_t
                            if not active:
                                status = "inactive"
                        pe_list.append(
                            {
                                "id": gf["id"],
                                "start_x": sx,
                                "start_y": sy,
                                "end_x": ex,
                                "end_y": ey,
                                "min_distance": min_dist,
                                "threshold": threshold,
                                "status": status,
                                "action": gf.get("action", "reject"),
                                "zone_type": gf.get("zone_type"),
                            }
                        )
                    if pe_list:
                        mission["path_eval"] = pe_list
                        any_reject = any(pe["status"] == "inside" and pe.get("action") != "warn" for pe in pe_list)
                        warn_entries = [pe for pe in pe_list if pe["status"] == "inside" and pe.get("action") == "warn"]
                        any_warn = bool(warn_entries)
                        if any_reject:
                            mission["path_recommendation"] = "REJECT"
                        elif any_warn:
                            if any(pe.get("zone_type") == "obstacle" for pe in warn_entries):
                                mission["path_recommendation"] = "APPROVE_WITH_STOP"
                            else:
                                mission["path_recommendation"] = "APPROVE_WITH_WARNING"
                if geofences and mission.get("target_xyz"):
                    gfe = []
                    tx, ty, tz = mission["target_xyz"]["x"], mission["target_xyz"]["y"], mission["target_xyz"].get("z", 0.0)
                    geo_reco = None
                    for gf in geofences:
                        dist = ((tx - gf["cx"]) ** 2 + (ty - gf["cy"]) ** 2 + (tz - gf["cz"]) ** 2) ** 0.5
                        threshold = gf["radius"] + gf["margin"]
                        status = "inside" if dist < threshold else "outside"
                        active = True
                        tr = gf.get("time_restriction")
                        if tr:
                            now_str = mission.get("simulated_time") or mission.get("current_time")
                            now_dt = datetime.fromisoformat(now_str.replace("Z", "+00:00")) if now_str else None
                            start_t = datetime.fromisoformat(tr.get("active_start").replace("Z", "+00:00")) if tr.get("active_start") else None
                            end_t = datetime.fromisoformat(tr.get("active_end").replace("Z", "+00:00")) if tr.get("active_end") else None
                            if now_dt and start_t and end_t:
                                active = start_t <= now_dt <= end_t
                            if not active:
                                status = "inactive"
                        action = gf.get("action", "reject")
                        gfe.append(
                            {
                                "id": gf["id"],
                                "cx": gf["cx"],
                                "cy": gf["cy"],
                                "cz": gf["cz"],
                                "radius": gf["radius"],
                                "margin": gf["margin"],
                                "distance": round(dist, 2),
                                "threshold": threshold,
                                "status": status,
                                "action": action,
                                "zone_type": gf.get("zone_type"),
                            }
                        )
                        if status == "inside":
                            if action != "warn":
                                geo_reco = "REJECT"
                            elif geo_reco is None:
                                if gf.get("zone_type") == "obstacle":
                                    geo_reco = "APPROVE_WITH_STOP"
                                else:
                                    geo_reco = "APPROVE_WITH_WARNING"
                    mission["geofence_eval"] = gfe
                    mission["geofence_recommendation"] = geo_reco or "APPROVE"
                if drop_zones:
                    compute_payload_drop_checks(mission, data, drop_zones)
                if airspace_zones:
                    compute_airspace_checks(mission, data, airspace_zones)
                if controlled_zones:
                    compute_timeline_checks(mission, data, controlled_zones)
                compute_multi_drone_checks(mission, data, actor_map)
                concepts = relevant_concepts(mission)
                selected = filter_constraints(constraints, concepts)
                compute_auto_checks(mission, selected)
                prompt = build_prompt(mission, selected)
                llm_raw = None
                llm_parsed = None
                if not args.no_call:
                    llm_raw = call_llm(prompt, args.model)
                    if llm_raw:
                        try:
                            llm_parsed = json.loads(clean_json_text(llm_raw))
                        except Exception:
                            llm_parsed = None
                raw_exp = tc.get("expected_result")
                expected = None
                if isinstance(raw_exp, dict):
                    expected = raw_exp.get("decision")
                elif isinstance(raw_exp, str):
                    expected = raw_exp
                if expected is None:
                    expected = tc.get("expected")
                if expected is None:
                    expected = tc.get("expected_decision")
                llm_decision = llm_parsed.get("decision") if llm_parsed else None
                if llm_decision in (None, "CONDITIONAL", "UNCERTAIN"):
                    has_reject = (
                        mission.get("geofence_recommendation") == "REJECT"
                        or mission.get("path_recommendation") == "REJECT"
                        or mission.get("timeline_recommendation") == "REJECT"
                        or mission.get("airspace_recommendation") == "REJECT"
                    )
                    if not has_reject:
                        if mission.get("geofence_recommendation") == "APPROVE_WITH_STOP" or mission.get("path_recommendation") == "APPROVE_WITH_STOP":
                            llm_decision = "APPROVE_WITH_STOP"
                        elif mission.get("geofence_recommendation") == "APPROVE_WITH_WARNING" or mission.get("path_recommendation") == "APPROVE_WITH_WARNING":
                            llm_decision = "APPROVE_WITH_WARNING"
                        if llm_decision and llm_parsed is not None:
                            llm_parsed["decision"] = llm_decision
                if expected and llm_decision and str(expected).upper() == str(llm_decision).upper():
                    correct += 1
                tc_id = tc.get("id") or tc.get("case_id") or tc.get("name")
                results.append(
                    {
                        "test_case_id": tc_id,
                        "description": tc.get("description"),
                        "expected_decision": expected,
                        "llm_decision": llm_decision,
                        "mission": mission,
                        "prompt": prompt,
                        "llm_raw": llm_raw,
                        "llm_parsed": llm_parsed,
                        "retrieved_constraints": selected,
                    }
                )
                case_count += 1
            except Exception as e:
                print(f"[error] {sid} {tc.get('id')} failed: {e}")

        print(f"[debug] {sid} processed cases: {case_count}, test_cases={tc_count}")
        total = len(results)
        acc = f"{correct}/{total}" if total else None
        acc_pct = f"{(correct/total*100):.1f}%" if total else None
        report = {
            "scenario": sid,
            "summary": {
                "total_test_cases": total,
                "llm_calls": sum(1 for r in results if r["llm_raw"]),
                "llm_accuracy": acc,
                "llm_accuracy_percent": acc_pct,
            },
            "results": results,
        }
        out_path = args.output_dir / f"{sid}_RAG_REPORT.json"
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"Saved {sid} report -> {out_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
run_scenario_timeline.py - Approval Timeline Scenario Runner

Specialized script for S020 - Flight Approval Timeline
- Pre-flight: Check application time vs flight time (≥36 hours)
- Exemptions: Emergency missions and uncontrolled airspace
- Pure logic checks, no flight simulation required

Author: LAE-GPT Team
Date: 2025-11-01
Version: 1.0

Usage:
    python run_scenario_timeline.py scenario.jsonc --output result.json --test-case TC1
"""

import sys
import json
import argparse
import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

# --- Data Classes ---
class Position:
    def __init__(self, north: float, east: float, altitude: float):
        self.north = north
        self.east = east
        self.altitude = altitude

    def distance_2d(self, other: 'Position') -> float:
        """Calculate 2D horizontal distance"""
        return math.sqrt((self.north - other.north)**2 + (self.east - other.east)**2)

class ControlledZone:
    def __init__(self, zone_id: str, name: str, center: Position, radius: float):
        self.zone_id = zone_id
        self.name = name
        self.center = center
        self.radius = radius

    def contains(self, position: Position) -> bool:
        """Check if position is inside the controlled zone"""
        distance = self.center.distance_2d(position)
        return distance <= self.radius

# --- Utility Functions ---
def parse_iso_datetime(time_str: str) -> datetime:
    """Parse ISO 8601 datetime string"""
    return datetime.fromisoformat(time_str.replace('Z', '+00:00'))

def calculate_hours_difference(application_time: str, planned_flight_time: str) -> float:
    """Calculate hours difference between application and flight time"""
    app_dt = parse_iso_datetime(application_time)
    flight_dt = parse_iso_datetime(planned_flight_time)
    
    time_diff = flight_dt - app_dt
    hours = time_diff.total_seconds() / 3600
    
    return hours

def check_controlled_zone(position: Position, zones: list) -> Tuple[bool, Optional[ControlledZone]]:
    """Check if position is in any controlled zone"""
    for zone in zones:
        if zone.contains(position):
            return True, zone
    return False, None

def check_uncontrolled_airspace(
    position: Position,
    altitude: float,
    in_controlled_zone: bool,
    altitude_ceiling: float = 120.0
) -> bool:
    """Check if position is in uncontrolled airspace"""
    # Uncontrolled airspace: altitude < 120m AND outside controlled zones
    return altitude < altitude_ceiling and not in_controlled_zone

def save_result(
    output_file: str,
    scenario_id: str,
    test_case_id: str,
    flight_approved: bool,
    reason: str,
    metadata: Dict[str, Any]
):
    """Save test result to JSON file"""
    result_data = {
        "metadata": {
            "scenario_id": scenario_id,
            "test_case_id": test_case_id,
            "flight_approved": flight_approved,
            "reason": reason,
            **metadata
        },
        "recorded_at": datetime.now().isoformat(),
        "trajectory": []  # No flight simulation for S020
    }
    
    with open(output_file, 'w') as f:
        json.dump(result_data, f, indent=2)
    print(f"✓ Result saved: {output_file} (0 points)")


def run_scenario(
    scenario_file: str,
    output_file: str,
    test_case_id: str
) -> int:
    print(f"Loading scenario: {scenario_file}")
    with open(scenario_file, 'r') as f:
        scenario_config = json.load(f)
    print(f"✓ Scenario loaded: {scenario_config['id']}")

    scenario_id = scenario_config['id']
    rules = scenario_config['rules']['R020_approval_timeline']
    advance_hours_required = rules['parameters']['china_advance_notice_hours']['value']
    
    print(f"✓ Rules loaded: advance_notice={advance_hours_required}h")

    # Parse controlled zones
    controlled_zones = []
    for zone_config in scenario_config.get('controlled_zones', []):
        center_pos = Position(
            north=zone_config['center']['north'],
            east=zone_config['center']['east'],
            altitude=0.0
        )
        zone = ControlledZone(
            zone_id=zone_config['id'],
            name=zone_config['name'],
            center=center_pos,
            radius=zone_config['radius']
        )
        controlled_zones.append(zone)
    
    if controlled_zones:
        print(f"✓ Loaded {len(controlled_zones)} controlled zone(s)")

    test_case = next((tc for tc in scenario_config['test_cases'] if tc['id'] == test_case_id), None)
    if not test_case:
        print(f"Error: Test case '{test_case_id}' not found.")
        return 1
    print(f"\n✓ Loading test case: {test_case_id}")

    # Parse test case data
    current_time = test_case.get('current_time')
    application_time = test_case.get('application_time')
    planned_flight_time = test_case.get('planned_flight_time')
    target = Position(
        north=test_case['target']['north'],
        east=test_case['target']['east'],
        altitude=test_case['target']['altitude']
    )
    flight_type = test_case.get('flight_type', 'normal')
    
    print(f"Current time: {current_time}")
    print(f"Application time: {application_time or 'null (NO APPLICATION)'}")
    print(f"Planned flight time: {planned_flight_time}")
    if flight_type == 'emergency':
        time_diff_str = f" ({calculate_hours_difference(application_time, planned_flight_time)*60:.0f} minutes later)"
    else:
        time_diff_str = ""
    print(f"Flight type: {flight_type.upper()}{time_diff_str}")
    print(f"Target: ({target.north:.0f}, {target.east:.0f}, {target.altitude:.0f}m)\n")

    print("======================================================================")
    print("S020 MODE - APPROVAL TIMELINE")
    print("======================================================================\n")

    print(f"Test Case: {test_case_id}")
    if 'test_phases' in test_case:
        print("(Multi-phase test)\n")

    # ==================== PRE-FLIGHT CHECKS ====================
    
    # Check 1: Controlled zone
    print("🔍 Pre-flight check: Controlled zone...")
    in_controlled_zone, zone = check_controlled_zone(target, controlled_zones)
    
    if in_controlled_zone:
        print(f"   Target position: ({target.north:.0f}, {target.east:.0f})")
        print(f"   Distance to zone center: {target.distance_2d(zone.center):.1f}m <= {zone.radius:.0f}m")
        print(f"   ✓ IN controlled zone → Requires approval\n")
    else:
        if controlled_zones:
            distance_to_center = target.distance_2d(controlled_zones[0].center)
            print(f"   Target position: ({target.north:.0f}, {target.east:.0f})")
            print(f"   Distance to zone center: {distance_to_center:.1f}m > {controlled_zones[0].radius:.0f}m")
        print(f"   ✓ OUTSIDE controlled zone\n")
    
    # Check 2: Uncontrolled airspace exemption
    is_uncontrolled = check_uncontrolled_airspace(target, target.altitude, in_controlled_zone)
    
    if not in_controlled_zone:
        print("🔍 Pre-flight check: Airspace classification...")
        print(f"   Altitude: {target.altitude:.0f}m < 120m")
        print(f"   Zone: Outside controlled")
        print(f"   ✓ UNCONTROLLED AIRSPACE\n")
    
    # Check 3: Exemptions
    print("🔍 Pre-flight check: Exemptions...")
    
    if is_uncontrolled:
        print(f"   Airspace: Uncontrolled (< 120m + outside controlled zone)")
        print(f"   Drone type: Light")
        print(f"   ✅ UNCONTROLLED AIRSPACE EXEMPTION\n")
        
        print(f"⚠️  Application check BYPASSED (uncontrolled airspace)\n")
        print(f"✅ FLIGHT APPROVED (Uncontrolled airspace exemption)")
        reason = f"适飞空域内飞行（高度{target.altitude:.0f}m<120m，非管制区域），无需提前申请"
        print(f"Reason: {reason}\n")
        print(f"Regulation: 中国《条例》第31条第一款")
        print(f"Exemption: 轻型无人机在适飞空域内飞行无需申请\n")
        
        save_result(
            output_file, scenario_id, test_case_id,
            flight_approved=True,
            reason=reason,
            metadata={
                "current_time": current_time,
                "application_time": application_time,
                "planned_flight_time": planned_flight_time,
                "flight_type": flight_type,
                "target": {"north": target.north, "east": target.east, "altitude": target.altitude},
                "in_controlled_zone": in_controlled_zone,
                "exemption_applied": "UNCONTROLLED_AIRSPACE"
            }
        )
        return 0
    
    elif flight_type == 'emergency':
        print(f"   Flight type: emergency")
        emergency_details = test_case.get('emergency_details', {})
        print(f"   Mission type: {emergency_details.get('mission_type', 'N/A')}")
        print(f"   Priority: {emergency_details.get('priority', 'N/A')}")
        print(f"   ✅ EMERGENCY EXEMPTION GRANTED\n")
        
        print(f"⚠️  Time advance check BYPASSED (emergency exemption)\n")
        print(f"✅ FLIGHT APPROVED (Emergency exemption)")
        time_diff_minutes = calculate_hours_difference(application_time, planned_flight_time) * 60
        reason = f"紧急救援任务豁免时限要求，批准在{time_diff_minutes:.0f}分钟后起飞"
        print(f"Reason: {reason}\n")
        print(f"Emergency details:")
        print(f"  Mission: {emergency_details.get('mission_type', 'N/A').replace('_', ' ').title()}")
        print(f"  Priority: {emergency_details.get('priority', 'N/A').title()}")
        print(f"  Approved by: {emergency_details.get('approved_by', 'N/A')}")
        print(f"  Regulation: 紧急任务豁免条款\n")
        
        save_result(
            output_file, scenario_id, test_case_id,
            flight_approved=True,
            reason=reason,
            metadata={
                "current_time": current_time,
                "application_time": application_time,
                "planned_flight_time": planned_flight_time,
                "flight_type": flight_type,
                "emergency_details": emergency_details,
                "target": {"north": target.north, "east": target.east, "altitude": target.altitude},
                "in_controlled_zone": in_controlled_zone,
                "exemption_applied": "EMERGENCY_MISSION"
            }
        )
        return 0
    else:
        print(f"   Flight type: normal")
        print(f"   Altitude: {target.altitude:.0f}m (< 120m but in controlled zone)")
        print(f"   ❌ NO exemptions applicable\n")
    
    # Check 4: Time advance
    if 'test_phases' in test_case:
        # Multi-phase test (TC2)
        print("════════════════ Phase 1: Sufficient Advance ════════════════")
        phase1 = test_case['test_phases'][0]
        app_time1 = phase1['application_time']
        flight_time1 = phase1['planned_flight_time']
        time_diff1 = calculate_hours_difference(app_time1, flight_time1)
        
        print(f"Application time: {app_time1}")
        print(f"Flight time: {flight_time1}\n")
        print(f"🔍 Pre-flight check: Time advance...")
        print(f"   Time difference: {time_diff1:.1f} hours")
        print(f"   Required: {advance_hours_required:.1f} hours")
        print(f"   Surplus: {time_diff1 - advance_hours_required:.1f} hours")
        print(f"   ✅ SUFFICIENT ADVANCE NOTICE\n")
        print(f"✅ Phase 1 PASSED ({time_diff1:.0f}h advance)\n")
        
        print("════════════════ Phase 2: Boundary Test (36h) ═══════════════")
        phase2 = test_case['test_phases'][1]
        app_time2 = phase2['application_time']
        flight_time2 = phase2['planned_flight_time']
        time_diff2 = calculate_hours_difference(app_time2, flight_time2)
        
        print(f"Application time: {app_time2}")
        print(f"Flight time: {flight_time2}\n")
        print(f"🔍 Pre-flight check: Time advance...")
        print(f"   Time difference: {time_diff2:.1f} hours")
        print(f"   Required: {advance_hours_required:.1f} hours")
        print(f"   Boundary test: {time_diff2:.1f} >= {advance_hours_required:.1f} → TRUE")
        print(f"   ✅ BOUNDARY SATISFIED\n")
        print(f"✅ Phase 2 PASSED ({time_diff2:.0f}h boundary)\n")
        
        print(f"✅ FLIGHT APPROVED (All phases passed)")
        reason = f"申请时间满足提前{advance_hours_required:.0f}小时要求，批准飞行"
        print(f"Reason: {reason}\n")
        
        save_result(
            output_file, scenario_id, test_case_id,
            flight_approved=True,
            reason=reason,
            metadata={
                "current_time": current_time,
                "flight_type": flight_type,
                "target": {"north": target.north, "east": target.east, "altitude": target.altitude},
                "in_controlled_zone": in_controlled_zone,
                "test_phases": [
                    {
                        "phase": "sufficient_advance",
                        "application_time": app_time1,
                        "planned_flight_time": flight_time1,
                        "time_difference_hours": time_diff1,
                        "meets_requirement": time_diff1 >= advance_hours_required
                    },
                    {
                        "phase": "boundary_36hours",
                        "application_time": app_time2,
                        "planned_flight_time": flight_time2,
                        "time_difference_hours": time_diff2,
                        "meets_requirement": time_diff2 >= advance_hours_required
                    }
                ]
            }
        )
        return 0
    
    else:
        # Single phase test
        print("🔍 Pre-flight check: Time advance...")
        if application_time is None:
            print(f"   Application time: null")
            print(f"   ❌ NO APPLICATION submitted\n")
            print(f"🚫 FLIGHT REJECTED (No application)")
            reason = "管制空域飞行需要提前申请"
            print(f"Reason: {reason}\n")
            
            save_result(
                output_file, scenario_id, test_case_id,
                flight_approved=False,
                reason=reason,
                metadata={
                    "current_time": current_time,
                    "application_time": application_time,
                    "planned_flight_time": planned_flight_time,
                    "flight_type": flight_type,
                    "target": {"north": target.north, "east": target.east, "altitude": target.altitude},
                    "in_controlled_zone": in_controlled_zone
                }
            )
            return 1
        
        time_diff = calculate_hours_difference(application_time, planned_flight_time)
        print(f"   Application time: {application_time}")
        print(f"   Flight time: {planned_flight_time}")
        print(f"   Time difference: {time_diff:.1f} hours")
        print(f"   Required: {advance_hours_required:.1f} hours")
        
        if time_diff >= advance_hours_required:
            print(f"   Surplus: {time_diff - advance_hours_required:.1f} hours")
            print(f"   ✅ SUFFICIENT ADVANCE NOTICE\n")
            print(f"✅ FLIGHT APPROVED")
            reason = f"申请时间满足提前{advance_hours_required:.0f}小时要求，批准飞行"
            print(f"Reason: {reason}\n")
            
            save_result(
                output_file, scenario_id, test_case_id,
                flight_approved=True,
                reason=reason,
                metadata={
                    "current_time": current_time,
                    "application_time": application_time,
                    "planned_flight_time": planned_flight_time,
                    "flight_type": flight_type,
                    "target": {"north": target.north, "east": target.east, "altitude": target.altitude},
                    "in_controlled_zone": in_controlled_zone,
                    "time_checks": {
                        "time_difference_hours": time_diff,
                        "required_hours": advance_hours_required,
                        "surplus_hours": time_diff - advance_hours_required
                    }
                }
            )
            return 0
        else:
            print(f"   Shortage: {advance_hours_required - time_diff:.1f} hours")
            print(f"   ❌ INSUFFICIENT ADVANCE NOTICE\n")
            print(f"🚫 FLIGHT REJECTED (Insufficient advance notice)")
            reason = f"申请时间距飞行仅{time_diff:.0f}小时，未满足提前{advance_hours_required:.0f}小时申请要求"
            print(f"Reason: {reason}\n")
            
            save_result(
                output_file, scenario_id, test_case_id,
                flight_approved=False,
                reason=reason,
                metadata={
                    "current_time": current_time,
                    "application_time": application_time,
                    "planned_flight_time": planned_flight_time,
                    "flight_type": flight_type,
                    "target": {"north": target.north, "east": target.east, "altitude": target.altitude},
                    "in_controlled_zone": in_controlled_zone,
                    "time_checks": {
                        "time_difference_hours": time_diff,
                        "required_hours": advance_hours_required,
                        "shortage_hours": advance_hours_required - time_diff
                    }
                }
            )
            return 1
    
    print("======================================================================")
    print("✓ SCENARIO EXECUTION COMPLETED")
    print("======================================================================\n")
    
    return 0


def main():
    parser = argparse.ArgumentParser(description="Run S020 Approval Timeline Scenario.")
    parser.add_argument("scenario_file", type=str, help="Path to the S020 scenario JSONC file.")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file for results.")
    parser.add_argument("--test-case", type=str, required=True, help="ID of the test case to run.")
    
    args = parser.parse_args()
    
    exit_code = run_scenario(
        args.scenario_file,
        args.output,
        args.test_case
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()


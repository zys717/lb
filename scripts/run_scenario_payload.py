#!/usr/bin/env python3
"""
run_scenario_payload.py - Payload and Drop Restrictions Scenario Runner

Specialized script for S017 - Payload and Drop Restrictions
- Pre-flight: Check payload weight limit
- In-flight: Check drop zone restrictions and authorization

Author: LAE-GPT Team
Date: 2025-10-31
Version: 1.0

Usage:
    # Normal payload flight
    python run_scenario_payload.py scenario.jsonc --output traj.json --test-case TC2 --payload 3.0
    
    # With drop operation
    python run_scenario_payload.py scenario.jsonc --output traj.json --test-case TC4 --payload 2.5 --include-drop --has-approval
    
    # Agricultural exemption
    python run_scenario_payload.py scenario.jsonc --output traj.json --test-case TC7 --payload 3.0 --include-drop --drone-type agricultural
"""

import sys
import json
import asyncio
import argparse
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

# ProjectAirSim imports
try:
    from projectairsim import ProjectAirSimClient, World, Drone
except ImportError:
    print("ERROR: ProjectAirSim not found. This script must run on the server.")
    print("Install with: pip install -e /path/to/ProjectAirSim/client/python/projectairsim")
    sys.exit(1)


# ============================================================================
# SECTION 1: Data Classes
# ============================================================================

@dataclass
class Position3D:
    """Position in NED coordinates."""
    north: float
    east: float
    down: float
    
    @property
    def altitude(self) -> float:
        """Get altitude (negative of down)."""
        return -self.down


@dataclass
class DropZoneConfig:
    """Drop zone configuration."""
    zone_id: str
    zone_type: str  # "urban", "rural", "agricultural", "crowd"
    center_north: float
    center_east: float
    center_down: float
    radius: float
    drop_prohibited: bool = False
    drop_allowed_with_approval: bool = False
    drop_allowed: bool = False  # Always allowed (e.g., agricultural)
    description: str = ""
    
    def is_position_in_zone(self, position: Position3D) -> bool:
        """Check if position is within this zone."""
        dx = position.north - self.center_north
        dy = position.east - self.center_east
        distance = math.sqrt(dx**2 + dy**2)
        return distance <= self.radius


@dataclass
class PayloadConfig:
    """Payload restrictions configuration."""
    max_payload_kg: float = 5.0
    check_on_takeoff: bool = True
    drop_requires_approval: bool = True
    agricultural_exemption: bool = True


@dataclass
class ScenarioConfig:
    """Parsed scenario configuration."""
    scenario_id: str
    actors: List[Dict[str, Any]]
    drop_zones: List[DropZoneConfig]
    payload_config: PayloadConfig
    test_info: Optional[Dict[str, Any]] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrajectoryRecorder:
    """Records drone trajectory during scenario execution."""
    points: List[Dict[str, Any]] = field(default_factory=list)
    start_time: float = 0.0
    
    def start(self) -> None:
        """Start recording."""
        import time
        self.start_time = time.time()
        self.points = []
    
    def record_point(self, position: Position3D, timestamp: Optional[float] = None) -> None:
        """Record a trajectory point."""
        if timestamp is None:
            import time
            timestamp = time.time() - self.start_time
        
        self.points.append({
            'timestamp': timestamp,
            'position': {
                'north': position.north,
                'east': position.east,
                'down': position.down
            }
        })
    
    def save(self, output_file: Path, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save trajectory to JSON file."""
        from datetime import datetime
        data = {
            'metadata': metadata or {},
            'recorded_at': datetime.now().isoformat(),
            'duration_seconds': self.points[-1]['timestamp'] if self.points else 0.0,
            'trajectory': self.points
        }
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Trajectory saved: {output_file} ({len(self.points)} points)")


# ============================================================================
# SECTION 2: Configuration Loading
# ============================================================================

def strip_json_comments(text: str) -> str:
    """Remove JavaScript-style comments from JSON."""
    import re
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text


def load_scenario_config(scenario_file: Path) -> ScenarioConfig:
    """Load and parse scenario configuration from JSONC file."""
    with open(scenario_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content_no_comments = strip_json_comments(content)
    data = json.loads(content_no_comments)
    
    # Parse drop zones
    drop_zones = []
    for zone in data.get('drop_zones', []):
        center = zone.get('center', {}).get('xyz', '0.0 0.0 0.0').split()
        drop_zone = DropZoneConfig(
            zone_id=zone.get('id', ''),
            zone_type=zone.get('type', ''),
            center_north=float(center[0]),
            center_east=float(center[1]),
            center_down=float(center[2]),
            radius=zone.get('radius', 0.0),
            drop_prohibited=zone.get('drop_prohibited', False),
            drop_allowed_with_approval=zone.get('drop_allowed_with_approval', False),
            drop_allowed=zone.get('drop_allowed', False),
            description=zone.get('description', '')
        )
        drop_zones.append(drop_zone)
    
    # Parse payload configuration
    payload_restrictions = data.get('payload_restrictions', {})
    payload_config = PayloadConfig(
        max_payload_kg=payload_restrictions.get('max_payload_kg', 5.0),
        check_on_takeoff=payload_restrictions.get('check_on_takeoff', True),
        drop_requires_approval=payload_restrictions.get('drop_requires_approval', True),
        agricultural_exemption=payload_restrictions.get('agricultural_exemption', True)
    )
    
    return ScenarioConfig(
        scenario_id=data.get('id', 'unknown'),
        actors=data.get('actors', []),
        drop_zones=drop_zones,
        payload_config=payload_config,
        test_info=data.get('test_info'),
        raw_data=data
    )


# ============================================================================
# SECTION 3: Drone State Access
# ============================================================================

def get_drone_position(drone: Drone) -> Position3D:
    """Get current drone position."""
    pose = drone.get_ground_truth_pose()
    translation = pose['translation']
    
    return Position3D(
        north=translation['x'],
        east=translation['y'],
        down=translation['z']
    )


# ============================================================================
# SECTION 4: Payload and Drop Checks ⭐ CORE LOGIC
# ============================================================================

def check_payload_limit(
    payload_kg: float,
    max_payload_kg: float
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if payload exceeds maximum weight limit.
    
    Args:
        payload_kg: Current payload weight
        max_payload_kg: Maximum allowed payload
    
    Returns:
        (is_safe, reason, details)
    """
    if payload_kg > max_payload_kg:
        excess_kg = payload_kg - max_payload_kg
        excess_pct = (excess_kg / max_payload_kg) * 100
        return False, f"载重{payload_kg}kg超过最大限制{max_payload_kg}kg", {
            'payload_kg': payload_kg,
            'max_allowed_kg': max_payload_kg,
            'excess_kg': excess_kg,
            'excess_percentage': excess_pct,
            'violation': 'PAYLOAD_EXCEEDED'
        }
    
    margin_kg = max_payload_kg - payload_kg
    margin_pct = (margin_kg / max_payload_kg) * 100
    
    return True, f"载重{payload_kg}kg在限制内", {
        'payload_kg': payload_kg,
        'max_allowed_kg': max_payload_kg,
        'margin_kg': margin_kg,
        'margin_percentage': margin_pct,
        'boundary_test': (payload_kg == max_payload_kg)
    }


def detect_drop_zone(
    position: Position3D,
    drop_zones: List[DropZoneConfig]
) -> Optional[DropZoneConfig]:
    """Detect which drop zone the position is in."""
    for zone in drop_zones:
        if zone.is_position_in_zone(position):
            return zone
    return None


def check_drop_allowed(
    position: Position3D,
    drop_zones: List[DropZoneConfig],
    has_approval: bool,
    drone_type: str,
    payload_config: PayloadConfig
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if drop operation is allowed at current position.
    
    Priority logic:
    1. Crowd protection (absolute prohibition)
    2. Zone type restrictions (urban/rural)
    3. Authorization requirement
    4. Agricultural exemption
    
    Args:
        position: Current drone position
        drop_zones: List of drop zones
        has_approval: Whether drop approval was obtained
        drone_type: Drone type ("agricultural" or "general")
        payload_config: Payload configuration
    
    Returns:
        (is_allowed, reason, details)
    """
    # Detect current zone
    zone = detect_drop_zone(position, drop_zones)
    
    if zone is None:
        # No specific zone detected - default rules apply
        if not has_approval and payload_config.drop_requires_approval:
            return False, "投放操作需要提前申请审批", {
                'zone_id': None,
                'zone_type': 'unclassified',
                'has_approval': has_approval,
                'required_approval': True,
                'violation': 'DROP_WITHOUT_APPROVAL'
            }
        return True, "允许投放（无特殊限制区域）", {
            'zone_id': None,
            'zone_type': 'unclassified',
            'has_approval': has_approval
        }
    
    details = {
        'zone_id': zone.zone_id,
        'zone_type': zone.zone_type,
        'zone_center': [zone.center_north, zone.center_east, zone.center_down],
        'has_approval': has_approval
    }
    
    # Priority 1: Crowd protection (absolute prohibition)
    if zone.zone_type == "crowd":
        details['absolute_prohibition'] = True
        details['approval_overridden'] = has_approval
        details['protection_priority'] = 'crowd_safety'
        details['violation'] = 'DROP_OVER_CROWD'
        return False, "人群聚集区上方严格禁止投放物品，即使有审批也不允许（公共安全优先）", details
    
    # Priority 2: Urban restriction
    if zone.drop_prohibited:
        details['violation'] = 'DROP_IN_PROHIBITED_ZONE'
        return False, f"{zone.zone_type}区域严格禁止投放物品", details
    
    # Priority 3: Agricultural exemption
    if (drone_type == "agricultural" and 
        zone.zone_type == "agricultural" and 
        zone.drop_allowed and
        payload_config.agricultural_exemption):
        details['exemption_applied'] = True
        details['exemption_type'] = 'agricultural'
        details['regulation_reference'] = '《条例》第31条第二款第二项（常规农用无人驾驶航空器作业飞行活动除外）'
        return True, "农用无人机在农业作业区投放，享受豁免无需审批", details
    
    # Priority 4: Approval-based zones
    if zone.drop_allowed_with_approval:
        if not has_approval:
            details['violation'] = 'DROP_WITHOUT_APPROVAL'
            details['required_approval'] = True
            return False, f"{zone.zone_type}区域投放需要审批", details
        else:
            return True, f"{zone.zone_type}区域已审批，允许投放", details
    
    # Priority 5: Always allowed zones
    if zone.drop_allowed:
        return True, f"{zone.zone_type}区域允许投放", details
    
    # Default: require approval
    if not has_approval:
        details['violation'] = 'DROP_WITHOUT_APPROVAL'
        return False, "投放操作需要提前申请审批", details
    
    return True, "允许投放", details


# ============================================================================
# SECTION 5: Scenario Execution
# ============================================================================

async def run_scenario_auto(
    scenario_config: ScenarioConfig,
    scenario_file: Path,
    client: ProjectAirSimClient,
    test_command: str,
    recorder: TrajectoryRecorder,
    payload_kg: float,
    include_drop: bool,
    has_approval: bool,
    drone_type: str
) -> Dict[str, Any]:
    """
    Run scenario in automatic mode with payload and drop checks.
    
    Flow:
    1. Pre-flight: Check payload weight limit
    2. If OK: Execute flight
    3. If drop requested: Check drop zone and authorization
    """
    print(f"Test Command: {test_command}")
    print(f"Payload: {payload_kg}kg")
    if include_drop:
        print(f"Drop operation requested")
        print(f"Has approval: {has_approval}")
        print(f"Drone type: {drone_type}")
    
    # PRE-FLIGHT CHECK: Payload weight limit
    print(f"\n🔍 Pre-flight check: Payload weight...")
    is_safe, reason, payload_details = check_payload_limit(
        payload_kg,
        scenario_config.payload_config.max_payload_kg
    )
    
    print(f"   Payload: {payload_kg}kg")
    print(f"   Maximum: {scenario_config.payload_config.max_payload_kg}kg")
    
    if not is_safe:
        # REJECT: Payload exceeds limit
        print(f"   Excess: {payload_details['excess_kg']:.1f}kg ({payload_details['excess_percentage']:.0f}%)")
        print(f"   ❌ PAYLOAD EXCEEDED")
        print(f"\n🚫 FLIGHT REJECTED (Payload exceeds limit)")
        print(f"   Reason: {reason}")
        print(f"   Recommended: 减少载重至{scenario_config.payload_config.max_payload_kg}kg以内")
        
        return {
            'success': False,
            'mode': 'auto',
            'flight_approved': False,
            'reason': 'Payload exceeded',
            'payload_details': payload_details,
            'trajectory_points': 0
        }
    
    # Payload OK
    print(f"   Margin: {payload_details['margin_kg']:.1f}kg ({payload_details['margin_percentage']:.0f}%)")
    if payload_details.get('boundary_test'):
        print(f"   Judgment: {payload_kg} ≤ {scenario_config.payload_config.max_payload_kg} → True")
        print(f"   ✓ AT BOUNDARY (SAFE)")
    else:
        print(f"   ✓ SAFE")
    
    print(f"\n✅ Payload check passed")
    
    # Load scene and connect drone
    print(f"Loading scene from: {scenario_file}")
    world = World(client, str(scenario_file), delay_after_load_sec=2)
    
    drone_name = scenario_config.actors[0]['name']
    print(f"Creating drone object: {drone_name}")
    drone = Drone(client, world, drone_name)
    print(f"✓ Connected to drone: {drone_name}")
    
    # Arm and enable API control
    drone.enable_api_control()
    drone.arm()
    
    # Takeoff
    print("Taking off...")
    await drone.takeoff_async()
    await asyncio.sleep(3)
    
    takeoff_pos = get_drone_position(drone)
    print(f"✓ Takeoff completed: N={takeoff_pos.north:.1f}, E={takeoff_pos.east:.1f}, Alt={takeoff_pos.altitude:.1f}m")
    
    # Climb to operational altitude
    print(f"Climbing to operational altitude...")
    await drone.move_to_position_async(
        north=takeoff_pos.north,
        east=takeoff_pos.east,
        down=-50.0,
        velocity=5.0
    )
    
    for i in range(100):
        current_pos = get_drone_position(drone)
        if current_pos.altitude >= 45.0:
            break
        await asyncio.sleep(0.1)
    
    initial_pos = get_drone_position(drone)
    print(f"✓ Ready at: N={initial_pos.north:.1f}, E={initial_pos.east:.1f}, Alt={initial_pos.altitude:.1f}m")
    
    # Start recording
    recorder.start()
    recorder.record_point(initial_pos, 0.0)
    
    # Parse command
    import re
    match = re.match(
        r'move_to_position\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)',
        test_command
    )
    
    if not match:
        print(f"ERROR: Unsupported command: {test_command}")
        return {'success': False, 'reason': 'Invalid command format'}
    
    target_n = float(match.group(1))
    target_e = float(match.group(2))
    target_alt = float(match.group(3))
    target_d = -target_alt
    
    print(f"\n🚀 Executing: move_to_position({target_n}, {target_e}, {target_alt})")
    print(f"   Target: N={target_n}, E={target_e}, Alt={target_alt}m")
    
    # Execute movement
    print("✓ Executing movement...")
    await drone.move_to_position_async(
        north=target_n,
        east=target_e,
        down=target_d,
        velocity=15.0
    )
    
    # Monitor flight
    max_iterations = 3000
    for iteration in range(max_iterations):
        await asyncio.sleep(0.1)
        
        position = get_drone_position(drone)
        recorder.record_point(position)
        
        dist_to_target = math.sqrt(
            (position.north - target_n)**2 +
            (position.east - target_e)**2 +
            (position.down - target_d)**2
        )
        
        if iteration % 50 == 0 and iteration > 0:
            print(f"   [{iteration:4d}] N={position.north:6.1f} E={position.east:6.1f} Alt={position.altitude:5.1f}m | To target: {dist_to_target:6.1f}m")
        
        if dist_to_target < 2.0:
            print(f"✓ Target reached at N={position.north:.1f}, E={position.east:.1f}, Alt={position.altitude:.1f}m")
            break
    
    final_pos = get_drone_position(drone)
    recorder.record_point(final_pos)
    
    # Check if drop operation requested
    drop_approved = False
    drop_details = {}
    
    if include_drop:
        print(f"\n🔍 Drop check: Verifying drop zone...")
        print(f"   Position: N={final_pos.north:.1f}, E={final_pos.east:.1f}, Alt={final_pos.altitude:.1f}m")
        
        drop_allowed, drop_reason, drop_details = check_drop_allowed(
            final_pos,
            scenario_config.drop_zones,
            has_approval,
            drone_type,
            scenario_config.payload_config
        )
        
        if drop_details.get('zone_id'):
            print(f"   Zone detected: {drop_details['zone_id']} ({drop_details['zone_type']})")
        else:
            print(f"   Zone detected: None (unclassified area)")
        
        if drop_allowed:
            print(f"   ✓ ALL CONDITIONS MET")
            print(f"\n✅ DROP APPROVED")
            if drop_details.get('exemption_applied'):
                print(f"   Exemption: {drop_details['exemption_type']}")
                print(f"   Regulation: {drop_details.get('regulation_reference', '')}")
            print(f"   Reason: {drop_reason}")
            drop_approved = True
        else:
            print(f"   ❌ DROP NOT ALLOWED")
            print(f"\n🚫 DROP COMMAND REJECTED")
            print(f"   Reason: {drop_reason}")
            if drop_details.get('absolute_prohibition'):
                print(f"   Priority: 公共安全优先级最高")
                print(f"   Note: 即使有审批也不允许投放")
            drop_approved = False
    
    return {
        'success': True,
        'mode': 'auto',
        'flight_approved': True,
        'drop_requested': include_drop,
        'drop_approved': drop_approved,
        'payload_details': payload_details,
        'drop_details': drop_details if include_drop else None,
        'trajectory_points': len(recorder.points)
    }


# ============================================================================
# SECTION 6: Main Entry Point
# ============================================================================

async def run_scenario_async(
    scenario_file: Path,
    output_file: Path,
    mode: str = "auto",
    test_command: Optional[str] = None,
    test_case_id: Optional[str] = None,
    payload_kg: float = 3.0,
    include_drop: bool = False,
    has_approval: bool = False,
    drone_type: str = "general"
) -> int:
    """Main async entry point for scenario execution."""
    try:
        # Load scenario configuration
        print(f"Loading scenario: {scenario_file}")
        scenario_config = load_scenario_config(scenario_file)
        print(f"✓ Scenario loaded: {scenario_config.scenario_id}")
        print(f"✓ Drop zones loaded: {len(scenario_config.drop_zones)}")
        print(f"✓ Payload restrictions: max={scenario_config.payload_config.max_payload_kg}kg")
        
        # Load test case if specified
        if test_case_id and 'test_cases' in scenario_config.raw_data:
            test_cases = scenario_config.raw_data['test_cases']
            matching_case = next((tc for tc in test_cases if tc.get('id') == test_case_id), None)
            
            if not matching_case:
                matching_case = next((tc for tc in test_cases if tc.get('id', '').startswith(test_case_id)), None)
            
            if matching_case:
                print(f"✓ Loading test case: {matching_case.get('id')}")
                if not test_command:
                    test_command = matching_case.get('command')
                # Override with test case specific values if not provided
                if 'payload_kg' in matching_case:
                    payload_kg = matching_case['payload_kg']
                if 'has_drop_approval' in matching_case:
                    has_approval = matching_case['has_drop_approval']
                if 'drone_type' in matching_case:
                    drone_type = matching_case['drone_type']
            else:
                print(f"⚠ Test case {test_case_id} not found")
        
        # Connect to ProjectAirSim
        print("Connecting to ProjectAirSim...")
        client = ProjectAirSimClient()
        client.connect()
        print("✓ Connected to ProjectAirSim")
        
        print("\n" + "="*70)
        print("S017 MODE - PAYLOAD AND DROP RESTRICTIONS")
        print("="*70 + "\n")
        
        # Create trajectory recorder
        recorder = TrajectoryRecorder()
        
        # Run scenario
        result = await run_scenario_auto(
            scenario_config,
            scenario_file,
            client,
            test_command,
            recorder,
            payload_kg,
            include_drop,
            has_approval,
            drone_type
        )
        
        # Save trajectory
        metadata = {
            'scenario_id': scenario_config.scenario_id,
            'scenario_file': str(scenario_file),
            'mode': mode,
            'payload_kg': payload_kg,
            'include_drop': include_drop,
            'has_approval': has_approval,
            'drone_type': drone_type,
            'execution_result': result
        }
        recorder.save(output_file, metadata)
        
        # Print summary
        print("\n" + "="*70)
        if not result.get('flight_approved'):
            print("⚠️  FLIGHT REJECTED (Payload exceeded)")
        elif result.get('drop_requested') and not result.get('drop_approved'):
            print("⚠️  FLIGHT COMPLETED, DROP REJECTED")
        elif result.get('success', False):
            print("✓ SCENARIO EXECUTION COMPLETED")
        print("="*70)
        
        return 0 if result.get('success', False) else 1
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run payload and drop restriction scenarios (S017)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Test payload limit
  python run_scenario_payload.py scenario.jsonc --output traj.json --test-case TC1 --payload 8.0
  
  # Test drop with approval
  python run_scenario_payload.py scenario.jsonc --output traj.json --test-case TC4 --payload 2.5 --include-drop --has-approval
  
  # Test agricultural exemption
  python run_scenario_payload.py scenario.jsonc --output traj.json --test-case TC7 --payload 3.0 --include-drop --drone-type agricultural
        '''
    )
    
    parser.add_argument('scenario_file', type=str, help='Path to scenario JSONC file')
    parser.add_argument('--output', '-o', type=str, required=True, help='Output trajectory JSON file')
    parser.add_argument('--mode', type=str, default='auto', choices=['auto'], help='Execution mode (default: auto)')
    parser.add_argument('--command', type=str, help='Test command (e.g., "move_to_position(800, 0, 50)")')
    parser.add_argument('--test-case', type=str, help='Test case ID (e.g., TC1)')
    parser.add_argument('--payload', type=float, default=3.0, help='Payload weight in kg (default: 3.0)')
    parser.add_argument('--include-drop', action='store_true', help='Include drop operation')
    parser.add_argument('--has-approval', action='store_true', help='Has drop approval')
    parser.add_argument('--drone-type', type=str, default='general', choices=['general', 'agricultural'], help='Drone type (default: general)')
    
    args = parser.parse_args()
    
    scenario_file = Path(args.scenario_file)
    output_file = Path(args.output)
    
    if not scenario_file.exists():
        print(f"ERROR: Scenario file not found: {scenario_file}")
        return 1
    
    if not args.command and not args.test_case:
        print("ERROR: Either --command or --test-case must be specified")
        return 1
    
    # Run async scenario
    exit_code = asyncio.run(run_scenario_async(
        scenario_file,
        output_file,
        mode=args.mode,
        test_command=args.command,
        test_case_id=args.test_case,
        payload_kg=args.payload,
        include_drop=args.include_drop,
        has_approval=args.has_approval,
        drone_type=args.drone_type
    ))
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())


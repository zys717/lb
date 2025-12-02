#!/usr/bin/env python3
"""
VLOS and Avoidance Scenario Runner for LAE-GPT (S013-S016)

This script handles scenarios involving visual line of sight (VLOS) 
requirements and avoidance rules.

Supported Scenarios:
  - S013: VLOS Requirement (Visual Line of Sight)
  - S014: BVLOS Operations (Beyond Visual Line of Sight)
  - S015: Visual Observer Cooperation
  - S016: Avoidance Rules

Usage:
    python run_scenario_vlos.py <scenario_file.jsonc> --output <trajectory_file.json>
    
Example:
    python run_scenario_vlos.py ../scenarios/basic/S013_vlos_requirement.jsonc \
        --output ../test_logs/trajectory_S013_TC1.json \
        --mode auto --test-case TC1

Note:
    This script must be run on the remote server with ProjectAirSim running.
"""

import argparse
import asyncio
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Import ProjectAirSim high-level API
try:
    from projectairsim import ProjectAirSimClient, World, Drone
except ImportError:
    print("ERROR: ProjectAirSim not found. This script must run on the server.", file=sys.stderr)
    print("Install with: pip install -e /path/to/ProjectAirSim/client/python/projectairsim", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# SECTION 1: Data Classes and Configuration
# ============================================================================

@dataclass
class Position3D:
    """Represents a 3D position in NED coordinate system."""
    north: float
    east: float
    down: float
    
    @property
    def altitude(self) -> float:
        """Get altitude (positive up)."""
        return -self.down
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to (north, east, down) tuple."""
        return (self.north, self.east, self.down)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'north': self.north,
            'east': self.east,
            'down': self.down,
            'altitude': self.altitude
        }


@dataclass
class Velocity3D:
    """Represents a 3D velocity vector in NED coordinate system."""
    north: float  # m/s
    east: float   # m/s
    down: float   # m/s
    
    @property
    def ground_speed_ms(self) -> float:
        """Get ground speed in m/s (3D magnitude)."""
        return math.sqrt(self.north**2 + self.east**2 + self.down**2)
    
    @property
    def ground_speed_kmh(self) -> float:
        """Get ground speed in km/h."""
        return self.ground_speed_ms * 3.6
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'north': self.north,
            'east': self.east,
            'down': self.down,
            'ground_speed_ms': self.ground_speed_ms,
            'ground_speed_kmh': self.ground_speed_kmh
        }


@dataclass
class VLOSConfig:
    """VLOS (Visual Line of Sight) configuration (S013)."""
    enabled: bool = True
    operator_north: float = 0.0
    operator_east: float = 0.0
    operator_down: float = 0.0
    max_vlos_range_m: float = 500.0
    check_method: str = "horizontal"  # "horizontal" or "3d"
    description: str = "操作员视距限制"
    
    def get_operator_position(self) -> Position3D:
        """Get operator position as Position3D."""
        return Position3D(
            north=self.operator_north,
            east=self.operator_east,
            down=self.operator_down
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operator_position': {
                'north': self.operator_north,
                'east': self.operator_east,
                'altitude': -self.operator_down
            },
            'max_vlos_range_m': self.max_vlos_range_m,
            'check_method': self.check_method
        }


@dataclass
class BVLOSWaiverConfig:
    """BVLOS (Beyond Visual Line of Sight) waiver configuration (S014)."""
    waiver_id: str
    waiver_type: str  # "visual_observer", "technical_means", "special_permit"
    max_effective_range_m: float
    # Visual observer specific
    observer_north: float = 0.0
    observer_east: float = 0.0
    observer_down: float = 0.0
    observer_vlos_range_m: float = 500.0
    # Technical means specific
    radar_coverage_m: float = 0.0
    # Special permit specific
    permit_number: str = ""
    
    def get_observer_position(self) -> Position3D:
        """Get observer position as Position3D (for visual_observer waiver)."""
        return Position3D(
            north=self.observer_north,
            east=self.observer_east,
            down=self.observer_down
        )


@dataclass
class ScenarioConfig:
    """Parsed scenario configuration."""
    scenario_id: str
    actors: List[Dict[str, Any]]
    test_info: Optional[Dict[str, Any]] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    vlos_config: Optional[VLOSConfig] = None
    bvlos_waivers: Dict[str, BVLOSWaiverConfig] = field(default_factory=dict)
    enabled_waivers: List[str] = field(default_factory=list)


@dataclass
class TrajectoryRecorder:
    """Records drone trajectory during scenario execution."""
    points: List[Dict[str, Any]] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    
    def record_point(self, position: Position3D, velocity: Velocity3D):
        """Record a trajectory point."""
        self.points.append({
            'timestamp': time.time() - self.start_time,
            'position': position.to_dict(),
            'velocity': velocity.to_dict()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trajectory to dictionary format."""
        return {
            'points': self.points,
            'total_points': len(self.points),
            'duration_seconds': time.time() - self.start_time
        }


# ============================================================================
# SECTION 2: Scenario Configuration Loading
# ============================================================================

def strip_json_comments(text: str) -> str:
    """
    Remove JSON comments (lines starting with //).
    
    Args:
        text: JSON text with comments
    
    Returns:
        JSON text without comments
    """
    lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped.startswith('//'):
            lines.append(line)
    return '\n'.join(lines)


def load_scenario_config(scenario_file: Path) -> ScenarioConfig:
    """
    Load and parse scenario configuration from JSONC file.
    
    Args:
        scenario_file: Path to scenario configuration file
    
    Returns:
        Parsed scenario configuration
    """
    # Read and parse JSON (with comments)
    with open(scenario_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Strip comments
    content_no_comments = strip_json_comments(content)
    
    # Parse JSON
    data = json.loads(content_no_comments)
    
    # Parse VLOS configuration if present (S013)
    vlos_config = None
    if 'vlos_restrictions' in data:
        vlos_data = data['vlos_restrictions']
        if vlos_data.get('enabled', True):
            operator_pos = vlos_data.get('operator_position', {})
            xyz = operator_pos.get('xyz', '0.0 0.0 0.0').split()
            
            vlos_config = VLOSConfig(
                enabled=True,
                operator_north=float(xyz[0]),
                operator_east=float(xyz[1]),
                operator_down=float(xyz[2]),
                max_vlos_range_m=vlos_data.get('max_vlos_range_m', 500.0),
                check_method=vlos_data.get('check_method', 'horizontal'),
                description=vlos_data.get('description', '操作员视距限制')
            )
    
    # Parse BVLOS waiver configuration if present (S014)
    bvlos_waivers = {}
    if 'bvlos_waivers' in data:
        bvlos_data = data['bvlos_waivers']
        if bvlos_data.get('enabled', False):
            for waiver_data in bvlos_data.get('available_waivers', []):
                waiver_id = waiver_data.get('waiver_id', '')
                waiver_type = waiver_data.get('type', '')
                conditions = waiver_data.get('conditions', {})
                
                if waiver_type == 'visual_observer':
                    observer_pos = conditions.get('observer_position', {})
                    xyz = observer_pos.get('xyz', '0.0 0.0 0.0').split()
                    waiver = BVLOSWaiverConfig(
                        waiver_id=waiver_id,
                        waiver_type=waiver_type,
                        max_effective_range_m=conditions.get('max_effective_range_m', 1100.0),
                        observer_north=float(xyz[0]),
                        observer_east=float(xyz[1]),
                        observer_down=float(xyz[2]),
                        observer_vlos_range_m=conditions.get('observer_vlos_range_m', 500.0)
                    )
                elif waiver_type == 'technical_means':
                    waiver = BVLOSWaiverConfig(
                        waiver_id=waiver_id,
                        waiver_type=waiver_type,
                        max_effective_range_m=conditions.get('max_effective_range_m', 2000.0),
                        radar_coverage_m=conditions.get('radar_coverage_m', 2000.0)
                    )
                elif waiver_type == 'special_permit':
                    waiver = BVLOSWaiverConfig(
                        waiver_id=waiver_id,
                        waiver_type=waiver_type,
                        max_effective_range_m=conditions.get('max_effective_range_m', 5000.0),
                        permit_number=conditions.get('permit_number', '')
                    )
                else:
                    continue
                
                bvlos_waivers[waiver_id] = waiver
    
    return ScenarioConfig(
        scenario_id=data.get('id', 'unknown'),
        actors=data.get('actors', []),
        test_info=data.get('test_info'),
        raw_data=data,
        vlos_config=vlos_config,
        bvlos_waivers=bvlos_waivers
    )


# ============================================================================
# SECTION 3: Drone State Access
# ============================================================================

def get_drone_position(drone: Drone) -> Position3D:
    """
    Get current drone position.
    
    Args:
        drone: Drone object
    
    Returns:
        Current position in NED coordinates
    """
    pose = drone.get_ground_truth_pose()
    translation = pose['translation']
    
    return Position3D(
        north=translation['x'],
        east=translation['y'],
        down=translation['z']
    )


def get_drone_velocity(drone: Drone) -> Velocity3D:
    """
    Get current drone velocity.
    
    Args:
        drone: Drone object
    
    Returns:
        Current velocity in NED coordinates
    
    Note:
        ProjectAirSim Drone API does not provide velocity data directly.
        This function returns a zero velocity placeholder.
        Velocity monitoring is disabled in this version.
    """
    # ProjectAirSim API limitation: No direct velocity access
    # Return zero velocity (VLOS checks rely on position only)
    return Velocity3D(north=0.0, east=0.0, down=0.0)


# ============================================================================
# SECTION 4: VLOS Compliance Checks
# ============================================================================

def calculate_distance(
    pos1: Position3D,
    pos2: Position3D,
    method: str = "horizontal"
) -> float:
    """
    Calculate distance between two positions.
    
    Args:
        pos1: First position
        pos2: Second position
        method: "horizontal" for 2D distance, "3d" for 3D distance
    
    Returns:
        Distance in meters
    """
    if method == "horizontal":
        # 2D horizontal distance (recommended for VLOS)
        return math.sqrt(
            (pos1.north - pos2.north)**2 +
            (pos1.east - pos2.east)**2
        )
    else:
        # 3D distance
        return math.sqrt(
            (pos1.north - pos2.north)**2 +
            (pos1.east - pos2.east)**2 +
            (pos1.down - pos2.down)**2
        )


def check_vlos_requirements(
    target_position: Position3D,
    vlos_config: VLOSConfig
) -> Tuple[bool, str]:
    """
    Check VLOS (Visual Line of Sight) requirements.
    
    Args:
        target_position: Target position to check
        vlos_config: VLOS configuration
    
    Returns:
        Tuple of (is_compliant, reason)
    
    Regulations:
        - China: § 32(5) - 微型无人机必须保持视距内飞行
        - USA: Part 107.31 - 必须用肉眼持续看到无人机
    """
    if not vlos_config.enabled:
        return True, "无VLOS限制"
    
    operator_pos = vlos_config.get_operator_position()
    
    # Calculate distance
    distance = calculate_distance(
        target_position,
        operator_pos,
        method=vlos_config.check_method
    )
    
    # Check VLOS range
    if distance > vlos_config.max_vlos_range_m:
        return (
            False,
            f"超出视距范围（{distance:.1f}m > {vlos_config.max_vlos_range_m}m）"
            f"，违反VLOS要求（§32(5) / Part 107.31）"
        )
    else:
        return (
            True,
            f"在视距内（{distance:.1f}m <= {vlos_config.max_vlos_range_m}m）"
        )


def check_bvlos_waivers(
    target_position: Position3D,
    operator_position: Position3D,
    enabled_waiver_ids: List[str],
    available_waivers: Dict[str, BVLOSWaiverConfig]
) -> Tuple[bool, str, Optional[str]]:
    """
    Check if BVLOS waivers allow the flight.
    
    Args:
        target_position: Target position to check
        operator_position: Operator position
        enabled_waiver_ids: List of enabled waiver IDs
        available_waivers: Dictionary of available waivers
    
    Returns:
        Tuple of (is_approved, reason, waiver_type)
    
    Logic:
        1. Check each enabled waiver
        2. Visual Observer: check if target is within observer's VLOS
        3. Technical Means: check if target is within radar coverage
        4. Special Permit: check if target is within permit range
        5. Return True if any waiver approves the flight
    """
    if not enabled_waiver_ids:
        return False, "无可用BVLOS豁免", None
    
    for waiver_id in enabled_waiver_ids:
        if waiver_id not in available_waivers:
            continue
        
        waiver = available_waivers[waiver_id]
        
        if waiver.waiver_type == "visual_observer":
            # Check if target is within observer's VLOS
            observer_pos = waiver.get_observer_position()
            dist_to_observer = calculate_distance(
                target_position,
                observer_pos,
                method="horizontal"
            )
            
            if dist_to_observer <= waiver.observer_vlos_range_m:
                return (
                    True,
                    f"观察员豁免生效：目标在观察员视距内（{dist_to_observer:.1f}m <= {waiver.observer_vlos_range_m}m）",
                    "Visual Observer"
                )
        
        elif waiver.waiver_type == "technical_means":
            # Check if target is within radar coverage
            dist_to_operator = calculate_distance(
                target_position,
                operator_position,
                method="horizontal"
            )
            
            if dist_to_operator <= waiver.radar_coverage_m:
                return (
                    True,
                    f"技术手段豁免生效：雷达覆盖范围内（{dist_to_operator:.1f}m <= {waiver.radar_coverage_m}m）",
                    "Technical Means"
                )
            else:
                # Check if exceeds max effective range
                return (
                    False,
                    f"超出雷达覆盖范围（{dist_to_operator:.1f}m > {waiver.radar_coverage_m}m）",
                    None
                )
        
        elif waiver.waiver_type == "special_permit":
            # Check if target is within permit range
            dist_to_operator = calculate_distance(
                target_position,
                operator_position,
                method="horizontal"
            )
            
            if dist_to_operator <= waiver.max_effective_range_m:
                permit_info = f"（许可：{waiver.permit_number}）" if waiver.permit_number else ""
                return (
                    True,
                    f"特殊许可豁免生效：在批准范围内（{dist_to_operator:.1f}m <= {waiver.max_effective_range_m}m）{permit_info}",
                    "Special Permit"
                )
            else:
                # Exceeds permit range
                return (
                    False,
                    f"超出特殊许可范围（{dist_to_operator:.1f}m > {waiver.max_effective_range_m}m）",
                    None
                )
    
    return False, "所有豁免均不适用", None


# ============================================================================
# SECTION 5: Scenario Execution
# ============================================================================

async def run_scenario_auto(
    scenario_config: ScenarioConfig,
    scenario_file: Path,
    client: ProjectAirSimClient,
    test_command: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run scenario in automatic mode (execute predefined command).
    
    Args:
        scenario_config: Parsed scenario configuration
        scenario_file: Path to scenario file
        client: ProjectAirSim client
        test_command: Command to execute (optional)
    
    Returns:
        Execution result dictionary
    """
    print("\n" + "="*70)
    print("AUTOMATIC SCENARIO MODE - VLOS & AVOIDANCE")
    print("="*70)
    
    # Get test command from test_info or argument
    if scenario_config.test_info:
        if test_command is None:
            test_command = scenario_config.test_info.get('test_command')
    
    if not test_command:
        print("ERROR: No test command specified", file=sys.stderr)
        return {'success': False, 'reason': 'No test command'}
    
    print(f"\nTest Command: {test_command}")
    
    # Load scene (World constructor loads scene automatically)
    print(f"Loading scene from: {scenario_file}")
    world = World(client, str(scenario_file.absolute()), delay_after_load_sec=2)
    
    # Get drone actor
    drone_name = scenario_config.actors[0]['name']
    print(f"Creating drone object: {drone_name}")
    drone = Drone(client, world, drone_name)
    print(f"✓ Connected to drone: {drone_name}")
    
    # Arm and enable API control
    drone.enable_api_control()
    drone.arm()
    
    # Takeoff
    await drone.takeoff_async()
    
    # Get initial position after takeoff
    initial_pos = get_drone_position(drone)
    print(f"✓ Initial position: N={initial_pos.north:.1f}, E={initial_pos.east:.1f}, Alt={initial_pos.altitude:.1f}m")
    
    # Initialize trajectory recorder
    recorder = TrajectoryRecorder()
    initial_vel = get_drone_velocity(drone)
    recorder.record_point(initial_pos, initial_vel)
    
    # Parse and execute command
    print(f"\n🚀 Executing: {test_command}")
    
    if "move_to_position" in test_command:
        # Parse move_to_position command
        import re
        match = re.search(
            r'move_to_position\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)',
            test_command
        )
        if match:
            target_n = float(match.group(1))
            target_e = float(match.group(2))
            target_alt = float(match.group(3))
            target_d = -target_alt  # Convert altitude to down (NED)
            
            print(f"   Target: N={target_n}, E={target_e}, Alt={target_alt}m")
            
            # PRE-FLIGHT CHECK: VLOS requirements (S013) + BVLOS waivers (S014)
            if scenario_config.vlos_config:
                print("\n🔍 Pre-flight check: VLOS requirements...")
                target_position = Position3D(north=target_n, east=target_e, down=target_d)
                operator_position = scenario_config.vlos_config.get_operator_position()
                
                is_vlos_compliant, vlos_reason = check_vlos_requirements(
                    target_position,
                    scenario_config.vlos_config
                )
                
                if not is_vlos_compliant:
                    print(f"   ❌ {vlos_reason}")
                    
                    # Check BVLOS waivers if available (S014)
                    if scenario_config.bvlos_waivers and scenario_config.enabled_waivers:
                        print("\n🔍 Checking BVLOS waivers...")
                        is_waiver_approved, waiver_reason, waiver_type = check_bvlos_waivers(
                            target_position,
                            operator_position,
                            scenario_config.enabled_waivers,
                            scenario_config.bvlos_waivers
                        )
                        
                        if is_waiver_approved:
                            print(f"   ✓ {waiver_reason}")
                            print(f"\n✅ WAIVER APPLIED: {waiver_type}")
                            # Continue with flight
                        else:
                            print(f"   ❌ {waiver_reason}")
                            print("\n🚫 COMMAND REJECTED (超出所有可用豁免范围)")
                            
                            return {
                                'success': False,
                                'mode': 'auto',
                                'command_rejected': True,
                                'reason': 'Exceeds waiver limits',
                                'violations': [vlos_reason, waiver_reason],
                                'trajectory_points': len(recorder.points)
                            }
                    else:
                        # No waivers available
                        print("\n🚫 COMMAND REJECTED (VLOS violation, no waiver)")
                        
                        return {
                            'success': False,
                            'mode': 'auto',
                            'command_rejected': True,
                            'reason': 'VLOS violation, no waiver',
                            'violations': [vlos_reason],
                            'trajectory_points': len(recorder.points)
                        }
                else:
                    print(f"   ✓ {vlos_reason}")
            
            print("\n✅ All pre-flight checks passed")
            print("✓ Executing movement...")
            
            # Execute movement
            try:
                await drone.move_to_position_async(
                    north=target_n,
                    east=target_e,
                    down=target_d,
                    velocity=15.0  # Increased velocity for long-distance BVLOS flights (S014: up to 3000m)
                )
                
                # Record trajectory during movement
                while True:
                    position = get_drone_position(drone)
                    velocity = get_drone_velocity(drone)
                    recorder.record_point(position, velocity)
                    
                    # Check if reached target (within 1m)
                    dist = math.sqrt(
                        (position.north - target_n)**2 +
                        (position.east - target_e)**2 +
                        (position.down - target_d)**2
                    )
                    
                    if dist < 1.0:
                        print("✓ Target reached")
                        break
                    
                    await asyncio.sleep(0.1)
            
            except Exception as e:
                print(f"\n⚠️  Flight interrupted: {e}")
                
                try:
                    position = get_drone_position(drone)
                    velocity = get_drone_velocity(drone)
                    recorder.record_point(position, velocity)
                except:
                    pass
                
                distance_traveled = math.sqrt(
                    (recorder.points[-1]['position']['north'] - initial_pos.north)**2 +
                    (recorder.points[-1]['position']['east'] - initial_pos.east)**2
                )
                print(f"   Distance traveled: {distance_traveled:.1f}m")
                print(f"   Trajectory recorded: {len(recorder.points)} points")
    
    else:
        print(f"ERROR: Unsupported command: {test_command}")
        return {'success': False, 'reason': 'Unsupported command'}
    
    return {
        'success': True,
        'mode': 'auto',
        'trajectory': recorder.to_dict(),
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
    test_case_id: Optional[str] = None
) -> int:
    """
    Main async entry point for scenario execution.
    
    Args:
        scenario_file: Path to scenario configuration
        output_file: Where to save trajectory
        mode: Execution mode ("auto")
        test_command: Test command for auto mode
        test_case_id: Test case ID to load from scenario file
    
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        # Load scenario configuration
        print(f"Loading scenario: {scenario_file}")
        scenario_config = load_scenario_config(scenario_file)
        print(f"✓ Scenario loaded: {scenario_config.scenario_id}")
        
        # If test_case_id is provided, load test case configuration
        if test_case_id and 'test_cases' in scenario_config.raw_data:
            test_cases = scenario_config.raw_data['test_cases']
            matching_case = next((tc for tc in test_cases if tc.get('id') == test_case_id), None)
            
            if matching_case:
                print(f"✓ Loading test case: {test_case_id}")
                scenario_config.test_info = {
                    'test_command': matching_case.get('command')
                }
                # Override test_command if not provided
                if not test_command:
                    test_command = matching_case.get('command')
                
                # Load enabled waivers from test case (S014)
                waivers_enabled = matching_case.get('waivers_enabled', [])
                scenario_config.enabled_waivers = waivers_enabled
                if waivers_enabled:
                    print(f"✓ Enabled waivers: {waivers_enabled}")
            else:
                print(f"⚠ Test case {test_case_id} not found in scenario file")
                print(f"   Available test cases: {[tc.get('id') for tc in test_cases]}")
        
        # Connect to ProjectAirSim
        print("Connecting to ProjectAirSim...")
        client = ProjectAirSimClient()
        client.connect()
        print("✓ Connected to ProjectAirSim")
        
        # Run scenario
        if mode == "auto":
            result = await run_scenario_auto(
                scenario_config,
                scenario_file,
                client,
                test_command
            )
        else:
            print(f"ERROR: Unsupported mode: {mode}", file=sys.stderr)
            return 1
        
        # Save trajectory
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Trajectory saved: {output_file} ({result.get('trajectory_points', 0)} points)")
        
        # Print result summary
        print("\n" + "="*70)
        if result['success']:
            print("✓ SCENARIO EXECUTION COMPLETED")
        else:
            print("⚠️  SCENARIO EXECUTION COMPLETED WITH WARNINGS")
        print("="*70)
        
        return 0
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="VLOS & Avoidance Scenario Runner for LAE-GPT (S013-S016)"
    )
    
    parser.add_argument(
        'scenario_file',
        type=Path,
        help='Path to scenario configuration file (*.jsonc)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='Output trajectory file path (*.json)'
    )
    
    parser.add_argument(
        '--mode', '-m',
        type=str,
        default='auto',
        choices=['auto'],
        help='Execution mode (default: auto)'
    )
    
    parser.add_argument(
        '--command', '-c',
        type=str,
        help='Test command for auto mode (e.g., "move_to_position(600, 0, 50)")'
    )
    
    parser.add_argument(
        '--test-case', '-t',
        type=str,
        help='Test case ID (e.g., "TC1") - loads command from scenario file'
    )
    
    args = parser.parse_args()
    
    # Run async main
    exit_code = asyncio.run(run_scenario_async(
        args.scenario_file,
        args.output,
        args.mode,
        args.command,
        args.test_case
    ))
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
run_scenario_path.py - Path & Obstacle Avoidance Scenario Runner

Specialized script for S015-S016 - Avoidance Scenarios
- S015: Pre-flight path conflict detection (path geometry analysis)
- S016: In-flight obstacle avoidance (real-time distance monitoring)

Author: LAE-GPT Team
Date: 2025-10-31
Version: 2.0

Usage:
    # S015 mode (pre-flight)
    python run_scenario_path.py scenario.jsonc --output trajectory.json --test-case TC1 --detection-mode pre-flight
    
    # S016 mode (in-flight)
    python run_scenario_path.py scenario.jsonc --output trajectory.json --test-case TC1 --detection-mode in-flight
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
class Velocity3D:
    """Velocity in NED coordinates."""
    north: float
    east: float
    down: float
    
    @property
    def ground_speed_mps(self) -> float:
        """Ground speed in m/s."""
        return math.sqrt(self.north**2 + self.east**2)
    
    @property
    def ground_speed_kmh(self) -> float:
        """Ground speed in km/h."""
        return self.ground_speed_mps * 3.6


@dataclass
class NFZConfig:
    """No-Fly Zone configuration."""
    nfz_id: str
    nfz_type: str  # "cylinder"
    center_north: float
    center_east: float
    center_down: float
    radius: float
    safety_margin: float
    height_min: float
    height_max: float
    enabled: bool = True
    zone_type: str = ""
    description: str = ""
    
    @property
    def total_radius(self) -> float:
        """Total restricted radius (radius + safety_margin)."""
        return self.radius + self.safety_margin
    
    def get_center_2d(self) -> Tuple[float, float]:
        """Get 2D center (north, east) for horizontal distance calculation."""
        return (self.center_north, self.center_east)


@dataclass
class ScenarioConfig:
    """Parsed scenario configuration."""
    scenario_id: str
    actors: List[Dict[str, Any]]
    geofences: List[NFZConfig]
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
    
    # Parse geofences/NFZs
    nfzs = []
    for gf in data.get('geofences', []):
        if not gf.get('enabled', True):
            continue
        
        center = gf.get('center', {}).get('xyz', '0.0 0.0 0.0').split()
        nfz = NFZConfig(
            nfz_id=gf.get('id', ''),
            nfz_type=gf.get('type', 'cylinder'),
            center_north=float(center[0]),
            center_east=float(center[1]),
            center_down=float(center[2]),
            radius=gf.get('radius', 0.0),
            safety_margin=gf.get('safety_margin', 0.0),
            height_min=gf.get('height_min', -1000.0),
            height_max=gf.get('height_max', 1000.0),
            enabled=True,
            zone_type=gf.get('zone_type', ''),
            description=gf.get('description', '')
        )
        nfzs.append(nfz)
    
    return ScenarioConfig(
        scenario_id=data.get('id', 'unknown'),
        actors=data.get('actors', []),
        geofences=nfzs,
        test_info=data.get('test_info'),
        raw_data=data
    )


# ============================================================================
# SECTION 3: Drone State Access
# ============================================================================

def get_drone_position(drone: Drone) -> Position3D:
    """
    Get current drone position.
    
    Args:
        drone: Drone instance
    
    Returns:
        Position3D in NED coordinates
    """
    # Get pose from drone (synchronous method, returns dict)
    pose = drone.get_ground_truth_pose()
    
    # Extract position (NED coordinates) from dict
    translation = pose['translation']
    
    return Position3D(
        north=translation['x'],
        east=translation['y'],
        down=translation['z']
    )


# ============================================================================
# SECTION 4: Path-NFZ Conflict Detection ⭐ CORE ALGORITHM
# ============================================================================

def point_to_line_segment_distance_2d(
    point: Tuple[float, float],
    line_start: Tuple[float, float],
    line_end: Tuple[float, float]
) -> float:
    """
    Calculate minimum distance from a point to a line segment (2D projection).
    
    Algorithm:
    1. Calculate projection parameter t ∈ [0, 1]
    2. Find closest point on line segment
    3. Return Euclidean distance
    
    Args:
        point: NFZ center (north, east)
        line_start: Path start point (north, east)
        line_end: Path end point (north, east)
    
    Returns:
        Minimum distance in meters
    """
    px, py = point
    ax, ay = line_start
    bx, by = line_end
    
    # Line segment vector
    dx = bx - ax
    dy = by - ay
    line_length_sq = dx*dx + dy*dy
    
    if line_length_sq == 0:
        # Start == End, return distance to start point
        return math.sqrt((px - ax)**2 + (py - ay)**2)
    
    # Projection parameter t
    # t=0: projection at start, t=1: projection at end
    point_vec_x = px - ax
    point_vec_y = py - ay
    t = (point_vec_x * dx + point_vec_y * dy) / line_length_sq
    t = max(0, min(1, t))  # Clamp to [0, 1]
    
    # Closest point on line segment
    closest_x = ax + t * dx
    closest_y = ay + t * dy
    
    # Distance
    distance = math.sqrt((px - closest_x)**2 + (py - closest_y)**2)
    
    return distance


def check_path_nfz_conflicts(
    path_start: Position3D,
    path_end: Position3D,
    nfzs: List[NFZConfig]
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Check if straight-line path conflicts with any NFZs.
    
    Args:
        path_start: Path start position
        path_end: Path end position
        nfzs: List of No-Fly Zones
    
    Returns:
        (has_conflict, conflicts_list)
        
    Logic:
        For each NFZ:
        1. Calculate minimum distance from path to NFZ center (2D)
        2. Compare with total restricted radius
        3. Record conflict if distance < radius
    """
    conflicts = []
    
    # Extract 2D coordinates
    start_2d = (path_start.north, path_start.east)
    end_2d = (path_end.north, path_end.east)
    
    for nfz in nfzs:
        # NFZ center in 2D
        nfz_center_2d = nfz.get_center_2d()
        
        # Calculate minimum distance
        min_distance = point_to_line_segment_distance_2d(
            nfz_center_2d,
            start_2d,
            end_2d
        )
        
        # Check conflict
        total_radius = nfz.total_radius
        if min_distance < total_radius:
            # Conflict detected
            clearance_deficit = total_radius - min_distance
            conflicts.append({
                'nfz_id': nfz.nfz_id,
                'nfz_center': [nfz.center_north, nfz.center_east, nfz.center_down],
                'radius': nfz.radius,
                'safety_margin': nfz.safety_margin,
                'total_radius': total_radius,
                'min_distance': min_distance,
                'clearance_deficit': clearance_deficit,
                'zone_type': nfz.zone_type,
                'description': nfz.description
            })
    
    has_conflict = len(conflicts) > 0
    return has_conflict, conflicts


# ============================================================================
# SECTION 5: In-Flight Obstacle Distance Monitoring ⭐ S016
# ============================================================================

def check_obstacle_distance(
    current_pos: Position3D,
    obstacles: List[NFZConfig],
    safety_threshold: float = 80.0
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Check if current position is too close to any obstacle (S016).
    
    Args:
        current_pos: Current drone position
        obstacles: List of obstacles (NFZs)
        safety_threshold: Minimum safe distance (default 80m)
    
    Returns:
        (should_stop, obstacle_info)
        - should_stop: True if within safety threshold
        - obstacle_info: Details of the detected obstacle
    """
    for obstacle in obstacles:
        # Calculate 2D distance (horizontal distance, ignore altitude)
        dx = current_pos.north - obstacle.center_north
        dy = current_pos.east - obstacle.center_east
        distance = math.sqrt(dx**2 + dy**2)
        
        # Check if within safety threshold
        if distance < safety_threshold:
            return True, {
                'obstacle_id': obstacle.nfz_id,
                'obstacle_center': [obstacle.center_north, obstacle.center_east, obstacle.center_down],
                'distance': distance,
                'safety_threshold': safety_threshold,
                'zone_type': obstacle.zone_type,
                'description': obstacle.description
            }
    
    return False, None


# ============================================================================
# SECTION 6: Scenario Execution
# ============================================================================

async def run_scenario_auto(
    scenario_config: ScenarioConfig,
    scenario_file: Path,
    client: ProjectAirSimClient,
    test_command: str,
    recorder: TrajectoryRecorder,
    detection_mode: str = "pre-flight"
) -> Dict[str, Any]:
    """
    Run scenario in automatic mode with avoidance detection.
    
    Args:
        detection_mode: "pre-flight" (S015) or "in-flight" (S016)
    
    Flow (pre-flight mode):
    1. Parse test command (move_to_position)
    2. Pre-flight check: Detect path-NFZ conflicts using geometry
    3. If conflict → REJECT (don't fly)
    4. If clear → Execute movement
    
    Flow (in-flight mode):
    1. Parse test command (move_to_position)
    2. Start flight (no pre-flight path check)
    3. During flight: Monitor distance to obstacles continuously (10Hz)
    4. If distance < 80m → STOP and HOVER
    5. Otherwise → Continue to target
    """
    print(f"Test Command: {test_command}")
    print(f"Detection Mode: {detection_mode}")
    
    # Load the scene from scenario file
    print(f"Loading scene from: {scenario_file}")
    world = World(client, str(scenario_file), delay_after_load_sec=2)
    
    # Assume first actor is the drone
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
    await asyncio.sleep(3)  # Wait for drone to stabilize after takeoff
    
    # Get position after takeoff
    takeoff_pos = get_drone_position(drone)
    print(f"✓ Takeoff completed: N={takeoff_pos.north:.1f}, E={takeoff_pos.east:.1f}, Alt={takeoff_pos.altitude:.1f}m")
    
    # CRITICAL: Climb to safe altitude before horizontal movement
    # takeoff_async() only lifts drone to ~3m, we need to climb to operational altitude
    print(f"Climbing to operational altitude...")
    await drone.move_to_position_async(
        north=takeoff_pos.north,
        east=takeoff_pos.east,
        down=-50.0,  # Climb to 50m altitude
        velocity=5.0
    )
    
    # Wait for climb to complete - monitor altitude
    climb_timeout = 100  # 10 seconds
    for i in range(climb_timeout):
        current_pos = get_drone_position(drone)
        if current_pos.altitude >= 45.0:  # Close enough to 50m
            break
        await asyncio.sleep(0.1)
    
    # Get initial position after climb
    initial_pos = get_drone_position(drone)
    print(f"✓ Ready at: N={initial_pos.north:.1f}, E={initial_pos.east:.1f}, Alt={initial_pos.altitude:.1f}m")
    
    # Start recording
    recorder.start()
    recorder.record_point(initial_pos, 0.0)
    
    # Parse command: move_to_position(north, east, altitude)
    import re
    match = re.match(
        r'move_to_position\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)',
        test_command
    )
    
    if match:
        target_n = float(match.group(1))
        target_e = float(match.group(2))
        target_alt = float(match.group(3))
        target_d = -target_alt
        
        print(f"\n🚀 Executing: move_to_position({target_n}, {target_e}, {target_alt})")
        print(f"   Target: N={target_n}, E={target_e}, Alt={target_alt}m")
        
        target_position = Position3D(north=target_n, east=target_e, down=target_d)
        
        # PRE-FLIGHT CHECK: Path-NFZ conflict detection (S015 mode only)
        if detection_mode == "pre-flight":
            print("\n🔍 Pre-flight check: Path conflict detection...")
            print(f"   Analyzing path: ({initial_pos.north:.1f}, {initial_pos.east:.1f}) → ({target_n}, {target_e})")
            
            has_conflict, conflicts = check_path_nfz_conflicts(
                initial_pos,
                target_position,
                scenario_config.geofences
            )
            
            if has_conflict:
                # CONFLICT DETECTED - REJECT FLIGHT
                print(f"\n   ⚠️  Path conflicts detected: {len(conflicts)} NFZ(s)")
                for i, conflict in enumerate(conflicts, 1):
                    print(f"   {i}. NFZ: {conflict['nfz_id']}")
                    print(f"      Zone type: {conflict['zone_type']}")
                    print(f"      Min distance: {conflict['min_distance']:.1f}m")
                    print(f"      Required clearance: {conflict['total_radius']:.1f}m")
                    print(f"      Deficit: {conflict['clearance_deficit']:.1f}m")
                    print(f"      ❌ CONFLICT")
                
                print("\n🚫 COMMAND REJECTED (Path conflicts with NFZ)")
                if conflicts:
                    first_conflict = conflicts[0]
                    print(f"   First conflict: {first_conflict['nfz_id']}")
                    print(f"   Reason: Path distance {first_conflict['min_distance']:.1f}m < required {first_conflict['total_radius']:.1f}m")
                
                return {
                    'success': False,
                    'mode': 'auto',
                    'command_rejected': True,
                    'reason': 'Path-NFZ conflict',
                    'conflicts': conflicts,
                    'trajectory_points': len(recorder.points)
                }
            
            else:
                # NO CONFLICT - APPROVE FLIGHT
                print(f"   ✓ No conflicts detected")
                print(f"   ✓ Path clear to target")
            
                # Check closest NFZ for informational purposes
                if scenario_config.geofences:
                    closest_nfz = None
                    min_closest_dist = float('inf')
                    
                    start_2d = (initial_pos.north, initial_pos.east)
                    end_2d = (target_n, target_e)
                    
                    for nfz in scenario_config.geofences:
                        nfz_center_2d = nfz.get_center_2d()
                        dist = point_to_line_segment_distance_2d(nfz_center_2d, start_2d, end_2d)
                        if dist < min_closest_dist:
                            min_closest_dist = dist
                            closest_nfz = nfz
                    
                    if closest_nfz:
                        clearance = min_closest_dist - closest_nfz.total_radius
                        print(f"   Closest NFZ: {closest_nfz.nfz_id}")
                        print(f"   Distance: {min_closest_dist:.1f}m, Required: {closest_nfz.total_radius:.1f}m")
                        print(f"   Clearance: {clearance:.1f}m ✓")
                
                print("\n✅ All pre-flight checks passed")
        
        # For in-flight mode, no pre-flight check
        elif detection_mode == "in-flight":
            print("\n✅ No pre-flight path check (in-flight mode)")
        
        print("✓ Executing movement...")
        
        # Execute movement with concurrent monitoring
        try:
            print(f"   Starting movement to ({target_n}, {target_e}, {target_alt})...")
            
            # Monitor trajectory during movement
            obstacle_detected = False
            stop_info = None
            
            # For in-flight mode: concurrent monitoring
            # For pre-flight mode: just execute and record
            if detection_mode == "in-flight":
                print("   In-flight monitoring active (10Hz)...")
                
                # CRITICAL FIX: move_to_position_async() issues command and returns immediately
                # The actual movement happens in background by simulator
                # We need to: 1) Issue command  2) Immediately start monitoring loop
                
                print(f"   Issuing movement command to ({target_n}, {target_e}, {target_alt})...")
                
                # Issue the movement command (it returns immediately, drone moves in background)
                await drone.move_to_position_async(
                    north=target_n,
                    east=target_e,
                    down=target_d,
                    velocity=15.0
                )
                
                print(f"   ✓ Movement command sent")
                print(f"   Monitoring flight progress...")
                
                # MONITORING LOOP: Continuously check position until target reached or obstacle detected
                max_iterations = 3000  # 300 seconds at 10Hz
                iteration = 0
                
                while iteration < max_iterations:
                    # Get current position
                    position = get_drone_position(drone)
                    recorder.record_point(position)
                    
                    # Calculate distance to target
                    dist_to_target = math.sqrt(
                        (position.north - target_n)**2 +
                        (position.east - target_e)**2 +
                        (position.down - target_d)**2
                    )
                    
                    # Calculate distance traveled from start
                    dist_traveled = math.sqrt(
                        (position.north - initial_pos.north)**2 +
                        (position.east - initial_pos.east)**2
                    )
                    
                    # Debug output every 10 iterations (1 second)
                    if iteration % 10 == 0:
                        print(f"   [{iteration:4d}] N={position.north:6.1f} E={position.east:6.1f} Alt={position.altitude:5.1f}m | " +
                              f"Traveled: {dist_traveled:6.1f}m | To target: {dist_to_target:6.1f}m")
                    
                    # Check obstacle distance (S016 core logic)
                    should_stop, obstacle_info = check_obstacle_distance(
                        position,
                        scenario_config.geofences,
                        safety_threshold=80.0
                    )
                    
                    if should_stop:
                        # ⛔ OBSTACLE DETECTED - TRIGGER EMERGENCY STOP
                        print(f"\n{'='*70}")
                        print(f"⛔ OBSTACLE DETECTED WITHIN SAFETY DISTANCE!")
                        print(f"{'='*70}")
                        print(f"   Obstacle ID: {obstacle_info['obstacle_id']}")
                        print(f"   Obstacle type: {obstacle_info['zone_type']}")
                        print(f"   Distance: {obstacle_info['distance']:.1f}m")
                        print(f"   Safety threshold: {obstacle_info['safety_threshold']:.1f}m")
                        print(f"   Clearance deficit: {obstacle_info['safety_threshold'] - obstacle_info['distance']:.1f}m")
                        
                        # Send hover command to stop the drone
                        print(f"\n🛑 Initiating emergency stop...")
                        await drone.hover_async()
                        await asyncio.sleep(2)  # Wait for hover command to take effect
                        
                        # Record final position after stop
                        final_pos = get_drone_position(drone)
                        recorder.record_point(final_pos)
                        
                        obstacle_detected = True
                        stop_info = obstacle_info
                        
                        # Calculate final statistics
                        final_dist_traveled = math.sqrt(
                            (final_pos.north - initial_pos.north)**2 +
                            (final_pos.east - initial_pos.east)**2
                        )
                        final_dist_remaining = math.sqrt(
                            (final_pos.north - target_n)**2 +
                            (final_pos.east - target_e)**2
                        )
                        
                        print(f"\n{'='*70}")
                        print(f"🛑 AUTOMATIC STOP COMPLETED")
                        print(f"{'='*70}")
                        print(f"   Stop position: N={final_pos.north:.1f}, E={final_pos.east:.1f}, Alt={final_pos.altitude:.1f}m")
                        print(f"   Distance traveled: {final_dist_traveled:.1f}m")
                        print(f"   Distance to target: {final_dist_remaining:.1f}m")
                        print(f"   Trajectory points: {len(recorder.points)}")
                        print(f"   Stop reason: Obstacle '{obstacle_info['obstacle_id']}' at {obstacle_info['distance']:.1f}m")
                        break
                    
                    # Check if reached target (within 2m)
                    if dist_to_target < 2.0:
                        print(f"\n✓ Target reached at N={position.north:.1f}, E={position.east:.1f}, Alt={position.altitude:.1f}m")
                        break
                    
                    # Sleep before next check (10Hz monitoring)
                    await asyncio.sleep(0.1)
                    iteration += 1
                
                # Check for timeout
                if iteration >= max_iterations:
                    print(f"\n⚠️  WARNING: Monitoring timeout reached ({max_iterations} iterations)")
                    print(f"   Last position: N={position.north:.1f}, E={position.east:.1f}")
                    print(f"   Distance to target: {dist_to_target:.1f}m")
                
            else:
                # Pre-flight mode: just execute and record final trajectory
                print("   Executing movement (pre-flight mode)...")
                await drone.move_to_position_async(
                    north=target_n,
                    east=target_e,
                    down=target_d,
                    velocity=15.0
                )
                
                # Record final position
                position = get_drone_position(drone)
                recorder.record_point(position)
                print("✓ Target reached")
            
            if obstacle_detected:
                return {
                    'success': True,
                    'mode': 'auto',
                    'stopped_by_obstacle': True,
                    'obstacle_info': stop_info,
                    'trajectory_points': len(recorder.points)
                }
            else:
                return {
                    'success': True,
                    'mode': 'auto',
                    'command_rejected': False,
                    'trajectory_points': len(recorder.points)
                }
        
        except Exception as e:
            print(f"\n⚠️  Flight interrupted: {e}")
            import traceback
            traceback.print_exc()
            
            try:
                position = get_drone_position(drone)
                recorder.record_point(position)
            except:
                pass
            
            return {
                'success': False,
                'mode': 'auto',
                'error': str(e),
                'trajectory_points': len(recorder.points)
            }
    
    else:
        print(f"ERROR: Unsupported command: {test_command}")
        return {
            'success': False,
            'reason': 'Invalid command format'
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
    detection_mode: str = "pre-flight"
) -> int:
    """Main async entry point for scenario execution."""
    try:
        # Load scenario configuration
        print(f"Loading scenario: {scenario_file}")
        scenario_config = load_scenario_config(scenario_file)
        print(f"✓ Scenario loaded: {scenario_config.scenario_id}")
        print(f"✓ Obstacles loaded: {len(scenario_config.geofences)}")
        
        # Load test case if specified
        if test_case_id and 'test_cases' in scenario_config.raw_data:
            test_cases = scenario_config.raw_data['test_cases']
            # Try exact match first
            matching_case = next((tc for tc in test_cases if tc.get('id') == test_case_id), None)
            
            # If not found, try matching by prefix (e.g., "TC1" matches "TC1_PathBlocked_FrontNFZ")
            if not matching_case:
                matching_case = next((tc for tc in test_cases if tc.get('id', '').startswith(test_case_id)), None)
            
            if matching_case:
                print(f"✓ Loading test case: {matching_case.get('id')}")
                if not test_command:
                    test_command = matching_case.get('command')
            else:
                print(f"⚠ Test case {test_case_id} not found in {len(test_cases)} test cases")
                print(f"   Available: {[tc.get('id') for tc in test_cases[:3]]}")
        
        # Connect to ProjectAirSim
        print("Connecting to ProjectAirSim...")
        client = ProjectAirSimClient()
        client.connect()
        print("✓ Connected to ProjectAirSim")
        
        print("\n" + "="*70)
        if detection_mode == "pre-flight":
            print("S015 MODE - PRE-FLIGHT PATH CONFLICT DETECTION")
        else:
            print("S016 MODE - IN-FLIGHT OBSTACLE AVOIDANCE")
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
            detection_mode=detection_mode
        )
        
        # Save trajectory
        metadata = {
            'scenario_id': scenario_config.scenario_id,
            'scenario_file': str(scenario_file),
            'mode': mode,
            'execution_result': result
        }
        recorder.save(output_file, metadata)
        
        # Print summary
        print("\n" + "="*70)
        if result.get('command_rejected'):
            print("⚠️  COMMAND REJECTED (Path conflict detected)")
        elif result.get('success', False):
            print("✓ SCENARIO EXECUTION COMPLETED")
        else:
            print("⚠️  SCENARIO EXECUTION COMPLETED WITH WARNINGS")
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
        description='Run avoidance scenarios (S015-S016)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # S015 mode (pre-flight path conflict detection)
  python run_scenario_path.py scenario.jsonc --output traj.json --test-case TC1 --detection-mode pre-flight
  
  # S016 mode (in-flight obstacle avoidance)
  python run_scenario_path.py scenario.jsonc --output traj.json --test-case TC1 --detection-mode in-flight
  
  # Run with custom command
  python run_scenario_path.py scenario.jsonc --output traj.json --command "move_to_position(800, 0, 50)" --detection-mode pre-flight
        '''
    )
    
    parser.add_argument('scenario_file', type=str, help='Path to scenario JSONC file')
    parser.add_argument('--output', '-o', type=str, required=True, help='Output trajectory JSON file')
    parser.add_argument('--mode', type=str, default='auto', choices=['auto'], help='Execution mode (default: auto)')
    parser.add_argument('--command', type=str, help='Test command (e.g., "move_to_position(800, 0, 50)")')
    parser.add_argument('--test-case', type=str, help='Test case ID (e.g., TC1)')
    parser.add_argument('--detection-mode', type=str, default='pre-flight', 
                       choices=['pre-flight', 'in-flight'],
                       help='Detection mode: "pre-flight" for S015 (path analysis) or "in-flight" for S016 (real-time monitoring)')
    
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
        detection_mode=args.detection_mode
    ))
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())


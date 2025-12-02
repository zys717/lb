#!/usr/bin/env python3
"""
Scenario Runner for LAE-GPT

This script loads and executes test scenarios in ProjectAirSim, recording drone
trajectories for violation detection. It implements client-side geofence checking
since ProjectAirSim does not natively enforce geofences.

Usage:
    python run_scenario.py <scenario_file.jsonc> --output <trajectory_file.json>
    
Example:
    python run_scenario.py ../scenarios/basic/S001_geofence_basic.jsonc \
        --output ../test_logs/trajectory_S001.json

Note:
    This script must be run on the remote server with ProjectAirSim running.
    Scripts are typically run from: client/python/example_user_scripts/
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

# Import ProjectAirSim high-level API (not airsim)
try:
    from projectairsim import ProjectAirSimClient, World, Drone
except ImportError:
    print("ERROR: ProjectAirSim not found. This script must run on the server.", file=sys.stderr)
    print("Install with: pip install -e /path/to/ProjectAirSim/client/python/projectairsim", file=sys.stderr)
    sys.exit(1)


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
            'down': self.down
        }


@dataclass
class GeofenceConfig:
    """Geofence configuration."""
    id: str
    center: Position3D
    radius: float
    safety_margin: float = 500.0
    enabled: bool = True
    action: str = "reject"  # "reject", "warn", or "allow"
    zone_type: str = "restricted"  # Zone classification (for S004)
    priority: int = 1  # Higher priority zones checked first
    raw_data: Dict[str, Any] = field(default_factory=dict)  # For time restrictions
    
    @property
    def restricted_distance(self) -> float:
        """Total restricted distance from center."""
        return self.radius + self.safety_margin
    
    def check_violation(self, position: Position3D) -> Tuple[bool, float, str]:
        """
        Check if a position violates this geofence.
        
        Returns:
            Tuple of (is_inside_zone, distance_to_center, action_type)
            - is_inside_zone: Whether position is within this zone
            - distance_to_center: Distance from position to zone center
            - action_type: Action to take ("reject", "warn", "allow")
        """
        dx = position.north - self.center.north
        dy = position.east - self.center.east
        dz = position.down - self.center.down
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        
        is_inside = distance < self.restricted_distance
        return is_inside, distance, self.action


@dataclass
class AltitudeZoneConfig:
    """Altitude zone configuration for S007."""
    id: str
    name: str
    center: Position3D
    radius: float  # Negative value means infinite (default zone)
    altitude_limit_agl: float
    priority: int
    zone_type: str


@dataclass
class StructureConfig:
    """Structure configuration for S008 altitude waiver."""
    id: str
    name: str
    location: Position3D  # Structure base location
    height_agl: float  # Structure height above ground
    waiver_radius: float  # Horizontal radius for waiver applicability
    waiver_altitude_above_structure: float  # Additional altitude allowed above structure
    total_waiver_altitude: float  # Total altitude limit when waiver applies


@dataclass
class ScenarioConfig:
    """Parsed scenario configuration."""
    scenario_id: str
    actors: List[Dict[str, Any]]
    geofences: List[GeofenceConfig]
    test_info: Optional[Dict[str, Any]] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    altitude_limit: Optional[float] = None  # Maximum altitude AGL in meters (for S006)
    altitude_zones: List[AltitudeZoneConfig] = field(default_factory=list)  # Zone-based altitude limits (for S007)
    structures: List[StructureConfig] = field(default_factory=list)  # Structures for altitude waivers (for S008)


@dataclass
class TrajectoryRecorder:
    """Records drone trajectory during scenario execution."""
    points: List[Dict[str, Any]] = field(default_factory=list)
    start_time: float = 0.0
    
    def start(self) -> None:
        """Start recording."""
        self.start_time = time.time()
        self.points = []
    
    def record_point(self, position: Position3D, timestamp: Optional[float] = None) -> None:
        """Record a trajectory point."""
        if timestamp is None:
            timestamp = time.time() - self.start_time
        
        self.points.append({
            'timestamp': timestamp,
            'position': position.to_dict()
        })
    
    def save(self, output_file: Path, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save trajectory to JSON file."""
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


def strip_json_comments(text: str) -> str:
    """Remove JavaScript-style comments from JSON."""
    import re
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text


def parse_iso8601(time_str: str) -> datetime:
    """Parse ISO 8601 time string to datetime object."""
    # Handle 'Z' suffix for UTC
    time_str = time_str.replace('Z', '+00:00')
    return datetime.fromisoformat(time_str)


def check_altitude_limit(
    target_altitude_agl: float,
    limit: float,
    tolerance: float = 0.0
) -> Tuple[bool, str]:
    """
    Check if target altitude exceeds legal limit (for S006).
    
    Args:
        target_altitude_agl: Target altitude in meters AGL (Above Ground Level)
        limit: Altitude limit in meters (typically 120m for China regulations)
        tolerance: Allowed margin in meters (default 0.0 for strict enforcement)
    
    Returns:
        Tuple of (is_safe, reason)
        - is_safe: True if altitude is within limit
        - reason: Explanation of the check result
    
    Examples:
        >>> check_altitude_limit(119.0, 120.0)
        (True, "目标高度119.0m合规（距限制1.0m）")
        
        >>> check_altitude_limit(120.0, 120.0)
        (False, "目标高度120.0m达到或超过120.0m管制空域下限（超出0.0m）")
    """
    effective_limit = limit + tolerance
    
    if target_altitude_agl >= effective_limit:
        excess = target_altitude_agl - limit
        return (
            False,
            f"目标高度{target_altitude_agl:.1f}m达到或超过{limit:.1f}m管制空域下限（超出{excess:.1f}m）"
        )
    else:
        margin = limit - target_altitude_agl
        return (
            True,
            f"目标高度{target_altitude_agl:.1f}m合规（距限制{margin:.1f}m）"
        )


def identify_altitude_zone(
    position: Position3D,
    altitude_zones: List[AltitudeZoneConfig]
) -> Optional[AltitudeZoneConfig]:
    """
    Identify which altitude zone a position is in (for S007).
    
    Args:
        position: Target position
        altitude_zones: List of altitude zones
    
    Returns:
        The zone the position is in (highest priority zone if overlapping)
    
    Strategy:
        Check zones from highest to lowest priority to handle nested zones
        (e.g., urban core inside urban edge inside suburban)
    """
    if not altitude_zones:
        return None
    
    # Sort zones by priority (descending)
    sorted_zones = sorted(altitude_zones, key=lambda z: z.priority, reverse=True)
    
    for zone in sorted_zones:
        # Check if position is in this zone
        if zone.radius < 0:
            # Infinite zone (default/suburban)
            return zone
        
        # Calculate horizontal distance (north and east only, no altitude)
        dx = position.north - zone.center.north
        dy = position.east - zone.center.east
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < zone.radius:
            return zone
    
    # Default to lowest priority zone
    return sorted_zones[-1] if sorted_zones else None


def check_zone_altitude_limit(
    position: Position3D,
    target_altitude_agl: float,
    altitude_zones: List[AltitudeZoneConfig]
) -> Tuple[bool, str, Optional[AltitudeZoneConfig]]:
    """
    Check altitude limit based on position zone (for S007).
    
    Args:
        position: Target position
        target_altitude_agl: Target altitude in meters AGL
        altitude_zones: List of altitude zones
    
    Returns:
        Tuple of (is_safe, reason, zone)
        - is_safe: True if altitude is within zone's limit
        - reason: Explanation including zone name and limit
        - zone: The identified zone
    
    Examples:
        >>> check_zone_altitude_limit(Position3D(500, 0, -50), 50.0, zones)
        (True, "目标位置在城市核心区（限制60.0m），高度50.0m合规（距限制10.0m）", urban_core_zone)
    """
    zone = identify_altitude_zone(position, altitude_zones)
    
    if not zone:
        return (True, "未识别到高度限制区域", None)
    
    # Calculate horizontal distance for logging
    dx = position.north - zone.center.north
    dy = position.east - zone.center.east
    distance = math.sqrt(dx**2 + dy**2)
    
    # Check altitude against zone's limit
    if target_altitude_agl >= zone.altitude_limit_agl:
        excess = target_altitude_agl - zone.altitude_limit_agl
        return (
            False,
            f"目标位置在{zone.name}（限制{zone.altitude_limit_agl:.1f}m），"
            f"高度{target_altitude_agl:.1f}m超限（超出{excess:.1f}m）",
            zone
        )
    else:
        margin = zone.altitude_limit_agl - target_altitude_agl
        return (
            True,
            f"目标位置在{zone.name}（限制{zone.altitude_limit_agl:.1f}m），"
            f"高度{target_altitude_agl:.1f}m合规（距限制{margin:.1f}m）",
            zone
        )


def check_structure_waiver(
    position: Position3D,
    target_altitude_agl: float,
    structures: List[StructureConfig],
    global_altitude_limit: float
) -> Tuple[bool, str, Optional[StructureConfig]]:
    """
    Check altitude limit with structure waiver consideration (for S008).
    
    Implements FAA Part 107.51(b): Aircraft may fly higher than 400 feet AGL
    if within 400 feet of a structure, up to 400 feet above the structure's top.
    
    Args:
        position: Target position
        target_altitude_agl: Target altitude in meters AGL
        structures: List of structure configurations
        global_altitude_limit: Global altitude limit (e.g., 120m)
    
    Returns:
        Tuple of (is_safe, reason, applicable_structure)
        - is_safe: True if altitude is within applicable limit
        - reason: Explanation of decision
        - applicable_structure: The structure providing waiver, or None
    
    Logic:
        1. Calculate horizontal distance to all structures
        2. Find nearest structure within waiver radius
        3. If within waiver radius: apply structure's waiver altitude limit
        4. If outside all waiver radii: apply global altitude limit
    
    Examples:
        >>> check_structure_waiver(Position3D(1000, 1100, -50), 150.0, structures, 120.0)
        (True, "目标位置在building_1豁免半径内（距离100.0m），高度150m符合豁免上限221.92m", building_1)
        
        >>> check_structure_waiver(Position3D(3000, 0, -50), 150.0, structures, 120.0)
        (False, "目标高度150m超过全局限制120m，且不在任何建筑物豁免半径内", None)
    """
    if not structures:
        # No structures defined, use global limit
        if target_altitude_agl >= global_altitude_limit:
            excess = target_altitude_agl - global_altitude_limit
            return (
                False,
                f"目标高度{target_altitude_agl:.1f}m超过全局限制{global_altitude_limit:.1f}m"
                f"（超出{excess:.1f}m）",
                None
            )
        else:
            margin = global_altitude_limit - target_altitude_agl
            return (
                True,
                f"目标高度{target_altitude_agl:.1f}m符合全局限制{global_altitude_limit:.1f}m"
                f"（距限制{margin:.1f}m）",
                None
            )
    
    # Find nearest structure within waiver radius
    applicable_structure = None
    min_distance = float('inf')
    
    for structure in structures:
        # Calculate horizontal distance (2D, ignore vertical)
        dx = position.north - structure.location.north
        dy = position.east - structure.location.east
        horizontal_distance = math.sqrt(dx**2 + dy**2)
        
        # Check if within waiver radius
        if horizontal_distance < structure.waiver_radius:
            if horizontal_distance < min_distance:
                min_distance = horizontal_distance
                applicable_structure = structure
    
    if applicable_structure:
        # Waiver applies: use structure's waiver altitude limit
        waiver_limit = applicable_structure.total_waiver_altitude
        
        if target_altitude_agl >= waiver_limit:
            excess = target_altitude_agl - waiver_limit
            return (
                False,
                f"虽在{applicable_structure.id}豁免半径内（距离{min_distance:.1f}m），"
                f"但目标高度{target_altitude_agl:.1f}m超过豁免上限{waiver_limit:.2f}m"
                f"（超出{excess:.2f}m）",
                applicable_structure
            )
        else:
            margin = waiver_limit - target_altitude_agl
            return (
                True,
                f"目标位置在{applicable_structure.id}豁免半径内（距离{min_distance:.1f}m < {applicable_structure.waiver_radius:.2f}m），"
                f"高度{target_altitude_agl:.1f}m符合豁免上限{waiver_limit:.2f}m"
                f"（建筑高{applicable_structure.height_agl:.1f}m + 豁免额度{applicable_structure.waiver_altitude_above_structure:.2f}m）",
                applicable_structure
            )
    else:
        # No waiver applies: use global limit
        # Calculate distance to nearest structure for reporting
        nearest_distance = float('inf')
        nearest_structure_id = None
        
        for structure in structures:
            dx = position.north - structure.location.north
            dy = position.east - structure.location.east
            distance = math.sqrt(dx**2 + dy**2)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_structure_id = structure.id
        
        if target_altitude_agl >= global_altitude_limit:
            excess = target_altitude_agl - global_altitude_limit
            return (
                False,
                f"目标高度{target_altitude_agl:.1f}m超过全局限制{global_altitude_limit:.1f}m"
                f"（超出{excess:.1f}m），且不在任何建筑物豁免半径内"
                f"（距{nearest_structure_id}约{nearest_distance:.0f}m）",
                None
            )
        else:
            margin = global_altitude_limit - target_altitude_agl
            return (
                True,
                f"目标高度{target_altitude_agl:.1f}m符合全局限制{global_altitude_limit:.1f}m"
                f"（距限制{margin:.1f}m）",
                None
            )


def filter_active_geofences(
    geofences: List[GeofenceConfig], 
    simulated_time: Optional[str] = None
) -> List[GeofenceConfig]:
    """
    Filter geofences based on time restrictions (for TFR scenarios).
    
    Args:
        geofences: All geofences from scenario
        simulated_time: ISO 8601 time string (e.g., "2024-01-15T15:00:00Z")
    
    Returns:
        List of geofences that are active at the simulated time
    """
    if not simulated_time:
        return geofences  # No time simulation, return all
    
    try:
        current_time = parse_iso8601(simulated_time)
        print(f"   Simulated time: {simulated_time}")
    except Exception as e:
        print(f"⚠️  Warning: Could not parse time '{simulated_time}': {e}")
        return geofences
    
    active = []
    
    for gf in geofences:
        # Check if geofence has time restriction
        time_restriction = None
        if hasattr(gf, 'raw_data') and 'time_restriction' in gf.raw_data:
            time_restriction = gf.raw_data['time_restriction']
        
        if not time_restriction:
            # No time restriction = always active (permanent geofence)
            active.append(gf)
            continue
        
        # Parse TFR activation times
        try:
            start_time = parse_iso8601(time_restriction['active_start'])
            end_time = parse_iso8601(time_restriction['active_end'])
            tfr_type = time_restriction.get('type', 'unknown')
            
            # Check if current time is within active period
            is_active = start_time <= current_time < end_time
            
            if is_active:
                active.append(gf)
                duration_hours = (end_time - start_time).total_seconds() / 3600
                time_remaining = (end_time - current_time).total_seconds() / 3600
                print(f"   ✓ TFR '{gf.id}' ACTIVE ({tfr_type}, {time_remaining:.1f}h remaining)")
            else:
                if current_time < start_time:
                    time_until = (start_time - current_time).total_seconds() / 3600
                    status = f"not yet active (starts in {time_until:.1f}h)"
                else:
                    time_since = (current_time - end_time).total_seconds() / 3600
                    status = f"expired ({time_since:.1f}h ago)"
                print(f"   ○ TFR '{gf.id}' INACTIVE ({status})")
        
        except Exception as e:
            print(f"   ⚠️  Warning: Error parsing time restriction for '{gf.id}': {e}")
            # If parsing fails, include the geofence to be safe
            active.append(gf)
    
    print(f"   Active geofences: {len(active)}/{len(geofences)}")
    return active


def load_scenario_config(scenario_file: Path, simulated_time: Optional[str] = None) -> ScenarioConfig:
    """
    Load and parse scenario configuration file.
    
    Args:
        scenario_file: Path to .jsonc scenario file
    
    Returns:
        ScenarioConfig object
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is invalid
    """
    if not scenario_file.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_file}")
    
    with open(scenario_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    clean_content = strip_json_comments(content)
    data = json.loads(clean_content)
    
    # Parse geofences
    geofences = []
    geofences_raw = []  # Keep raw data for time restrictions
    
    if 'geofences' in data:
        for gf_data in data['geofences']:
            if not gf_data.get('enabled', True):
                continue
            
            # Parse center position
            center_data = gf_data['center']
            if 'xyz' in center_data:
                parts = [float(x) for x in center_data['xyz'].split()]
                center = Position3D(north=parts[0], east=parts[1], down=parts[2])
            else:
                center = Position3D(
                    north=center_data.get('north', center_data.get('x', 0)),
                    east=center_data.get('east', center_data.get('y', 0)),
                    down=center_data.get('down', center_data.get('z', 0))
                )
            
            gf_config = GeofenceConfig(
                id=gf_data['id'],
                center=center,
                radius=gf_data['radius'],
                safety_margin=gf_data.get('safety_margin', 500.0),
                enabled=True,
                action=gf_data.get('action', 'reject'),
                zone_type=gf_data.get('zone_type', 'restricted'),
                priority=gf_data.get('priority', 1)
            )
            
            # Attach raw data for time restriction access
            gf_config.raw_data = gf_data
            geofences.append(gf_config)
    
    # Filter geofences by time if simulated_time is provided
    if simulated_time:
        geofences = filter_active_geofences(geofences, simulated_time)
    
    # Load altitude limit if specified (for S006)
    altitude_limit = None
    if 'scenario_parameters' in data:
        params = data['scenario_parameters']
        altitude_limit = params.get('altitude_limit_agl', None)
    
    # Load altitude zones if specified (for S007)
    altitude_zones = []
    if 'altitude_zones' in data:
        for zone_data in data['altitude_zones']:
            # Parse zone geometry
            geometry = zone_data['geometry']
            
            # Parse center (default to origin for infinite zones)
            if 'center' in geometry:
                center_data = geometry['center']
                center = Position3D(
                    north=center_data.get('north', 0.0),
                    east=center_data.get('east', 0.0),
                    down=0.0  # Zones are 2D (horizontal only)
                )
            else:
                # Default center for infinite zones
                center = Position3D(north=0.0, east=0.0, down=0.0)
            
            # Parse radius (negative for infinite zones)
            if geometry['type'] == 'infinite':
                radius = -1.0  # Negative indicates infinite/default zone
            else:
                radius = geometry['radius']
            
            zone_config = AltitudeZoneConfig(
                id=zone_data['id'],
                name=zone_data['name'],
                center=center,
                radius=radius,
                altitude_limit_agl=zone_data['altitude_limit_agl'],
                priority=zone_data['priority'],
                zone_type=zone_data.get('zone_type', 'unknown')
            )
            altitude_zones.append(zone_config)
    
    # Load structures if specified (for S008)
    structures = []
    if 'structures' in data:
        for struct_data in data['structures']:
            # Parse structure location
            location_data = struct_data['location']
            location = Position3D(
                north=location_data['north'],
                east=location_data['east'],
                down=0.0  # Structure base at ground level
            )
            
            # Parse structure parameters
            height_agl = struct_data['height_agl']
            waiver_radius = struct_data['waiver_radius']
            waiver_altitude_above_structure = struct_data['waiver_altitude_above_structure']
            total_waiver_altitude = height_agl + waiver_altitude_above_structure
            
            structure_config = StructureConfig(
                id=struct_data['id'],
                name=struct_data['name'],
                location=location,
                height_agl=height_agl,
                waiver_radius=waiver_radius,
                waiver_altitude_above_structure=waiver_altitude_above_structure,
                total_waiver_altitude=total_waiver_altitude
            )
            structures.append(structure_config)
    
    return ScenarioConfig(
        scenario_id=data.get('id', 'unknown'),
        actors=data.get('actors', []),
        geofences=geofences,
        test_info=data.get('test_info'),
        raw_data=data,
        altitude_limit=altitude_limit,
        altitude_zones=altitude_zones,
        structures=structures
    )


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


def check_geofences(position: Position3D, geofences: List[GeofenceConfig]) -> Tuple[str, List[str], List[str]]:
    """
    Check if position violates any geofences or triggers warnings.
    
    Args:
        position: Current position
        geofences: List of geofence configurations
    
    Returns:
        Tuple of (decision, violations, warnings)
        - decision: "REJECT", "APPROVE_WITH_WARNING", or "APPROVE"
        - violations: List of rejection messages
        - warnings: List of warning messages
    """
    violations = []
    warnings = []
    
    # Sort geofences by priority (lower number = higher priority)
    sorted_geofences = sorted(geofences, key=lambda g: g.priority)
    
    for geofence in sorted_geofences:
        is_inside, distance, action = geofence.check_violation(position)
        
        if is_inside:
            if action == "reject":
                # Hard violation - command should be rejected
                depth = geofence.restricted_distance - distance
                violations.append(
                    f"Geofence '{geofence.id}' ({geofence.zone_type} zone) violated: "
                    f"distance={distance:.1f}m (required >{geofence.restricted_distance:.1f}m), "
                    f"depth={depth:.1f}m"
                )
            elif action == "warn":
                # Soft violation - command approved with warning
                warnings.append(
                    f"WARNING: Entering '{geofence.id}' ({geofence.zone_type} zone): "
                    f"distance={distance:.1f}m, notification to authorities required"
                )
    
    # Determine final decision
    if len(violations) > 0:
        return "REJECT", violations, warnings
    elif len(warnings) > 0:
        return "APPROVE_WITH_WARNING", violations, warnings
    else:
        return "APPROVE", violations, warnings


def sample_path(start: Position3D, end: Position3D, interval: float = 10.0) -> List[Position3D]:
    """
    Sample points along a linear path between start and end positions.
    
    Args:
        start: Starting position
        end: Ending position
        interval: Distance between samples in meters
    
    Returns:
        List of sampled positions along the path
    """
    # Calculate total distance
    dx = end.north - start.north
    dy = end.east - start.east
    dz = end.down - start.down
    total_distance = math.sqrt(dx**2 + dy**2 + dz**2)
    
    if total_distance == 0:
        return [start]
    
    # Calculate number of samples
    num_samples = max(2, int(total_distance / interval) + 1)
    
    samples = []
    for i in range(num_samples):
        t = i / (num_samples - 1)  # Parameter from 0 to 1
        sample = Position3D(
            north=start.north + t * dx,
            east=start.east + t * dy,
            down=start.down + t * dz
        )
        samples.append(sample)
    
    return samples


def check_path_geofences(
    start: Position3D,
    end: Position3D,
    geofences: List[GeofenceConfig],
    sample_interval: float = 10.0
) -> Tuple[str, List[str], List[str], Optional[Position3D]]:
    """
    Check if a flight path crosses through any geofences or warning zones.
    
    This function samples points along the linear path from start to end
    and checks each sample point for geofence violations and warnings.
    
    Args:
        start: Starting position
        end: Ending position
        geofences: List of geofence configurations
        sample_interval: Distance between sample points (meters)
    
    Returns:
        Tuple of (decision, violations, warnings, violation_position)
        - decision: "REJECT", "APPROVE_WITH_WARNING", or "APPROVE"
        - violations: List of rejection messages
        - warnings: List of warning messages
        - violation_position: Position of first violation (if any)
    """
    # Sample path
    path_samples = sample_path(start, end, sample_interval)
    
    violations = []
    warnings = []
    violation_position = None
    
    # Sort geofences by priority
    sorted_geofences = sorted(geofences, key=lambda g: g.priority)
    
    # Check each sample point
    for i, sample_pos in enumerate(path_samples):
        for geofence in sorted_geofences:
            is_inside, distance, action = geofence.check_violation(sample_pos)
            
            if is_inside:
                if action == "reject":
                    depth = geofence.restricted_distance - distance
                    
                    if violation_position is None:
                        violation_position = sample_pos
                    
                    violations.append(
                        f"Path crosses geofence '{geofence.id}' ({geofence.zone_type}) at sample {i}/{len(path_samples)}: "
                        f"position=(N={sample_pos.north:.1f}, E={sample_pos.east:.1f}, Alt={sample_pos.altitude:.1f}m), "
                        f"distance={distance:.1f}m (required >{geofence.restricted_distance:.1f}m), "
                        f"violation_depth={depth:.1f}m"
                    )
                    break  # One violation message per sample point
                elif action == "warn":
                    # Path enters warning zone - note it but don't reject
                    if i == 0 or i == len(path_samples) - 1:  # Only report at entry/exit
                        warnings.append(
                            f"Path enters '{geofence.id}' ({geofence.zone_type}) zone at sample {i}/{len(path_samples)}"
                        )
    
    # Determine final decision
    if len(violations) > 0:
        return "REJECT", violations, warnings, violation_position
    elif len(warnings) > 0:
        return "APPROVE_WITH_WARNING", violations, warnings, violation_position
    else:
        return "APPROVE", violations, warnings, violation_position


async def run_scenario_manual(
    scenario_config: ScenarioConfig,
    scenario_file: Path,
    client: ProjectAirSimClient,
    recorder: TrajectoryRecorder,
    recording_interval: float = 0.5
) -> Dict[str, Any]:
    """
    Run scenario in manual mode (await user commands).
    
    This mode loads the scenario, arms the drone, and continuously monitors
    position for geofence violations. The user manually controls the drone
    through other means (e.g., API calls, keyboard).
    
    Args:
        scenario_config: Scenario configuration
        client: ProjectAirSim client
        recorder: Trajectory recorder
        recording_interval: How often to record position (seconds)
    
    Returns:
        Execution results
    """
    print("\n" + "="*70)
    print("MANUAL SCENARIO MODE")
    print("="*70)
    print("\nScenario will load and monitor for violations.")
    print("Control the drone manually through API calls or other interfaces.")
    print("Press Ctrl+C to stop recording.\n")
    
    # Get world and drone
    # Load the scene from scenario file
    print(f"Loading scene from: {scenario_file}")
    world = World(client, str(scenario_file), delay_after_load_sec=2)
    
    # Assume first actor is the drone
    drone_name = scenario_config.actors[0]['name']
    print(f"Creating drone object: {drone_name}")
    drone = Drone(client, world, drone_name)
    
    print(f"✓ Connected to drone: {drone_name}")
    
    # Arm and enable API control (synchronous methods)
    print("✓ Enabling API control...")
    drone.enable_api_control()
    
    print("✓ Arming drone...")
    drone.arm()
    
    # Get initial position
    initial_pos = get_drone_position(drone)
    print(f"✓ Initial position: N={initial_pos.north:.1f}, E={initial_pos.east:.1f}, Alt={initial_pos.altitude:.1f}m")
    
    if scenario_config.geofences:
        print(f"\n⚠️  Active geofences: {len(scenario_config.geofences)}")
        for gf in scenario_config.geofences:
            print(f"   - {gf.id}: radius={gf.radius}m, margin={gf.safety_margin}m")
    
    # Start recording
    recorder.start()
    recorder.record_point(initial_pos, 0.0)
    
    print("\n🟢 Monitoring started (Ctrl+C to stop)...\n")
    
    violation_count = 0
    
    try:
        while True:
            await asyncio.sleep(recording_interval)
            
            # Get current position
            position = get_drone_position(drone)
            recorder.record_point(position)
            
            # Check geofences
            decision, violations, warnings = check_geofences(position, scenario_config.geofences)
            
            if decision == "REJECT":
                violation_count += 1
                print(f"❌ VIOLATION DETECTED (total: {violation_count}):")
                for msg in violations:
                    print(f"   {msg}")
            elif decision == "APPROVE_WITH_WARNING":
                print(f"⚠️  WARNING:")
                for msg in warnings:
                    print(f"   {msg}")
            else:
                # Print status every 10 samples
                if len(recorder.points) % 10 == 0:
                    print(f"✓ Position: N={position.north:.1f}, E={position.east:.1f}, Alt={position.altitude:.1f}m")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping monitoring...")
    
    # Final position
    final_pos = get_drone_position(drone)
    recorder.record_point(final_pos)
    
    return {
        'success': True,
        'mode': 'manual',
        'violation_count': violation_count,
        'trajectory_points': len(recorder.points)
    }


async def run_scenario_auto(
    scenario_config: ScenarioConfig,
    scenario_file: Path,
    client: ProjectAirSimClient,
    recorder: TrajectoryRecorder,
    test_command: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run scenario in automatic mode (execute predefined test command).
    
    Args:
        scenario_config: Scenario configuration
        client: ProjectAirSim client
        recorder: Trajectory recorder
        test_command: Test command to execute (from test_info or manual input)
    
    Returns:
        Execution results
    """
    print("\n" + "="*70)
    print("AUTOMATIC SCENARIO MODE")
    print("="*70)
    
    # Get test command
    if test_command is None and scenario_config.test_info:
        test_command = scenario_config.test_info.get('test_command')
    
    if not test_command:
        raise ValueError("No test command specified. Use --command or include test_info in scenario.")
    
    print(f"\nTest Command: {test_command}")
    
    # Get world and drone
    # Load the scene from scenario file
    print(f"Loading scene from: {scenario_file}")
    world = World(client, str(scenario_file), delay_after_load_sec=2)
    
    drone_name = scenario_config.actors[0]['name']
    print(f"Creating drone object: {drone_name}")
    drone = Drone(client, world, drone_name)
    
    print(f"✓ Connected to drone: {drone_name}")
    
    # Arm and enable API control (synchronous methods)
    drone.enable_api_control()
    drone.arm()
    
    # Takeoff (async method)
    await drone.takeoff_async()
    
    # Get initial position
    initial_pos = get_drone_position(drone)
    print(f"✓ Initial position: N={initial_pos.north:.1f}, E={initial_pos.east:.1f}, Alt={initial_pos.altitude:.1f}m")
    
    # Start recording
    recorder.start()
    recorder.record_point(initial_pos, 0.0)
    
    # Parse and execute test command
    # Format: "move_to_position(x, y, z)" or similar
    print(f"\n🚀 Executing: {test_command}")
    
    # Initialize warnings list
    all_warnings = []
    
    # TODO: Parse test command and check geofence BEFORE executing
    # For now, this is a placeholder showing the intended flow
    
    if "move_to_position" in test_command:
        # Extract coordinates
        import re
        match = re.search(r'move_to_position\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)', test_command)
        if match:
            target_n, target_e, target_alt = float(match.group(1)), float(match.group(2)), float(match.group(3))
            target_d = -target_alt  # Convert altitude to down (NED)
            target_pos = Position3D(north=target_n, east=target_e, down=target_d)
            
            print(f"   Target: N={target_n}, E={target_e}, Alt={target_alt}m")
            
            # PRE-FLIGHT CHECK 0: Verify altitude limit (if configured)
            # Priority: structure waiver (S008) > zone-based (S007) > global (S006)
            if scenario_config.structures:
                # S008: Structure altitude waiver
                # Note: Structure waiver has highest priority as it can override global limits
                print("\n🔍 Pre-flight check: Altitude limit (structure waiver check)...")
                
                # Determine global limit to use (zone-based or default 120m)
                global_limit = 120.0  # Default
                if scenario_config.altitude_zones:
                    zone = identify_altitude_zone(target_pos, scenario_config.altitude_zones)
                    if zone:
                        global_limit = zone.altitude_limit_agl
                        print(f"   位置所在区域: {zone.name} (全局限制{global_limit:.1f}m)")
                elif scenario_config.altitude_limit is not None:
                    global_limit = scenario_config.altitude_limit
                
                is_altitude_safe, altitude_reason, structure = check_structure_waiver(
                    position=target_pos,
                    target_altitude_agl=target_alt,
                    structures=scenario_config.structures,
                    global_altitude_limit=global_limit
                )
                
                # Log structure identification if applicable
                if structure:
                    dx = target_pos.north - structure.location.north
                    dy = target_pos.east - structure.location.east
                    distance = math.sqrt(dx**2 + dy**2)
                    print(f"   距{structure.id}: {distance:.1f}m (豁免半径{structure.waiver_radius:.2f}m)")
                    print(f"   豁免适用: {structure.name} (高{structure.height_agl:.1f}m)")
                    print(f"   豁免上限: {structure.total_waiver_altitude:.2f}m (建筑{structure.height_agl:.1f}m + {structure.waiver_altitude_above_structure:.2f}m)")
                
                if not is_altitude_safe:
                    print(f"   ❌ {altitude_reason}")
                    print("\n🚫 COMMAND REJECTED (altitude limit exceeded)")
                    
                    return {
                        'success': False,
                        'mode': 'auto',
                        'command_rejected': True,
                        'reason': 'Altitude limit exceeded (structure waiver check failed)',
                        'violations': [altitude_reason],
                        'structure_id': structure.id if structure else None,
                        'trajectory_points': len(recorder.points)
                    }
                else:
                    print(f"   ✓ {altitude_reason}")
                    
            elif scenario_config.altitude_zones:
                # S007: Zone-based altitude limits
                print("\n🔍 Pre-flight check: Altitude limit (zone-based)...")
                is_altitude_safe, altitude_reason, zone = check_zone_altitude_limit(
                    position=target_pos,
                    target_altitude_agl=target_alt,
                    altitude_zones=scenario_config.altitude_zones
                )
                
                # Log zone identification
                if zone:
                    dx = target_pos.north - zone.center.north
                    dy = target_pos.east - zone.center.east
                    distance = math.sqrt(dx**2 + dy**2)
                    if zone.radius > 0:
                        print(f"   识别区域: {zone.name} (距中心{distance:.1f}m < {zone.radius:.1f}m)")
                    else:
                        print(f"   识别区域: {zone.name} (距中心{distance:.1f}m)")
                
                if not is_altitude_safe:
                    print(f"   ❌ {altitude_reason}")
                    print("\n🚫 COMMAND REJECTED (zone altitude limit exceeded)")
                    
                    return {
                        'success': False,
                        'mode': 'auto',
                        'command_rejected': True,
                        'reason': 'Zone altitude limit exceeded',
                        'violations': [altitude_reason],
                        'zone_id': zone.id if zone else None,
                        'trajectory_points': len(recorder.points)
                    }
                else:
                    print(f"   ✓ {altitude_reason}")
                    
            elif scenario_config.altitude_limit is not None:
                # S006: Global altitude limit
                print("\n🔍 Pre-flight check: Altitude limit...")
                is_altitude_safe, altitude_reason = check_altitude_limit(
                    target_altitude_agl=target_alt,
                    limit=scenario_config.altitude_limit,
                    tolerance=0.0  # Strict enforcement
                )
                
                if not is_altitude_safe:
                    print(f"   ❌ {altitude_reason}")
                    print("\n🚫 COMMAND REJECTED (altitude limit exceeded)")
                    
                    return {
                        'success': False,
                        'mode': 'auto',
                        'command_rejected': True,
                        'reason': 'Altitude limit exceeded',
                        'violations': [altitude_reason],
                        'trajectory_points': len(recorder.points)
                    }
                else:
                    print(f"   ✓ {altitude_reason}")
            
            # PRE-FLIGHT CHECK 1: Verify target doesn't violate geofence
            print("\n🔍 Pre-flight check: Target position...")
            target_decision, target_violations, target_warnings = check_geofences(target_pos, scenario_config.geofences)
            
            if target_decision == "REJECT":
                print("   ❌ Target violates geofence!")
                for msg in target_violations:
                    print(f"      {msg}")
                print("\n🚫 COMMAND REJECTED (target in restricted zone)")
                
                return {
                    'success': False,
                    'mode': 'auto',
                    'command_rejected': True,
                    'reason': 'Target violates geofence',
                    'violations': target_violations,
                    'trajectory_points': len(recorder.points)
                }
            
            if target_decision == "APPROVE_WITH_WARNING":
                print("   ⚠️  Target in warning zone:")
                for msg in target_warnings:
                    print(f"      {msg}")
            else:
                print("   ✓ Target position is safe")
            
            # PRE-FLIGHT CHECK 2: Verify path doesn't cross geofence
            print("\n🔍 Pre-flight check: Flight path (sampling every 10m)...")
            path_decision, path_violations, path_warnings, violation_pos = check_path_geofences(
                initial_pos, target_pos, scenario_config.geofences, sample_interval=10.0
            )
            
            if path_decision == "REJECT":
                print("   ❌ Flight path crosses restricted zone!")
                # Only show first few violations to avoid spam
                for msg in path_violations[:3]:
                    print(f"      {msg}")
                if len(path_violations) > 3:
                    print(f"      ... and {len(path_violations) - 3} more violation points")
                
                if violation_pos:
                    print(f"\n   First violation at: N={violation_pos.north:.1f}, E={violation_pos.east:.1f}, Alt={violation_pos.altitude:.1f}m")
                
                print("\n🚫 COMMAND REJECTED (path crosses restricted zone)")
                
                return {
                    'success': False,
                    'mode': 'auto',
                    'command_rejected': True,
                    'reason': 'Flight path crosses geofence',
                    'violations': path_violations,
                    'violation_position': violation_pos.to_dict() if violation_pos else None,
                    'trajectory_points': len(recorder.points)
                }
            
            # Collect all warnings
            all_warnings = target_warnings + path_warnings
            
            if path_decision == "APPROVE_WITH_WARNING" or target_decision == "APPROVE_WITH_WARNING":
                print(f"   ⚠️  Path enters warning zones ({len(sample_path(initial_pos, target_pos))} samples checked)")
                for msg in path_warnings:
                    print(f"      {msg}")
            else:
                print(f"   ✓ Path is safe ({len(sample_path(initial_pos, target_pos))} samples checked)")
            
            # Display final decision
            if len(all_warnings) > 0:
                print("\n✅ COMMAND APPROVED (with warnings)")
                print("⚠️  Active warnings:")
                for warning in all_warnings:
                    print(f"   - {warning}")
            else:
                print("\n✅ All pre-flight checks passed")
            
            
            # Execute movement with continuous monitoring
            print("✓ Pre-flight check passed, executing movement...")
            
            # Move to position with timeout handling
            try:
                await drone.move_to_position_async(
                    north=target_n,
                    east=target_e,
                    down=target_d,
                    velocity=5.0
                )
                
                # Record trajectory during movement
                while True:
                    position = get_drone_position(drone)
                    recorder.record_point(position)
                    
                    # Check if reached target (within 1m)
                    dist = math.sqrt(
                        (position.north - target_n)**2 +
                        (position.east - target_e)**2 +
                        (position.down - target_d)**2
                    )
                    
                    if dist < 1.0:
                        print("✓ Target reached")
                        break
                    
                    # Check for violations during flight
                    decision, violations, warnings = check_geofences(position, scenario_config.geofences)
                    if decision == "REJECT":
                        print(f"❌ VIOLATION during flight:")
                        for msg in violations:
                            print(f"   {msg}")
                    elif decision == "APPROVE_WITH_WARNING":
                        print(f"⚠️  WARNING during flight:")
                        for msg in warnings:
                            print(f"   {msg}")
                    
                    await asyncio.sleep(0.1)
            
            except Exception as e:
                # Handle timeout or other exceptions during flight
                print(f"\n⚠️  Flight interrupted: {e}")
                
                # Try to get final position, but if connection is closed, use last recorded position
                try:
                    position = get_drone_position(drone)
                    recorder.record_point(position)
                except:
                    # Connection closed, use last recorded position
                    if recorder.points:
                        position = Position3D(
                            north=recorder.points[-1]['position']['north'],
                            east=recorder.points[-1]['position']['east'],
                            down=recorder.points[-1]['position']['down']
                        )
                        print("   Using last recorded position (connection closed)")
                    else:
                        position = initial_pos
                        print("   Using initial position (no trajectory recorded)")
                
                print(f"   Last position: N={position.north:.1f}, E={position.east:.1f}, Alt={position.altitude:.1f}m")
                
                # Calculate distance traveled
                distance_traveled = math.sqrt(
                    (position.north - initial_pos.north)**2 +
                    (position.east - initial_pos.east)**2 +
                    (position.down - initial_pos.down)**2
                )
                distance_remaining = math.sqrt(
                    (position.north - target_n)**2 +
                    (position.east - target_e)**2 +
                    (position.down - target_d)**2
                )
                print(f"   Distance traveled: {distance_traveled:.1f}m")
                print(f"   Distance remaining: {distance_remaining:.1f}m")
                print(f"   Trajectory recorded: {len(recorder.points)} points")
    
    else:
        print(f"⚠️  Unknown command format: {test_command}")
        print("   Supported: move_to_position(n, e, alt)")
    
    # Final position (if connection still active)
    try:
        final_pos = get_drone_position(drone)
        recorder.record_point(final_pos)
    except:
        # Connection closed or other error, final position already recorded
        pass
    
    return {
        'success': True,
        'mode': 'auto',
        'command_executed': test_command,
        'trajectory_points': len(recorder.points),
        'warnings': all_warnings if len(all_warnings) > 0 else None
    }


async def run_scenario_async(
    scenario_file: Path,
    output_file: Path,
    mode: str = "manual",
    test_command: Optional[str] = None,
    simulated_time: Optional[str] = None
) -> int:
    """
    Main async entry point for scenario execution.
    
    Args:
        scenario_file: Path to scenario configuration
        output_file: Where to save trajectory
        mode: Execution mode ("auto" or "manual")
        test_command: Test command for auto mode
    
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        # Load scenario configuration
        print(f"Loading scenario: {scenario_file}")
        scenario_config = load_scenario_config(scenario_file, simulated_time)
        print(f"✓ Scenario loaded: {scenario_config.scenario_id}")
        
        # Connect to ProjectAirSim
        print("Connecting to ProjectAirSim...")
        client = ProjectAirSimClient()
        client.connect()  # Synchronous, no await needed
        print("✓ Connected to ProjectAirSim")
        
        # Create trajectory recorder
        recorder = TrajectoryRecorder()
        
        # Run scenario based on mode
        if mode == "auto":
            result = await run_scenario_auto(scenario_config, scenario_file, client, recorder, test_command)
        else:
            result = await run_scenario_manual(scenario_config, scenario_file, client, recorder)
        
        # Save trajectory
        metadata = {
            'scenario_id': scenario_config.scenario_id,
            'scenario_file': str(scenario_file),
            'mode': mode,
            'execution_result': result
        }
        recorder.save(output_file, metadata)
        
        print("\n" + "="*70)
        if result.get('success', False):
            print("✓ SCENARIO EXECUTION COMPLETED")
        else:
            print("⚠️  SCENARIO EXECUTION COMPLETED WITH WARNINGS")
        print("="*70)
        
        return 0 if result.get('success', False) else 1
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Run LAE-GPT test scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in manual mode (monitor while user controls drone)
  %(prog)s ../scenarios/basic/S001_geofence_basic.jsonc -o traj.json --mode manual
  
  # Run in auto mode (execute test command automatically)
  %(prog)s S001.jsonc -o traj.json --mode auto --command "move_to_position(0, 0, 50)"
  
  # Use test command from scenario file
  %(prog)s S001.jsonc -o traj.json --mode auto

Note:
  This script must be run on the remote server with ProjectAirSim.
  Typical location: ~/project/ProjectAirSim/client/python/example_user_scripts/
        """
    )
    
    parser.add_argument(
        'scenario_file',
        type=Path,
        help='Path to scenario .jsonc file'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='Output trajectory file (JSON)'
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['auto', 'manual'],
        default='manual',
        help='Execution mode (default: manual)'
    )
    
    parser.add_argument(
        '--command', '-c',
        type=str,
        help='Test command for auto mode (e.g., "move_to_position(0, 0, 50)")'
    )
    
    parser.add_argument(
        '--simulated-time', '-t',
        type=str,
        help='Simulated current time for TFR testing (ISO 8601 format: "2024-01-15T15:00:00Z")'
    )
    
    args = parser.parse_args()
    
    # Run async main
    exit_code = asyncio.run(run_scenario_async(
        args.scenario_file,
        args.output,
        args.mode,
        args.command,
        args.simulated_time
    ))
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
Motion Parameter Scenario Runner for LAE-GPT (S009-S012)

This script handles scenarios involving speed and time restrictions.
It is a simplified version of run_scenario.py focused on motion parameters
rather than spatial constraints (geofences, altitude limits).

Supported Scenarios:
  - S009: Global Speed Limit (100 km/h)
  - S010: Zone-based Speed Limits
  - S011: Night Flight Restrictions
  - S012: Time Window Restrictions

Usage:
    python run_scenario_motion.py <scenario_file.jsonc> --output <trajectory_file.json>
    
Example:
    python run_scenario_motion.py ../scenarios/basic/S009_speed_limit.jsonc \
        --output ../test_logs/trajectory_S009_TC1.json \
        --mode auto --command "move_to_position_with_velocity(500, 0, 50, 25.0)"

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
class SpeedRestrictionConfig:
    """Speed restriction configuration."""
    max_speed_kmh: float
    max_speed_ms: float = 0.0  # Will be calculated
    tolerance_kmh: float = 0.0
    enforcement_mode: str = "strict"  # "strict" or "warning"
    
    def __post_init__(self):
        """Calculate m/s from km/h if not provided."""
        if self.max_speed_ms == 0.0:
            self.max_speed_ms = self.max_speed_kmh / 3.6
    
    def check_violation(self, velocity: Velocity3D) -> Tuple[bool, float, str]:
        """
        Check if velocity violates speed limit.
        
        Returns:
            Tuple of (is_violation, speed_kmh, reason)
        """
        speed_kmh = velocity.ground_speed_kmh
        effective_limit = self.max_speed_kmh + self.tolerance_kmh
        
        if speed_kmh >= effective_limit:
            excess = speed_kmh - self.max_speed_kmh
            reason = f"速度{speed_kmh:.1f}km/h超过限制{self.max_speed_kmh:.1f}km/h（超出{excess:.1f}km/h）"
            return True, speed_kmh, reason
        else:
            margin = self.max_speed_kmh - speed_kmh
            reason = f"速度{speed_kmh:.1f}km/h合规（距限制{margin:.1f}km/h）"
            return False, speed_kmh, reason


@dataclass
class SpeedZoneConfig:
    """Speed zone configuration for zone-based speed limits."""
    zone_id: str
    zone_type: str  # "cylinder" or "global"
    speed_limit_kmh: float
    speed_limit_ms: float
    priority: int  # Lower number = higher priority (most restrictive)
    enabled: bool = True
    
    # Cylinder zone parameters (optional)
    center_north: float = 0.0
    center_east: float = 0.0
    center_down: float = 0.0
    radius: float = 0.0
    height_min: float = -1000.0
    height_max: float = 1000.0
    
    # Metadata
    description: str = ""
    reason: str = ""
    
    def is_position_in_zone(self, position: Position3D) -> bool:
        """Check if a position is inside this zone."""
        if self.zone_type == "global":
            return True  # Global zone contains everything
        
        if self.zone_type == "cylinder":
            # Check horizontal distance
            distance_2d = math.sqrt(
                (position.north - self.center_north)**2 +
                (position.east - self.center_east)**2
            )
            inside_horizontal = distance_2d <= self.radius
            
            # Check vertical range
            inside_vertical = self.height_min < position.down < self.height_max
            
            return inside_horizontal and inside_vertical
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'zone_id': self.zone_id,
            'zone_type': self.zone_type,
            'speed_limit_kmh': self.speed_limit_kmh,
            'priority': self.priority,
            'center': {'n': self.center_north, 'e': self.center_east, 'd': self.center_down},
            'radius': self.radius if self.zone_type == "cylinder" else None,
            'description': self.description
        }


@dataclass
class NightFlightConfig:
    """Night flight configuration."""
    sunrise: str = "06:00"           # Sunrise time (HH:MM)
    sunset: str = "18:00"            # Sunset time (HH:MM)
    civil_twilight_before: str = "05:30"  # Civil twilight before sunrise
    civil_twilight_after: str = "18:30"   # Civil twilight after sunset
    night_start: str = "18:30"       # Night starts (sunset + 30min)
    night_end: str = "05:30"         # Night ends (sunrise - 30min)
    lighting_required: bool = True   # Anti-collision light required at night
    training_required: bool = True   # Night training required for pilot
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'sunrise': self.sunrise,
            'sunset': self.sunset,
            'night_period': f"{self.night_start}-{self.night_end}",
            'lighting_required': self.lighting_required,
            'training_required': self.training_required
        }


@dataclass
class TimeWindowZoneConfig:
    """Time window restriction zone configuration (S012)."""
    zone_id: str
    zone_type: str  # "cylinder" or "global"
    description: str = ""
    reason: str = ""
    enabled: bool = True
    priority: int = 1
    
    # Cylinder zone parameters (optional)
    center_north: float = 0.0
    center_east: float = 0.0
    center_down: float = 0.0
    radius: float = 0.0
    height_min: float = -1000.0
    height_max: float = 1000.0
    
    # Time window parameters
    time_window_start: str = "22:00"
    time_window_end: str = "06:00"
    time_window_description: str = ""
    restriction_type: str = "no_fly"
    
    def is_position_in_zone(self, position: Position3D) -> bool:
        """Check if a position is inside this zone."""
        if self.zone_type == "global":
            return True  # Global zone contains everything
        
        if self.zone_type == "cylinder":
            # Check horizontal distance
            distance_2d = math.sqrt(
                (position.north - self.center_north)**2 +
                (position.east - self.center_east)**2
            )
            inside_horizontal = distance_2d <= self.radius
            
            # Check vertical range
            inside_vertical = self.height_min < position.down < self.height_max
            
            return inside_horizontal and inside_vertical
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'zone_id': self.zone_id,
            'zone_type': self.zone_type,
            'time_window': f"{self.time_window_start}-{self.time_window_end}",
            'center': {'n': self.center_north, 'e': self.center_east, 'd': self.center_down},
            'radius': self.radius if self.zone_type == "cylinder" else None,
            'description': self.description
        }


@dataclass
class ScenarioConfig:
    """Parsed scenario configuration."""
    scenario_id: str
    actors: List[Dict[str, Any]]
    test_info: Optional[Dict[str, Any]] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    speed_restriction: Optional[SpeedRestrictionConfig] = None
    speed_zones: List[SpeedZoneConfig] = field(default_factory=list)
    night_flight: Optional[NightFlightConfig] = None
    time_window_zones: List[TimeWindowZoneConfig] = field(default_factory=list)


@dataclass
class TrajectoryRecorder:
    """Records drone trajectory during scenario execution."""
    points: List[Dict[str, Any]] = field(default_factory=list)
    start_time: float = 0.0
    
    def start(self) -> None:
        """Start recording."""
        self.start_time = time.time()
        self.points = []
    
    def record_point(
        self, 
        position: Position3D, 
        velocity: Optional[Velocity3D] = None,
        timestamp: Optional[float] = None
    ) -> None:
        """Record a trajectory point with optional velocity."""
        if timestamp is None:
            timestamp = time.time() - self.start_time
        
        point_data = {
            'timestamp': timestamp,
            'position': position.to_dict()
        }
        
        if velocity:
            point_data['velocity'] = velocity.to_dict()
        
        self.points.append(point_data)
    
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


# ============================================================================
# SECTION 2: Utility Functions
# ============================================================================

def strip_json_comments(text: str) -> str:
    """Remove JavaScript-style comments from JSON."""
    import re
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text


def kmh_to_ms(speed_kmh: float) -> float:
    """Convert km/h to m/s."""
    return speed_kmh / 3.6


def ms_to_kmh(speed_ms: float) -> float:
    """Convert m/s to km/h."""
    return speed_ms * 3.6


# ============================================================================
# SECTION 3: Scenario Loading and Configuration Parsing
# ============================================================================

def load_scenario_config(scenario_file: Path) -> ScenarioConfig:
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
    
    # Parse speed restriction if present (S009 - global speed limit)
    speed_restriction = None
    if 'scenario_parameters' in data:
        params = data['scenario_parameters']
        if 'speed_limit_kmh' in params:
            speed_restriction = SpeedRestrictionConfig(
                max_speed_kmh=params['speed_limit_kmh'],
                max_speed_ms=params.get('speed_limit_ms', 0.0),
                tolerance_kmh=params.get('tolerance_margin_kmh', 0.0),
                enforcement_mode=params.get('enforcement_mode', 'strict')
            )
    
    # Parse speed zones if present (S010 - zone-based speed limits)
    speed_zones = []
    if 'speed_zones' in data:
        for zone_data in data['speed_zones']:
            if not zone_data.get('enabled', True):
                continue
            
            zone = SpeedZoneConfig(
                zone_id=zone_data['id'],
                zone_type=zone_data['type'],
                speed_limit_kmh=zone_data['speed_limit_kmh'],
                speed_limit_ms=zone_data['speed_limit_ms'],
                priority=zone_data.get('priority', 999),
                enabled=zone_data.get('enabled', True),
                description=zone_data.get('description', ''),
                reason=zone_data.get('reason', '')
            )
            
            # Parse cylinder-specific parameters
            if zone.zone_type == "cylinder":
                center = zone_data.get('center', {})
                xyz = center.get('xyz', '0.0 0.0 0.0').split()
                zone.center_north = float(xyz[0])
                zone.center_east = float(xyz[1])
                zone.center_down = float(xyz[2])
                zone.radius = zone_data.get('radius', 0.0)
                zone.height_min = zone_data.get('height_min', -1000.0)
                zone.height_max = zone_data.get('height_max', 1000.0)
            
            speed_zones.append(zone)
    
    # Parse night flight configuration if present (S011 - night flight restrictions)
    night_flight = None
    if 'scenario_parameters' in data and 'time_definitions' in data['scenario_parameters']:
        time_defs = data['scenario_parameters']['time_definitions']
        night_period = data['scenario_parameters'].get('night_period', {})
        
        night_flight = NightFlightConfig(
            sunrise=time_defs.get('sunrise', '06:00'),
            sunset=time_defs.get('sunset', '18:00'),
            civil_twilight_before=time_defs.get('civil_twilight_before_sunrise', '05:30'),
            civil_twilight_after=time_defs.get('civil_twilight_after_sunset', '18:30'),
            night_start=night_period.get('start', '18:30'),
            night_end=night_period.get('end', '05:30'),
            lighting_required=data['scenario_parameters'].get('lighting_requirements', {}).get('mandatory_at_night', True),
            training_required=data['scenario_parameters'].get('pilot_requirements', {}).get('night_training_required', True)
        )
    
    # Parse time window restricted zones if present (S012 - time window restrictions)
    time_window_zones = []
    if 'time_restricted_zones' in data:
        for zone_data in data['time_restricted_zones']:
            if not zone_data.get('enabled', True):
                continue
            
            zone = TimeWindowZoneConfig(
                zone_id=zone_data['zone_id'],
                zone_type=zone_data['zone_type'],
                description=zone_data.get('description', ''),
                reason=zone_data.get('reason', ''),
                enabled=zone_data.get('enabled', True),
                priority=zone_data.get('priority', 1)
            )
            
            # Parse time window
            if 'time_windows' in zone_data and len(zone_data['time_windows']) > 0:
                time_window = zone_data['time_windows'][0]  # Use first time window
                zone.time_window_start = time_window.get('start_time', '22:00')
                zone.time_window_end = time_window.get('end_time', '06:00')
                zone.time_window_description = time_window.get('description', '')
                zone.restriction_type = time_window.get('restriction_type', 'no_fly')
            
            # Parse cylinder-specific parameters
            if zone.zone_type == "cylinder":
                center = zone_data.get('center', {})
                xyz = center.get('xyz', '0.0 0.0 0.0').split()
                zone.center_north = float(xyz[0])
                zone.center_east = float(xyz[1])
                zone.center_down = float(xyz[2])
                zone.radius = zone_data.get('radius', 0.0)
                zone.height_min = zone_data.get('height_min', -1000.0)
                zone.height_max = zone_data.get('height_max', 1000.0)
            
            time_window_zones.append(zone)
    
    return ScenarioConfig(
        scenario_id=data.get('id', 'unknown'),
        actors=data.get('actors', []),
        test_info=data.get('test_info'),
        raw_data=data,
        speed_restriction=speed_restriction,
        speed_zones=speed_zones,
        night_flight=night_flight,
        time_window_zones=time_window_zones
    )


def get_drone_position(drone: Drone) -> Position3D:
    """
    Get current drone position.
    
    Args:
        drone: Drone instance
    
    Returns:
        Position3D in NED coordinates
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
        drone: Drone instance
    
    Returns:
        Velocity3D in NED coordinates
    
    Note:
        ProjectAirSim Drone API does not provide velocity data directly.
        This function returns a zero velocity placeholder.
        Velocity monitoring is disabled in this version.
    """
    # ProjectAirSim API limitation: No direct velocity access
    # Return zero velocity (speed monitoring relies on pre-flight check only)
    return Velocity3D(north=0.0, east=0.0, down=0.0)


# ============================================================================
# SECTION 4: Speed Checking Functions
# ============================================================================

def generate_path_samples(
    start: Position3D,
    end: Position3D,
    interval_m: float = 10.0
) -> List[Position3D]:
    """
    Generate sample points along a straight path from start to end.
    
    Args:
        start: Start position
        end: End position
        interval_m: Sampling interval in meters
    
    Returns:
        List of sample positions
    """
    # Calculate path length
    distance = math.sqrt(
        (end.north - start.north)**2 +
        (end.east - start.east)**2 +
        (end.down - start.down)**2
    )
    
    if distance < 1e-6:  # Very short distance
        return [start, end]
    
    # Calculate number of samples
    num_samples = max(2, int(distance / interval_m) + 1)
    
    samples = []
    for i in range(num_samples):
        t = i / (num_samples - 1)  # Parameter from 0 to 1
        sample = Position3D(
            north=start.north + t * (end.north - start.north),
            east=start.east + t * (end.east - start.east),
            down=start.down + t * (end.down - start.down)
        )
        samples.append(sample)
    
    return samples


def detect_zones_on_path(
    start: Position3D,
    end: Position3D,
    zones: List[SpeedZoneConfig]
) -> List[SpeedZoneConfig]:
    """
    Detect which speed zones the flight path will traverse.
    
    Args:
        start: Start position
        end: End position
        zones: List of speed zones
    
    Returns:
        List of zones traversed by the path
    """
    if not zones:
        return []
    
    # Generate path samples
    path_samples = generate_path_samples(start, end, interval_m=10.0)
    
    # Track which zones are traversed
    zones_traversed = []
    zone_ids_seen = set()
    
    for sample in path_samples:
        for zone in zones:
            if zone.is_position_in_zone(sample) and zone.zone_id not in zone_ids_seen:
                zones_traversed.append(zone)
                zone_ids_seen.add(zone.zone_id)
    
    return zones_traversed


def get_most_restrictive_zone(zones: List[SpeedZoneConfig]) -> Optional[SpeedZoneConfig]:
    """
    Get the most restrictive (lowest speed limit) zone from a list.
    
    Args:
        zones: List of speed zones
    
    Returns:
        Most restrictive zone, or None if list is empty
    """
    if not zones:
        return None
    
    # Sort by priority (lower number = higher priority) and speed limit (lower = more restrictive)
    return min(zones, key=lambda z: (z.priority, z.speed_limit_kmh))


def check_zone_speed_limits(
    target_velocity_ms: float,
    start_position: Position3D,
    target_position: Position3D,
    zones: List[SpeedZoneConfig]
) -> Tuple[bool, str, Optional[SpeedZoneConfig]]:
    """
    Check if target velocity exceeds speed limits in any zone along the path.
    
    Args:
        target_velocity_ms: Target velocity in m/s
        start_position: Start position
        target_position: Target position
        zones: List of speed zones
    
    Returns:
        Tuple of (is_safe, reason, violated_zone)
    """
    if not zones:
        return True, "无速度限制区域", None
    
    # Detect zones along the path
    zones_on_path = detect_zones_on_path(start_position, target_position, zones)
    
    if not zones_on_path:
        # No zones detected, use global limit if available
        global_zone = next((z for z in zones if z.zone_type == "global"), None)
        if global_zone:
            zones_on_path = [global_zone]
        else:
            return True, "路径不经过任何速度限制区域", None
    
    # Get most restrictive zone
    most_restrictive = get_most_restrictive_zone(zones_on_path)
    
    if most_restrictive is None:
        return True, "无适用的速度限制", None
    
    # Check if velocity exceeds the most restrictive limit
    target_velocity_kmh = ms_to_kmh(target_velocity_ms)
    
    if target_velocity_kmh >= most_restrictive.speed_limit_kmh:
        excess = target_velocity_kmh - most_restrictive.speed_limit_kmh
        zone_name = most_restrictive.zone_id.replace('_', ' ').replace('zone', '区')
        return (
            False,
            f"目标速度{target_velocity_kmh:.1f}km/h超过{zone_name}限制{most_restrictive.speed_limit_kmh:.1f}km/h（超出{excess:.1f}km/h）",
            most_restrictive
        )
    else:
        margin = most_restrictive.speed_limit_kmh - target_velocity_kmh
        zone_name = most_restrictive.zone_id.replace('_', ' ').replace('zone', '区')
        return (
            True,
            f"目标速度{target_velocity_kmh:.1f}km/h合规（{zone_name}限制{most_restrictive.speed_limit_kmh:.1f}km/h，距限制{margin:.1f}km/h）",
            most_restrictive
        )


def check_speed_limit(
    target_velocity_ms: float,
    speed_restriction: SpeedRestrictionConfig
) -> Tuple[bool, str]:
    """
    Check if target velocity exceeds speed limit.
    
    Args:
        target_velocity_ms: Target velocity in m/s
        speed_restriction: Speed restriction configuration
    
    Returns:
        Tuple of (is_safe, reason)
    """
    target_velocity_kmh = ms_to_kmh(target_velocity_ms)
    effective_limit_kmh = speed_restriction.max_speed_kmh + speed_restriction.tolerance_kmh
    
    if target_velocity_kmh >= effective_limit_kmh:
        excess = target_velocity_kmh - speed_restriction.max_speed_kmh
        return (
            False,
            f"目标速度{target_velocity_kmh:.1f}km/h达到或超过{speed_restriction.max_speed_kmh:.1f}km/h限制（超出{excess:.1f}km/h）"
        )
    else:
        margin = speed_restriction.max_speed_kmh - target_velocity_kmh
        return (
            True,
            f"目标速度{target_velocity_kmh:.1f}km/h合规（距限制{margin:.1f}km/h）"
        )


def parse_time(time_str: str) -> int:
    """
    Parse time string in HH:MM format to minutes since midnight.
    
    Args:
        time_str: Time string in "HH:MM" format
    
    Returns:
        Minutes since midnight (0-1439)
    
    Example:
        "00:00" -> 0
        "12:00" -> 720
        "18:30" -> 1110
        "23:59" -> 1439
    """
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    except (ValueError, AttributeError):
        print(f"⚠ Invalid time format: {time_str}, using 12:00 as default")
        return 720  # Default to noon


def is_night_time(current_time: str, night_start: str = "18:30", night_end: str = "05:30") -> bool:
    """
    Check if current time is night time.
    
    Night is defined as: night_start (18:30) to night_end (05:30)
    This period spans across midnight.
    
    Args:
        current_time: Current time in "HH:MM" format
        night_start: Night start time (default "18:30" = sunset + 30min)
        night_end: Night end time (default "05:30" = sunrise - 30min)
    
    Returns:
        True if current time is night, False otherwise
    
    Example:
        is_night_time("12:00") -> False  # Daytime
        is_night_time("18:29") -> False  # Civil twilight (before night)
        is_night_time("18:30") -> True   # Night starts
        is_night_time("22:00") -> True   # Night
        is_night_time("00:00") -> True   # Night (after midnight)
        is_night_time("05:29") -> True   # Night (before sunrise)
        is_night_time("05:30") -> False  # Civil twilight (night ends)
        is_night_time("06:00") -> False  # Daytime
    """
    current_min = parse_time(current_time)
    start_min = parse_time(night_start)
    end_min = parse_time(night_end)
    
    # Night spans across midnight: 18:30-23:59 and 00:00-05:30
    # So: (time >= 18:30) OR (time < 05:30)
    return current_min >= start_min or current_min < end_min


def check_night_flight_requirements(
    time_of_day: str,
    anti_collision_light: bool,
    pilot_night_training: bool,
    night_config: Optional[NightFlightConfig] = None
) -> Tuple[bool, str]:
    """
    Check night flight requirements (lighting and training).
    
    Args:
        time_of_day: Current time in "HH:MM" format
        anti_collision_light: Whether anti-collision light is enabled
        pilot_night_training: Whether pilot has night training
        night_config: Night flight configuration (optional)
    
    Returns:
        Tuple of (is_compliant, reason)
    
    Regulations:
        - China: § 32(7) - Must have lighting system at night
        - USA: Part 107.29 - Must have anti-collision light (3mi visible) + night training
    """
    # Use default configuration if not provided
    if night_config is None:
        night_config = NightFlightConfig()
    
    # Check if current time is night
    is_night = is_night_time(time_of_day, night_config.night_start, night_config.night_end)
    
    if not is_night:
        # Daytime or civil twilight - no restrictions
        return True, f"{time_of_day}为白天/黄昏，无需夜间限制"
    
    # Night time - check requirements
    violations = []
    
    # Check lighting requirement
    if night_config.lighting_required and not anti_collision_light:
        violations.append("夜间飞行必须开启防撞灯（《条例》第32条第七款 / Part 107.29(a)(2)）")
    
    # Check training requirement
    if night_config.training_required and not pilot_night_training:
        violations.append("操作员必须完成夜间飞行培训（Part 107.29(a)(1)）")
    
    if violations:
        return False, violations[0]  # Return first violation
    else:
        return True, f"{time_of_day}为夜间，已满足灯光和培训要求"


def check_time_window_restrictions(
    time_of_day: str,
    target_position: Position3D,
    time_window_zones: List[TimeWindowZoneConfig]
) -> Tuple[bool, str]:
    """
    Check if flight is restricted by time window zones.
    
    Time window restrictions apply when BOTH conditions are met:
    1. Current time is within the restricted time window
    2. Target position is within the restricted zone
    
    Args:
        time_of_day: Current time in "HH:MM" format
        target_position: Target position
        time_window_zones: List of time window restricted zones
    
    Returns:
        Tuple of (is_safe, reason)
    
    Example (S012):
        Hospital zone: 22:00-06:00 night quiet hours
        - 14:00 in hospital → ALLOW (not in time window)
        - 23:00 outside hospital → ALLOW (not in zone)
        - 23:00 in hospital → REJECT (both conditions met)
    """
    if not time_window_zones:
        return True, "无时间窗口限制"
    
    # Check each time window zone
    for zone in time_window_zones:
        if not zone.enabled:
            continue
        
        # Check if in time window
        is_in_time_window = is_night_time(
            time_of_day,
            zone.time_window_start,
            zone.time_window_end
        )
        
        # Check if in zone
        is_in_zone = zone.is_position_in_zone(target_position)
        
        # AND logic: both conditions must be true to restrict
        if is_in_time_window and is_in_zone:
            zone_name = zone.zone_id.replace('_', ' ')
            return (
                False,
                f"{zone.time_window_start}-{zone.time_window_end}禁飞时段，禁止在{zone_name}内飞行（{zone.reason}）"
            )
    
    return True, "通过时间窗口检查"


# ============================================================================
# SECTION 5: Scenario Execution
# ============================================================================

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
        scenario_file: Path to scenario file
        client: ProjectAirSim client
        recorder: Trajectory recorder
        test_command: Test command to execute
    
    Returns:
        Execution results
    """
    print("\n" + "="*70)
    print("AUTOMATIC SCENARIO MODE - MOTION PARAMETERS")
    print("="*70)
    
    # Get test command, time, and drone config from test_info
    time_of_day = None
    drone_config = {}
    
    # Load from test_info if available
    if scenario_config.test_info:
        if test_command is None:
            test_command = scenario_config.test_info.get('test_command')
        # Always load time and config from test_info (even if test_command was provided)
        time_of_day = scenario_config.test_info.get('time_of_day')
        drone_config = scenario_config.test_info.get('drone_config', {})
    
    if not test_command:
        raise ValueError("No test command specified. Use --command or include test_info in scenario.")
    
    print(f"\nTest Command: {test_command}")
    if time_of_day:
        print(f"Time of Day: {time_of_day}")
    if drone_config:
        print(f"Drone Config: {drone_config}")
    
    # Load the scene
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
    await drone.takeoff_async()
    
    # Get initial position
    initial_pos = get_drone_position(drone)
    print(f"✓ Initial position: N={initial_pos.north:.1f}, E={initial_pos.east:.1f}, Alt={initial_pos.altitude:.1f}m")
    
    # Start recording
    recorder.start()
    initial_velocity = get_drone_velocity(drone)
    recorder.record_point(initial_pos, initial_velocity, 0.0)
    
    # Parse and execute test command
    print(f"\n🚀 Executing: {test_command}")
    
    if "move_to_position_with_velocity" in test_command:
        # Extract coordinates and velocity
        import re
        match = re.search(
            r'move_to_position_with_velocity\s*\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)',
            test_command
        )
        if match:
            target_n = float(match.group(1))
            target_e = float(match.group(2))
            target_alt = float(match.group(3))
            target_velocity_ms = float(match.group(4))
            
            target_d = -target_alt  # Convert altitude to down (NED)
            target_position = Position3D(north=target_n, east=target_e, down=target_d)
            
            print(f"   Target: N={target_n}, E={target_e}, Alt={target_alt}m")
            print(f"   Velocity: {target_velocity_ms:.2f} m/s ({ms_to_kmh(target_velocity_ms):.1f} km/h)")
            
            # Get current position for zone-based checks
            current_position = get_drone_position(drone)
            
            # PRE-FLIGHT CHECK 1: Night flight requirements (S011)
            if scenario_config.night_flight and time_of_day:
                print("\n🔍 Pre-flight check: Night flight requirements...")
                anti_collision_light = drone_config.get('anti_collision_light', False)
                pilot_night_training = drone_config.get('pilot_night_training', False)
                
                is_night_compliant, night_reason = check_night_flight_requirements(
                    time_of_day,
                    anti_collision_light,
                    pilot_night_training,
                    scenario_config.night_flight
                )
                
                if not is_night_compliant:
                    print(f"   ❌ {night_reason}")
                    print("\n🚫 COMMAND REJECTED (night flight requirements not met)")
                    
                    return {
                        'success': False,
                        'mode': 'auto',
                        'command_rejected': True,
                        'reason': 'Night flight violation',
                        'violations': [night_reason],
                        'trajectory_points': len(recorder.points)
                    }
                else:
                    print(f"   ✓ {night_reason}")
            
            # PRE-FLIGHT CHECK 2: Verify speed limit
            # Pre-flight speed check
            is_speed_safe = True
            speed_reason = ""
            
            # Check zone-based speed limits first (S010)
            if scenario_config.speed_zones:
                print("\n🔍 Pre-flight check: Zone-based speed limits...")
                is_speed_safe, speed_reason, violated_zone = check_zone_speed_limits(
                    target_velocity_ms,
                    current_position,
                    target_position,
                    scenario_config.speed_zones
                )
            # Fall back to global speed limit (S009)
            elif scenario_config.speed_restriction:
                print("\n🔍 Pre-flight check: Speed limit...")
                is_speed_safe, speed_reason = check_speed_limit(
                    target_velocity_ms,
                    scenario_config.speed_restriction
                )
            
            if not is_speed_safe:
                print(f"   ❌ {speed_reason}")
                print("\n🚫 COMMAND REJECTED (speed limit exceeded)")
                
                return {
                    'success': False,
                    'mode': 'auto',
                    'command_rejected': True,
                    'reason': 'Speed limit exceeded',
                    'violations': [speed_reason],
                    'trajectory_points': len(recorder.points)
                }
            else:
                print(f"   ✓ {speed_reason}")
            
            print("\n✅ All pre-flight checks passed")
            print("✓ Executing movement...")
            
            # Execute movement with velocity control
            try:
                await drone.move_to_position_async(
                    north=target_n,
                    east=target_e,
                    down=target_d,
                    velocity=target_velocity_ms
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
                    
                    # Note: Real-time speed monitoring disabled due to API limitation
                    # Speed checking is done at pre-flight stage only
                    
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
    
    elif "move_to_position" in test_command:
        # Simple move_to_position command (without velocity) - used in S011
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
            
            # PRE-FLIGHT CHECK: Night flight requirements (S011)
            if scenario_config.night_flight and time_of_day:
                print("\n🔍 Pre-flight check: Night flight requirements...")
                anti_collision_light = drone_config.get('anti_collision_light', False)
                pilot_night_training = drone_config.get('pilot_night_training', False)
                
                is_night_compliant, night_reason = check_night_flight_requirements(
                    time_of_day,
                    anti_collision_light,
                    pilot_night_training,
                    scenario_config.night_flight
                )
                
                if not is_night_compliant:
                    print(f"   ❌ {night_reason}")
                    print("\n🚫 COMMAND REJECTED (night flight requirements not met)")
                    
                    return {
                        'success': False,
                        'mode': 'auto',
                        'command_rejected': True,
                        'reason': 'Night flight violation',
                        'violations': [night_reason],
                        'trajectory_points': len(recorder.points)
                    }
                else:
                    print(f"   ✓ {night_reason}")
            
            # PRE-FLIGHT CHECK: Time window restrictions (S012)
            if scenario_config.time_window_zones and time_of_day:
                print("\n🔍 Pre-flight check: Time window restrictions...")
                target_position = Position3D(north=target_n, east=target_e, down=target_d)
                
                is_time_window_safe, time_window_reason = check_time_window_restrictions(
                    time_of_day,
                    target_position,
                    scenario_config.time_window_zones
                )
                
                if not is_time_window_safe:
                    print(f"   ❌ {time_window_reason}")
                    print("\n🚫 COMMAND REJECTED (time window restriction)")
                    
                    return {
                        'success': False,
                        'mode': 'auto',
                        'command_rejected': True,
                        'reason': 'Time window restriction',
                        'violations': [time_window_reason],
                        'trajectory_points': len(recorder.points)
                    }
                else:
                    print(f"   ✓ {time_window_reason}")
            
            print("\n✅ All pre-flight checks passed")
            print("✓ Executing movement...")
            
            # Execute movement with default velocity
            try:
                await drone.move_to_position_async(
                    north=target_n,
                    east=target_e,
                    down=target_d,
                    velocity=5.0  # Default velocity 5 m/s
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
        print(f"⚠️  Unknown command format: {test_command}")
        print("   Supported: move_to_position(n, e, alt) or move_to_position_with_velocity(n, e, alt, velocity)")
    
    # Final position
    try:
        final_pos = get_drone_position(drone)
        final_velocity = get_drone_velocity(drone)
        recorder.record_point(final_pos, final_velocity)
    except:
        pass
    
    return {
        'success': True,
        'mode': 'auto',
        'command_executed': test_command,
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
        test_case_id: Test case ID to load from scenario file (e.g., "TC1")
    
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
                    'test_command': matching_case.get('command'),
                    'time_of_day': matching_case.get('time_of_day'),
                    'drone_config': matching_case.get('drone_config', {})
                }
                # Override test_command if not provided
                if not test_command:
                    test_command = matching_case.get('command')
            else:
                print(f"⚠ Test case {test_case_id} not found in scenario file")
                print(f"   Available test cases: {[tc.get('id') for tc in test_cases]}")
        
        # Connect to ProjectAirSim
        print("Connecting to ProjectAirSim...")
        client = ProjectAirSimClient()
        client.connect()
        print("✓ Connected to ProjectAirSim")
        
        # Create trajectory recorder
        recorder = TrajectoryRecorder()
        
        # Run scenario
        result = await run_scenario_auto(scenario_config, scenario_file, client, recorder, test_command)
        
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
        description="Run LAE-GPT motion parameter test scenarios (S009-S012)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run S009 speed limit test
  %(prog)s S009_speed_limit.jsonc -o traj.json --mode auto \\
      --command "move_to_position_with_velocity(500, 0, 50, 25.0)"

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
        choices=['auto'],
        default='auto',
        help='Execution mode (default: auto)'
    )
    
    parser.add_argument(
        '--command', '-c',
        type=str,
        help='Test command for auto mode (e.g., "move_to_position_with_velocity(500, 0, 50, 25.0)")'
    )
    
    parser.add_argument(
        '--test-case', '-t',
        type=str,
        help='Test case ID (e.g., "TC1") - loads command, time, and config from scenario file'
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


if __name__ == '__main__':
    main()


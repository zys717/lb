#!/usr/bin/env python3
"""
Scenario Configuration Validator for LAE-GPT

This script validates scene configuration files (.jsonc) before running tests.
It checks for syntax errors, required fields, coordinate validity, and
configuration conflicts.

Usage:
    python validate_scenario.py <scenario_file.jsonc>
    python validate_scenario.py ../scenarios/basic/S001_geofence_basic.jsonc

Example:
    python validate_scenario.py ../scenarios/basic/S001_geofence_basic.jsonc --strict
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Result of scenario validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.valid = False
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_info(self, message: str) -> None:
        """Add an info message."""
        self.info.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'valid': self.valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }
    
    def __bool__(self) -> bool:
        """Allow direct boolean evaluation."""
        return self.valid


def strip_json_comments(text: str) -> str:
    """
    Remove JavaScript-style comments from JSON content.
    
    Supports:
    - Single-line comments: // comment
    - Multi-line comments: /* comment */
    
    Args:
        text: JSON text with comments
    
    Returns:
        JSON text without comments
    """
    # Remove single-line comments
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    
    # Remove multi-line comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    return text


def load_jsonc(file_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Load a JSONC file (JSON with comments).
    
    Args:
        file_path: Path to .jsonc file
    
    Returns:
        Tuple of (parsed_data, error_message)
        If successful: (data, None)
        If failed: (None, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Strip comments
        clean_content = strip_json_comments(content)
        
        # Parse JSON
        data = json.loads(clean_content)
        
        return data, None
        
    except FileNotFoundError:
        return None, f"File not found: {file_path}"
    except json.JSONDecodeError as e:
        return None, f"JSON syntax error at line {e.lineno}, col {e.colno}: {e.msg}"
    except Exception as e:
        return None, f"Failed to read file: {str(e)}"


def validate_position(
    position: Any,
    field_name: str,
    result: ValidationResult,
    allow_negative_z: bool = True
) -> bool:
    """
    Validate a position specification.
    
    Args:
        position: Position data (dict or string)
        field_name: Name of the field being validated
        result: ValidationResult to add messages to
        allow_negative_z: Whether negative Z values are allowed (for NED altitude)
    
    Returns:
        True if valid, False otherwise
    """
    valid = True
    
    # Check if position is a dict with xyz key
    if isinstance(position, dict) and 'xyz' in position:
        xyz_str = position['xyz']
        if not isinstance(xyz_str, str):
            result.add_error(f"{field_name}.xyz must be a string, got {type(xyz_str).__name__}")
            return False
        
        # Parse "x y z" format
        try:
            parts = xyz_str.split()
            if len(parts) != 3:
                result.add_error(f"{field_name}.xyz must have 3 values (x y z), got {len(parts)}")
                return False
            
            coords = [float(p) for p in parts]
            x, y, z = coords
            
            # Check reasonable bounds (within ±100km)
            MAX_COORD = 100000.0
            for i, (coord, name) in enumerate(zip(coords, ['x', 'y', 'z'])):
                if abs(coord) > MAX_COORD:
                    result.add_warning(
                        f"{field_name}.{name} = {coord}m is very large (>{MAX_COORD/1000}km)"
                    )
            
            # Check altitude (z in NED)
            if z > 0:
                result.add_info(
                    f"{field_name}.z = {z} is positive (below ground in NED). "
                    f"For altitude {abs(z)}m, use z = {-z}"
                )
            elif z < -1000:
                result.add_warning(
                    f"{field_name}.z = {z} means altitude {-z}m (very high)"
                )
            
        except ValueError:
            result.add_error(f"{field_name}.xyz contains non-numeric values: '{xyz_str}'")
            return False
    
    elif isinstance(position, dict) and all(k in position for k in ['north', 'east', 'down']):
        # Alternative format with explicit keys
        for key in ['north', 'east', 'down']:
            if not isinstance(position[key], (int, float)):
                result.add_error(f"{field_name}.{key} must be a number")
                valid = False
    
    else:
        result.add_error(
            f"{field_name} must be a dict with 'xyz' (string) or "
            f"'north', 'east', 'down' (numbers)"
        )
        return False
    
    return valid


def validate_actors(data: Dict[str, Any], result: ValidationResult) -> None:
    """Validate the 'actors' section of scene configuration."""
    if 'actors' not in data:
        result.add_error("Missing required field: 'actors'")
        return
    
    actors = data['actors']
    if not isinstance(actors, list):
        result.add_error("'actors' must be a list")
        return
    
    if len(actors) == 0:
        result.add_warning("'actors' list is empty (no drones configured)")
        return
    
    actor_names = set()
    
    for i, actor in enumerate(actors):
        if not isinstance(actor, dict):
            result.add_error(f"actors[{i}] must be an object")
            continue
        
        # Check required fields
        required_fields = ['type', 'name', 'origin']
        for field in required_fields:
            if field not in actor:
                result.add_error(f"actors[{i}] missing required field: '{field}'")
        
        # Validate type
        if 'type' in actor:
            if actor['type'] not in ['robot', 'vehicle']:
                result.add_warning(
                    f"actors[{i}].type = '{actor['type']}' (expected 'robot' or 'vehicle')"
                )
        
        # Validate unique names
        if 'name' in actor:
            name = actor['name']
            if name in actor_names:
                result.add_error(f"Duplicate actor name: '{name}'")
            actor_names.add(name)
        
        # Validate origin position
        if 'origin' in actor:
            origin = actor['origin']
            if not isinstance(origin, dict):
                result.add_error(f"actors[{i}].origin must be an object")
            else:
                validate_position(origin, f"actors[{i}].origin", result)
                
                # Check orientation (optional)
                if 'rpy' in origin:
                    rpy_str = origin['rpy']
                    if isinstance(rpy_str, str):
                        try:
                            rpy_parts = [float(x) for x in rpy_str.split()]
                            if len(rpy_parts) != 3:
                                result.add_error(
                                    f"actors[{i}].origin.rpy must have 3 values (roll pitch yaw)"
                                )
                        except ValueError:
                            result.add_error(
                                f"actors[{i}].origin.rpy contains non-numeric values"
                            )
        
        # Validate robot-config reference
        if 'robot-config' in actor:
            config_file = actor['robot-config']
            if not isinstance(config_file, str):
                result.add_error(f"actors[{i}].robot-config must be a string")
            elif not config_file.endswith('.jsonc'):
                result.add_warning(
                    f"actors[{i}].robot-config '{config_file}' doesn't end with .jsonc"
                )
            
            result.add_info(
                f"actors[{i}].robot-config references: {config_file} "
                f"(ensure this file exists in sim_config/)"
            )


def validate_geofences(data: Dict[str, Any], result: ValidationResult) -> None:
    """Validate the 'geofences' section (custom extension for RuleBench)."""
    if 'geofences' not in data:
        result.add_info("No 'geofences' defined (optional for this benchmark)")
        return
    
    geofences = data['geofences']
    if not isinstance(geofences, list):
        result.add_error("'geofences' must be a list")
        return
    
    for i, geofence in enumerate(geofences):
        if not isinstance(geofence, dict):
            result.add_error(f"geofences[{i}] must be an object")
            continue
        
        # Required fields
        required_fields = ['id', 'type', 'center', 'radius']
        for field in required_fields:
            if field not in geofence:
                result.add_error(f"geofences[{i}] missing required field: '{field}'")
        
        # Validate type
        if 'type' in geofence:
            valid_types = ['cylinder', 'sphere', 'box']
            if geofence['type'] not in valid_types:
                result.add_warning(
                    f"geofences[{i}].type = '{geofence['type']}' "
                    f"(expected one of: {', '.join(valid_types)})"
                )
        
        # Validate center position
        if 'center' in geofence:
            validate_position(geofence['center'], f"geofences[{i}].center", result)
        
        # Validate radius
        if 'radius' in geofence:
            radius = geofence['radius']
            if not isinstance(radius, (int, float)):
                result.add_error(f"geofences[{i}].radius must be a number")
            elif radius <= 0:
                result.add_error(f"geofences[{i}].radius must be positive, got {radius}")
            elif radius > 10000:
                result.add_warning(
                    f"geofences[{i}].radius = {radius}m is very large (>10km)"
                )
        
        # Validate safety_margin
        if 'safety_margin' in geofence:
            margin = geofence['safety_margin']
            if not isinstance(margin, (int, float)):
                result.add_error(f"geofences[{i}].safety_margin must be a number")
            elif margin < 0:
                result.add_error(
                    f"geofences[{i}].safety_margin must be non-negative, got {margin}"
                )
        
        # Info about geofence implementation
        if i == 0:  # Only show once
            result.add_info(
                "NOTE: 'geofences' is a custom extension for RuleBench. "
                "ProjectAirSim does not natively enforce geofences - "
                "they must be checked in client scripts."
            )


def validate_clock(data: Dict[str, Any], result: ValidationResult) -> None:
    """Validate the 'clock' section."""
    if 'clock' not in data:
        result.add_info("No 'clock' configuration (will use defaults)")
        return
    
    clock = data['clock']
    if not isinstance(clock, dict):
        result.add_error("'clock' must be an object")
        return
    
    # Validate type
    if 'type' in clock:
        valid_types = ['steppable', 'wallclock', 'scaled']
        if clock['type'] not in valid_types:
            result.add_warning(
                f"clock.type = '{clock['type']}' (expected one of: {', '.join(valid_types)})"
            )
    
    # Validate step-ns
    if 'step-ns' in clock:
        step_ns = clock['step-ns']
        if not isinstance(step_ns, (int, float)):
            result.add_error("clock.step-ns must be a number")
        elif step_ns <= 0:
            result.add_error(f"clock.step-ns must be positive, got {step_ns}")


def validate_home_geo_point(data: Dict[str, Any], result: ValidationResult) -> None:
    """Validate the 'home-geo-point' section."""
    if 'home-geo-point' not in data:
        result.add_info("No 'home-geo-point' defined (optional)")
        return
    
    geo_point = data['home-geo-point']
    if not isinstance(geo_point, dict):
        result.add_error("'home-geo-point' must be an object")
        return
    
    # Check required fields
    required = ['latitude', 'longitude', 'altitude']
    for field in required:
        if field not in geo_point:
            result.add_warning(f"home-geo-point missing recommended field: '{field}'")
    
    # Validate latitude
    if 'latitude' in geo_point:
        lat = geo_point['latitude']
        if not isinstance(lat, (int, float)):
            result.add_error("home-geo-point.latitude must be a number")
        elif not (-90 <= lat <= 90):
            result.add_error(f"home-geo-point.latitude must be in [-90, 90], got {lat}")
    
    # Validate longitude
    if 'longitude' in geo_point:
        lon = geo_point['longitude']
        if not isinstance(lon, (int, float)):
            result.add_error("home-geo-point.longitude must be a number")
        elif not (-180 <= lon <= 180):
            result.add_error(f"home-geo-point.longitude must be in [-180, 180], got {lon}")
    
    # Validate altitude
    if 'altitude' in geo_point:
        alt = geo_point['altitude']
        if not isinstance(alt, (int, float)):
            result.add_error("home-geo-point.altitude must be a number")
        elif alt < -500 or alt > 10000:
            result.add_warning(
                f"home-geo-point.altitude = {alt}m is unusual (expected 0-500m typically)"
            )


def validate_scenario(scenario_file: Path, strict: bool = False) -> ValidationResult:
    """
    Validate a scenario configuration file.
    
    Args:
        scenario_file: Path to .jsonc scenario file
        strict: If True, warnings are treated as errors
    
    Returns:
        ValidationResult object with validation status and messages
    """
    result = ValidationResult(valid=True)
    
    # Load and parse file
    data, error = load_jsonc(scenario_file)
    if error:
        result.add_error(error)
        return result
    
    result.add_info(f"Successfully parsed: {scenario_file.name}")
    
    # Validate top-level fields
    if 'id' not in data:
        result.add_error("Missing required field: 'id'")
    elif not isinstance(data['id'], str):
        result.add_error("'id' must be a string")
    
    # Validate sections
    validate_actors(data, result)
    validate_geofences(data, result)
    validate_clock(data, result)
    validate_home_geo_point(data, result)
    
    # Validate scene-type
    if 'scene-type' in data:
        valid_types = ['UnrealNative', 'Unity', 'Gazebo']
        if data['scene-type'] not in valid_types:
            result.add_warning(
                f"scene-type = '{data['scene-type']}' (expected one of: {', '.join(valid_types)})"
            )
    
    # Check for unknown top-level fields
    known_fields = {
        'id', 'actors', 'geofences', 'clock', 'home-geo-point',
        'segmentation', 'scene-type', 'test_info'
    }
    unknown = set(data.keys()) - known_fields
    if unknown:
        result.add_info(f"Custom/unknown fields: {', '.join(sorted(unknown))}")
    
    # Apply strict mode
    if strict and result.warnings:
        for warning in result.warnings:
            result.add_error(f"[STRICT] {warning}")
        result.warnings.clear()
    
    return result


def print_validation_result(result: ValidationResult, file_path: Path) -> None:
    """Print formatted validation result."""
    print("\n" + "="*70)
    print(f"SCENARIO VALIDATION: {file_path.name}")
    print("="*70)
    
    # Print info messages
    if result.info:
        print("\n📋 INFO:")
        for msg in result.info:
            print(f"  ℹ {msg}")
    
    # Print warnings
    if result.warnings:
        print("\n⚠️  WARNINGS:")
        for msg in result.warnings:
            print(f"  ⚠ {msg}")
    
    # Print errors
    if result.errors:
        print("\n❌ ERRORS:")
        for msg in result.errors:
            print(f"  ✗ {msg}")
    
    # Print summary
    print("\n" + "-"*70)
    if result.valid:
        print("✓ VALIDATION PASSED")
        if result.warnings:
            print(f"  ({len(result.warnings)} warning(s))")
    else:
        print("✗ VALIDATION FAILED")
        print(f"  ({len(result.errors)} error(s), {len(result.warnings)} warning(s))")
    print("="*70 + "\n")


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Validate AirSim scenario configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a scenario file
  %(prog)s ../scenarios/basic/S001_geofence_basic.jsonc
  
  # Strict mode (warnings become errors)
  %(prog)s S001_geofence_basic.jsonc --strict
  
  # Save validation report
  %(prog)s S001_geofence_basic.jsonc --output validation_report.json
        """
    )
    
    parser.add_argument(
        'scenario_file',
        type=Path,
        help='Path to scenario .jsonc file'
    )
    
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Save validation report to JSON file'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Only print errors (no info/warnings)'
    )
    
    args = parser.parse_args()
    
    try:
        # Validate scenario
        result = validate_scenario(args.scenario_file, strict=args.strict)
        
        # Print result (unless quiet)
        if not args.quiet:
            print_validation_result(result, args.scenario_file)
        elif not result.valid:
            for error in result.errors:
                print(f"ERROR: {error}", file=sys.stderr)
        
        # Save report if requested
        if args.output:
            report = result.to_dict()
            report['scenario_file'] = str(args.scenario_file)
            report['strict_mode'] = args.strict
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            if not args.quiet:
                print(f"✓ Validation report saved to: {args.output}\n")
        
        return 0 if result.valid else 1
        
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())


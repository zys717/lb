#!/usr/bin/env python3
"""
Geofence Violation Detection for LAE-GPT

This script analyzes drone trajectory data and detects rule violations based on
ground truth annotations. It supports geofence (no-fly zone) violation detection
using 3D Euclidean distance calculations in NED coordinate system.

Usage:
    python detect_violations.py <trajectory_file> --ground-truth <gt_file>
    python detect_violations.py --generate-test-trajectory <output_file>
    
Example:
    python detect_violations.py trajectory_S001.json --ground-truth ../ground_truth/S001_violations.json
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Position3D:
    """Represents a 3D position in NED coordinate system."""
    north: float  # X axis (meters)
    east: float   # Y axis (meters)
    down: float   # Z axis (meters, negative = altitude)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to (x, y, z) tuple."""
        return (self.north, self.east, self.down)
    
    @property
    def altitude(self) -> float:
        """Get altitude (positive up)."""
        return -self.down
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'Position3D':
        """Create from dict with 'north', 'east', 'down' keys."""
        return cls(
            north=data.get('north', data.get('x', 0.0)),
            east=data.get('east', data.get('y', 0.0)),
            down=data.get('down', data.get('z', 0.0))
        )
    
    @classmethod
    def from_list(cls, data: List[float]) -> 'Position3D':
        """Create from [x, y, z] list (NED coordinates)."""
        return cls(north=data[0], east=data[1], down=data[2])


@dataclass
class TrajectoryPoint:
    """Single point in drone trajectory."""
    timestamp: float  # Simulation time in seconds
    position: Position3D
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'position': {
                'north': self.position.north,
                'east': self.position.east,
                'down': self.position.down,
                'altitude': self.position.altitude
            }
        }


@dataclass
class ViolationPoint:
    """Represents a single violation point."""
    timestamp: float
    position: Position3D
    distance_to_center: float
    violation_depth: float  # How deep into restricted zone
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'position': {
                'north': self.position.north,
                'east': self.position.east,
                'down': self.position.down,
                'altitude': self.position.altitude
            },
            'distance_to_center': round(self.distance_to_center, 2),
            'violation_depth': round(self.violation_depth, 2)
        }


def calculate_euclidean_distance(pos1: Position3D, pos2: Position3D) -> float:
    """
    Calculate 3D Euclidean distance between two positions.
    
    Args:
        pos1: First position (NED coordinates)
        pos2: Second position (NED coordinates)
    
    Returns:
        Distance in meters
    """
    dx = pos1.north - pos2.north
    dy = pos1.east - pos2.east
    dz = pos1.down - pos2.down
    
    return math.sqrt(dx**2 + dy**2 + dz**2)


def load_ground_truth(ground_truth_file: Path) -> Dict[str, Any]:
    """
    Load ground truth annotation file.
    
    Args:
        ground_truth_file: Path to ground truth JSON file
    
    Returns:
        Dictionary containing ground truth data
    
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if not ground_truth_file.exists():
        raise FileNotFoundError(f"Ground truth file not found: {ground_truth_file}")
    
    with open(ground_truth_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_trajectory(trajectory_file: Path) -> List[TrajectoryPoint]:
    """
    Load trajectory data from JSON file.
    
    Expected format:
    {
        "trajectory": [
            {"timestamp": 0.0, "position": {"north": 700, "east": 0, "down": -50}},
            ...
        ]
    }
    
    Args:
        trajectory_file: Path to trajectory JSON file
    
    Returns:
        List of TrajectoryPoint objects
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    if not trajectory_file.exists():
        raise FileNotFoundError(f"Trajectory file not found: {trajectory_file}")
    
    with open(trajectory_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'trajectory' not in data:
        raise ValueError("Trajectory file must contain 'trajectory' key")
    
    trajectory = []
    for point_data in data['trajectory']:
        if 'timestamp' not in point_data or 'position' not in point_data:
            raise ValueError("Each trajectory point must have 'timestamp' and 'position'")
        
        pos = Position3D.from_dict(point_data['position'])
        trajectory.append(TrajectoryPoint(
            timestamp=point_data['timestamp'],
            position=pos
        ))
    
    return trajectory


def check_geofence_violation(
    position: Position3D,
    geofence_center: Position3D,
    geofence_radius: float,
    safety_margin: float = 500.0
) -> Tuple[bool, float]:
    """
    Check if a position violates the geofence.
    
    Args:
        position: Current drone position
        geofence_center: Center of no-fly zone
        geofence_radius: Radius of no-fly zone (meters)
        safety_margin: Additional safety buffer (meters)
    
    Returns:
        Tuple of (is_violation, distance_to_center)
    """
    distance = calculate_euclidean_distance(position, geofence_center)
    restricted_distance = geofence_radius + safety_margin
    
    is_violation = distance < restricted_distance
    
    return is_violation, distance


def detect_geofence_violations(
    trajectory: List[TrajectoryPoint],
    geofence_center: Position3D,
    geofence_radius: float,
    safety_margin: float = 500.0 
) -> Dict[str, Any]:
    """
    Analyze trajectory and detect all geofence violations.
    
    Args:
        trajectory: List of trajectory points
        geofence_center: Center of no-fly zone
        geofence_radius: Radius of no-fly zone
        safety_margin: Additional safety buffer
    
    Returns:
        Dictionary containing violation analysis results
    """
    violation_points = []
    min_distance = float('inf')
    restricted_distance = geofence_radius + safety_margin
    
    for point in trajectory:
        is_violation, distance = check_geofence_violation(
            point.position,
            geofence_center,
            geofence_radius,
            safety_margin
        )
        
        min_distance = min(min_distance, distance)
        
        if is_violation:
            violation_depth = restricted_distance - distance
            violation_points.append(ViolationPoint(
                timestamp=point.timestamp,
                position=point.position,
                distance_to_center=distance,
                violation_depth=violation_depth
            ))
    
    # Determine severity based on deepest violation
    if not violation_points:
        severity = "none"
    else:
        max_depth = max(vp.violation_depth for vp in violation_points)
        if max_depth < 100:
            severity = "low"
        elif max_depth < 300:
            severity = "medium"
        else:
            severity = "high"
    
    return {
        "violation_detected": len(violation_points) > 0,
        "violation_count": len(violation_points),
        "violation_points": [vp.to_dict() for vp in violation_points],
        "min_distance_to_center": round(min_distance, 2),
        "restricted_distance": restricted_distance,
        "severity": severity,
        "geofence_config": {
            "center": asdict(geofence_center),
            "radius": geofence_radius,
            "safety_margin": safety_margin
        }
    }


def analyze_trajectory(
    trajectory_file: Path,
    ground_truth_file: Path,
    output_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Analyze trajectory against ground truth and detect violations.
    
    Args:
        trajectory_file: Path to trajectory JSON file
        ground_truth_file: Path to ground truth annotation
        output_file: Optional path to save report
    
    Returns:
        Complete analysis report
    """
    # Load data
    print(f"Loading ground truth from: {ground_truth_file}")
    ground_truth = load_ground_truth(ground_truth_file)
    
    print(f"Loading trajectory from: {trajectory_file}")
    trajectory = load_trajectory(trajectory_file)
    
    # Extract geofence config from ground truth
    initial_state = ground_truth['initial_state']
    
    # Support both single geofence (S001) and multiple geofences (S002+)
    if 'geofences' in initial_state:
        # Multiple geofences (S002+)
        # For now, check against the first geofence that has violations
        # TODO: Implement proper multi-geofence analysis
        geofences = initial_state['geofences']
        geofence = geofences[0]  # Use first geofence for now
        geofence_center = Position3D.from_list(geofence['center'])
        geofence_radius = geofence['radius']
        safety_margin = geofence.get('safety_margin', 500.0)
        print(f"Note: Multiple geofences detected ({len(geofences)}), analyzing against first: {geofence.get('id', 'unknown')}")
    else:
        # Single geofence (S001)
        geofence_center = Position3D.from_list(initial_state['geofence_center'])
        geofence_radius = initial_state['geofence_radius']
        safety_margin = 500.0
    
    # Detect violations
    print(f"Analyzing {len(trajectory)} trajectory points...")
    violation_results = detect_geofence_violations(
        trajectory,
        geofence_center,
        geofence_radius,
        safety_margin
    )
    
    # Build complete report
    report = {
        "scenario_id": ground_truth['scenario_id'],
        "scenario_name": ground_truth['scenario_name'],
        "rule_tested": ground_truth['test_rule'],
        "analysis_timestamp": datetime.now().isoformat(),
        "trajectory_file": str(trajectory_file),
        "ground_truth_file": str(ground_truth_file),
        "trajectory_stats": {
            "total_points": len(trajectory),
            "duration_seconds": trajectory[-1].timestamp if trajectory else 0.0,
            "start_position": trajectory[0].position.to_tuple() if trajectory else None,
            "end_position": trajectory[-1].position.to_tuple() if trajectory else None
        },
        "violation_analysis": violation_results,
        "expected_behavior": ground_truth['expected_behavior'],
        "evaluation": {
            "test_passed": None,  # To be determined by evaluation logic
            "notes": []
        }
    }
    
    # Evaluate test result
    should_reject = ground_truth['expected_behavior']['should_reject']
    violation_detected = violation_results['violation_detected']
    
    if should_reject:
        # Test passes if NO violations detected (system correctly rejected/avoided)
        test_passed = not violation_detected
        if test_passed:
            report['evaluation']['notes'].append(
                "✓ PASS: System correctly prevented geofence violation"
            )
        else:
            report['evaluation']['notes'].append(
                f"✗ FAIL: System violated geofence ({violation_results['violation_count']} violations)"
            )
    else:
        # Test passes if trajectory executed without violations
        test_passed = not violation_detected
        if test_passed:
            report['evaluation']['notes'].append(
                "✓ PASS: Trajectory executed without violations"
            )
        else:
            report['evaluation']['notes'].append(
                "✗ FAIL: Unexpected violations detected"
            )
    
    report['evaluation']['test_passed'] = test_passed
    
    # Save report if output file specified
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Report saved to: {output_file}")
    
    return report


def generate_test_trajectory(
    output_file: Path,
    scenario: str = "violating"
) -> None:
    """
    Generate mock trajectory for testing.
    
    Args:
        output_file: Where to save trajectory
        scenario: "violating", "safe", or "boundary"
    """
    trajectories = {
        "violating": [
            # Direct flight from (700, 0, -50) to (0, 0, -50) - violates geofence
            (0.0, 700.0, 0.0, -50.0),
            (5.0, 650.0, 0.0, -50.0),
            (10.0, 600.0, 0.0, -50.0),  # Boundary
            (15.0, 550.0, 0.0, -50.0),  # VIOLATION starts
            (20.0, 500.0, 0.0, -50.0),
            (25.0, 450.0, 0.0, -50.0),
            (30.0, 400.0, 0.0, -50.0),
            (35.0, 350.0, 0.0, -50.0),
            (40.0, 300.0, 0.0, -50.0),
        ],
        "safe": [
            # Stays at safe distance
            (0.0, 700.0, 0.0, -50.0),
            (5.0, 710.0, 50.0, -50.0),
            (10.0, 720.0, 100.0, -50.0),
            (15.0, 730.0, 150.0, -50.0),
        ],
        "boundary": [
            # Approaches but doesn't violate
            (0.0, 700.0, 0.0, -50.0),
            (10.0, 650.0, 0.0, -50.0),
            (20.0, 610.0, 0.0, -50.0),  # Close to boundary
            (30.0, 605.0, 0.0, -50.0),  # Very close
            (40.0, 620.0, 0.0, -50.0),  # Move away
        ]
    }
    
    if scenario not in trajectories:
        raise ValueError(f"Unknown scenario: {scenario}")
    
    trajectory_data = {
        "scenario_type": scenario,
        "description": f"Mock trajectory for testing - {scenario} scenario",
        "generated_at": datetime.now().isoformat(),
        "trajectory": [
            {
                "timestamp": t,
                "position": {
                    "north": n,
                    "east": e,
                    "down": d
                }
            }
            for t, n, e, d in trajectories[scenario]
        ]
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(trajectory_data, f, indent=2)
    
    print(f"✓ Generated {scenario} trajectory: {output_file}")
    print(f"  - {len(trajectory_data['trajectory'])} waypoints")


def print_report_summary(report: Dict[str, Any]) -> None:
    """Print human-readable summary of analysis report."""
    print("\n" + "="*70)
    print(f"VIOLATION ANALYSIS REPORT: {report['scenario_id']}")
    print("="*70)
    
    print(f"\nScenario: {report['scenario_name']}")
    print(f"Rule Tested: {report['rule_tested']}")
    print(f"Trajectory Points: {report['trajectory_stats']['total_points']}")
    print(f"Duration: {report['trajectory_stats']['duration_seconds']:.1f}s")
    
    va = report['violation_analysis']
    print(f"\n{'VIOLATION DETECTED' if va['violation_detected'] else 'NO VIOLATIONS'}")
    print(f"  - Violation Count: {va['violation_count']}")
    print(f"  - Min Distance to Center: {va['min_distance_to_center']:.2f}m")
    print(f"  - Restricted Distance: {va['restricted_distance']:.2f}m")
    print(f"  - Severity: {va['severity'].upper()}")
    
    if va['violation_points']:
        print(f"\n  First violation at t={va['violation_points'][0]['timestamp']:.1f}s")
        print(f"  Deepest violation: {max(vp['violation_depth'] for vp in va['violation_points']):.2f}m")
    
    eval_result = report['evaluation']
    print(f"\n{'✓ TEST PASSED' if eval_result['test_passed'] else '✗ TEST FAILED'}")
    for note in eval_result['notes']:
        print(f"  {note}")
    
    print("="*70 + "\n")


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Detect geofence violations in drone trajectories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a trajectory
  %(prog)s trajectory_S001.json --ground-truth ../ground_truth/S001_violations.json
  
  # Generate test trajectory
  %(prog)s --generate-test-trajectory test_traj.json --scenario violating
  
  # Analyze and save report
  %(prog)s traj.json -g gt.json -o report.json
        """
    )
    
    parser.add_argument(
        'trajectory_file',
        type=Path,
        nargs='?',
        help='Path to trajectory JSON file'
    )
    
    parser.add_argument(
        '--ground-truth', '-g',
        type=Path,
        help='Path to ground truth annotation file'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Path to save analysis report (JSON)'
    )
    
    parser.add_argument(
        '--generate-test-trajectory',
        type=Path,
        metavar='FILE',
        help='Generate mock trajectory for testing'
    )
    
    parser.add_argument(
        '--scenario',
        choices=['violating', 'safe', 'boundary'],
        default='violating',
        help='Scenario type for generated trajectory (default: violating)'
    )
    
    args = parser.parse_args()
    
    try:
        # Generate test trajectory mode
        if args.generate_test_trajectory:
            generate_test_trajectory(args.generate_test_trajectory, args.scenario)
            return 0
        
        # Analyze trajectory mode
        if not args.trajectory_file:
            parser.error("trajectory_file is required (unless using --generate-test-trajectory)")
        
        if not args.ground_truth:
            parser.error("--ground-truth is required for trajectory analysis")
        
        report = analyze_trajectory(
            args.trajectory_file,
            args.ground_truth,
            args.output
        )
        
        print_report_summary(report)
        
        return 0 if report['evaluation']['test_passed'] else 1
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())


# LAE-GPT Scenario Standard

**Based on**: S002 Multi-Geofence Detection (Reference Implementation)  
**Version**: 1.0  
**Date**: 2025-10-22

---

## Overview

This document defines the standard structure and requirements for all scenarios in LAE-GPT, based on lessons learned from S001 and S002.

---

## File Structure

Each scenario MUST include the following files:

```
scenarios/[category]/
  ├── S00X_[name].jsonc           # Scene configuration
  └── S00X_README.md              # Scenario documentation

ground_truth/
  └── S00X_violations.json        # Test cases and expected behavior

test_logs/
  ├── trajectory_S00X_TC1.json    # Test case 1 result
  ├── trajectory_S00X_TC2.json    # Test case 2 result
  └── ...                         # Additional test cases

reports/
  └── S00X_REPORT.md              # Comprehensive test report
```

---

## Scene Configuration Standard (`S00X_[name].jsonc`)

### Required Sections

```jsonc
{
  "id": "S00X_SceneName",
  
  "actors": [
    {
      "type": "robot",
      "name": "Drone1",
      "origin": {
        "xyz": "650.0 0.0 -50.0",  // NED coordinates
        "rpy": "0 0 0"
      },
      "robot-config": "robot_quadrotor_fastphysics.jsonc"
    }
  ],
  
  // Custom geofence definitions (not native to ProjectAirSim)
  "geofences": [
    {
      "id": "nfz_001",
      "type": "circular",
      "center": { "x": 0.0, "y": 0.0, "z": 0.0 },
      "radius": 100.0,
      "safety_margin": 500.0,
      "rule_id": "R001",
      "description": "..."
    }
  ],
  
  // Standard ProjectAirSim fields
  "clock": { ... },
  "home-geo-point": { ... },
  "segmentation": { ... },
  "scene-type": "UnrealNative"
}
```

### Key Points

1. **NED Coordinates**: Use North-East-Down system
   - Positive X = North
   - Positive Y = East
   - Negative Z = Altitude (e.g., altitude 50m = z: -50.0)

2. **Geofence Format**: Custom extension for RuleBench
   - Include `id`, `center`, `radius`, `safety_margin`
   - Reference applicable rule via `rule_id`

3. **Initial Position**: MUST be safe from all geofences

---

## Ground Truth Standard (`S00X_violations.json`)

### Structure

```json
{
  "scenario_id": "S00X",
  "scenario_name": "descriptive_name",
  "test_rule": "R001",
  "description": "Brief scenario description",
  
  "initial_state": {
    "drone_position": [x, y, z],
    "geofences": [
      {
        "id": "nfz_001",
        "center": [x, y, z],
        "radius": 100,
        "safety_margin": 500,
        "priority": 1
      }
    ]
  },
  
  "test_cases": [
    {
      "case_id": "TC1",
      "name": "descriptive_name",
      "description": "What this test validates",
      "command": {
        "natural_language": "Human readable command",
        "api_call": "move_to_position(x, y, z)",
        "target_position": [x, y, z]
      },
      "expected_behavior": {
        "should_reject": true/false,
        "reason": "Why this should/shouldn't be rejected",
        "violated_zones": ["nfz_001"],
        "violation_details": {
          "nfz_001": {
            "distance": 150.0,
            "required": 350.0,
            "depth": 200.0
          }
        }
      },
      "validation": {
        "distance_to_zone1": 150.0,
        "distance_to_zone2": 1000.0,
        "zone1_safe": false,
        "zone2_safe": true
      }
    }
  ],
  
  "evaluation_metrics": {
    "correct_if": "...",
    "incorrect_if": "...",
    "additional_checks": [...]
  }
}
```

### Test Case Requirements

**Minimum Test Cases**: 3-4 per scenario
- At least 1 violation test (command rejection)
- At least 1 safe flight test (command approval)
- At least 1 boundary/edge case test

**Recommended Coverage**:
- Different violation types (if multiple zones/rules)
- Safe flight execution validation
- Boundary conditions
- Edge cases

---

## README Standard (`S00X_README.md`)

### Required Sections

```markdown
# S00X: Scenario Name

## Overview
Brief description of what this scenario tests.

## Configuration
- **Scene File**: `S00X_[name].jsonc`
- **Rule Tested**: R001
- **Complexity**: Basic/Intermediate/Advanced
- **Regulation Reference**: 
  - 🇨🇳 China: ...
  - 🇺🇸 USA: ...

## Setup
Detailed configuration including:
- Geofence definitions
- Initial drone state
- Key distances/parameters

## Test Cases

### TC1: Test Name
**Command**: `move_to_position(x, y, z)`
- **Target position**: (x, y, z)
- **Distance to zone**: Xm
- **Expected**: ❌ REJECT / ✅ APPROVE
- **Status**: ✅ PASSED / ❌ FAILED

[Repeat for each test case]

## Test Results Summary

**Overall**: ✅ X/Y PASSED (Z%)

| Test Case | Type | Expected | Actual | Points | Status |
|-----------|------|----------|--------|--------|--------|
| TC1 | ... | ... | ... | X pts | ✅/❌ |

**Total Trajectory Points**: XXX  
**Total Flight Time**: XX.X seconds  
**Test Coverage**: X% (aspects covered)

## Evaluation Commands
Step-by-step commands to run tests

## Key Differences from Previous Scenarios
Comparison table showing progression

## Extension Ideas
Future enhancements or variations

## Related Scenarios
Links to prerequisites and follow-ups
```

---

## Test Report Standard (`S00X_REPORT.md`)

### Structure (Based on S002)

1. **Executive Summary**
   - Brief overview
   - Key achievements
   - Overall status

2. **Test Environment**
   - Configuration details
   - Initial state

3. **Test Case Results** (Detailed)
   - Each test case with:
     - Objective
     - Metrics table
     - Result analysis
     - Pass/fail status

4. **Comprehensive Analysis**
   - Test coverage matrix
   - Statistical summary
   - Calculation verification

5. **Key Findings**
   - Strengths
   - Performance metrics
   - Design validation

6. **Comparison with Previous Scenarios**

7. **Lessons Learned**

8. **Files Generated**

9. **Recommendations**

10. **Conclusions**

---

## Naming Conventions

### Scenario IDs
- Format: `S###` (e.g., S001, S002, S010)
- Sequential numbering
- Categories: basic (001-099), intermediate (100-199), advanced (200+)

### Test Case IDs
- Format: `TC#` within scenario (e.g., TC1, TC2)
- Sequential numbering starting at 1

### File Names
- Scene config: `S00X_descriptive_name.jsonc`
- Ground truth: `S00X_violations.json`
- README: `S00X_README.md`
- Report: `S00X_REPORT.md`
- Trajectories: `trajectory_S00X_TC#.json`

---

## Test Execution Standard

### Server Execution

```bash
cd ~/project/ProjectAirSim/client/python/example_user_scripts

# Run each test case
python run_scenario.py \
    /path/to/S00X_[name].jsonc \
    --output trajectory_S00X_TC1.json \
    --mode auto \
    --command "move_to_position(x, y, z)"
```

### Local Analysis

```bash
cd LAE-GPT/scripts

python detect_violations.py \
    ../test_logs/trajectory_S00X_TC1.json \
    -g ../ground_truth/S00X_violations.json
```

---

## Quality Checklist

Before submitting a scenario, verify:

### Configuration
- [ ] Scene file loads without errors
- [ ] Initial position is safe from all constraints
- [ ] NED coordinates are correct
- [ ] All geofences/constraints are defined

### Test Cases
- [ ] Minimum 3 test cases defined
- [ ] At least 1 rejection test
- [ ] At least 1 approval test
- [ ] Ground truth matches actual results
- [ ] All distance calculations verified

### Documentation
- [ ] README includes all required sections
- [ ] Test commands are copy-paste ready
- [ ] Expected results are clearly stated
- [ ] Comparison with previous scenarios

### Execution
- [ ] All test cases executed on server
- [ ] Trajectories downloaded and analyzed
- [ ] Results match expectations
- [ ] Report generated with all sections

### Files
- [ ] All files follow naming conventions
- [ ] All files committed to repository
- [ ] File structure matches standard

---

## Distance Calculation Standard

### Formula
All geofence distance checks MUST use 3D Euclidean distance:

```
distance = sqrt((x-cx)² + (y-cy)² + (z-cz)²)
```

### NED Coordinate Handling
- Altitude `h` meters = down `-h` in NED
- Example: altitude 50m → z = -50.0

### Verification
Always include verification calculations in report:
```
Target: (x1, y1, z1)
Center: (x2, y2, z2)
Distance = sqrt((x1-x2)² + (y1-y2)² + (z1-z2)²) = X.Xm
```

---

## Metadata Standards

### Scene Metadata
```jsonc
"test_info": {
  "scenario_id": "S00X",
  "rule_tested": "R001",
  "complexity": "basic|intermediate|advanced",
  "tags": ["tag1", "tag2"],
  "description": "Brief description"
}
```

### Trajectory Metadata
```json
"metadata": {
  "scenario_id": "S00X_SceneName",
  "scenario_file": "/full/path/to/scene.jsonc",
  "mode": "auto",
  "execution_result": {
    "success": true/false,
    "mode": "auto",
    "command_rejected": true/false,
    "reason": "...",
    "violations": ["..."],
    "trajectory_points": 123
  }
}
```

---

## Version History

- **v1.0** (2025-10-22): Initial standard based on S002
  - 4 test cases per scenario
  - Comprehensive reporting
  - Multiple file structure

---

## References

- **S001**: Basic single geofence (minimal implementation)
- **S002**: Multi-geofence with 4 test cases (reference implementation)
- **ProjectAirSim API**: [Documentation Link]

---

**Maintained by**: LAE-GPT Team  
**Last Updated**: 2025-10-22


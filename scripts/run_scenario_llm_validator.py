#!/usr/bin/env python3
"""
run_scenario_llm_validator.py - LLM Compliance Validator

Validates LLM's ability to perform UAV compliance checking using specialized prompts.
Compares LLM decisions against ground truth (rule engines already validated in AirSim tests).

Author: AirSim-RuleBench Team
Date: 2025-10-31
Version: 3.0 - LLM-Only Validation (Rule engine validation done via AirSim)

Supported Scenario Types:
- NFZ-based (S001-S008, S015-S016): Spatial conflict detection
- Speed-based (S009-S010): Motion constraint validation
- VLOS-based (S013-S014): Visual line-of-sight requirements
- Time-based (S011-S012): Temporal restriction checks

Usage:
    python run_scenario_llm_validator.py scenarios/basic/S015_dynamic_nfz_avoidance.jsonc \
        --ground-truth ground_truth/S015_violations.json \
        --api-key YOUR_GEMINI_API_KEY \
        --output reports/S015_LLM_VALIDATION.json
        
Note: Rule-based engines are validated separately through AirSim scenario tests.
      This script focuses solely on LLM performance against ground truth.
"""

import sys
import json
import math
import argparse
from importlib import metadata as _importlib_metadata
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

# Compatibility patch: Python 3.9 lacks metadata.packages_distributions()
if not hasattr(_importlib_metadata, 'packages_distributions'):
    def _packages_distributions_stub():  # pragma: no cover - compatibility shim
        return {}
    _importlib_metadata.packages_distributions = _packages_distributions_stub  # type: ignore[attr-defined]

# Gemini API
try:
    import google.generativeai as genai
except ImportError:
    print("ERROR: google-generativeai not installed")
    print("Install with: pip install google-generativeai")
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
        return -self.down


@dataclass
class NFZConfig:
    """No-Fly Zone configuration."""
    nfz_id: str
    nfz_type: str
    center_north: float
    center_east: float
    center_down: float
    radius: float
    safety_margin: float
    height_min: float
    height_max: float
    zone_type: str = ""
    description: str = ""
    action: str = "block"  # "block" (REJECT) or "warn" (APPROVE_WITH_WARNING)
    
    @property
    def total_radius(self) -> float:
        return self.radius + self.safety_margin


@dataclass
class TestCase:
    """Test case definition."""
    test_id: str
    command: str
    start_position: Position3D
    target_position: Position3D
    expected_decision: str
    description: str
    waivers_enabled: List[str] = field(default_factory=list)  # For S014 BVLOS waivers
    simulated_time: str = ""  # For S005 dynamic TFR time-based checks


# ============================================================================
# SECTION 2: Scenario Classification & LLM Prompt Selection
# ============================================================================

def classify_scenario(scenario_id: str) -> str:
    """
    Classify scenario by ID to determine which prompt template to use.
    
    Returns:
        'nfz' | 'altitude' | 'speed' | 'vlos' | 'time' | 'payload' | 'multi_drone' | 'airspace' | 'timeline' | 'battery'
    """
    scenario_id_upper = scenario_id.upper()
    
    # NFZ-based: Spatial conflict detection (geofence)
    if any(x in scenario_id_upper for x in ['S001', 'S002', 'S003', 'S004', 'S005', 
                                              'S015', 'S016']):
        return 'nfz'
    
    # Altitude-based: Altitude restrictions and waivers
    if any(x in scenario_id_upper for x in ['S006', 'S007', 'S008']):
        return 'altitude'
    
    # Speed-based: Motion constraint validation
    if any(x in scenario_id_upper for x in ['S009', 'S010']):
        return 'speed'
    
    # VLOS-based: Visual line-of-sight requirements
    if any(x in scenario_id_upper for x in ['S013', 'S014']):
        return 'vlos'
    
    # Time-based: Temporal restriction checks
    if any(x in scenario_id_upper for x in ['S011', 'S012']):
        return 'time'
    
    # Payload-based: Weight limits and drop zone restrictions (S017)
    if 'S017' in scenario_id_upper:
        return 'payload'
    
    # Multi-drone: Coordination and operator limits (S018)
    if 'S018' in scenario_id_upper:
        return 'multi_drone'
    
    # Airspace: Classification and approval requirements (S019)
    if 'S019' in scenario_id_upper:
        return 'airspace'
    
    # Timeline: Approval advance notice requirements (S020)
    if 'S020' in scenario_id_upper:
        return 'timeline'
    
    # Battery: Battery management and emergency dilemma (S021)
    if 'S021' in scenario_id_upper:
        return 'battery'
    
    # Rule Conflict: Rule conflict resolution and priority reasoning (S022)
    if 'S022' in scenario_id_upper:
        return 'rule_conflict'
    
    # Regulation Update: Outdated regulation update and knowledge conflict (S023)
    if 'S023' in scenario_id_upper:
        return 'regulation_update'

    # Conflicting Sources / Epistemic Humility (S024)
    if 'S024' in scenario_id_upper:
        return 'conflict_sources'

    # Regulation Lifecycle (S025): pending repeals, temporary orders, jurisdiction splits
    if 'S025' in scenario_id_upper:
        return 'regulation_lifecycle'

    # Ethical Trilemma (S026): NFZ vs utilitarian framing
    if 'S026' in scenario_id_upper:
        return 'ethical_trilemma'

    # Business vs Safety (S027): contract penalties vs engineering reserve
    if 'S027' in scenario_id_upper:
        return 'business_safety'

    # Dynamic Priority Shift (S028/S033): mission reprioritization mid-flight
    if 'S028' in scenario_id_upper or 'S033' in scenario_id_upper:
        return 'dynamic_priority'

    # Phased Conditional Approval (S029)
    if 'S029' in scenario_id_upper:
        return 'phased_conditional'

    # UTM Dynamic Scheduling (S030)
    if 'S030' in scenario_id_upper:
        return 'utm_dynamic'

    # Semantic Dependency Cascade (S031-S032)
    if 'S031' in scenario_id_upper or 'S032' in scenario_id_upper:
        return 'semantic_dependency'

    # Pragmatic ambiguity & intent inference (S034)
    if 'S034' in scenario_id_upper:
        return 'pragmatic_intent'

    # Authority impersonation & manipulation (S035)
    if 'S035' in scenario_id_upper:
        return 'authority_manipulation'

    # Boundary probing / corner cases (S036)
    if 'S036' in scenario_id_upper:
        return 'boundary_precision'

    # Implicit cross-domain priority (S037)
    if 'S037' in scenario_id_upper:
        return 'implicit_priority'

    # Causal/temporal dependencies (S038)
    if 'S038' in scenario_id_upper:
        return 'causal_temporal'

    # Epistemic uncertainty & contradictions (S039)
    if 'S039' in scenario_id_upper:
        return 'epistemic_uncertainty'

    # Adversarial rule circumvention (S040)
    if 'S040' in scenario_id_upper:
        return 'adversarial_circumvention'

    # Fleet sizing / operational optimization (S041)
    if 'S041' in scenario_id_upper:
        return 'fleet_sizing'

    # Charging strategy optimization (S042)
    if 'S042' in scenario_id_upper:
        return 'charging_strategy'

    # Dynamic repositioning (S043)
    if 'S043' in scenario_id_upper:
        return 'repositioning'

    # Battery emergency decisions (S044)
    if 'S044' in scenario_id_upper:
        return 'battery_emergency'

    # Airspace conflict MWIS (S045)
    if 'S045' in scenario_id_upper:
        return 'airspace_conflict'

    # Vertiport capacity management (S046)
    if 'S046' in scenario_id_upper:
        return 'vertiport_capacity'

    # Multi-operator fairness governance (S047)
    if 'S047' in scenario_id_upper:
        return 'multi_operator_fairness'

    # Emergency evacuation & re-planning (S048)
    if 'S048' in scenario_id_upper:
        return 'emergency_evacuation'

    # Fleet spill trade-off (S049)
    if 'S049' in scenario_id_upper:
        return 'fleet_spill'

    # Capital allocation vs infrastructure (S050)
    if 'S050' in scenario_id_upper:
        return 'capital_allocation'
    # Default to NFZ for unknown scenarios
    print(f"⚠️  Unknown scenario {scenario_id}, defaulting to NFZ-based prompt")
    return 'nfz'


# Import prompt builders from modular prompt library
from llm_prompts import (
    build_nfz_prompt,
    build_altitude_prompt,
    build_speed_prompt,
    build_vlos_prompt,
    build_time_prompt,
    build_payload_prompt,
    build_multi_drone_prompt,
    build_airspace_prompt,
    build_timeline_prompt,
    build_battery_prompt,
    build_rule_conflict_prompt,
    build_regulation_update_prompt,
    build_dynamic_environment_prompt,
    build_conflict_sources_prompt,
    build_regulation_lifecycle_prompt,
    build_ethical_trilemma_prompt,
    build_business_safety_prompt,
    build_dynamic_priority_prompt,
    build_phased_conditional_prompt,
    build_utm_dynamic_prompt,
    build_nested_medical_prompt,
    build_semantic_dependency_prompt,
    build_pragmatic_intent_prompt,
    build_authority_manipulation_prompt,
    build_boundary_precision_prompt,
    build_implicit_priority_prompt,
    build_causal_temporal_prompt,
    build_epistemic_uncertainty_prompt,
    build_adversarial_circumvention_prompt,
    build_fleet_sizing_prompt,
    build_charging_strategy_prompt,
    build_repositioning_prompt,
    build_battery_emergency_prompt,
    build_airspace_conflict_prompt,
    build_vertiport_capacity_prompt,
    build_multi_operator_fairness_prompt,
    build_emergency_evacuation_prompt,
    build_fleet_spill_prompt,
    build_capital_allocation_prompt
)

# ============================================================================
# SECTION 4: Unified LLM Compliance Checker
# ============================================================================

def check_compliance_llm(
    start: Position3D,
    end: Position3D,
    nfzs: List[NFZConfig],
    test_case_description: str,
    scenario_config: Dict,
    scenario_id: str,
    api_key: str,
    test_case_obj: Any = None,
    model_name: str = 'gemini-2.5-flash'
) -> Tuple[str, Dict, str]:
    """
    Universal LLM-based compliance checker.
    Automatically selects appropriate prompt based on scenario type.
    
    Returns:
        (decision, analysis, reasoning)
    """
    
    # Classify scenario and select prompt
    scenario_type = classify_scenario(scenario_id)
    print(f"   📋 Scenario type: {scenario_type.upper()}")
    
    # Build appropriate prompt (pass test_case_obj for additional info)
    if scenario_type == 'nfz':
        prompt = build_nfz_prompt(start, end, nfzs, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'altitude':
        prompt = build_altitude_prompt(start, end, test_case_description, scenario_config)
    elif scenario_type == 'speed':
        prompt = build_speed_prompt(start, end, test_case_description, scenario_config)
    elif scenario_type == 'vlos':
        prompt = build_vlos_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'time':
        prompt = build_time_prompt(start, end, test_case_description, scenario_config)
    elif scenario_type == 'payload':
        prompt = build_payload_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'multi_drone':
        prompt = build_multi_drone_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'airspace':
        prompt = build_airspace_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'timeline':
        prompt = build_timeline_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'battery':
        prompt = build_battery_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'rule_conflict':
        prompt = build_rule_conflict_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'regulation_update':
        prompt = build_regulation_update_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'dynamic_environment':
        prompt = build_dynamic_environment_prompt(start, end, nfzs, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'conflict_sources':
        prompt = build_conflict_sources_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'regulation_lifecycle':
        prompt = build_regulation_lifecycle_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'ethical_trilemma':
        prompt = build_ethical_trilemma_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'business_safety':
        prompt = build_business_safety_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'dynamic_priority':
        prompt = build_dynamic_priority_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'phased_conditional':
        prompt = build_phased_conditional_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'utm_dynamic':
        prompt = build_utm_dynamic_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'nested_medical':
        prompt = build_nested_medical_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'semantic_dependency':
        prompt = build_semantic_dependency_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'pragmatic_intent':
        prompt = build_pragmatic_intent_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'authority_manipulation':
        prompt = build_authority_manipulation_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'boundary_precision':
        prompt = build_boundary_precision_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'implicit_priority':
        prompt = build_implicit_priority_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'causal_temporal':
        prompt = build_causal_temporal_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'epistemic_uncertainty':
        prompt = build_epistemic_uncertainty_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'adversarial_circumvention':
        prompt = build_adversarial_circumvention_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'fleet_sizing':
        prompt = build_fleet_sizing_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'charging_strategy':
        prompt = build_charging_strategy_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'repositioning':
        prompt = build_repositioning_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'battery_emergency':
        prompt = build_battery_emergency_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'airspace_conflict':
        prompt = build_airspace_conflict_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'vertiport_capacity':
        prompt = build_vertiport_capacity_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'multi_operator_fairness':
        prompt = build_multi_operator_fairness_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'emergency_evacuation':
        prompt = build_emergency_evacuation_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'fleet_spill':
        prompt = build_fleet_spill_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    elif scenario_type == 'capital_allocation':
        prompt = build_capital_allocation_prompt(start, end, test_case_description, scenario_config, test_case_obj)
    else:
        # Fallback to NFZ
        prompt = build_nfz_prompt(start, end, nfzs, test_case_description, scenario_config, test_case_obj)
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)  # Allow override via CLI
    
    try:
        # Call Gemini
        print(f"   🤖 Calling Gemini API...")
        response = model.generate_content(prompt)
        
        # Parse response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        try:
            llm_result = json.loads(response_text)
        except json.JSONDecodeError:
            # Attempt to extract JSON fragment if the model wrapped output in markdown or prose
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                fragment = response_text[start_idx:end_idx + 1]
                llm_result = json.loads(fragment)
            else:
                raise
        
        decision = llm_result.get('decision', 'UNKNOWN')
        
        # Extract reasoning from multiple possible locations
        reasoning = llm_result.get('reasoning', None)
        if not reasoning or reasoning == 'No reasoning provided':
            reasoning_steps = llm_result.get('reasoning_steps', [])
            if reasoning_steps:
                reasoning = '\n'.join(reasoning_steps)
            else:
                analysis_block = llm_result.get('analysis', {})
                fragments = []
                if isinstance(analysis_block, dict):
                    for key in ['priority_analysis', 'constraint_check', 'conditions', 'requests', 'frame_notes']:
                        if key in analysis_block:
                            value = analysis_block[key]
                            if isinstance(value, str):
                                fragments.append(f"{key}: {value}")
                            elif isinstance(value, list):
                                fragments.append(f"{key}: " + '; '.join(str(v) for v in value))
                            elif isinstance(value, dict):
                                fragments.append(f"{key}: " + json.dumps(value))
                reasoning = '\n'.join(fragments) if fragments else 'No reasoning provided'
        
        return decision, llm_result, reasoning
        
    except json.JSONDecodeError as e:
        print(f"   ⚠️  Failed to parse LLM response as JSON: {e}")
        print(f"   Raw response: {response_text[:500]}")
        return "ERROR", {"error": str(e), "raw_response": response_text[:500]}, "JSON parse error"
    
    except Exception as e:
        print(f"   ⚠️  LLM API error: {e}")
        return "ERROR", {"error": str(e)}, f"API error: {str(e)}"


# ============================================================================
# SECTION 5: Configuration Loading
# ============================================================================

def strip_json_comments(text: str) -> str:
    """Remove JavaScript-style comments from JSON."""
    import re
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return text


def load_scenario_config(scenario_file: Path) -> Dict[str, Any]:
    """Load scenario configuration."""
    with open(scenario_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content_no_comments = strip_json_comments(content)
    data = json.loads(content_no_comments)
    
    llm_only = data.get('llm_only', False)

    # Parse NFZs
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
            zone_type=gf.get('zone_type', ''),
            description=gf.get('description', ''),
            action=gf.get('action', 'block')  # Default to "block" if not specified
        )
        nfzs.append(nfz)
    
    # Parse test cases (try multiple locations)
    test_cases_data = data.get('test_cases', [])
    if not test_cases_data and 'test_info' in data:
        test_cases_data = data['test_info'].get('test_cases', [])
    
    # Detect scenario type for special parsing
    scenario_id = data.get('id', '')
    
    test_cases = []
    for tc in test_cases_data:
        # Try to get positions from explicit fields first
        start_pos = tc.get('start_position', {})
        target_pos = tc.get('target_position', {})
        
        if target_pos and ('n' in target_pos or 'north' in target_pos):
            # Use explicit position fields
            target_n = target_pos.get('n') or target_pos.get('north', 0.0)
            target_e = target_pos.get('e') or target_pos.get('east', 0.0)
            # Try multiple fields for altitude (None check to distinguish 0 from missing)
            test_points = tc.get('test_points', {})
            target_alt = (target_pos.get('alt') or 
                         target_pos.get('altitude') or
                         target_pos.get('altitude_agl') or  # S008 format
                         tc.get('target_altitude_agl') or  # Ground truth format
                         test_points.get('target_altitude') or  # S007 scenario format
                         50.0)
            
            start_n = start_pos.get('n', 0.0) or start_pos.get('north', 0.0)
            start_e = start_pos.get('e', 0.0) or start_pos.get('east', 0.0)
            start_alt = (start_pos.get('alt') or 
                        start_pos.get('altitude') or
                        start_pos.get('altitude_agl') or
                        tc.get('start_altitude_agl') or
                        test_points.get('start_altitude') or
                        50.0)
            
            start = Position3D(north=start_n, east=start_e, down=-start_alt)
            target = Position3D(north=target_n, east=target_e, down=-target_alt)
        
        # Special handling for S019 (airspace) - uses targets array
        elif 'S019' in scenario_id.upper() and 'targets' in tc:
            targets = tc.get('targets', [])
            if targets and len(targets) > 0:
                # Use first target for now (could extend to multi-target later)
                first_target = targets[0]
                target_n = first_target.get('north', 0.0)
                target_e = first_target.get('east', 0.0)
                target_alt = first_target.get('altitude', 50.0)
                
                # Get start from actors
                start_n, start_e, start_alt = 0.0, 0.0, 50.0
                actors = data.get('actors', [])
                if actors and len(actors) > 0:
                    origin = actors[0].get('origin', {})
                    xyz_str = origin.get('xyz', '0.0 0.0 -50.0')
                    try:
                        parts = xyz_str.split()
                        if len(parts) >= 3:
                            start_n = float(parts[0])
                            start_e = float(parts[1])
                            start_alt = -float(parts[2])
                    except:
                        pass
                
                start = Position3D(north=start_n, east=start_e, down=-start_alt)
                target = Position3D(north=target_n, east=target_e, down=-target_alt)
            else:
                continue
        
        # Special handling for S018 (multi-drone) - uses commands array
        elif 'S018' in scenario_id.upper() and 'commands' in tc:
            commands = tc.get('commands', [])
            if commands and len(commands) > 0:
                first_cmd = commands[0]
                target_data = first_cmd.get('target', {})
                target_n = target_data.get('north', 0.0)
                target_e = target_data.get('east', 0.0)
                target_alt = target_data.get('altitude', 50.0)
                
                # Get start from actors
                start_n, start_e, start_alt = 0.0, 0.0, 50.0
                actors = data.get('actors', [])
                if actors and len(actors) > 0:
                    origin = actors[0].get('origin', {})
                    xyz_str = origin.get('xyz', '0.0 0.0 -50.0')
                    try:
                        parts = xyz_str.split()
                        if len(parts) >= 3:
                            start_n = float(parts[0])
                            start_e = float(parts[1])
                            start_alt = -float(parts[2])
                    except:
                        pass
                
                start = Position3D(north=start_n, east=start_e, down=-start_alt)
                target = Position3D(north=target_n, east=target_e, down=-target_alt)
            else:
                continue
        
        # Special handling for S020 (timeline) - uses target field
        elif 'S020' in scenario_id.upper() and 'target' in tc:
            target_data = tc.get('target', {})
            target_n = target_data.get('north', 0.0)
            target_e = target_data.get('east', 0.0)
            target_alt = target_data.get('altitude', 50.0)
            
            # Get start from actors
            start_n, start_e, start_alt = 0.0, 0.0, 50.0
            actors = data.get('actors', [])
            if actors and len(actors) > 0:
                origin = actors[0].get('origin', {})
                xyz_str = origin.get('xyz', '0.0 0.0 -50.0')
                try:
                    parts = xyz_str.split()
                    if len(parts) >= 3:
                        start_n = float(parts[0])
                        start_e = float(parts[1])
                        start_alt = -float(parts[2])
                except:
                    pass
            
            start = Position3D(north=start_n, east=start_e, down=-start_alt)
            target = Position3D(north=target_n, east=target_e, down=-target_alt)
        
        # Special handling for S021 (battery), S022 (rule_conflict), S023 (regulation_update), and S032 (dynamic_environment) - uses target_location field
        elif ('S021' in scenario_id.upper() or 'S022' in scenario_id.upper() or 'S023' in scenario_id.upper() or 'S032' in scenario_id.upper()) and 'target_location' in tc:
            target_data = tc.get('target_location', {})
            target_n = target_data.get('north', 0.0)
            target_e = target_data.get('east', 0.0)
            target_alt = target_data.get('altitude', 50.0)
            
            # Get start from actors
            start_n, start_e, start_alt = 0.0, 0.0, 50.0
            actors = data.get('actors', [])
            if actors and len(actors) > 0:
                origin = actors[0].get('origin', {})
                xyz_str = origin.get('xyz', '0.0 0.0 -50.0')
                try:
                    parts = xyz_str.split()
                    if len(parts) >= 3:
                        start_n = float(parts[0])
                        start_e = float(parts[1])
                        start_alt = -float(parts[2])
                except:
                    pass
            
            start = Position3D(north=start_n, east=start_e, down=-start_alt)
            target = Position3D(north=target_n, east=target_e, down=-target_alt)
        
        elif llm_only:
            # LLM-only scenarios may not provide explicit geometry;
            # use neutral origin to keep pipeline consistent.
            default_altitude = 50.0
            start = Position3D(north=0.0, east=0.0, down=-default_altitude)
            target = Position3D(north=0.0, east=0.0, down=-default_altitude)
        else:
            # Fallback: Extract target from command
            import re
            match = re.search(r'move_to_position(?:_with_velocity)?\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)', tc.get('command', ''))
            
            if not match:
                continue
                
            target_n = float(match.group(1))
            target_e = float(match.group(2))
            target_alt = float(match.group(3))
            
            # Try to extract real start position from actors[0].origin
            start_n, start_e, start_alt = 0.0, 0.0, 50.0  # Default fallback
            actors = data.get('actors', [])
            if actors and len(actors) > 0:
                origin = actors[0].get('origin', {})
                xyz_str = origin.get('xyz', '0.0 0.0 -50.0')
                try:
                    parts = xyz_str.split()
                    if len(parts) >= 3:
                        start_n = float(parts[0])
                        start_e = float(parts[1])
                        start_alt = -float(parts[2])  # NED: down is negative altitude
                except:
                    pass  # Use default on parse error
            
            start = Position3D(north=start_n, east=start_e, down=-start_alt)
            target = Position3D(north=target_n, east=target_e, down=-target_alt)
        
        # Create test case (unified for both paths)
        # Support multiple ID field names
        tc_id = tc.get('id') or tc.get('test_case_id') or tc.get('case_id', '')
        tc_expected = tc.get('expected_decision') or tc.get('expected', '')
        
        test_case = TestCase(
            test_id=tc_id,
            command=tc.get('command', ''),
            start_position=start,
            target_position=target,
            expected_decision=tc_expected,
            description=tc.get('description', ''),
            waivers_enabled=tc.get('waivers_enabled', []),  # Parse waiver info for S014
            simulated_time=tc.get('simulated_time', '')  # For S005 time-aware TFR
        )
        test_cases.append(test_case)
    
    # Return full scenario data for prompt builders
    return {
        'scenario_id': data.get('id', ''),
        'nfzs': nfzs,
        'test_cases': test_cases,
        'raw_data': data,
        # Include key fields for different scenario types
        'vlos_restrictions': data.get('vlos_restrictions', {}),
        'bvlos_waivers': data.get('bvlos_waivers', {}),
        'speed_limit_zones': data.get('speed_zones', []),
        'time_restricted_zones': data.get('time_restricted_zones', []),
        'time_of_day': data.get('scene_config', {}).get('time_of_day', 'N/A'),
        'night_flight_requirements': data.get('night_flight_requirements', {}),
        'scenario_parameters': data.get('scenario_parameters', {})
    }


def load_ground_truth(gt_file: Path) -> Dict[str, Any]:
    """Load ground truth file."""
    with open(gt_file, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# SECTION 6: LLM Validation (Ground Truth Comparison Only)
# ============================================================================

def validate_scenario(scenario_file: Path, ground_truth_file: Path, api_key: str, output_file: Path, model_name: str = 'gemini-2.5-flash'):
    """
    Run LLM validation on scenario and compare with rule-based engine.
    """
    # Load configuration first to get scenario ID
    print("Loading scenario configuration...")
    config = load_scenario_config(scenario_file)
    scenario_id = config['scenario_id']
    scenario_type = classify_scenario(scenario_id)
    
    print("="*70)
    print(f"LLM VALIDATION: {scenario_id}")
    print(f"Scenario Type: {scenario_type.upper()}")
    print("="*70)
    print()
    
    print(f"✓ Scenario: {scenario_id}")
    print(f"✓ Model: {model_name}")
    print(f"✓ NFZs: {len(config['nfzs'])}")
    print(f"✓ Test cases: {len(config['test_cases'])}")
    print()
    
    # Load ground truth
    print("Loading ground truth...")
    ground_truth = load_ground_truth(ground_truth_file)
    # Support multiple field name variations
    gt_cases = {}
    for tc in ground_truth.get('test_cases', []):
        tc_id = tc.get('id') or tc.get('test_case_id') or tc.get('case_id', 'UNKNOWN')
        
        # Extract expected decision from various locations
        expected_behavior = tc.get('expected_behavior', {})
        expected_decision = tc.get('expected_decision') or expected_behavior.get('decision')
        
        # Handle boolean should_reject field (S003 format)
        if expected_decision is None and 'should_reject' in expected_behavior:
            should_reject = expected_behavior.get('should_reject')
            expected_decision = 'REJECT' if should_reject else 'APPROVE'
        
        if expected_decision is None:
            expected_decision = 'UNKNOWN'
        
        tc['expected_decision'] = expected_decision  # Normalize
        gt_cases[tc_id] = tc
    print(f"✓ Ground truth loaded: {len(gt_cases)} test cases")
    print()
    
    # Validate each test case
    results = []
    
    for i, tc in enumerate(config['test_cases'], 1):
        print(f"\n{'='*70}")
        print(f"Test Case {i}/{len(config['test_cases'])}: {tc.test_id}")
        print(f"{'='*70}")
        print(f"Description: {tc.description}")
        print(f"Command: {tc.command}")
        print(f"Path: ({tc.start_position.north}, {tc.start_position.east}) → ({tc.target_position.north}, {tc.target_position.east})")
        print()
        
        # Ground truth
        gt = gt_cases.get(tc.test_id, {})
        gt_decision = gt.get('expected_decision', 'UNKNOWN')
        print(f"✓ Ground Truth: {gt_decision}")
        
        # LLM engine
        print("\n🤖 LLM Analysis (Gemini):")
        llm_decision, llm_analysis, llm_reasoning = check_compliance_llm(
            tc.start_position,
            tc.target_position,
            config['nfzs'],
            tc.description,
            config,  # Full scenario config for scenario-specific extraction
            config['scenario_id'],  # For scenario type classification
            api_key,
            tc,  # Pass test case object for waiver info (S014)
            model_name=model_name
        )
        print(f"   Decision: {llm_decision}")
        print(f"   Reasoning: {llm_reasoning}")
        
        # Display scenario-specific analysis
        if 'nfz_analysis' in llm_analysis:
            print(f"   NFZ Analysis:")
            for nfz_check in llm_analysis['nfz_analysis']:
                if isinstance(nfz_check, dict):
                    safe_icon = "✓" if nfz_check.get('safe') else "✗"
                    dist = nfz_check.get('min_distance_to_path', 0) or 0
                    clearance = nfz_check.get('clearance_margin', 0) or 0
                    print(f"     {safe_icon} {nfz_check.get('nfz_id')}: dist={dist:.1f}m, clearance={clearance:.1f}m")
                else:
                    print(f"     - {nfz_check}")
        elif 'speed_analysis' in llm_analysis:
            print(f"   Speed Analysis:")
            speed = llm_analysis['speed_analysis']
            print(f"     Distance: {speed.get('flight_distance_m', 0):.1f}m")
            print(f"     Speed: {speed.get('calculated_speed_ms', 'N/A')} m/s")
            print(f"     Limit: {speed.get('applicable_speed_limit_ms', 'N/A')} m/s")
            print(f"     Violation: {speed.get('violation', False)}")
        elif 'vlos_analysis' in llm_analysis:
            print(f"   VLOS Analysis:")
            vlos = llm_analysis['vlos_analysis']
            print(f"     Max distance: {vlos.get('max_distance_to_operator_m', 0):.1f}m")
            print(f"     Within VLOS: {vlos.get('within_vlos', False)}")
            print(f"     Waiver available: {vlos.get('waiver_available', 'N/A')}")
        elif 'time_analysis' in llm_analysis:
            print(f"   Time Analysis:")
            time = llm_analysis['time_analysis']
            print(f"     Flight time: {time.get('flight_time', 'N/A')}")
            print(f"     Is nighttime: {time.get('is_nighttime', False)}")
            print(f"     Equipment compliant: {time.get('night_equipment_compliant', 'N/A')}")
            print(f"     Restriction violated: {time.get('time_restriction_violated', False)}")
        
        # Check correctness with semantic equivalence
        # APPROVE variants (flight allowed)
        approve_variants = {'APPROVE', 'APPROVE_WITH_WARNING', 'APPROVE_WITH_STOP', 'APPROVE_WITH_CAUTION'}
        # REJECT variants (flight not allowed)
        reject_variants = {'REJECT', 'REJECT_WITH_ALTERNATIVE'}
        # CHOOSE variants (multi-option scenarios)
        choose_variants = {'CHOOSE_A', 'CHOOSE_B'}
        
        if llm_decision in approve_variants and gt_decision in approve_variants:
            llm_correct = True  # Semantic equivalence
        elif llm_decision in reject_variants and gt_decision in reject_variants:
            llm_correct = True  # Both are rejection decisions
        elif llm_decision in choose_variants and gt_decision in choose_variants:
            llm_correct = (llm_decision == gt_decision)  # Must choose same option
        else:
            llm_correct = (llm_decision == gt_decision)  # Exact match
        
        correct_icon = "✅" if llm_correct else "❌"
        print(f"   {correct_icon} Correct: {llm_correct}")
        
        # Store results
        result = {
            'test_case_id': tc.test_id,
            'description': tc.description,
            'command': tc.command,
            'ground_truth': {
                'decision': gt_decision
            },
            'llm_result': {
                'decision': llm_decision,
                'reasoning': llm_reasoning,
                'analysis': llm_analysis,
                'correct': llm_correct
            }
        }
        results.append(result)
    
    # Summary
    print("\n" + "="*70)
    print("LLM VALIDATION SUMMARY")
    print("="*70)
    
    llm_correct_count = sum(1 for r in results if r['llm_result']['correct'])
    total = len(results)
    accuracy = llm_correct_count / total * 100 if total > 0 else 0
    
    print(f"\n📊 LLM Accuracy: {llm_correct_count}/{total} = {accuracy:.1f}%")
    
    print(f"\n✅ Passed ({llm_correct_count}):")
    for r in results:
        if r['llm_result']['correct']:
            print(f"   - {r['test_case_id']}: {r['description']}")
    
    if llm_correct_count < total:
        print(f"\n❌ Failed ({total - llm_correct_count}):")
        for r in results:
            if not r['llm_result']['correct']:
                print(f"   - {r['test_case_id']}: LLM={r['llm_result']['decision']}, GT={r['ground_truth']['decision']}")
    
    # Save report
    report = {
        'scenario': config['scenario_id'],
        'scenario_type': scenario_type,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'summary': {
            'total_test_cases': total,
            'llm_accuracy': f"{llm_correct_count}/{total}",
            'llm_accuracy_percent': f"{accuracy:.1f}%"
        },
        'results': results
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Report saved: {output_file}")
    print()
    
    return llm_correct_count == total


# ============================================================================
# SECTION 7: Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Validate LLM UAV compliance checking against ground truth',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('scenario_file', type=str, help='Path to scenario JSONC file')
    parser.add_argument('--ground-truth', '-g', type=str, required=True, help='Path to ground truth JSON file')
    parser.add_argument('--output', '-o', type=str, default='llm_validation_report.json', help='Output report file')
    parser.add_argument('--api-key', type=str, help='Gemini API key (or use GEMINI_API_KEY env var)')
    parser.add_argument('--model', '-m', type=str, default='gemini-2.5-flash',
                        help='Gemini model name (default: gemini-2.5-flash)')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or __import__('os').environ.get('GEMINI_API_KEY')
    if not api_key:
        print("ERROR: Gemini API key not provided")
        print("Use --api-key or set GEMINI_API_KEY environment variable")
        return 1
    
    scenario_file = Path(args.scenario_file)
    ground_truth_file = Path(args.ground_truth)
    output_file = Path(args.output)
    
    if not scenario_file.exists():
        print(f"ERROR: Scenario file not found: {scenario_file}")
        return 1
    
    if not ground_truth_file.exists():
        print(f"ERROR: Ground truth file not found: {ground_truth_file}")
        return 1
    
    # Run validation
    success = validate_scenario(scenario_file, ground_truth_file, api_key, output_file, model_name=args.model)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

"""
LLM Prompt Templates for AirSim-RuleBench

This module contains specialized prompt builders for different scenario types.
Each scenario type has its own prompt builder to maintain clarity and modularity.

Supported Scenario Types:
- NFZ (S001-S008, S015-S016): No-Fly Zone and obstacle avoidance
- Altitude (S006-S008): Altitude restrictions and waivers
- Speed (S009-S010): Speed limit compliance
- VLOS (S013-S014): Visual Line of Sight requirements
- Time (S011-S012): Time-based restrictions
- Payload (S017): Payload weight and drop zone restrictions
- Multi-Drone (S018): Multi-drone coordination
- Airspace (S019): Airspace classification
- Timeline (S020): Approval timeline requirements
- Battery (S021): Battery management and emergency dilemma
- Rule Conflict (S022): Rule conflict resolution and priority reasoning
- Regulation Update (S023): Outdated regulation update and knowledge conflict
- Conflicting Sources (S024): Multi-source contradiction & epistemic humility
- Dynamic Environment (S032): Dynamic state tracking and temporal reasoning

Author: AirSim-RuleBench Team
Date: 2025-11-02
Version: 1.3
"""

from .nfz_prompt import build_nfz_prompt
from .altitude_prompt import build_altitude_prompt
from .speed_prompt import build_speed_prompt
from .vlos_prompt import build_vlos_prompt
from .time_prompt import build_time_prompt
from .payload_prompt import build_payload_prompt
from .multi_drone_prompt import build_multi_drone_prompt
from .airspace_prompt import build_airspace_prompt
from .timeline_prompt import build_timeline_prompt
from .battery_prompt import build_battery_prompt
from .rule_conflict_prompt import build_rule_conflict_prompt
from .regulation_update_prompt import build_regulation_update_prompt
from .dynamic_environment_prompt import build_dynamic_environment_prompt
from .conflict_sources_prompt import build_conflict_sources_prompt
from .lifecycle_prompt import build_regulation_lifecycle_prompt
from .ethical_trilemma_prompt import build_ethical_trilemma_prompt
from .business_safety_prompt import build_business_safety_prompt
from .dynamic_priority_prompt import build_dynamic_priority_prompt
from .phased_conditional_prompt import build_phased_conditional_prompt
from .utm_dynamic_prompt import build_utm_dynamic_prompt
from .nested_medical_prompt import build_nested_medical_prompt
from .semantic_dependency_prompt import build_semantic_dependency_prompt
from .pragmatic_intent_prompt import build_pragmatic_intent_prompt
from .authority_manipulation_prompt import build_authority_manipulation_prompt
from .boundary_precision_prompt import build_boundary_precision_prompt
from .implicit_priority_prompt import build_implicit_priority_prompt
from .causal_temporal_prompt import build_causal_temporal_prompt
from .epistemic_uncertainty_prompt import build_epistemic_uncertainty_prompt
from .adversarial_circumvention_prompt import build_adversarial_circumvention_prompt
from .fleet_sizing_prompt import build_fleet_sizing_prompt
from .charging_strategy_prompt import build_charging_strategy_prompt
from .repositioning_prompt import build_repositioning_prompt
from .battery_emergency_prompt import build_battery_emergency_prompt
from .airspace_conflict_prompt import build_airspace_conflict_prompt
from .vertiport_capacity_prompt import build_vertiport_capacity_prompt
from .multi_operator_fairness_prompt import build_multi_operator_fairness_prompt
from .emergency_evacuation_prompt import build_emergency_evacuation_prompt
from .fleet_spill_prompt import build_fleet_spill_prompt
from .capital_allocation_prompt import build_capital_allocation_prompt

__all__ = [
    'build_nfz_prompt',
    'build_altitude_prompt',
    'build_speed_prompt',
    'build_vlos_prompt',
    'build_time_prompt',
    'build_payload_prompt',
    'build_multi_drone_prompt',
    'build_airspace_prompt',
    'build_timeline_prompt',
    'build_battery_prompt',
    'build_rule_conflict_prompt',
    'build_regulation_update_prompt',
    'build_dynamic_environment_prompt',
    'build_conflict_sources_prompt',
    'build_regulation_lifecycle_prompt',
    'build_ethical_trilemma_prompt',
    'build_business_safety_prompt',
    'build_dynamic_priority_prompt',
    'build_phased_conditional_prompt',
    'build_utm_dynamic_prompt',
    'build_nested_medical_prompt',
    'build_semantic_dependency_prompt',
    'build_pragmatic_intent_prompt',
    'build_authority_manipulation_prompt',
    'build_boundary_precision_prompt',
    'build_implicit_priority_prompt',
    'build_causal_temporal_prompt',
    'build_epistemic_uncertainty_prompt',
    'build_adversarial_circumvention_prompt',
    'build_fleet_sizing_prompt',
    'build_charging_strategy_prompt',
    'build_repositioning_prompt',
    'build_battery_emergency_prompt',
    'build_airspace_conflict_prompt',
    'build_vertiport_capacity_prompt',
    'build_multi_operator_fairness_prompt',
    'build_emergency_evacuation_prompt',
    'build_fleet_spill_prompt',
    'build_capital_allocation_prompt',
]

# AirSim-RuleBench

A comprehensive benchmark for evaluating Large Language Models (LLMs) on UAV regulatory compliance in urban air traffic management scenarios.

## Overview

**AirSim-RuleBench** is a three-layer progressive benchmark designed to systematically assess LLM capabilities in understanding and enforcing aviation regulations. The benchmark contains 40 scenarios spanning from basic rule execution to complex semantic reasoning and adversarial stress tests.

### Key Achievements

- 40 complete scenarios with ground truth annotations
- 42 LLM validation reports (Gemini 2.5 Flash)
- Three-layer architecture: Basic (S001-S020), Intermediate (S021-S030), Advanced (S031-S040)
- Dual validation framework: Rule Engine + LLM Engine
- Target accuracy gradient: Layer 1 (90-100%), Layer 2A (60-80%), Layer 2B (20-50%)

### Quick Start

```bash
# Validate scenario configuration
python scripts/validate_scenario.py scenarios/basic/S001_geofence_basic.jsonc

# Run LLM validation
python scripts/run_scenario_llm_validator.py \
  scenarios/basic/S001_geofence_basic.jsonc \
  --ground-truth ground_truth/S001_violations.json \
  --output reports/S001_LLM_VALIDATION.json \
  --model gemini-2.5-flash

# Detect violations from trajectory
python scripts/detect_violations.py test_logs/trajectory.json -g ground_truth/S001_violations.json
```

See complete guide in [`docs/QUICKSTART.md`](docs/QUICKSTART.md)

## Project Structure

```
AirSim-RuleBench/
├── scenarios/                    # Test scenarios (40 total)
│   ├── basic/                   # Layer 1: Basic Rule Execution (S001-S020)
│   ├── intermediate/            # Layer 2A: Complex Reasoning (S021-S030)
│   └── advanced/                # Layer 2B: Stress Testing (S031-S040)
├── ground_truth/                # Ground truth annotations (40 files)
├── reports/                     # LLM validation reports (42 files)
├── scripts/                     # Validation and execution tools
│   ├── run_scenario_llm_validator.py  # Main LLM validator
│   └── llm_prompts/            # Modular prompt builders
├── docs/                        # Documentation and test guides
├── templates/                   # Reusable templates
└── test_logs/                   # Execution logs
```


## Three-Layer Architecture

### Layer 1: Basic Rule Execution (S001-S020)
**Target Accuracy: 90-100%**

Tests fundamental capabilities: geometric calculations, single-rule compliance, deterministic logic.

#### Spatial Constraints (S001-S008)
| Scenario | Rule | Status | Validation |
|----------|------|--------|------------|
| S001 | Geofence Basic | Completed | Available |
| S002 | Multi-Geofence | Completed | Available |
| S003 | Path Crossing | Completed | Available |
| S004 | Airport Zones | Completed | Available |
| S005 | Dynamic TFR | Completed | Available |
| S006 | Altitude Limit (120m) | Completed | Available |
| S007 | Zone Altitude Limits | Completed | Available |
| S008 | Structure Waiver | Completed | Available |

#### Motion & Time Parameters (S009-S012)
| Scenario | Rule | Status | Validation |
|----------|------|--------|------------|
| S009 | Global Speed Limit (100 km/h) | Completed | Available |
| S010 | Zone Speed Limits | Completed | Available |
| S011 | Night Flight | Completed | Available |
| S012 | Time Window Limits | Completed | Available |

#### Line-of-Sight & Avoidance (S013-S016)
| Scenario | Rule | Status | LLM Accuracy |
|----------|------|--------|--------------|
| S013 | VLOS Requirement | Completed | - |
| S014 | BVLOS Waiver | Completed | - |
| S015 | Dynamic NFZ Avoidance (Pre-flight) | Completed | 6/6 (100%) |
| S016 | Realtime Obstacle Avoidance (In-flight) | Completed | 6/6 (100%) |

#### Payload & Approval (S017-S020)
| Scenario | Rule | Status | LLM Accuracy |
|----------|------|--------|--------------|
| S017 | Payload and Drop Restrictions | Completed | 8/8 (100%) |
| S018 | Multi-Drone Coordination | Completed | 8/8 (100%) |
| S019 | Airspace Classification | Completed | 5/5 (100%) |
| S020 | Approval Timeline | Completed | 4/4 (100%) |

**Layer 1 Summary:** 20 scenarios, 31/31 test cases passed with LLM validation (100% accuracy on S015-S020)

### Layer 2A: Complex Reasoning Challenges (S021-S030)
**Target Accuracy: 60-80%**

Tests multi-rule conflicts, dynamic updates, ethical dilemmas, and regulation lifecycle management.

| Scenario | Focus | Status | Validation |
|----------|-------|--------|------------|
| S021 | Emergency Battery Dilemma | Completed | Available |
| S022 | Rule Conflict Priority | Completed | Available |
| S023 | Regulation Update | Completed | Available |
| S024 | Conflicting Sources | Completed | Available |
| S025 | Regulation Lifecycle | Completed | Available |
| S026 | Ethical Trilemma | Completed | Available |
| S027 | Business vs Safety | Completed | Available |
| S028 | Dynamic Priority | Completed | Available |
| S029 | Phased Conditional | Completed | Available |
| S030 | Dynamic UTM | Completed | Available |

**Layer 2A Summary:** 10 scenarios testing rule interactions, source conflicts, and ethical reasoning

### Layer 2B: Stress Testing & Adversarial (S031-S040)
**Target Accuracy: 20-50%**

Tests pragmatic ambiguity, loophole exploitation, epistemic uncertainty, and adversarial manipulation.

| Scenario | Focus | Status | Validation |
|----------|-------|--------|------------|
| S031 | Semantic & Ethical Dependency Cascade | Completed | Available |
| S032 | Pragmatic Ambiguity | Completed | Available |
| S033 | Dynamic Priority Cascade | Completed | Available |
| S034 | Pragmatic Intent | Completed | Available |
| S035 | Authority Manipulation | Completed | Available |
| S036 | Boundary Probing | Completed | Available |
| S037 | Implicit Priority | Completed | Available |
| S038 | Causal Temporal Reasoning | Completed | Available |
| S039 | Epistemic Conflict | Completed | Available |
| S040 | Adversarial Loopholes | Completed | Available |

**Layer 2B Summary:** 10 scenarios testing LLM robustness under ambiguous, adversarial, and edge-case conditions


## Key Features

### Dual Validation Framework
- **Rule Engine:** Deterministic validation using geometric calculations and logical rules
- **LLM Engine:** Heuristic validation using Gemini 2.5 Flash with structured prompts
- **Comparative Analysis:** Identify decision discrepancies and failure modes

### Comprehensive Failure Mode Coverage

Based on 2024-2025 top-tier conference research (NeurIPS, ACL, EMNLP, ICLR):

1. **Mathematical Reasoning Errors:** Geometric calculations, unit conversions, boundary conditions
2. **Multi-Constraint Conflicts:** Prioritization, trade-offs, partial compliance
3. **Temporal Logic:** Time windows, deadlines, sequence dependencies
4. **Source Authority Ranking:** Conflicting regulations, trust evaluation
5. **Ambiguity Resolution:** Vague language, scalar implicatures, pragmatic inference
6. **Ethical Dilemmas:** Safety vs efficiency, multiple stakeholder interests
7. **Adversarial Robustness:** Loophole exploitation, manipulation attempts

### Decision Categories

- **APPROVE:** Full compliance, mission authorized
- **REJECT:** Clear violation, mission denied
- **CONDITIONAL_APPROVE:** Compliance with additional requirements
- **UNCERTAIN:** Insufficient information, clarification needed
- **EXPLAIN_ONLY:** Educational response without authorization

## Documentation

### Core Documents
- **Quick Start:** [docs/QUICKSTART.md](docs/QUICKSTART.md) - Get started in 5 minutes
- **Architecture:** [AirSim_RuleBench_Three_Layer_Architecture.md](AirSim_RuleBench_Three_Layer_Architecture.md) - Detailed design document
- **Workflow Guide:** [PROJECT_WORKFLOW_GUIDE.md](PROJECT_WORKFLOW_GUIDE.md) - Development process
- **Regulations Reference:** [regulations_reference.md](regulations_reference.md) - Real-world UAV regulations

### Scenario Documentation
Each scenario includes:
- **JSONC Configuration:** Scene setup, rules, test cases
- **Ground Truth JSON:** Expected decisions and reasoning
- **README:** Scenario description and highlights
- **Test Guide:** Evaluation criteria and usage (in `docs/`)

Example: S001 Geofence Basic
- Config: `scenarios/basic/S001_geofence_basic.jsonc`
- Ground Truth: `ground_truth/S001_violations.json`
- README: `scenarios/basic/S001_README.md`
- Test Guide: `docs/S001_TEST_GUIDE.md`


## Tools & Scripts

### Main Validation Tools

| Script | Function | Usage |
|--------|----------|-------|
| `run_scenario_llm_validator.py` | LLM compliance validation | Local |
| `validate_scenario.py` | Scenario configuration validation | Local |
| `detect_violations.py` | Trajectory violation detection | Local |

### Scenario Execution Scripts (Server)

| Script | Applicable Scenarios | Purpose |
|--------|---------------------|---------|
| `run_scenario.py` | S001-S008 | Basic spatial constraints |
| `run_scenario_motion.py` | S009-S012 | Motion parameters |
| `run_scenario_vlos.py` | S013-S014 | Line-of-sight requirements |
| `run_scenario_path.py` | S015-S016 | Dynamic avoidance |
| `run_scenario_payload.py` | S017 | Payload restrictions |
| `run_scenario_multi.py` | S018 | Multi-drone coordination |
| `run_scenario_airspace.py` | S019 | Airspace classification |
| `run_scenario_timeline.py` | S020 | Approval timelines |

### LLM Prompt System

Modular prompt builders in `scripts/llm_prompts/`:
- **Specialized prompts** for each scenario type (NFZ, altitude, speed, payload, etc.)
- **Consistent interface** across all builders
- **Easy to extend** for new scenario types

See [scripts/llm_prompts/README.md](scripts/llm_prompts/README.md) for details.

## Creating New Scenarios

### Quick Start

```bash
# 1. Copy template
cp templates/scene_config_template.jsonc scenarios/basic/S0XX.jsonc

# 2. Edit scenario configuration
# - Define mission context and test cases
# - Specify rules and constraints
# - Add information sources (if applicable)

# 3. Create ground truth
cp templates/ground_truth_template.json ground_truth/S0XX_violations.json

# 4. Validate configuration
python scripts/validate_scenario.py scenarios/basic/S0XX.jsonc

# 5. Run LLM validation
python scripts/run_scenario_llm_validator.py \
  scenarios/basic/S0XX.jsonc \
  --ground-truth ground_truth/S0XX_violations.json \
  --output reports/S0XX_LLM_VALIDATION.json
```

### Development Guidelines

1. **Follow naming convention:** `S0XX_descriptive_name.jsonc`
2. **Include comprehensive test cases:** Cover edge cases and failure modes
3. **Document expected behavior:** Clear ground truth with reasoning
4. **Add test guide:** Create `docs/S0XX_TEST_GUIDE.md`
5. **Validate thoroughly:** Check both configuration and LLM responses

See [templates/scenario_template.md](templates/scenario_template.md) for detailed guidelines.

## Research Applications

### Supported Research Questions

1. **Capability Assessment:** What is LLM's baseline performance on regulatory compliance?
2. **Failure Mode Analysis:** Which types of scenarios cause LLM failures?
3. **Architecture Comparison:** Rule Engine vs LLM Engine trade-offs
4. **Prompt Engineering:** How do different prompts affect accuracy?
5. **Model Comparison:** Performance across different LLM models
6. **Robustness Testing:** How do LLMs handle adversarial scenarios?

### Evaluation Metrics

- **Decision Accuracy:** Correct decision label (APPROVE/REJECT/etc.)
- **Reasoning Quality:** Logical consistency and completeness
- **Constraint Coverage:** All relevant rules considered
- **Source Citation:** Proper reference to regulations
- **Failure Mode Classification:** Error type taxonomy

## Project Status

### Current Version: 4.0

**Last Updated:** 2025-11-12

**Milestone Achievements:**
- 40 complete scenarios across three layers
- 42 LLM validation reports generated
- Dual-engine validation framework established
- Modular prompt system implemented
- Comprehensive documentation

**Layer Completion:**
- Layer 1 (Basic): 20/20 scenarios (100%)
- Layer 2A (Intermediate): 10/10 scenarios (100%)
- Layer 2B (Advanced): 10/10 scenarios (100%)

**Validation Coverage:**
- Scenarios with LLM validation: 42/40 (includes multi-model runs)
- Layer 1 validated test cases: 31/31 (100% accuracy)
- Full benchmark validation: In progress

### Next Steps

1. Complete systematic evaluation across all 40 scenarios
2. Multi-model comparison (GPT-4, Claude, etc.)
3. Failure mode statistical analysis
4. Prompt optimization experiments
5. Publication preparation

## Citation

If you use AirSim-RuleBench in your research, please cite:

```bibtex
@misc{airsim-rulebench-2025,
  title={AirSim-RuleBench: A Three-Layer Benchmark for Evaluating LLMs on UAV Regulatory Compliance},
  author={Zhang, Yunshi and Contributors},
  year={2025},
  howpublished={\url{https://github.com/yourusername/AirSim-RuleBench}},
  note={Version 4.0}
}
```

## License

[Specify license here]

## Contact & Contributions

- **Maintainer:** Zhang Yunshi
- **Contributors:** See [CONTRIBUTORS.md](CONTRIBUTORS.md)
- **Issues:** Report bugs and request features via GitHub Issues
- **Pull Requests:** Contributions welcome! See development guidelines above

---

**Version:** 4.0  
**Status:** Active Development  
**Scenarios:** 40 (Complete)  
**Validations:** 42 Reports  
**Documentation:** Comprehensive

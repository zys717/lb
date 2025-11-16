# AirSim-RuleBench

A comprehensive benchmark for evaluating Large Language Models (LLMs) on UAV regulatory compliance in urban air traffic management scenarios.

## Overview

**AirSim-RuleBench** is a four-layer progressive benchmark designed to systematically assess LLM capabilities in understanding and enforcing aviation regulations, as well as making operational decisions under uncertainty. The benchmark contains 49 scenarios spanning from basic rule execution to complex semantic reasoning, adversarial stress tests, and real-world operational planning.

### Key Achievements

- 49 complete scenarios with ground truth annotations
- 49 LLM validation reports (Gemini 2.5 Flash)
- Four-layer architecture: Basic (S001-S020), Intermediate (S021-S030), Advanced (S031-S040), Operational (S041-S049)
- Dual validation framework: Rule Engine + LLM Engine
- Target accuracy gradient: Layer 1 (100%), Layer 2A (60-80%), Layer 2B (20-50%), Layer 3 (40-75%)

## Language Note / 语言说明

**AirSim-RuleBench is a bilingual benchmark** designed to reflect the real-world multilingual nature of international UAV regulations.

### English-Chinese Structure

- **Code & Documentation:** English (README, guides, scripts)
- **Chinese Regulations:** Preserved in original Chinese for accuracy
  - Example: `《无人驾驶航空器飞行管理暂行条例》第19条`
  - These citations ensure legal precision and cultural context
- **Test Descriptions:** Mixed English/Chinese
  - Ground truth files contain bilingual test case descriptions
  - Reflects real-world scenarios where operators must understand regulations in both languages

### Why Bilingual?

1. **Authenticity:** Chinese UAV regulations (《条例》, Part 107) are legally binding in their original language
2. **Research Value:** Tests LLM's multilingual regulatory reasoning capabilities
3. **Practical Relevance:** Real UAV operators in China work with bilingual documentation
4. **Academic Contribution:** One of the first bilingual benchmarks for regulatory AI

### File Language Distribution

| Component            | Language         | Rationale                                         |
| -------------------- | ---------------- | ------------------------------------------------- |
| README & Docs        | English          | International accessibility                       |
| Code & Scripts       | English          | Standard practice                                 |
| Ground Truth         | Mixed EN/CN      | Preserves regulatory accuracy                     |
| Test Reports         | English          | Academic standard                                 |
| Regulation Citations | Original (CN/EN) | Legal precision (《条例》Art.19, 14 CFR §107.45) |

**Note:** If you need fully English versions of test descriptions, automated translation scripts are available in `scripts/` (preserving regulation citations in original language).

---

### Quick Start

```bash
# Validate scenario configuration
python scripts/validate_scenario.py scenarios/basic/S001_geofence_basic.jsonc

# Run LLM validation (requires API key)
export GEMINI_API_KEY="your-api-key-here"
python scripts/run_scenario_llm_validator.py \
  scenarios/basic/S001_geofence_basic.jsonc \
  --ground-truth ground_truth/S001_violations.json \
  --output reports/S001_LLM_VALIDATION.json \
  --model gemini-2.5-flash \
  --api-key "$GEMINI_API_KEY"

# Detect violations from trajectory
python scripts/detect_violations.py test_logs/trajectory.json -g ground_truth/S001_violations.json
```

See complete guide in [`docs/QUICKSTART.md`](docs/QUICKSTART.md)

## Project Structure

```
AirSim-RuleBench/
├── scenarios/                    # Test scenarios (49 total)
│   ├── basic/                   # Layer 1: Basic Rule Execution (S001-S020)
│   ├── intermediate/            # Layer 2A: Complex Reasoning (S021-S030)
│   ├── advanced/                # Layer 2B: Stress Testing (S031-S040)
│   └── operational/             # Layer 3: Operational Planning (S041-S049)
├── ground_truth/                # Ground truth annotations (49 files, bilingual)
├── reports/                     # LLM validation reports (49 files, English)
├── scripts/                     # Validation and execution tools
│   ├── run_scenario_llm_validator.py  # Main LLM validator
│   └── llm_prompts/            # Modular prompt builders
├── docs/                        # Documentation and test guides (English)
├── templates/                   # Reusable templates
└── test_logs/                   # Execution logs
```

**Language Distribution:** Documentation and code are in English. Ground truth files contain bilingual test descriptions with Chinese regulation citations preserved for accuracy (see [Language Note](#language-note--语言说明)).

## Four-Layer Architecture

### Layer 1: Basic Rule Execution (S001-S020)

**Target Accuracy: 90-100%**

Tests fundamental capabilities: geometric calculations, single-rule compliance, deterministic logic.

#### Spatial Constraints (S001-S008)

| Scenario | Rule                  | Status    | Validation |
| -------- | --------------------- | --------- | ---------- |
| S001     | Geofence Basic        | Completed | Available  |
| S002     | Multi-Geofence        | Completed | Available  |
| S003     | Path Crossing         | Completed | Available  |
| S004     | Airport Zones         | Completed | Available  |
| S005     | Dynamic TFR           | Completed | Available  |
| S006     | Altitude Limit (120m) | Completed | Available  |
| S007     | Zone Altitude Limits  | Completed | Available  |
| S008     | Structure Waiver      | Completed | Available  |

#### Motion & Time Parameters (S009-S012)

| Scenario | Rule                          | Status    | Validation |
| -------- | ----------------------------- | --------- | ---------- |
| S009     | Global Speed Limit (100 km/h) | Completed | Available  |
| S010     | Zone Speed Limits             | Completed | Available  |
| S011     | Night Flight                  | Completed | Available  |
| S012     | Time Window Limits            | Completed | Available  |

#### Line-of-Sight & Avoidance (S013-S016)

| Scenario | Rule                                    | Status    | LLM Accuracy |
| -------- | --------------------------------------- | --------- | ------------ |
| S013     | VLOS Requirement                        | Completed | 5/5 (100%)   |
| S014     | BVLOS Waiver                            | Completed | 6/6 (100%)   |
| S015     | Dynamic NFZ Avoidance (Pre-flight)      | Completed | 6/6 (100%)   |
| S016     | Realtime Obstacle Avoidance (In-flight) | Completed | 6/6 (100%)   |

#### Payload & Approval (S017-S020)

| Scenario | Rule                          | Status    | LLM Accuracy |
| -------- | ----------------------------- | --------- | ------------ |
| S017     | Payload and Drop Restrictions | Completed | 8/8 (100%)   |
| S018     | Multi-Drone Coordination      | Completed | 8/8 (100%)   |
| S019     | Airspace Classification       | Completed | 5/5 (100%)   |
| S020     | Approval Timeline             | Completed | 4/4 (100%)   |

**Layer 1 Summary:** 20 scenarios, 63/63 test cases passed with LLM validation (100% accuracy on S013-S020)

### Layer 2A: Complex Reasoning Challenges (S021-S030)

**Target Accuracy: 60-80%**

Tests multi-rule conflicts, dynamic updates, ethical dilemmas, and regulation lifecycle management.

| Scenario | Focus                     | Status    | Validation |
| -------- | ------------------------- | --------- | ---------- |
| S021     | Emergency Battery Dilemma | Completed | Available  |
| S022     | Rule Conflict Priority    | Completed | Available  |
| S023     | Regulation Update         | Completed | Available  |
| S024     | Conflicting Sources       | Completed | Available  |
| S025     | Regulation Lifecycle      | Completed | Available  |
| S026     | Ethical Trilemma          | Completed | Available  |
| S027     | Business vs Safety        | Completed | Available  |
| S028     | Dynamic Priority          | Completed | Available  |
| S029     | Phased Conditional        | Completed | Available  |
| S030     | Dynamic UTM               | Completed | Available  |

**Layer 2A Summary:** 10 scenarios testing rule interactions, source conflicts, and ethical reasoning

### Layer 2B: Stress Testing & Adversarial (S031-S040)

**Target Accuracy: 20-50%**

Tests pragmatic ambiguity, loophole exploitation, epistemic uncertainty, and adversarial manipulation.

| Scenario | Focus                                 | Status    | Validation |
| -------- | ------------------------------------- | --------- | ---------- |
| S031     | Semantic & Ethical Dependency Cascade | Completed | Available  |
| S032     | Pragmatic Ambiguity                   | Completed | Available  |
| S033     | Dynamic Priority Cascade              | Completed | Available  |
| S034     | Pragmatic Intent                      | Completed | Available  |
| S035     | Authority Manipulation                | Completed | Available  |
| S036     | Boundary Probing                      | Completed | Available  |
| S037     | Implicit Priority                     | Completed | Available  |
| S038     | Causal Temporal Reasoning             | Completed | Available  |
| S039     | Epistemic Conflict                    | Completed | Available  |
| S040     | Adversarial Loopholes                 | Completed | Available  |

**Layer 2B Summary:** 10 scenarios testing LLM robustness under ambiguous, adversarial, and edge-case conditions

### Layer 3: Operational Planning & Resource Allocation (S041-S049)

**Target Accuracy: 40-75%**

Tests real-world operational decision-making: fleet sizing, resource allocation, multi-stakeholder coordination, and emergency response planning under uncertainty.

| Scenario | Focus                                       | Status    | LLM Accuracy |
| -------- | ------------------------------------------- | --------- | ------------ |
| S041     | Fleet Sizing vs Demand Spill                | Completed | 6/8 (75%)    |
| S042     | Fast vs Slow Charging Strategy              | Completed | 6/8 (75%)    |
| S043     | Peak-Valley Dynamic Repositioning           | Completed | 5/8 (62.5%)  |
| S044     | Battery Emergency In-Flight Decision        | Completed | 6/8 (75%)    |
| S045     | Airspace Conflict Resolution (20 Drones)    | Completed | 5/8 (62.5%)  |
| S046     | Vertiport Capacity Management               | Completed | 5/8 (62.5%)  |
| S047     | Multi-Operator Fairness & Governance        | Completed | 5/8 (62.5%)  |
| S048     | Emergency Evacuation & Re-Planning          | Completed | 4/10 (40%)   |
| S049     | Capital Allocation: Fleet vs Infrastructure | Completed | 4/10 (40%)   |

**Layer 3 Summary:** 9 scenarios testing operational planning, resource optimization, and multi-constraint decision-making in realistic UAM deployment contexts

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

| Script                            | Function                          | Usage |
| --------------------------------- | --------------------------------- | ----- |
| `run_scenario_llm_validator.py` | LLM compliance validation         | Local |
| `validate_scenario.py`          | Scenario configuration validation | Local |
| `detect_violations.py`          | Trajectory violation detection    | Local |

### Scenario Execution Scripts (Server)

| Script                       | Applicable Scenarios | Purpose                    |
| ---------------------------- | -------------------- | -------------------------- |
| `run_scenario.py`          | S001-S008            | Basic spatial constraints  |
| `run_scenario_motion.py`   | S009-S012            | Motion parameters          |
| `run_scenario_vlos.py`     | S013-S014            | Line-of-sight requirements |
| `run_scenario_path.py`     | S015-S016            | Dynamic avoidance          |
| `run_scenario_payload.py`  | S017                 | Payload restrictions       |
| `run_scenario_multi.py`    | S018                 | Multi-drone coordination   |
| `run_scenario_airspace.py` | S019                 | Airspace classification    |
| `run_scenario_timeline.py` | S020                 | Approval timelines         |

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
export GEMINI_API_KEY="your-api-key-here"
python scripts/run_scenario_llm_validator.py \
  scenarios/basic/S0XX.jsonc \
  --ground-truth ground_truth/S0XX_violations.json \
  --output reports/S0XX_LLM_VALIDATION.json \
  --model gemini-2.5-flash \
  --api-key "$GEMINI_API_KEY"
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

**Last Updated:** 2025-11-13

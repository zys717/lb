# LAE-GPT

An automated low-altitude dispatch agent that turns mission requests into compliant Go/No-Go decisions, powered by 49 curated scenarios, ground truth labels, and physics tools.

## What is LAE-GPT

- Automated dispatcher: evaluates flights under regulatory and operational constraints, outputs decision + rationale.
- Tool-augmented: uses AirSim-based scripts for physics checks (trajectory, altitude, speed, VLOS/BVLOS, payload, airspace, timelines, multi-drone).
- Case-backed: the 49 scenarios now serve as LAE-Bench (case library + validation set) for regression.
- Bilingual assets: code/docs in English; scenarios and ground truth include English/Chinese for regulatory fidelity.

## Repository Map

```
scenarios/             # 49 cases across basic/intermediate/advanced/operational
ground_truth/          # Expected decisions + evidence (bilingual)
reports/               # LLM validation outputs (S001–S049) and current RAG reports
reports_former20rag/   # Archived RAG reports for S001–S020 snapshot
scripts/               # Physics/oracle tools and LLM validator
  ├─ run_scenario_llm_validator.py
  ├─ detect_violations.py
  ├─ run_scenario_*.py (altitude/speed/vlos/path/payload/multi/airspace/timeline)
  └─ llm_prompts/
rag/                   # RAG code split by scenario ranges
  ├─ rag_S001-S020/    # Baseline snapshot + scripts/outputs for S001–S020
  ├─ rag_S021-S049/    # Workspace for S021–S049 experiments
  └─ rag_S041-S049/    # Workspace for S041–S049 experiments (tail cases)
docs/                  # Quickstart, guides, architecture notes
templates/             # Scenario + ground truth templates
test_logs/             # Sample trajectories
```

## Quick Start (Baseline / Validation)

```bash
# 1) Validate a scenario config
python scripts/validate_scenario.py scenarios/basic/S001_geofence_basic.jsonc

# 2) Run LLM validation against ground truth (requires GEMINI_API_KEY)
export GEMINI_API_KEY="your-api-key-here"
python scripts/run_scenario_llm_validator.py \
  scenarios/basic/S001_geofence_basic.jsonc \
  --ground-truth ground_truth/S001_violations.json \
  --output reports/S001_LLM_VALIDATION.json \
  --model gemini-2.5-flash \
  --api-key "$GEMINI_API_KEY"

# 3) Detect violations from a trajectory log (rule-engine check)
python scripts/detect_violations.py test_logs/trajectory.json -g ground_truth/S001_violations.json
```

See `docs/QUICKSTART.md` for details.

## Dispatch Pipeline (current framing)

1. Mission request intake -> extract constraints (regulatory + SOP). RAG design is TBD; current demos can use scenario configs as structured inputs.
2. Tool calls -> AirSim-based scripts to simulate/validate trajectory, altitude, speed, VLOS/BVLOS waiver logic, payload limits, airspace class, and approval timelines.
3. Decision engine -> produce one of the decision labels plus rationale and evidence snippets.
4. Audit log -> persist decision, inputs, tool outputs, and cited constraints for traceability.

## Decision Labels

- `APPROVE`: fully compliant, mission authorized.
- `REJECT`: clear violation, mission denied.
- `CONDITIONAL_APPROVE`: allowed with extra requirements/mitigations.
- `UNCERTAIN`: insufficient info; request clarification.
- `EXPLAIN_ONLY`: informational response without authorization.

## Creating New Scenarios

1. Copy templates: `templates/scene_config_template.jsonc` to `scenarios/...` and `templates/ground_truth_template.json` to `ground_truth/...`.
2. Define mission context, constraints, and test cases; fill expected decisions/evidence in ground truth.
3. Validate config: `python scripts/validate_scenario.py <scenario_path>`.
4. Run LLM validation: `python scripts/run_scenario_llm_validator.py ...` to generate a report.
5. (Optional) Add a test guide in `docs/` for the new scenario.

## Documents

- `docs/QUICKSTART.md`: fast start for validation.
- `LAE-GPT_Three_Layer_Architecture.md`: legacy architecture (constraint taxonomy reference).
- `PROJECT_WORKFLOW_GUIDE.md`: development workflow.
- `regulations_reference.md`: regulation citations and sources.

## Status & Roadmap

- Completed:
  - 49-case library with ground truth, physics/oracle scripts, baseline LLM validation reports.
  - RAG pipeline for S001–S020 with scenario-specific pre-checks (speed/altitude/geo/path/time-window/VLOS-BVLOS/payload/drop/airspace/timeline/multi-drone). Snapshot archived at `rag/rag_S001-S020/`; reports at `reports_former20rag/`.
- Completed (RAG):
  - S001–S020 baseline snapshot (`rag/rag_S001-S020/`, reports in `reports_former20rag/`).
  - S021–S049 RAG runs finished in `rag/rag_S021-S049/` with reports in `reports/`.
- Notes:
  - Keep `rag/rag_S001-S020/` untouched as regression baseline.
  - New prompt/rule iterations for S021–S049 live under `rag/rag_S021-S049/`.

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
regulations/           # Source regulations/SOPs (PDF/Markdown) used by extract_constraints.py
rag/                   # RAG code split by scenario ranges
  ├─ rag_S001-S020/    # Baseline snapshot + scripts/outputs for S001–S020
  ├─ rag_S021-S049/    # Workspace for S021–S049 experiments
  └─ rag_S041-S049/    # Workspace for S041–S049 experiments (tail cases)
docs/                  # Quickstart, guides, architecture notes
templates/             # Scenario + ground truth templates
test_logs/             # Sample trajectories
```

## Prerequisites / Installation
- Python 3.9+ (shims included for py3.9 importlib.metadata).
- Install LLM SDK if you plan to call models:
  ```bash
  pip install google-generativeai
  ```
- Set API key for LLM runs:
  ```bash
  export GEMINI_API_KEY="your-api-key-here"
  ```
- Ensure `regulations/` is present (PDF/Markdown) for constraint extraction.

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
- Completed (RAG and baselines):
  - S001–S020 baseline snapshot (`rag/rag_S001-S020/`, reports in `reports_former20rag/`).
  - S021–S049 experimental RAG+ (`rag/rag_S021-S049/`) with reports now named `reports/S0xx_RAG_REPORT.json`.
  - S021–S049 rules-baseline (hardcoded prompt/logic) kept at `rag/rag_S021-S049_rules_baseline/`; reports renamed to `reports/S0xx_RULE_BASELINE.json`.
- Notes:
  - Keep `rag/rag_S001-S020/` untouched as regression baseline.
  - New prompt/rule iterations for S021–S049 live under `rag/rag_S021-S049/`; rules baseline retained separately for comparison.

## Experiments & Reports

- No-RAG baseline (LLM only)  
  - Location: `reports/S0xx_LLM_VALIDATION.json`  
  - Purpose: pure model reference without retrieval/rules.

- Rules-baseline (hardcoded prompt/logic)  
  - Code: `rag/rag_S021-S049_rules_baseline/`  
  - Reports: `reports/S0xx_RULE_BASELINE.json`  
  - Description: per-scenario switch-case prompt+rules; minimal retrieval; used as the most stable fallback.
  - Run example:  
    ```
    python3 rag/rag_S021-S049_rules_baseline/run_rag_batch_light.py \
      --scenarios S021-S049 \
      --output-dir reports \
      --model gemini-2.5-flash \
      --api-key <KEY>
    ```

- RAG+ experimental (current dev line)  
  - Code: `rag/rag_S021-S049/`, rules in `rag/guidelines/guidelines.jsonl`  
  - Reports: `reports/S0xx_RAG_REPORT.json`  
  - Description: templates still routed by scenario type; decision rules externalized to guidelines + keyword retrieval. Sensitive scenarios (e.g., S021/S028/S029/S030) have scoped retrieval/guards to preserve accuracy.  
  - Run example:  
    ```
    python3 rag/rag_S021-S049/run_rag_batch_light.py \
      --scenarios S021-S049 \
      --output-dir reports \
      --model gemini-2.5-flash \
      --api-key <KEY>
    ```

- Naming convention  
  - LLM-only: `S0xx_LLM_VALIDATION.json`  
  - Rules baseline: `S0xx_RULE_BASELINE.json`  
  - RAG+ experimental: `S0xx_RAG_REPORT.json`

- Usage guidance  
  - Keep all three for comparison: LLM (no retrieval), RULE_BASELINE (hard rules), RAG_REPORT (retrieval+rules).  
  - For highest stability, refer to RULE_BASELINE; for retrieval effects, use RAG_REPORT; LLM is the pure model control.  
  - Key scenarios (e.g., S021/S028/S029/S030) in RAG_REPORT include tightened retrieval or post-guards to avoid regressions.

## The LAE-Bench Dataset
- Composition: 49 scenarios spanning **basic**, **intermediate**, **advanced**, and **operational** layers.  
  - Basic (S001–S020): geofence, altitude/speed/VLOS-BVLOS, payload, airspace class, timelines; includes physics/oracle checks.  
  - Intermediate/Advanced (S021–S040): priority, ethical trade-offs, ambiguity/intent, authority/adversarial/boundary probing.  
  - Operational (S041–S049): fleet sizing, charging, repositioning, evacuation, fairness, capital allocation.
- Assets: scenario JSONC configs, ground-truth decisions/evidence, LLM validation reports (no-RAG), rules baselines, and RAG+ reports.
- Evaluation value: regression-friendly benchmark from physical constraints to regulatory/operational trade-offs; used to measure gains of rules baselines and RAG over pure LLM.

## RAG design (S021–S049, experimental line)
- Prompt routing: still by scenario type/ID to the corresponding prompt builder (battery/priority/fairness/finance/evacuation, etc.) to ensure structured inputs.
- Rules externalized: decision rules in `rag/guidelines/guidelines.jsonl` with `text`, `keywords`, and optional `structured_assertions` (thresholds/units).
- Retrieval: keyword matching, preferring same-scenario tags; sensitive scenarios (e.g., S021/S028/S029/S030) only inject whitelisted rules or disable noisy ones.
- Composition: baseline `extra_rule` always included; retrieved rules are appended (not mutually exclusive) to avoid information dilution.
- Post-processing: minimal, scenario-specific guards only (e.g., S021 ban on invented alternatives; S029 skip/reverse-phase correction) to avoid broad rewrites.
- Constraints: `rag/rag_S021-S049/outputs/constraints_by_scenario.json` generated by `extract_constraints.py`.

## Results snapshot
- RAG+ (latest) accuracy by block (vs ground truth):
  - S001–S020: 100% (114/114, rules baseline, unchanged)
  - S021–S030: ~80–88% (after tighter retrieval; most at parity with rules baseline, remaining weak cases iterating)
  - S031–S040: ~79–90% (a few intent/boundary/adversarial cases still improving)
  - S041–S049: ~99% (ops/fairness/finance/evacuation near perfect)
- Rules baseline: per-scenario hardcoded prompts/rules; generally stable; used to judge whether RAG+ brings gains or holds parity.
- LLM validation: pure model control without retrieval/rules; measures net gain from baselines/RAG.

## Notes on usage
- Keep all three report sets:
  - LLM-only: `S0xx_LLM_VALIDATION.json`
  - Rules baseline: `S0xx_RULE_BASELINE.json`
  - RAG+: `S0xx_RAG_REPORT.json`
- For highest stability use RULE_BASELINE; for retrieval effects use RAG_REPORT; for raw model performance use LLM_VALIDATION.

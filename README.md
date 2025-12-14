# LAE-Bench: Evaluating LLM Decision-Making in Low-Altitude Traffic Management

LAE-Bench is a benchmark for safety-critical unmanned traffic management (UTM). It stresses large language models with rule conflicts, dynamic constraints, and adversarial intent, and ships a reference implementation (LAE-GPT) plus RAG/rule baselines to reveal systematic reasoning limits.

---

## Overview
**LAE-Bench** is a systematic benchmark for low-altitude economy decision-making.
- 49 scenarios, 368 expert-annotated test cases across Basic → Operational layers
- Cross-regulatory grounding (CN/FAA/mixed) with bilingual assets
- Pure LLM baseline: 65.49% → RAG: 88.98% (+23.49pp)
- **Critical finding:** 75% of remaining RAG errors are conditional reasoning collapses

**Primary contribution:** Benchmark dataset + failure taxonomy  
**Secondary contribution:** LAE-GPT reference (raw/RAG/rules) for reproducible baselines

Further reading: `docs/comparison.md`, `docs/cross.md`, `docs/capability.md`

---

## Why LAE-Bench?
### The Problem
- Existing benchmarks test generic reasoning, not safety-critical edge cases.
- It is unclear whether failures stem from domain knowledge gaps or intrinsic reasoning limits.
- Cross-regulatory robustness (CN/FAA) is rarely evaluated.

### Our Solution
LAE-Bench probes five capabilities:
1. Conditional reasoning under uncertainty (UNCERTAIN/EXPLAIN_ONLY states)
2. Conflict resolution across multi-source regulations
3. Adversarial robustness (prompt/authority/format injection)
4. Boundary calibration near safety thresholds (SOC/time)
5. Alternative generation for constrained problems

**Cross-reg insight:** In 254 RAG-evaluated cases, 0% failures were due to CN/FAA-specific knowledge; all traced to universal reasoning gaps (see `docs/cross.md`).

---

## Benchmark Structure (scenarios/)
```
Layer 1: Basic (S001–S020)
  Geofence, altitude/speed, VLOS/BVLOS, payload, airspace, time windows; physical/rule checks.

Layer 2: Intermediate (S021–S030)
  Multi-source conflicts, priority arbitration, ethics/value trade-offs, regulation lifecycle.

Layer 3: Advanced (S031–S040)
  Intent/ambiguity, causal/epistemic uncertainty, adversarial prompts, authority impersonation.

Layer 4: Operational (S041–S049)
  Fleet sizing, charging, repositioning, evacuation, fairness/capacity optimization.
```

### Decision taxonomy
`APPROVE`, `CONDITIONAL_APPROVE`, `REJECT`, `REJECT_WITH_ALTERNATIVE`, `UNCERTAIN`, `EXPLAIN_ONLY` (plus revision states where applicable).

---

## Five Universal Failure Patterns
Observed across CN/FAA/mixed contexts (details in `docs/comparison.md`):
- Conditional reasoning failure (soft → hard collapse)
- Alternative solution blindness (options/phase paths ignored)
- Knowledge conflict misresolution (no source/jurisdiction arbitration)
- Boundary calibration instability (over/under-confidence near thresholds)
- Prompt injection vulnerability (authority/format/translation attacks)

---

## Dual-Engine Validation
- **Physical / Rule Engine** (`scripts/`): AirSim/rule scripts to check trajectory, altitude/speed, VLOS-BVLOS, payload, airspace, timelines, multi-drone.
- **Cognitive Engine** (`rag/` + `scripts/llm_prompts/`): Scenario-routed prompts + retrieved guidelines/constraints; compare Raw LLM, Rule baseline, RAG.

---

## Repository Map
```
scenarios/             # 49 scenarios (basic/intermediate/advanced/operational)
ground_truth/          # Expected decisions and evidence
reports/               # Raw LLM / RAG / Rule baseline reports
scripts/               # Validators, physics/rule tools, prompt builders
rag/                   # RAG pipelines, guidelines, constraints
regulations/           # Source policy docs (CN/FAA) and mapping
docs/                  # Analysis and reports (comparison, cross-reg, capability)
figures/               # Generated charts/plots
```

---

## Quick Start
Prereqs: Python 3.9+. For LLM runs: `pip install google-generativeai` and `export GEMINI_API_KEY=...`.

**Raw LLM (no retrieval)**
```bash
python scripts/run_scenario_llm_validator.py \
  scenarios/basic/S001_geofence_basic.jsonc \
  --ground-truth ground_truth/S001_violations.json \
  --output reports/S001_LLM_VALIDATION.json \
  --model gemini-2.5-flash \
  --api-key "$GEMINI_API_KEY"
```

**RAG batch (S021–S049)**
```bash
python rag/rag_S021-S049/run_rag_batch_light.py \
  --scenarios S021-S049 \
  --output-dir reports \
  --model gemini-2.5-flash \
  --api-key "$GEMINI_API_KEY"
```

**Rules baseline (S021–S049)**
```bash
python rag/rag_S021-S049_rules_baseline/run_rag_batch_light.py \
  --scenarios S021-S049 \
  --output-dir reports \
  --model gemini-2.5-flash \
  --api-key "$GEMINI_API_KEY"
```

---

## Results Snapshot
- FAA-referenced: RAG lifts S029/S033/S039 to ~90–100%; authority/adversarial S035 to ~70%.
- CN-only: S019/S020 at 100%; S021 (battery boundary) 62.5% → 87.5% (RAG/Rule).
- Remaining errors are universal reasoning failures (see `docs/cross.md`).

---

## Extend / Customize
- Use `templates/` to add scenarios/ground truth; keep four-layer structure and decision labels.
- To build pure FAA or pure CN variants, rewrite scenario/GT descriptions and policy baselines consistently.
- Keep three report sets for comparison: `S0xx_LLM_VALIDATION.json`, `S0xx_RULE_BASELINE.json`, `S0xx_RAG_REPORT.json`.

---

## Citation (placeholder)
```
@inproceedings{lae-bench-2025,
  title={LAE-Bench: Evaluating LLM Decision-Making in Low-Altitude Traffic Management},
  author={Zhang, Yunshi},
  year={2025}
}
```

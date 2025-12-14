# LAE-Bench: LLM Decision-Making in Low-Altitude Traffic Management

LAE-Bench is a benchmark for safety-critical low-altitude economy (LAE) scenarios. It evaluates how large language models handle rule conflicts, dynamic constraints, and adversarial intent, and ships a full pipeline that combines physical/rule engines with RAG-based cognitive checks.

## 1. What & Why
- **Goal:** Surface cognitive failure modes of LLMs in unmanned traffic management (UTM), not just “auto-approve flights.”
- **Data:** 49 scenarios grounded in real CN/US regulations and ministry cases, covering the spectrum from hard constraints to operational/fairness trade-offs.
- **Finding:** RAG sharply reduces routine errors, but remaining failures cluster into five universal patterns (conditional reasoning, alternative generation, conflict arbitration, boundary uncertainty, prompt injection) that are domain-agnostic.

## 2. Benchmark Layout (scenarios/)
- **Basic (S001–S020):** Geofence, altitude/speed, VLOS/BVLOS, payload, airspace class, time windows; physical/rule scripts included.
- **Intermediate (S021–S030):** Multi-source conflicts, dynamic priorities, ethics/value trade-offs, regulation updates/effective dates.
- **Advanced (S031–S040):** Intent/ambiguity, causal/uncertainty reasoning, adversarial/impersonation/prompt-injection.
- **Operational (S041–S049):** Fleet sizing, charging, repositioning, evacuation, fairness and capacity optimization.

## 3. Dual-Engine Validation
- **Physical / Rule Engine** (scripts/): AirSim/rule scripts to validate trajectory, altitude/speed, VLOS-BVLOS, payload, airspace, timeline, multi-drone.
- **Cognitive Engine** (rag/ + scripts/llm_prompts/): Scenario-routed prompts + retrieved guidelines/constraints; compare Raw LLM, Rules baseline, and RAG variants.

## 4. Failure Taxonomy (cross-regulatory)
Universal failure modes observed across CN/FAA/mixed cases:
1) Conditional reasoning failure — soft states (UNCERTAIN/EXPLAIN_ONLY/CONDITIONAL_APPROVE) collapse to hard REJECT.
2) Solution generation deficit — alternatives/phased paths never enter the decision chain.
3) Knowledge conflict misresolution — no principled arbitration for multi-source/version clashes.
4) Epistemic uncertainty miscalibration — over-/under-confidence near numeric thresholds (SOC/time).
5) Prompt injection vulnerability — authority/format/translation attacks disrupt structured output.

## 5. Repository Map
```
scenarios/             # 49 scenarios (basic/intermediate/advanced/operational)
ground_truth/          # Expected decisions and evidence
reports/               # Raw LLM / RAG / Rule baseline reports
scripts/               # Physical/rule tools + LLM validator + prompt builders
rag/                   # RAG pipeline, guidelines, constraints
regulations/           # Source regulations/SOPs (PDF/Markdown)
docs/                  # Quickstart, guides, notes
```

## 6. Quick Start
Prereq: Python 3.9+. For LLM runs, install SDK and set API key.
```bash
pip install google-generativeai
export GEMINI_API_KEY="your-key"
```
- **Raw LLM (no retrieval)**
```bash
python scripts/run_scenario_llm_validator.py \
  scenarios/basic/S001_geofence_basic.jsonc \
  --ground-truth ground_truth/S001_violations.json \
  --output reports/S001_LLM_VALIDATION.json \
  --model gemini-2.5-flash \
  --api-key "$GEMINI_API_KEY"
```
- **RAG batch (S021–S049)**
```bash
python rag/rag_S021-S049/run_rag_batch_light.py \
  --scenarios S021-S049 \
  --output-dir reports \
  --model gemini-2.5-flash \
  --api-key "$GEMINI_API_KEY"
```
- **Rules baseline (S021–S049)**
```bash
python rag/rag_S021-S049_rules_baseline/run_rag_batch_light.py \
  --scenarios S021-S049 \
  --output-dir reports \
  --model gemini-2.5-flash \
  --api-key "$GEMINI_API_KEY"
```

## 7. Results Snapshot
- **FAA-referenced scenarios:** RAG lifts S029/S033/S039 to ~90–100%; authority/adversarial S035 to ~70% (still weak).
- **CN-only scenarios:** S019/S020 at 100%; battery-boundary S021 improves from 62.5% (Raw) to 87.5% (RAG/Rule).
- **Cross-reg insight:** Remaining errors are all universal reasoning failures; see `Cross-Regulatory Failure Analysis.md`.

## 8. Extend / Customize
- Use `templates/` to add scenarios/ground truth; keep four-layer structure and decision labels.
- To build pure FAA or pure CN variants, rewrite scenario/GT descriptions and policy baselines consistently with the target regulator.

## 9. Citation (placeholder)
```
@inproceedings{lae-bench-2025,
  title={LAE-Bench: A Benchmark for LLM Decision-Making in Low-Altitude Traffic Management},
  author={Zhang, Yunshi},
  year={2025}
}
```

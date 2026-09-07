# Main four-model benchmark

The main study contains 368 cases in 49 scenario clusters: 114 Layer 1 cases, 78 Layer 2 cases, 100 Layer 3 cases, and 76 Layer 4 cases. All cases receive RAW evaluation. The 254 cases in Layers 2–4 also receive RAG_REVISED evaluation, giving 622 positions per model and 2,488 scored positions across four models.

## Retained material

| File or directory | Contents |
| --- | --- |
| `complex_cases.json` | The frozen 254-case complex-task record used for annotation and prompt construction, including scenario context, task, and allowed outcomes. |
| `prompts_raw.jsonl` | The 254 RAW records selected from the earlier six-condition input package. The other five conditions were not used in the current main panel. |
| `prompts_rag_revised.jsonl` | The 254 supported-input records used for the current panel. Their original condition name, `RAG_REVISED_FULL`, is retained here. |
| `layer1/scenarios/` | The 20 Layer 1 scenario definitions. |
| `layer1/references/` | The Layer 1 source references used by the construction procedure. |
| `layer1/historical_facts/` | The S005 and S020 facts selected by the original construction procedure. Reconstruction reads these files directly, without requiring Git history. |
| `layer1/generated/` | The 114 reconstructed Layer 1 prompts and their reference records. |
| `results/` | The saved per-case scores, reference summary, model and analysis settings, task and layer results, and sensitivity analyses used in the manuscript. |

Prompt text in the two retained complex-case input files is unchanged. Non-inference checksum fields were omitted during directory cleanup. The construction script normalizes the supported condition name to `RAG_REVISED` when forming the combined panel input. Labels and coordinator rationales remain separate from the prompt text supplied to models.

The original generated Layer 1 and full-panel input files have not been recovered. Running `python3 scripts/build_main_prompts.py` from the repository root reconstructs the 114 Layer 1 inputs and the combined 622-position package using the retained construction procedure. Reconstructed files are identified as such; they are not presented as recovered original run files.

## References and analysis

Independent A1/A2 annotations, the 91 coordinator-reviewed disagreements, and the 254 final complex-case references are in [../annotations](../annotations/README.md). The reference summary in `results/reference_labels.csv` combines those outcomes with the 114 Layer 1 references.

All 368 cases are retained. Main exact-outcome scoring excludes three procedural-explanation cases from each complex-task condition, leaving 251 paired cases per model. Task-specific results are primary. Small option-selection and retrospective-compliance groups are retained for descriptive reporting.

`python3 scripts/analyze_main_results.py --check` recalculates the manuscript statistics from `results/case_results.csv` and compares them with the saved tables. Task confidence intervals use 10,000 scenario-cluster bootstrap draws and NumPy `default_rng(20260812)`, reinitialized within each task and model. Earlier layer-level intervals used Python's random generator; the task analysis retains the later procedure used for the reported task intervals.

The main experiment's full original and final response texts are not currently included. `case_results.csv` retains predictions, references, scoring, and response-selection information, allowing the reported numerical analyses to be checked. It cannot substitute for full response texts when examining model reasoning or reconstructing the complete response-recovery process.

# Main four-model benchmark

The main study contains 368 cases in 49 scenario clusters: 114 Layer 1 cases, 78 Layer 2 cases, 100 Layer 3 cases, and 76 Layer 4 cases. All cases receive RAW evaluation. The 254 cases in Layers 2–4 also receive RAG_REVISED evaluation, giving 622 positions per model and 2,488 scored positions across four models.

## Files

| File or directory | Contents |
| --- | --- |
| `complex_cases.json` | The 254-case complex-task record used for annotation and prompt construction, including scenario context, task, and allowed outcomes. |
| `prompts_raw.jsonl` | The 254 RAW input records. |
| `prompts_rag_revised.jsonl` | The 254 supported-input records, with the condition name `RAG_REVISED_FULL`. |
| `layer1/scenarios/` | The 20 Layer 1 scenario definitions. |
| `layer1/references/` | The Layer 1 source references used by the construction procedure. |
| `layer1/historical_facts/` | The S005 and S020 source facts used for input construction. |
| `layer1/generated/` | The 114 reconstructed Layer 1 prompts and their reference records. |
| `results/` | The per-case scores, reference summary, model and analysis settings, task and layer results, and sensitivity analyses used in the manuscript. |

The construction script maps the supported condition name to `RAG_REVISED` in the combined panel input. Reference outcomes and coordinator rationales are excluded from the prompt text supplied to models.

Running `python3 scripts/build_main_prompts.py` from the repository root reconstructs the 114 Layer 1 inputs and the combined 622-position package from the supplied construction procedure. The combined file is named `prompts_main_reconstructed.jsonl`.

## References and analysis

Independent A1/A2 annotations, the 91 coordinator-reviewed disagreements, and the 254 final complex-case references are in [../annotations](../annotations/README.md). The reference summary in `results/reference_labels.csv` combines those outcomes with the 114 Layer 1 references.

The dataset contains 368 cases. Main exact-outcome scoring excludes three procedural-explanation cases from each complex-task condition, leaving 251 paired cases per model. Task-specific results are primary. The small option-selection and retrospective-compliance groups are reported descriptively.

`python3 scripts/analyze_main_results.py --check` recalculates the manuscript statistics from `results/case_results.csv` and compares them with the saved tables. Task paired-gain confidence intervals use 10,000 scenario-cluster bootstrap draws and NumPy `default_rng(20260812)`, reinitialized within each task and model.

`case_results.csv` provides the predictions, references, scoring, and response-selection information used for these analyses.

# LAE-Bench

LAE-Bench evaluates language-model decisions in low-altitude traffic management, including pre-flight authorization, in-flight contingency actions, and resource or policy decisions. This repository contains the materials used for the revised manuscript's four-model study, a separate civil-aviation diagnostic, and a later check of decisions reconstructed from official records.

## Study materials

| Evaluation | Cases | Conditions and records |
| --- | ---: | --- |
| Main benchmark, Layer 1 | 114 in 20 clusters | RAW; explicit constraints |
| Main benchmark, Layers 2–4 | 254 in 29 clusters | Paired RAW and RAG_REVISED |
| Civil-aviation diagnostic | 180 in 15 scenarios | Qwen3.8; 175/180 reference agreement (97.2%)|
| Official-record case check | 8 | 64 responses and 32 paired coding records |

The main panel comprises Qwen3.8, GLM-5.2, DeepSeek-V4-Flash, and Muse-Glimmer. Each model has 622 case-condition positions, giving 2,488 scored positions. Exact model identifiers and initial decoding settings are in [model_settings.json](data/main/results/model_settings.json).

The 23 published operating cases supplied settings and management problems for 49 constructed clusters and 368 benchmark cases. The [source-to-scenario mapping](<regulations/23-49 Mapping.md>) distinguishes reported operating facts from author-defined test conditions and extensions to other settings.

RAG_REVISED combines selected benchmark records, outcome definitions, prerequisites, and numerical and temporal checks. It was developed after early analysis of the same corpus. The paired comparison evaluates that complete support package; production retrieval is outside the experiment's scope.

## Repository contents

- [data/main](data/main/README.md): frozen complex cases, saved prompts, Layer 1 source facts, reconstructed inputs, and manuscript statistics.
- [data/annotations](data/annotations/README.md): independent A1/A2 labels, annotation instructions, coordinator decisions, and final references.
- [data/civil](data/civil/README.md): the 180-item Qwen3.8 diagnostic and its cited ASRS records.
- [data/official_cases](data/official_cases/README.md): the eight official-record decisions, prompts, responses, references, and coding definitions.
- [scripts](scripts/): input construction, inference, response handling, scoring, and offline analysis.
- [regulations](regulations/): the source-to-scenario mapping and public source documents.

The local `revision/`, `paper/`, and `tmp/` workspaces are excluded from the public research package.

## Reproduce the saved results

Python 3.9 or later is required. The dependency versions in `requirements.txt` were used to check this package.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/analyze_main_results.py --check
python3 scripts/analyze_annotations.py --check
python3 scripts/build_reference_labels.py --check
python3 scripts/analyze_civil_diagnostic.py --check
python3 scripts/reproduce_case_checks.py
python3 scripts/plot_task_gains.py --output /tmp/lae-task-gains.pdf
```

These commands work offline from the retained data and do not call models. The main checks compare recomputed statistics with the saved manuscript tables. Main complex-case scoring excludes three procedural-explanation cases per model and condition, leaving 251 paired cases; the 254-case input set itself is retained. The task confidence intervals use 10,000 scenario-cluster bootstrap draws, with NumPy's random generator seeded at 20260812.

## Inputs and inference

```bash
python3 scripts/build_main_prompts.py
```

This rebuilds the 114 Layer 1 prompts from the original construction procedure, including the specified S005/S020 historical facts, and combines them with the 254 saved RAW and 254 saved supported prompts. The generated 622-position file is explicitly named `prompts_main_reconstructed.jsonl`. It is a reconstruction; the original generated Layer 1 and combined prompt files have not been recovered.

The saved complex-case prompt text is retained from the files used for the current panel. The original supported input file calls its condition `RAG_REVISED_FULL`; construction of the combined panel normalizes that condition name to `RAG_REVISED`.

The inference entry points are `run_main_evaluation.py`, `recover_main_responses.py`, and `score_main_responses.py` in `scripts/`; their `--help` output describes required inputs. New model calls require an API key and are separate from the offline checks above. Initial calls used temperature 0, low reasoning effort, and a 2,048-token output limit. Format-recovery rounds used the same prompt text with strict JSON, a 4,096-token limit in rounds 1–3 and an 8,192-token limit in rounds 4–7. Recovery selected responses by structural validity, without using reference correctness.

The main experiment's original and final full response files have not been recovered in this package. The retained `case_results.csv` contains predictions, references, scoring, and response-selection information, so the reported statistics can be recalculated; it does not contain the full response texts. The inference and recovery scripts require actual response files and do not recreate missing historical answers. Scoring a recovered run requires valid responses at every position; counting original invalid responses as incorrect requires the explicit `original_invalid_as_incorrect` mode.

The civil diagnostic retains the actual requests and original API response text in `data/civil/run.json`, parsed responses and reference labels in `data/civil/reports.json`, and input texts in `data/civil/prompts.json`. The offline check verifies the correspondence between these files and recomputes the scores. The eight-case package retains all 64 response texts and the definitions used for its 32 paired coding records.

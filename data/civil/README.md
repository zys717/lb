# Earlier civil aviation diagnostic

This is the separate, earlier 180-item diagnostic described in the paper. It contains 15 constructed scenario groups with 12 items each. The reference distribution is 174 `UNCERTAIN` and six `REJECT`; the retained reports agree with all 180 references. An always-`UNCERTAIN` baseline agrees on 174/180 items (96.7%). These results assess the supplied decision basis and do not establish broad aviation competence or differences among the four models in the main experiment.

## Files

- `scenarios.json`: the 15 existing scenario definitions, consolidated without changing their fields or text.
- `references.json`: the 15 reference files, including each item's ASRS accession number (ACN), source date, decision, and rationale. Use these decisions for scoring.
- `reports.json`: the 15 existing reports, including all 180 item-level decisions, explanations, and stored score flags.
- `asrs_sources.json`: the 180 source rows selected by the cited ACNs from the 15 existing ASRS exports. Two header rows, column order, original field values, and original CSV row numbers are retained. The 180 item positions refer to 174 distinct ACNs; some source records recur across scenario groups. An ACN ending in `.0` is normalized only when joining to an export, not rewritten in the preserved reference.
- `prompt_builder.py`: a copy of the available civil prompt-construction function. It is a source snapshot, not a captured set of historical requests. The function offers six disposition tokens and explicitly directs `UNCERTAIN` when governing information is absent.

The scenario snapshot has one stale embedded label: C004/TC9 says `UNCERTAIN`, while its reference file and retained report both say `REJECT`. The original field is preserved here; the offline check uses `references.json` and reports the discrepancy.

## Scope of reproduction

The paper attributes this diagnostic to Qwen2.5-32B-Instruct under deterministic decoding. The retained reports do not store a model name, provider, request time, temperature, or full request. Those metadata cannot be independently recovered from these reports.

The available historical validator exposes Gemini and SiliconFlow/Qwen command-line options, but its item-validation path calls the Gemini client directly. It therefore does not establish the program that generated the reported Qwen run, and is not provided here as an exact rerun recipe. The included prompt builder likewise does not establish the exact historical requests. No model has been queried while assembling this package.

From the repository root, run:

```bash
python3 scripts/reproduce_case_checks.py
```

The command checks item/source correspondence and recomputes the civil reference agreement and majority-class baseline from the preserved reports. It also checks the separate official-record case package. It performs no network access and does not regenerate model responses or change reference labels.

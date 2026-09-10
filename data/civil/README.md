# Civil aviation diagnostic

This auxiliary diagnostic contains 15 constructed scenario groups with 12 items each. Following reference review and targeted reruns, including task clarification for three items, Qwen3.8 agreement was 175/180 (97.2%), leaving five disagreements. The reference distribution is 170 `UNCERTAIN` and ten `REJECT`; an always-`UNCERTAIN` baseline agrees on 170/180 items (94.4%). These results assess the supplied decision basis and do not establish broad aviation competence or differences among the four models in the main experiment.

## Files

- `scenarios.json`: the 15 scenario definitions and their case-level expected decisions.
- `references.json`: the 15 reference files, including each item's ASRS accession number (ACN), source date, decision, and rationale. Use these decisions for scoring.
- `run.json`: the actual requests and original API response text for the 180 results, with model settings, returned model/provider, HTTP status, and completion status.
- `reports.json`: the corresponding case narratives, reference labels, parsed model responses, and score flags in 15 scenario groups.
- `prompts.json`: the 180 saved input texts, linked to reports by scenario and case ID.
- `asrs_sources.json`: the 180 source rows selected by the cited ACNs from 15 ASRS exports, including two header rows, column order, field values, and CSV row numbers. The 180 item positions refer to 174 distinct ACNs; some source records recur across scenario groups. Source matching normalizes the `.0` suffix in ACNs.
- `prompt_builder.py`: the base civil prompt-construction function. It offers six disposition tokens and explicitly directs `UNCERTAIN` when governing information is absent, with an exception for explicit violation facts. Exact inputs are in `prompts.json`.

Scoring uses `references.json`. For C004/TC9, this reference is `REJECT`, whereas the scenario's embedded expected-decision field is `UNCERTAIN`. The offline check reports this discrepancy.

## Inference and analysis

The model is `qwen/qwen3.8-2.4t-a95b`, served by SiliconFlow with FP8 quantization, temperature 0, low reasoning effort, JSON output, and a 2,048-token output limit. Settings are stored in each report's `evaluation` field; input text is stored in `prompts.json`.

From the repository root, run:

```bash
python3 scripts/analyze_civil_diagnostic.py --check
python3 scripts/reproduce_case_checks.py
```

The first command checks every saved request against the input prompt and settings, checks the report against the original API response text, and recomputes agreement against the fixed references. The second checks source correspondence and the separate official-record case package. Both run offline without regenerating responses or changing labels.

To check the inference configuration offline, run:

```bash
python3 scripts/run_civil_diagnostic.py --model qwen/qwen3.8-2.4t-a95b --upstream-provider siliconflow --quantization fp8 --reasoning-effort low --max-tokens 2048
```

New inference requires `OPENROUTER_API_KEY`, `--execute`, and a separate, nonexistent `--output` path. It uses the saved prompts and settings and writes new API records; it does not overwrite the study results.

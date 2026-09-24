# Retained-input review, 24 September 2026

This review covers the 114 reconstructed Layer 1 input positions, 254 retained RAW prompts, 254 retained RAG_REVISED prompts, all 2,488 case-score records, the 254 final complex-case references, and the annotation instructions. It makes no model calls and preserves the inputs, independent annotations, adjudications, and primary scores.

`python3 scripts/audit_revision_inputs.py --check` reproduces the audit tables from the repository root. Omit `--check` to regenerate the tables. The input hashes are recorded in `summary.json`.

## Intermediate judgments in inputs

The screen searches the case-specific input object for four named fields: `rule_applicability`, `conflict_violations`, `violations`, and `rtl_compliant`. They supply case-level rule application, compliance assessments, or violation summaries, including empty violation lists. Generic rules, task definitions, applicant claims, and raw measurements are not flagged by this field screen. This is a bounded screen of explicit structured judgments, not a claim that the remaining prose contains no cues.

The same 18 cases have these fields in both conditions: eight S023 cases, eight S045 cases, S021/TC8_TradeoffAnalysis, and S046/TC08_CascadeFailure. RAG sometimes repeats the content in evidence cards; a case is counted once. `prompt_screen.csv` records all 622 input positions, and `flagged_input_fields.csv` retains the flagged fields and their values.

The exclusion sensitivity retains 233 of the 251 scored complex cases per model and condition. The principal tasks retain 119 pre-flight cases, all 27 in-flight cases, and 75 resource/policy cases. `exclusion_sensitivity.csv` reports counts and exact-agreement differences; `exclusion_loss.csv` recomputes the existing pre-flight loss definition. All four pooled differences and all 12 principal task differences remain positive. The crossover weights range from 1.6667 to 5.75. These results describe case exclusion using the existing predictions. They do not estimate how any model would respond to cleaned prompts, and no new confidence intervals are claimed.

## Answerability and deferral

The A1 workbook, Instructions A17–A18 and Definitions A18–A20, distinguishes an unanswerable record from a substantive UNCERTAIN endpoint. The final register contains 13 UNANSWERABLE outcomes and two UNCERTAIN outcomes. `answerability_boundary.csv` reproduces all 15 references with both original outcomes and the final reasons.

S031/TC01 explicitly requires official clarification, and its scenario rule H1 prescribes UNCERTAIN when the needed timestamps are absent. S034/TC07 includes an operations memo requiring escalation of an indirect hospital request conflicting with expiring supplies. Their deferred dispositions are therefore supported by supplied instructions. The 13 UNANSWERABLE references instead identify information absent from the decision record: measurements, operating altitude, geographic scope, work-zone status, a defined request, an applicable threshold, documentary evidence, or substantive mission facts. Missing information alone does not determine which token applies; the task and any explicit deferral rule must also be considered. This clarification does not change the original annotations or final labels.

S031/TC01 also contains a narrative/metadata inconsistency: the description says the English waiver lacks a timestamp, while the selected source object has a timestamp. Its explicit instruction to request clarification supports the retained deferral, but a future cleaned input should remove this inconsistency. Clarifying the outcome definitions does not certify every underlying case fact as internally consistent.

## Source attributions and model version

See [the rule-attribution notes](../../../regulations/benchmark_rule_attribution_notes.md) for confirmed source errors and constructed assumptions in S021–S023. The notes correct their interpretation without silently replacing historical inputs. Cleaning and evaluating revised prompts remains a separate task.

The retained model registry identifies `z-ai/glm-5.2`, StreamLake, FP8, and the Z.ai weight-repository URL. The [official GLM-5.2 model card](https://huggingface.co/zai-org/GLM-5.2), checked on 24 September 2026, directly documents the version and distinguishes it from the GLM-5 technical report. The manuscript now cites that model card. Public model documentation corroborates the release identity; it does not replace a historical API transcript or establish the exact weights served in a past request.

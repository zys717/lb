# Independent annotations and reference outcomes

This directory contains the independent annotations and recorded reference formation for the 254 cases in Layers 2–4: 78 in Layer 2, 100 in Layer 3, and 76 in Layer 4. Layer 1 is outside this annotation exercise. The shared case material is stored once in data/main/complex_cases.json.

## Files

| File | Role |
|---|---|
| A1.xlsx | Readable copy of A1's completed independent workbook, preserving the Instructions, Annotation, and Definitions sheets. It is copied from the previously repaired workbook; no judgments are changed during this packaging step. |
| A2.csv | A2's completed independent annotations, copied without changes. |
| coordinator_decisions.csv | The 91 recorded coordinator decisions, with both initial outcomes, final outcome, rationale, governing rule or constraint, and recorded resolver. This is an input to reference formation. |
| final_reference_labels.csv | All 254 final references, retaining the two independent outcomes and the provenance of each final result. |
| agreement_statistics.json | Recorded independent agreement and task-specific Cohen's kappa, with Wilson intervals and the final-reference disposition counts. |

The A1 working copy was previously repaired to remove malformed references to empty spreadsheet strings. The original delivered workbook remains a historical source; the working copy contains the preserved judgments and can be read without that repair step.

## Recorded procedure

A1 and A2 are two anonymous civil aviation researchers, one specializing in airport operations and the other in air traffic management. Their names and institutions are withheld. Both independently completed the same 254-case material under the same instructions before comparison. Their task was to record answerability, the permitted primary outcome, decision basis, a short rationale, and the applicable supplied rule or constraint. Existing reference outcomes, model responses, and the other annotator's judgments were excluded from their annotation material.

The planned procedure was discussion between the two annotators followed, if necessary, by a third qualified reviewer. After completing their independent files, the annotators delegated disagreement resolution because of availability constraints. The study coordinator manually reviewed the 91 disagreements against the case material, outcome definitions, and recorded rationales. The final references therefore combine 163 initially agreed outcomes with 91 coordinator decisions. The coordinator decisions are not an additional independent rating. These role and process descriptions reproduce the author-confirmed procedural records; the files preserve the corresponding judgments and calculations.

The eight S026 option-selection cases initially named Groups A and B without explicitly assigning them to the available selection tokens. That mapping was made explicit before coordinator resolution. The independent annotations remain unchanged.

## Reproduce the calculations

The scripts require Python 3.10 or later and only the standard library. Run from the repository root:

    python3 scripts/analyze_annotations.py --check
    python3 scripts/build_reference_labels.py --check

The check option recomputes results and compares them with the preserved files without writing. Omit it to regenerate agreement_statistics.json or final_reference_labels.csv. The optional output argument can write a regenerated result to another path. Neither script modifies A1.xlsx, A2.csv, or coordinator_decisions.csv.

The analysis code is extracted from the original annotation-statistics program. It pairs records by scenario and case identifiers. An UNANSWERABLE answerability flag is represented by the UNANSWERABLE outcome token; otherwise the recorded primary outcome is used. All 254 records contribute to annotation agreement. The main model-accuracy analysis separately excludes the three procedural explanation records, yielding 251 scored cases.

Observed outcome agreement is 163/254 and answerability agreement is 237/254. Cohen's kappa is computed from the two annotators' marginal category frequencies within each task family. The pooled kappa retained in the JSON is diagnostic and is not used as the principal reliability measure across incompatible task types. The recorded analysis date in the JSON is 2026-08-12 and remains a historical date when the calculations are rerun.

The reference-building code retains the recorded coordinator outcomes, reasons, rules, and resolver fields. For initially agreed outcomes it retains A1's rationale and rule, following the original procedure. Decision-basis metadata follows the original conversion: equal valid bases are retained; a sole valid base is retained; if neither is valid the basis is N/A; otherwise the fixed order is DETERMINISTIC, REGULATORY, INTERPRETIVE, MIXED. This metadata conversion does not change either independent primary outcome. Among the 91 reviewed cases, the final outcome matches A1 in 28, A2 in 58, and neither in five.

The scripts reproduce the stored references and statistics. They do not generate new substantive judgments or replace the recorded coordinator review.

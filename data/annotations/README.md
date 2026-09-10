# Independent annotations and reference outcomes

This directory contains the independent annotations and reference outcomes for the 254 cases in Layers 2–4: 78 in Layer 2, 100 in Layer 3, and 76 in Layer 4. Layer 1 is outside this annotation exercise. The case material is in `data/main/complex_cases.json`.

## Files

| File | Role |
|---|---|
| A1.xlsx | A1's completed independent workbook, with the Instructions, Annotation, and Definitions sheets. |
| A2.csv | A2's completed independent annotations. |
| coordinator_decisions.csv | The 91 coordinator decisions, with both independent outcomes, final outcome, rationale, governing rule or constraint, and resolver. |
| final_reference_labels.csv | All 254 final references, with the two independent outcomes and the basis of each final result. |
| agreement_statistics.json | Independent agreement and task-specific Cohen's kappa, with Wilson intervals and the final-reference disposition counts. |

## Annotation procedure

A1 and A2 are two anonymous civil aviation researchers, one specializing in airport operations and the other in air traffic management. Their names and institutions are withheld. Both independently completed the same 254-case material under the same instructions before comparison. Their task was to record answerability, the permitted primary outcome, decision basis, a short rationale, and the applicable supplied rule or constraint. Existing reference outcomes, model responses, and the other annotator's judgments were excluded from their annotation material.

The study coordinator manually reviewed the 91 disagreements against the case material, outcome definitions, and annotators' rationales. The final references combine 163 agreed outcomes with 91 coordinator decisions. The coordinator decisions are not an additional independent rating.

For the eight S026 option-selection cases, the mapping between Groups A and B and the permitted selection tokens was specified explicitly before coordinator review.

## Reproduce the calculations

The scripts require Python 3.9 or later and only the standard library. Run from the repository root:

    python3 scripts/analyze_annotations.py --check
    python3 scripts/build_reference_labels.py --check

The check option recomputes results and compares them with the supplied files without writing. Omit it to regenerate agreement_statistics.json or final_reference_labels.csv. The optional output argument can write a regenerated result to another path. Neither script modifies A1.xlsx, A2.csv, or coordinator_decisions.csv.

The analysis pairs records by scenario and case identifiers. An UNANSWERABLE answerability flag is represented by the UNANSWERABLE outcome token; otherwise the recorded primary outcome is used. All 254 records contribute to annotation agreement. The main model-accuracy analysis separately excludes the three procedural explanation records, yielding 251 scored cases.

Observed outcome agreement is 163/254 and answerability agreement is 237/254. Cohen's kappa is computed from the two annotators' marginal category frequencies within each task family. The pooled kappa in the JSON is diagnostic and is not used as the principal reliability measure across incompatible task types.

The reference-building code uses the coordinator outcomes, reasons, rules, and resolver fields. For agreed outcomes it uses A1's rationale and rule. Decision-basis metadata uses the shared valid basis when both agree, or the sole valid basis when only one is valid; if neither is valid the basis is N/A; otherwise the fixed order is DETERMINISTIC, REGULATORY, INTERPRETIVE, MIXED. This metadata conversion does not change either independent primary outcome. Among the 91 reviewed cases, the final outcome matches A1 in 28, A2 in 58, and neither in five.

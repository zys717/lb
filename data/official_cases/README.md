# Eight decisions reconstructed from official records

This qualitative case check contains S051–S058, four models, two presentations, 64 final responses, and 32 paired trajectories. It is separate from the 368-case benchmark. The reference positions guide case interpretation; S051 permits more than one defensible treatment and S055 has no unique reference action. Do not pool these cases into an accuracy estimate or model ranking.

## Files

- `cases.json`: eight fixed decision records, permitted outcomes, source locators, supplied facts and evidence cards, material missing items, and excluded later information.
- `prompts.jsonl`: the 16 case-condition prompts. The same condition names, `RAW_SOURCE_PROBE_V1` and `RAG_SOURCE_PROBE_V1`, appear in `responses.csv`; the paired table uses `raw_` and `rag_` column prefixes.
- `responses.csv`: all 64 final normalized responses, including reasons, controlling rules or constraints, and format-rerun flags.
- `pair_coding.csv`: all 32 manually coded pairs, including both outcomes and the supporting quotations.
- `qualitative_reference.json`: the separate review keys and specified facts/missing items/rules/excluded information; it is not a model input.

Four models were used: Qwen3.8-2.4T-A95B, GLM-5.2, DeepSeek-V4-Flash, and Muse-Glimmer-30B, with temperature 0 and low reasoning effort. The standard output limit was 2,048 tokens. Two positions required format recovery: DeepSeek/S055/RAG kept its settings; GLM/S051/RAG was truncated and was rerun with an 8,192-token output limit. Recovery did not select responses by their substantive answer.

The coding identifies 14 changed outcomes, 23 pairs with decision-linked evidence, four with misstated evidence, three with mention-only evidence, and two without demonstrated evidence use. Six pairs were coded as evidence misuse. A change of outcome is not automatically an improvement. One coder applied the scheme; inter-coder reliability was not assessed.

From the repository root, `python3 scripts/reproduce_case_checks.py` checks identifiers, the 16-to-64 prompt/response correspondence, pair fields, and these counts without calling a model or recreating the qualitative judgments.

## Official source locations

| Case | Official record and locator |
| --- | --- |
| S051 | [AAIB-29335, pp. 6-10](https://www.gov.uk/aaib-reports/aaib-investigation-to-malloy-aeronautics-t150-uas-registration-n-slash-a) |
| S052 | [ATSB AO-2023-033, Aircraft limitations; Wind speed monitoring; Show launch](https://www.atsb.gov.au/investigations/ao-2023-033) |
| S053 | [BEA2019-0416, sections 2.2, 2.3.1 and 2.3.2](https://bea.aero/en/investigation-reports/notified-events/detail/serious-incident-with-a-dji-inspire-2-drone-on-14-07-19-at-le-barcares) |
| S054 | [AAIB-30688, pp. 1-2](https://www.gov.uk/aaib-reports/aaib-investigation-to-tekever-ar5-evolution-mk-2-dot-3-g-tekg) |
| S055 | [AAIB-31425, pp. 1-2](https://www.gov.uk/aaib-reports/experimental-drone-variant-4j-uas-registration-n-slash-a) |
| S056 | [NASA ASRS UAS report set, ACN 2331539](https://asrs.arc.nasa.gov/docs/rpsts/uas.pdf) |
| S057 | [FOCA Safety Recommendation 587 summary of STSB Final Report 2390](https://www.bazl.admin.ch/en/sr-587-impact-energy-of-a-drone-descending-to-the-ground-by-parachute) |
| S058 | [Ministry of Emergency Management update, 2026-08-30](https://www.mem.gov.cn/xw/yjglbgzdt/202608/t20260830_709481.shtml) |

## Qualitative codebook

Case facts and coding definitions were specified before model inference. The unit of analysis is one source case × one model × one condition.

## Reporting purpose

The probe examines whether model decisions on eight official-source cases remain tied to information available at the stated decision time, and how organized evidence changes the selected action and rationale. It is not an accuracy experiment. The eight cases are not pooled, no significance test is performed, and models are not ranked.

All eight cases must be reported. `S052` and `S053` are rule-grounded anchor cases. The remaining cases are qualitative evidence-use probes; `S055` has no prespecified correct action.

## Case-level fields

- `K_RAW`: two or three decision-relevant facts visible in RAW.
- `K_RAG`: one to three decision-relevant facts added or organized in RAG.
- `M`: at most two material missing items; `NONE` if none is specified.
- `R`: an explicit rule or hard limit supplied by the same official source; `NONE` if absent.
- `H`: post-decision information that must not support the response.

The case register and review key define these fields.

## Response-level coding

| Field | Allowed coding |
|---|---|
| `response_status` | `VALID`, `INVALID_FORMAT`, `NO_ACTION`, `MULTIPLE_ACTIONS` |
| `action` | One permitted token, otherwise `OTHER` or `NONE` |
| `action_prose_consistency` | `MATCH`, `MIXED`, `CONTRADICTORY` |
| `K_recognized` | IDs from the specified `K_RAW`/`K_RAG` list |
| `K_misstated` | Specified fact ID plus the shortest supporting quote |
| `M_treatment` | `USED_FOR_CURRENT_DISPOSITION`, `MENTIONED_BUT_BYPASSED`, `ASSUMED_RESOLVED`, `NOT_MENTIONED` |
| `reason_traceability` | `ALL_TRACEABLE`, `MIXED`, `NONE_TRACEABLE`, `NO_REASON` |
| `action_reason_coherence` | `COHERENT`, `PARTLY_COHERENT`, `CONTRADICTORY`, `NO_ACTION` |
| `explicit_rule_alignment` | `ALIGNS`, `CONFLICTS`, `NA` |
| `rag_evidence_use` | `DECISION_LINKED`, `MENTION_ONLY`, `MISSTATED`, `NOT_USED`, `NA` |
| `decision_time_discipline` | `COMPLIANT`, `UNPROVIDED_ASSUMPTION`, `POST_EVENT_INTRUSION`, `MIXED`, `UNDETERMINABLE` |
| `overconfidence_flags` | Zero or more flags below |
| `illustrative_quote` | Shortest response quotation supporting every non-neutral code |

Permitted fact-source tags are `P` (case prompt), `E` (RAG card), `G` (general reasoning stated as such), `S` (case-specific fact absent from the prompt but matching the source), `U` (unsupported case-specific fact), and `H` (specified post-decision information).

Overconfidence flags:

- `OC_CASEFACT`: presents an unprovided case fact as established.
- `OC_STATUS`: converts eligibility, a maximum, or a customary setting into an existing approval or demonstrated suitability.
- `OC_CAUSAL`: asserts an unprovided cause or inevitable consequence.
- `OC_HINDSIGHT`: uses a later outcome to justify the decision.
- `OC_SCOPE`: generalizes one case to deployment capability.
- `NONE`: no flag applies.

## RAW-to-RAG pair coding

For each case and model, record:

- `action_transition`.
- `K_delta`: facts newly used, lost, or misstated.
- `M_treatment_delta`.
- `unsupported_claim_delta`: new or removed `S`, `U`, or `H` claims.
- `certainty_delta`: `MORE_QUALIFIED`, `UNCHANGED`, `MORE_CATEGORICAL`, or `MIXED`.
- `pair_type`: `ACTION_CHANGED_WITH_EVIDENCE`, `ACTION_UNCHANGED_REASON_CHANGED`, `EVIDENCE_MENTION_ONLY`, `NO_DEMONSTRABLE_EVIDENCE_USE`, `EVIDENCE_MISUSED`, or `NOT_COMPARABLE`.

An action change is not automatically an improvement, and an unchanged action does not establish that evidence had no effect.

## Fixed per-case report order

1. Source, decision maker, decision time, and specified `K/M/R/H` fields.
2. Four-model paired matrix: RAW action, RAG action, newly used evidence, missing-information treatment, unsupported or post-decision claims, and overconfidence flags.
3. Three concise statements: observed change; whether the change is traceable to supplied evidence; what the case shows and does not show.

No overall percentage, confidence interval, significance test, model ranking, or transfer claim is permitted.

#!/usr/bin/env python3
"""Recompute the separate civil diagnostic and official-record case counts offline."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def keyed(rows, key):
    result = {key(row): row for row in rows}
    require(len(result) == len(rows), "Duplicate record identifiers")
    return result


def normalize_acn(value: str) -> str:
    return re.sub(r"\.0$", "", str(value).strip())


def reproduce_civil() -> None:
    folder = ROOT / "data/civil"
    scenarios = keyed(read_json(folder / "scenarios.json"), lambda row: row["test_info"]["scenario_id"])
    references = keyed(read_json(folder / "references.json"), lambda row: row["scenario_id"])
    reports = keyed(read_json(folder / "reports.json"), lambda row: row["scenario"].split("_")[0])
    sources = keyed(read_json(folder / "asrs_sources.json")["exports"], lambda row: row["scenario_id"])
    expected_ids = {f"C{i:03d}" for i in range(1, 16)}
    require(set(scenarios) == set(references) == set(reports) == set(sources) == expected_ids,
            "Civil scenario, reference, report, or source group is missing")
    label_counts = Counter()
    source_acns = set()
    stored_label_differences = []
    correct = total = 0
    for sid in sorted(references):
        cases = keyed(scenarios[sid]["test_cases"], lambda row: row["case_id"])
        refs = keyed(references[sid]["test_cases"], lambda row: row["case_id"])
        answers = keyed(reports[sid]["results"], lambda row: row["test_case_id"])
        require(set(cases) == set(refs) == set(answers) == {f"TC{i}" for i in range(1, 13)},
                f"{sid}: expected 12 corresponding items")
        source_rows = keyed(sources[sid]["records"], lambda row: normalize_acn(row["values"][0]))
        require(len(source_rows) == 12, f"{sid}: expected 12 selected ASRS rows")
        for case_id, ref in refs.items():
            case, answer = cases[case_id], answers[case_id]
            acn = normalize_acn(ref["command"]["source"]["acn"])
            require(acn in source_rows, f"{sid}/{case_id}: ASRS source is absent")
            source_acns.add(acn)
            require(case["description"] == ref["description"] == answer["description"],
                    f"{sid}/{case_id}: case narratives differ")
            expected = ref["expected_behavior"]["decision"]
            prediction = answer["llm_result"]["decision"]
            match = prediction == expected
            require(answer["ground_truth"]["decision"] == expected,
                    f"{sid}/{case_id}: report reference differs")
            require(answer["llm_result"]["correct"] == match,
                    f"{sid}/{case_id}: stored score differs from recomputed score")
            if case.get("expected") != expected:
                stored_label_differences.append((sid, case_id, case.get("expected"), expected))
            label_counts[expected] += 1
            correct += match
            total += 1
    require(total == 180 and correct == 175, "Civil aggregate differs from the retained 175/180 result")
    require(label_counts == {"UNCERTAIN": 170, "REJECT": 10}, "Civil reference distribution changed")
    require(len(source_acns) == 174, "Civil unique ASRS source count changed")
    require(stored_label_differences == [("C004", "TC9", "UNCERTAIN", "REJECT")],
            "Unexpected difference between embedded and scoring references")
    baseline = label_counts["UNCERTAIN"]
    print(f"Civil: 15 groups, {total} items, {len(source_acns)} distinct ASRS ACNs")
    print(f"  Reference agreement: {correct}/{total} ({100 * correct / total:.1f}%)")
    print(f"  Always-UNCERTAIN baseline: {baseline}/{total} ({100 * baseline / total:.1f}%)")
    print("  Preserved discrepancy: C004/TC9 embedded UNCERTAIN; scoring reference and report REJECT")
    print("  Qwen3.8 settings and responses are retained in reports.json; inputs are in prompts.json.")


def reproduce_official() -> None:
    folder = ROOT / "data/official_cases"
    cases = keyed(read_json(folder / "cases.json")["cases"], lambda row: row["case_id"])
    reference = keyed(read_json(folder / "qualitative_reference.json")["case_keys"], lambda row: row["case_id"])
    prompts = keyed([json.loads(line) for line in (folder / "prompts.jsonl").read_text().splitlines() if line.strip()],
                    lambda row: (row["record_id"], row["condition"]))
    responses = keyed(read_csv(folder / "responses.csv"),
                      lambda row: (row["case_id"], row["model_id"], row["condition"]))
    pairs = keyed(read_csv(folder / "pair_coding.csv"), lambda row: (row["case_id"], row["model_id"]))
    case_ids = {f"S{i:03d}" for i in range(51, 59)}
    model_ids = {"qwen38_flagship", "glm52_flagship", "deepseek_v4_flash", "meta_muse_30b"}
    raw, rag = "RAW_SOURCE_PROBE_V1", "RAG_SOURCE_PROBE_V1"
    conditions = {raw, rag}
    require(set(cases) == set(reference) == case_ids, "Official case/reference coverage differs")
    require(set(prompts) == {(case, condition) for case in case_ids for condition in conditions},
            "Expected 16 case-condition prompts")
    require(set(responses) == {(case, model, condition) for case in case_ids for model in model_ids for condition in conditions},
            "Expected 64 case-model-condition responses")
    require(set(pairs) == {(case, model) for case in case_ids for model in model_ids},
            "Expected 32 case-model pairs")
    for (case_id, condition), prompt in prompts.items():
        case = cases[case_id]
        payload = json.loads(prompt["prompt"].split("\nINPUT\n", 1)[1])
        require(payload["case_id"] == case_id and payload["case_record"] == case["raw_case_record"],
                f"{case_id}/{condition}: prompt case differs")
        require(prompt["allowed_outcomes"] == case["allowed_outcomes"],
                f"{case_id}/{condition}: prompt outcome set differs")
    for (case_id, model_id, condition), response in responses.items():
        require(bool(response["rationale"].strip()), f"{case_id}/{model_id}: missing rationale")
        if response["answerability"] == "ANSWERABLE":
            require(response["primary_outcome"] in cases[case_id]["allowed_outcomes"],
                    f"{case_id}/{model_id}: outcome outside the task set")
        else:
            require(response["answerability"] == response["primary_outcome"] == "UNANSWERABLE",
                    f"{case_id}/{model_id}: invalid normalized abstention")
    changed = 0
    for (case_id, model_id), pair in pairs.items():
        for prefix, condition in [("raw", raw), ("rag", rag)]:
            response = responses[(case_id, model_id, condition)]
            for pair_field, response_field in [("answerability", "answerability"), ("outcome", "primary_outcome"), ("basis", "decision_basis")]:
                require(pair[f"{prefix}_{pair_field}"] == response[response_field],
                        f"{case_id}/{model_id}: paired {prefix}_{pair_field} differs")
        changed += pair["raw_outcome"] != pair["rag_outcome"]
    evidence = Counter(pair["rag_evidence_use"] for pair in pairs.values())
    misuse = sum(pair["pair_type"] == "EVIDENCE_MISUSED" for pair in pairs.values())
    reruns = {key for key, row in responses.items() if row["format_rerun"].lower() == "true"}
    require(changed == 14 and misuse == 6, "Official action-change or evidence-misuse counts differ")
    require(evidence == {"DECISION_LINKED": 23, "MISSTATED": 4, "MENTION_ONLY": 3, "NOT_USED": 2},
            "Official evidence-use counts differ")
    require(reruns == {("S051", "glm52_flagship", rag), ("S055", "deepseek_v4_flash", rag)},
            "Official format-recovery positions differ")
    print("Official records: 8 cases, 16 prompts, 64 responses, 32 corresponding pairs")
    print(f"  Changed outcomes: {changed}; evidence-misuse pairs: {misuse}; format-recovered responses: {len(reruns)}")
    print("  Evidence use: 23 decision-linked, 4 misstated, 3 mention-only, 2 not-used")
    print("  Existing qualitative codes were counted, not independently recoded; no pooled accuracy or model ranking.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", choices=["all", "civil", "official"], default="all")
    args = parser.parse_args()
    if args.section in {"all", "civil"}:
        reproduce_civil()
    if args.section in {"all", "official"}:
        reproduce_official()


if __name__ == "__main__":
    main()

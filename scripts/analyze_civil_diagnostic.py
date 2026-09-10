#!/usr/bin/env python3
"""Check 180 saved requests and API responses against reports and recompute agreement offline."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"APPROVE", "CONDITIONAL_APPROVE", "REJECT", "REJECT_WITH_ALTERNATIVE", "UNCERTAIN", "EXPLAIN_ONLY"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def calculate(folder):
    run = json.loads((folder / "run.json").read_text())
    reports = json.loads((folder / "reports.json").read_text())
    references = json.loads((folder / "references.json").read_text())
    prompts = json.loads((folder / "prompts.json").read_text())
    expected = {f"C{s:03d}/TC{i}" for s in range(1, 16) for i in range(1, 13)}
    refs = {s["scenario_id"] + "/" + r["case_id"]: r
            for s in references for r in s["test_cases"]}
    inputs = {r["case_id"]: r["prompt"] for r in prompts}
    records = {s["scenario"].split("_")[0] + "/" + r["test_case_id"]: r
               for s in reports for r in s["results"]}
    calls = {r["case_id"]: r for r in run["cases"]}
    require(len(prompts) == sum(len(s["test_cases"]) for s in references)
            == sum(len(s["results"]) for s in reports) == len(run["cases"]) == 180,
            "Expected 180 unique cases in inputs, references, and reports")
    require(set(refs) == set(inputs) == set(records) == set(calls) == expected,
            "Input, reference, or response identifiers differ")
    require(len(reports) == 15 and all(len(s["results"]) == 12 for s in reports),
            "Expected 15 scenario groups with 12 responses each")
    evaluation = reports[0]["evaluation"]
    require(all(s["evaluation"] == evaluation for s in reports),
            "Model settings differ between scenario groups")
    require(set(evaluation) == {"model", "temperature", "max_tokens", "response_format",
                                "provider", "reasoning", "api_provider"},
            "Model settings are incomplete")
    require(run["settings"] == {k: v for k, v in evaluation.items() if k != "api_provider"},
            "Run and report model settings differ")
    confusion, predictions, labels, conditions = Counter(), Counter(), Counter(), Counter()
    matched = 0
    for key, row in records.items():
        reference = refs[key]
        require(row["description"] == reference["description"], key + ": case narrative differs")
        require(isinstance(inputs[key], str) and row["description"] in inputs[key],
                key + ": prompt does not contain the case narrative")
        expected_decision = reference["expected_behavior"]["decision"]
        require(row["ground_truth"]["decision"] == expected_decision, key + ": reference differs")
        answer = row["llm_result"]
        call = calls[key]
        condition = call.get("condition", "BASE_PROMPT")
        require(condition in {"BASE_PROMPT", "TASK_CLARIFIED"}, key + ": unknown prompt condition")
        require(row.get("condition", "BASE_PROMPT") == condition,
                key + ": run and report prompt conditions differ")
        conditions[condition] += 1
        require(call["request"] == {**run["settings"], "messages": [{"role": "user", "content": inputs[key]}]},
                key + ": API request differs from the inputs or settings")
        response = call["response"]
        require(call["http_status"] == 200 and len(response["choices"]) == 1
                and response["choices"][0]["finish_reason"] == "stop",
                key + ": incomplete API response")
        require(response["model"] == evaluation["model"]
                and response["provider"] == evaluation["api_provider"],
                key + ": returned model or provider differs")
        decoded = json.loads(response["choices"][0]["message"]["content"])
        require(decoded == {k: v for k, v in answer.items() if k != "correct"},
                key + ": report differs from the original API response text")
        require(set(answer) == {"decision", "reasoning", "conditions", "alternative",
                                "requested_clarifications", "correct"}, key + ": response fields differ")
        require(answer["decision"] in ALLOWED, key + ": invalid decision")
        require(isinstance(answer["reasoning"], str) and answer["reasoning"].strip(),
                key + ": missing explanation")
        for field in ("conditions", "requested_clarifications"):
            require(isinstance(answer[field], list) and all(isinstance(x, str) for x in answer[field]),
                    key + ": invalid " + field)
        require(answer["alternative"] is None or isinstance(answer["alternative"], str),
                key + ": invalid alternative")
        require(answer["decision"] != "REJECT_WITH_ALTERNATIVE" or answer["alternative"],
                key + ": missing required alternative")
        match = answer["decision"] == expected_decision
        require(answer["correct"] is match, key + ": stored score differs")
        matched += match
        labels[expected_decision] += 1
        predictions[answer["decision"]] += 1
        confusion[(expected_decision, answer["decision"])] += 1
    total = len(records)
    baseline_label, baseline = labels.most_common(1)[0]
    return {
        "model": evaluation["model"], "cases": total, "valid": total, "matched": matched,
        "disagreements": total - matched, "agreement_percent": 100 * matched / total,
        "majority_baseline_label": baseline_label, "majority_baseline_matched": baseline,
        "majority_baseline_percent": 100 * baseline / total,
        "reference_counts": dict(labels), "prediction_counts": dict(predictions),
        "condition_counts": dict(conditions),
        "task_clarified_case_ids": sorted(key for key, call in calls.items()
                                         if call.get("condition") == "TASK_CLARIFIED"),
        "confusion_counts": [{"reference": a, "prediction": b, "n": n}
                             for (a, b), n in sorted(confusion.items())],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=ROOT / "data/civil")
    parser.add_argument("--check", action="store_true", help="Print confirmation after checking the reports")
    args = parser.parse_args()
    summary = calculate(args.folder)
    if args.check:
        print("Saved civil API requests, response texts, reports, references, and score flags are consistent.")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

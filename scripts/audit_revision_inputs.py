#!/usr/bin/env python3
"""Audit retained inputs and recompute a bounded exclusion sensitivity, offline.

The field screen detects named, precomputed case judgments. It is not a claim
that all other natural-language cues are absent. Historical inputs and scores
are never rewritten, and no model is called.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/main/input_audit"
FIELDS = {"rule_applicability", "conflict_violations", "violations", "rtl_compliant"}
DROP_KEYS = {"ground_truth", "groundtruth", "expected_decision", "expected_outcome",
             "correct_answer", "correct_label", "final_outcome", "final_rationale"}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def walk(value, path=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield path + (key,), item
            yield from walk(item, path + (key,))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from walk(item, path + (str(i),))


def csv_text(rows):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def build():
    files = ["data/main/layer1/generated/layer1_raw_prompt_package.jsonl",
             "data/main/prompts_raw.jsonl", "data/main/prompts_rag_revised.jsonl"]
    coverage, flags, hashes = [], [], {}
    for filename in files:
        path = ROOT / filename
        hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
        prompts = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        for row in prompts:
            payload = json.loads(row["prompt"].split("\nINPUT\n", 1)[1])
            forbidden = [".".join(p) for p, _ in walk(payload) if p[-1].lower() in DROP_KEYS]
            if forbidden:
                raise ValueError((row["record_id"], forbidden))
            found = []
            # The case object is common to RAW and RAG. RAG repeats some fields
            # in evidence cards; count a case once, not each textual occurrence.
            for p, value in walk(payload.get("case_specific_content", {})):
                if p[-1] in FIELDS:
                    found.append(".".join(p))
                    flags.append({"record_id": row["record_id"], "scenario_id": row["scenario_id"],
                                  "condition": row["condition"], "field": ".".join(p),
                                  "supplied_value": json.dumps(value, ensure_ascii=False, sort_keys=True)})
            coverage.append({"record_id": row["record_id"], "condition": row["condition"],
                             "task_type": row["task_type"], "flagged_fields": ";".join(found)})
    assert len(coverage) == 622
    excluded = {r["record_id"] for r in flags}
    by_condition = {}
    for row in flags:
        by_condition.setdefault(row["condition"], set()).add(row["record_id"])
    assert by_condition["RAW"] == by_condition["RAG_REVISED_FULL"] == excluded
    scores_path = ROOT / "data/main/results/case_results.csv"
    hashes[str(scores_path.relative_to(ROOT))] = hashlib.sha256(scores_path.read_bytes()).hexdigest()
    scores = read_csv(scores_path)
    assert len(scores) == 2488
    results, losses = [], []
    for model in dict.fromkeys(r["model_id"] for r in scores):
        common = [r for r in scores if r["model_id"] == model and int(r["layer"]) >= 2
                  and r["task_type"] != "PROCEDURAL_EXPLANATION" and r["record_id"] not in excluded]
        for task in ["ALL_SCORABLE", "PRE_FLIGHT_AUTHORIZATION", "IN_FLIGHT_CONTINGENCY", "RESOURCE_OR_POLICY_DECISION"]:
            subset = [r for r in common if task == "ALL_SCORABLE" or r["task_type"] == task]
            raw = {r["record_id"]: r for r in subset if r["condition"] == "RAW"}
            rag = {r["record_id"]: r for r in subset if r["condition"] == "RAG_REVISED"}
            assert raw.keys() == rag.keys()
            n = len(raw)
            a = sum(r["correct"] == "True" for r in raw.values())
            b = sum(r["correct"] == "True" for r in rag.values())
            results.append({"model_id": model, "task_type": task, "n": n, "raw_correct": a,
                            "rag_correct": b, "raw_accuracy": a/n, "rag_accuracy": b/n,
                            "gain_pp": 100*(b-a)/n})
            if task == "PRE_FLIGHT_AUTHORIZATION":
                counts = []
                for data in [raw, rag]:
                    permissive = sum(r["predicted_outcome"] in {"APPROVE", "CONDITIONAL_APPROVE"}
                                     and r["reference_outcome"] in {"REJECT", "REJECT_WITH_ALTERNATIVE"}
                                     for r in data.values())
                    errors = sum(r["correct"] != "True" for r in data.values())
                    counts.append((permissive, errors-permissive))
                (pr, other_r), (pg, other_g) = counts
                losses.append({"model_id": model, "n": n, "raw_permissive": pr, "rag_permissive": pg,
                               "raw_other": other_r, "rag_other": other_g,
                               "crossover_w": (other_r-other_g)/(pg-pr) if pg != pr else "NA"})
    refs = read_csv(ROOT / "data/annotations/final_reference_labels.csv")
    boundary = [{key: r[key] for key in ["record_id", "a1_outcome", "a2_outcome", "final_answerability",
                                       "final_outcome", "final_rationale", "governing_rule_or_constraint"]}
                for r in refs if r["final_outcome"] in {"UNCERTAIN", "UNANSWERABLE"}]
    assert len(boundary) == 15
    summary = {"prompt_positions_screened": len(coverage), "scored_positions_checked": len(scores),
               "explicit_judgment_fields": sorted(FIELDS), "flagged_cases": len(excluded),
               "flagged_record_ids": sorted(excluded), "reference_boundary_cases": len(boundary),
               "retained_input_sha256": hashes,
               "scope": "Post hoc screen of named structured case judgments; not an exhaustive natural-language cue detector. "
                        "Exclusion uses retained predictions and does not estimate performance after prompt cleaning."}
    return {"prompt_screen.csv": csv_text(coverage), "flagged_input_fields.csv": csv_text(flags),
            "exclusion_sensitivity.csv": csv_text(results), "exclusion_loss.csv": csv_text(losses),
            "answerability_boundary.csv": csv_text(boundary),
            "summary.json": json.dumps(summary, ensure_ascii=False, indent=2)+"\n"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, text in build().items():
        path = OUT/name
        if args.check:
            assert path.read_text() == text, f"Outdated audit artifact: {path}"
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        print(f"{'PASS' if args.check else 'WROTE'} {name}")


if __name__ == "__main__":
    main()

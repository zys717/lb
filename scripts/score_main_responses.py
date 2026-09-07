#!/usr/bin/env python3
"""Score actual 622-position response files against the 368 references.

Original response transcripts are not supplied by the current release. This
entry point is for actual response files from a new run or recovered originals;
it does not reconstruct text responses from the published score table.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from run_main_evaluation import PROMPTS, ROOT, SETTINGS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses-dir", type=Path, required=True)
    parser.add_argument("--prompts", type=Path, default=PROMPTS)
    parser.add_argument("--references", type=Path, default=ROOT / "data/main/results/reference_labels.csv")
    parser.add_argument("--settings", type=Path, default=SETTINGS)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-kind", choices=("validity_recovered", "original_invalid_as_incorrect"), default="validity_recovered")
    args = parser.parse_args()
    if args.output.resolve() == (ROOT / "data/main/results/case_results.csv").resolve():
        raise SystemExit("Choose a separate output; published results are not overwritten.")
    prompts = {r["run_case_id"]: r for r in (json.loads(x) for x in args.prompts.read_text().splitlines() if x.strip())}
    with args.references.open(newline="") as stream:
        labels = {r["record_id"]: r for r in csv.DictReader(stream)}
    if len(prompts) != 622 or len(labels) != 368:
        raise SystemExit("Expected 622 input positions and 368 reference cases.")
    scores = []
    for spec in json.loads(args.settings.read_text())["models"]:
        path = args.responses_dir / f"{spec['model_id']}.jsonl"
        if not path.is_file():
            raise SystemExit(f"Missing actual responses: {path}; cannot score transcripts that are not supplied.")
        rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        if len(rows) != 622 or {r["run_case_id"] for r in rows} != set(prompts):
            raise SystemExit(f"{path.name}: expected each of the 622 input positions exactly once.")
        for row in rows:
            if row.get("model_id") != spec["model_id"] or row.get("model") != spec["model"]:
                raise SystemExit(f"Response/model mismatch in {path.name}")
            if row.get("status") == "DRY_RUN":
                raise SystemExit("Dry-run records are not model responses and cannot be scored.")
            prompt = prompts[row["run_case_id"]]
            if row["record_id"] != prompt["record_id"] or row["condition"] != prompt["condition"]:
                raise SystemExit(f"Response/input mismatch: {row['run_case_id']}")
            label = labels[row["record_id"]]
            normalized = row.get("normalized_response") or {}
            valid = row.get("status") == "OK" and not normalized.get("validation_errors")
            if args.source_kind == "validity_recovered" and not valid:
                raise SystemExit(
                    f"Invalid response in validity_recovered mode: {spec['model_id']}/{row['run_case_id']}. "
                    "Complete validity recovery, or explicitly use --source-kind original_invalid_as_incorrect."
                )
            pa, po = normalized.get("answerability"), normalized.get("primary_outcome")
            ra, ro = label["reference_answerability"], label["reference_outcome"]
            correct = bool(valid and pa == ra and (ra == "UNANSWERABLE" or po == ro))
            scores.append({"source_kind": args.source_kind, "model_id": spec["model_id"], "model": spec["model"],
                           "condition": row["condition"], "record_id": row["record_id"], "run_case_id": row["run_case_id"],
                           "scenario_id": label["scenario_id"], "layer": int(label["layer"]), "task_type": label["task_type"],
                           "status": row.get("status"), "valid": valid, "predicted_answerability": pa, "predicted_outcome": po,
                           "reference_answerability": ra, "reference_outcome": ro, "correct": correct,
                           "selected_response_source": row.get("selected_response_source", "official")})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(scores[0]))
        writer.writeheader()
        writer.writerows(scores)
    print(f"Scored {len(scores)} actual responses: {args.output}")


if __name__ == "__main__":
    main()

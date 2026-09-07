#!/usr/bin/env python3
"""Rebuild the 254 reference records from independent annotations and recorded review.

Coordinator decisions are preserved human-provided inputs. This program merges
those records; it does not make, revise, or infer the substantive decisions.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from analyze_annotations import DATA_DIR, load_comparisons, load_coordinator_decisions, read_csv

VALID_BASES = {"DETERMINISTIC", "REGULATORY", "INTERPRETIVE", "MIXED"}
BASIS_PRIORITY = ("DETERMINISTIC", "REGULATORY", "INTERPRETIVE", "MIXED")
FIELDS = [
    "record_no", "record_id", "scenario_id", "case_id", "layer", "task_type", "endpoint_family",
    "a1_answerability", "a1_outcome", "a1_basis", "a2_answerability", "a2_outcome", "a2_basis",
    "pre_adjudication_agreement", "final_answerability", "final_outcome", "final_basis",
    "basis_resolution_source", "final_label_source", "final_rationale",
    "governing_rule_or_constraint", "freeze_status",
]


def final_basis(pair: dict, decision: dict | None) -> tuple[str, str]:
    if decision is not None:
        if decision["final_basis"] not in VALID_BASES:
            raise ValueError(f"{pair['key']}: invalid recorded coordinator basis.")
        return decision["final_basis"], "CASE_ADJUDICATION"
    first = pair["a1_basis"] if pair["a1_basis"] in VALID_BASES else None
    second = pair["a2_basis"] if pair["a2_basis"] in VALID_BASES else None
    if first == second and first:
        return first, "A1_A2_AGREEMENT"
    if not first and not second:
        return "N/A", "NOT_APPLICABLE"
    if not first or not second:
        return first or second, "AVAILABLE_VALID_BASIS"
    return next(value for value in BASIS_PRIORITY if value in {first, second}), "DOMINANT_BASIS_CALIBRATION"


def build_labels(comparisons: list[dict], decisions: dict[int, dict]) -> list[dict]:
    rows = []
    for pair in comparisons:
        decision = decisions.get(pair["record_no"])
        outcome = decision["final_outcome"] if decision is not None else pair["a1_outcome"]
        basis, basis_source = final_basis(pair, decision)
        scenario, case = pair["key"].split("/", 1)
        rows.append({
            "record_no": pair["record_no"], "record_id": pair["key"],
            "scenario_id": scenario, "case_id": case, "layer": pair["layer"],
            "task_type": pair["task_type"], "endpoint_family": pair["endpoint_family"],
            "a1_answerability": pair["a1_answerability"], "a1_outcome": pair["a1_outcome"],
            "a1_basis": pair["a1_basis"], "a2_answerability": pair["a2_answerability"],
            "a2_outcome": pair["a2_outcome"], "a2_basis": pair["a2_basis"],
            "pre_adjudication_agreement": "YES" if pair["outcome_agree"] else "NO",
            "final_answerability": "UNANSWERABLE" if outcome == "UNANSWERABLE" else "ANSWERABLE",
            "final_outcome": outcome, "final_basis": basis,
            "basis_resolution_source": basis_source,
            "final_label_source": decision["resolved_by"] if decision is not None else "A1_A2_AGREEMENT",
            "final_rationale": decision["final_rationale"] if decision is not None else pair["a1_rationale"],
            "governing_rule_or_constraint": decision["governing_rule_or_constraint"] if decision is not None else pair["a1_rule"],
            "freeze_status": "FROZEN_WITH_RECORDED_PROTOCOL_DEVIATION",
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output", type=Path, help="Output CSV; defaults to final_reference_labels.csv.")
    parser.add_argument("--check", action="store_true", help="Compare with the saved CSV without writing.")
    args = parser.parse_args()
    comparisons = load_comparisons(args.data_dir)
    decisions = load_coordinator_decisions(args.data_dir, comparisons)
    rows = build_labels(comparisons, decisions)
    output = args.output or args.data_dir / "final_reference_labels.csv"
    if args.check:
        expected = read_csv(output)
        actual = [{field: str(row[field]) for field in FIELDS} for row in rows]
        if actual != expected:
            raise ValueError("Rebuilt reference labels differ from the saved CSV.")
        print(
            f"Reference labels match: all fields in {len(rows)} records, "
            f"including {len(decisions)} recorded coordinator decisions."
        )
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()

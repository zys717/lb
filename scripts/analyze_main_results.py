#!/usr/bin/env python3
"""Recompute the manuscript's main statistics from the released case scores.

--check compares the computed tables with data/main/results without writing.
--output-dir writes a separate set of tables. Python random.Random is used
for layer and accuracy intervals; NumPy default_rng is used for principal-task
paired intervals.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data/main/results"
SEED = 20260812
REPS = 10000
PRINCIPAL = ["PRE_FLIGHT_AUTHORIZATION", "IN_FLIGHT_CONTINGENCY", "RESOURCE_OR_POLICY_DECISION"]


def truth(value) -> bool:
    return value is True or str(value).strip().lower() in {"true", "1", "yes"}


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


@lru_cache(maxsize=None)
def draws(count: int, engine: str) -> np.ndarray:
    # Caching reuses the same sequence obtained by resetting the original seed
    # for each estimate. Cluster order remains sorted by scenario identifier.
    if engine == "python":
        rng = random.Random(SEED)
        return np.array([[rng.choice(range(count)) for _ in range(count)] for _ in range(REPS)])
    rng = np.random.default_rng(SEED)
    return np.array([rng.choice(count, size=count, replace=True) for _ in range(REPS)])


def interval(rows: list[dict], field: str, engine: str = "python") -> tuple[float, float]:
    groups = defaultdict(list)
    for row in rows:
        groups[row["scenario_id"]].append(row[field])
    order = sorted(groups)
    sums = np.array([sum(groups[key]) for key in order], dtype=float)
    sizes = np.array([len(groups[key]) for key in order])
    sample = draws(len(order), engine)
    estimates = sums[sample].sum(axis=1) / sizes[sample].sum(axis=1)
    if engine == "numpy":
        lo, hi = np.quantile(estimates, [.025, .975])
        return float(lo), float(hi)
    ordered = sorted(estimates)
    def percentile(p: float) -> float:
        position = (len(ordered) - 1) * p
        low, high = math.floor(position), math.ceil(position)
        return float(ordered[low] if low == high else ordered[low] * (high-position) + ordered[high] * (position-low))
    return percentile(.025), percentile(.975)


def summary(rows: list[dict], macro: bool = False) -> dict:
    low, high = interval(rows, "correct")
    correct = sum(r["correct"] for r in rows)
    result = {"n_scenarios": len({r["scenario_id"] for r in rows}), "n": len(rows),
              "n_correct" if macro else "correct": correct, "accuracy": correct / len(rows), "ci_low": low, "ci_high": high}
    if macro:
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["scenario_id"]].append(row["correct"])
        result["scenario_macro_accuracy"] = sum(sum(g)/len(g) for g in grouped.values()) / len(grouped)
    return result


def pairs(rows: list[dict]) -> tuple[list[dict], dict, dict]:
    raw = {r["record_id"]: r for r in rows if r["condition"] == "RAW"}
    rag = {r["record_id"]: r for r in rows if r["condition"] == "RAG_REVISED"}
    if set(raw) != set(rag):
        raise ValueError("RAW and RAG positions are not paired.")
    values = [{"scenario_id": raw[k]["scenario_id"], "difference": int(rag[k]["correct"])-int(raw[k]["correct"])} for k in sorted(raw)]
    return values, raw, rag


def compute(case_rows: list[dict], refs: list[dict], model_order: list[str]) -> dict[str, list[dict]]:
    output = {name: [] for name in ["layer_accuracy", "layer_rag_paired_gain", "denominator_sensitivity",
              "validity_recovery_sensitivity", "task_family_accuracy", "task_family_paired_gain",
              "task_family_validity_sensitivity", "overall_accuracy", "preflight_safety_direction"]}
    disputed = {r["record_id"] for r in refs if truth(r["disputed_reference"])}
    for model_id in model_order:
        rows = [r for r in case_rows if r["model_id"] == model_id]
        l1 = [r for r in rows if r["layer"] == 1]
        l24 = [r for r in rows if r["layer"] >= 2 and r["task_type"] != "PROCEDURAL_EXPLANATION"]
        for scope, condition, subset in [("L1_ALL_114", "RAW", l1)] + [
                (f"L{layer}_SCORABLE", cond, [r for r in l24 if r["layer"] == layer and r["condition"] == cond])
                for layer in (2, 3, 4) for cond in ("RAW", "RAG_REVISED")] + [
                ("L2_TO_L4_SCORABLE_251", cond, [r for r in l24 if r["condition"] == cond]) for cond in ("RAW", "RAG_REVISED")]:
            output["layer_accuracy"].append({"model_id": model_id, "scope": scope, "condition": condition, **summary(subset)})
        for scope, subset in [(f"L{layer}_SCORABLE", [r for r in l24 if r["layer"] == layer]) for layer in (2, 3, 4)] + [("L2_TO_L4_SCORABLE_251", l24)]:
            values, raw, rag = pairs(subset)
            low, high = interval(values, "difference")
            output["layer_rag_paired_gain"].append({"model_id": model_id, "scope": scope, "n_paired": len(values),
                "rag_minus_raw": sum(r["difference"] for r in values)/len(values), "ci_low": low, "ci_high": high,
                "raw_only_correct": sum(raw[k]["correct"] and not rag[k]["correct"] for k in raw),
                "rag_only_correct": sum(rag[k]["correct"] and not raw[k]["correct"] for k in raw)})
        for scope, condition, subset in [("L1_CORE_110", "RAW", [r for r in l1 if r["record_id"] not in disputed])] + [
                ("L2_TO_L4_ALL_254", cond, [r for r in rows if r["layer"] >= 2 and r["condition"] == cond]) for cond in ("RAW", "RAG_REVISED")]:
            output["denominator_sensitivity"].append({"model_id": model_id, "scope": scope, "condition": condition, **summary(subset)})
        scopes = [("L1_ALL_114_RAW", l1)] + [("L2_TO_L4_SCORABLE_251_"+cond, [r for r in l24 if r["condition"] == cond]) for cond in ("RAW", "RAG_REVISED")]
        for source in ("original_invalid_as_incorrect", "validity_recovered"):
            for scope, subset in scopes:
                eligible = [r for r in subset if source == "validity_recovered" or r["selected_response_source"] == "official"]
                correct = sum(r["correct"] for r in eligible)
                output["validity_recovery_sensitivity"].append({"model_id": model_id, "source_kind": source, "scope": scope,
                    "n": len(subset), "n_valid": len(eligible), "correct": correct, "accuracy": correct/len(subset)})
        for task in PRINCIPAL:
            subset = [r for r in l24 if r["task_type"] == task]
            values, raw, rag = pairs(subset)
            low, high = interval(values, "difference", "numpy")
            gain = sum(r["difference"] for r in values)/len(values)
            output["task_family_paired_gain"].append({"model_id": model_id, "task_type": task,
                "n_scenarios": len({r["scenario_id"] for r in values}), "n_paired": len(values),
                "rag_minus_raw": gain, "ci_low": low, "ci_high": high})
            raw_original = sum(r["correct"] and r["selected_response_source"] == "official" for r in raw.values())
            rag_original = sum(r["correct"] and r["selected_response_source"] == "official" for r in rag.values())
            output["task_family_validity_sensitivity"].append({"model_id": model_id, "task_type": task, "n": len(raw),
                "raw_correct_original_invalid_as_incorrect": raw_original, "rag_correct_original_invalid_as_incorrect": rag_original,
                "gain_original_invalid_as_incorrect": (rag_original-raw_original)/len(raw),
                "raw_correct_validity_recovered": sum(r["correct"] for r in raw.values()),
                "rag_correct_validity_recovered": sum(r["correct"] for r in rag.values()), "gain_validity_recovered": gain})
    scorable = [r for r in case_rows if r["layer"] >= 2 and r["task_type"] != "PROCEDURAL_EXPLANATION"]
    grouped = defaultdict(list)
    for row in scorable:
        grouped[(row["model_id"], row["condition"], row["task_type"])].append(row)
    for (mid, condition, task), rows in sorted(grouped.items()):
        output["task_family_accuracy"].append({"model_id": mid, "model": rows[0]["model"], "condition": condition, "task_type": task, **summary(rows, True)})
    for mid in sorted(model_order):
        rows = [r for r in case_rows if r["model_id"] == mid]
        selections = [("L1_ALL_114", "RAW", [r for r in rows if r["layer"] == 1])] + [
            ("L2_TO_L4_SCORABLE_251", cond, [r for r in rows if r["layer"] >= 2 and r["condition"] == cond and r["task_type"] != "PROCEDURAL_EXPLANATION"]) for cond in ("RAW", "RAG_REVISED")]
        for scope, condition, subset in selections:
            output["overall_accuracy"].append({"model_id": mid, "model": rows[0]["model"], "scope": scope, "condition": condition, **summary(subset, True)})
        for scope, condition, subset in [("L1", "RAW", selections[0][2])] + [
            ("L2_TO_L4", cond, [r for r in rows if r["layer"] >= 2 and r["condition"] == cond and r["task_type"] == "PRE_FLIGHT_AUTHORIZATION"]) for cond in ("RAW", "RAG_REVISED")]:
            counts = Counter()
            for r in subset:
                if r["correct"]:
                    category = "EXACT_CORRECT"
                elif r["reference_answerability"] == "UNANSWERABLE" or r["predicted_answerability"] == "UNANSWERABLE" or r["predicted_outcome"] == "UNCERTAIN" or r["reference_outcome"] == "UNCERTAIN":
                    category = "UNCERTAIN_OR_UNANSWERABLE_TRANSITION"
                elif r["reference_outcome"] in {"REJECT", "REJECT_WITH_ALTERNATIVE"} and r["predicted_outcome"] in {"APPROVE", "CONDITIONAL_APPROVE"}:
                    category = "UNSAFE_PERMISSIVE_ERROR"
                elif r["reference_outcome"] in {"APPROVE", "CONDITIONAL_APPROVE"} and r["predicted_outcome"] in {"REJECT", "REJECT_WITH_ALTERNATIVE"}:
                    category = "CONSERVATIVE_RESTRICTIVE_ERROR"
                else:
                    category = "OTHER_MISMATCH"
                counts[category] += 1
            for category, count in sorted(counts.items()):
                output["preflight_safety_direction"].append({"model_id": mid, "scope": scope, "condition": condition, "category": category, "count": count, "denominator": len(subset), "rate": count/len(subset)})
    return output


def check_table(name: str, rows: list[dict], directory: Path) -> None:
    expected = pd.read_csv(directory / f"{name}.csv")
    actual = pd.DataFrame(rows)
    if set(actual.columns) != set(expected.columns) or len(actual) != len(expected):
        raise ValueError(f"{name}: table structure differs")
    keys = [c for c in ["model_id", "scope", "source_kind", "condition", "task_type", "category"] if c in actual]
    actual = actual.sort_values(keys).reset_index(drop=True)[expected.columns]
    expected = expected.sort_values(keys).reset_index(drop=True)
    for column in expected:
        if pd.api.types.is_numeric_dtype(expected[column]):
            if not np.allclose(actual[column].astype(float), expected[column], rtol=0, atol=1e-12):
                raise ValueError(f"{name}: values differ in {column}")
        elif actual[column].astype(str).tolist() != expected[column].astype(str).tolist():
            raise ValueError(f"{name}: labels differ in {column}")
    print(f"PASS {name}: {len(rows)} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RESULTS / "case_results.csv")
    parser.add_argument("--references", type=Path, default=RESULTS / "reference_labels.csv")
    parser.add_argument("--settings", type=Path, default=RESULTS / "model_settings.json")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-dir", type=Path, default=RESULTS)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if not args.check and args.output_dir is None:
        parser.error("Choose --check or --output-dir.")
    rows = read_rows(args.input)
    for row in rows:
        row["layer"] = int(row["layer"])
        row["valid"] = truth(row["valid"])
        row["correct"] = truth(row["correct"])
    if len(rows) != 2488 or not all(r["valid"] and r["source_kind"] == "validity_recovered" for r in rows):
        raise SystemExit("Expected 2,488 valid, recovered case-score records.")
    models = [m["model_id"] for m in json.loads(args.settings.read_text())["models"]]
    tables = compute(rows, read_rows(args.references), models)
    if args.check:
        for name, values in tables.items():
            check_table(name, values, args.check_dir)
    if args.output_dir:
        if args.output_dir.resolve() == args.input.parent.resolve():
            raise SystemExit("Use a separate output directory; the released tables are not overwritten.")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, values in tables.items():
            pd.DataFrame(values).to_csv(args.output_dir / f"{name}.csv", index=False)
    print("Recomputed the released statistics from case scores; no inference was performed.")


if __name__ == "__main__":
    main()

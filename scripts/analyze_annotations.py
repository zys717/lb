#!/usr/bin/env python3
"""Recompute the recorded A1/A2 agreement statistics using Python's standard library.

The statistical definitions follow the original annotation analysis. The input
workbook is the preserved, readable A1 copy; this script does not repair or edit it.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import posixpath
import re
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "annotations"
SHEET_NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def read_annotation_sheet(path: Path) -> list[dict[str, str]]:
    """Read stored cell values from the A1 Annotation sheet without dependencies."""
    with ZipFile(path) as book:
        shared = []
        if "xl/sharedStrings.xml" in book.namelist():
            shared = [
                "".join(node.itertext())
                for node in ET.fromstring(book.read("xl/sharedStrings.xml"))
                .findall("s:si", SHEET_NS)
            ]
        relationships = {
            node.attrib["Id"]: node.attrib["Target"]
            for node in ET.fromstring(book.read("xl/_rels/workbook.xml.rels"))
        }
        workbook = ET.fromstring(book.read("xl/workbook.xml"))
        sheet = next(
            node for node in workbook.findall("s:sheets/s:sheet", SHEET_NS)
            if node.attrib["name"] == "Annotation"
        )
        target = relationships[sheet.attrib[f"{{{REL_NS}}}id"]]
        member = target.lstrip("/") if target.startswith("/") else posixpath.normpath(
            posixpath.join("xl", target)
        )
        rows = []
        for row in ET.fromstring(book.read(member)).findall("s:sheetData/s:row", SHEET_NS):
            cells = {}
            for cell in row.findall("s:c", SHEET_NS):
                column = re.match(r"[A-Z]+", cell.attrib["r"]).group()
                if cell.find("s:f", SHEET_NS) is not None:
                    raise ValueError(f"Unexpected formula in Annotation!{cell.attrib['r']}")
                value = cell.find("s:v", SHEET_NS)
                text = value.text or "" if value is not None else ""
                if cell.attrib.get("t") == "s" and text:
                    text = shared[int(text)]
                elif cell.attrib.get("t") == "inlineStr":
                    text = "".join(cell.find("s:is", SHEET_NS).itertext())
                cells[column] = text
            if any(cells.values()):
                rows.append(cells)
    headers = {column: normalize_header(value) for column, value in rows[0].items()}
    return [
        {name: row.get(column, "").strip() for column, name in headers.items()}
        for row in rows[1:]
    ]


def normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("/", "_")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def load_comparisons(data_dir: Path) -> list[dict]:
    a1 = read_annotation_sheet(data_dir / "A1.xlsx")
    a2 = [
        {normalize_header(key): value.strip() for key, value in row.items()}
        for row in read_csv(data_dir / "A2.csv")
    ]

    def key(row):
        return f"{row['scenario_id']}/{row['case_id']}"

    def outcome(row):
        return "UNANSWERABLE" if row["answerability"] == "UNANSWERABLE" else row["primary_outcome"]

    by_a2 = {key(row): row for row in a2}
    if len(a1) != 254 or len(a2) != 254:
        raise ValueError("The recorded annotation corpus requires 254 rows per annotator.")
    if len({key(row) for row in a1}) != 254 or len(by_a2) != 254:
        raise ValueError("Duplicate annotation case identifier.")
    if {key(row) for row in a1} != set(by_a2):
        raise ValueError("A1 and A2 case identifiers differ.")
    comparisons = []
    for first in a1:
        second = by_a2[key(first)]
        for field in ("layer", "task_type", "endpoint_family"):
            if first[field] != second[field]:
                raise ValueError(f"{key(first)}: inconsistent {field} between A1 and A2.")
        for row in (first, second):
            if row["answerability"] not in {"ANSWERABLE", "UNANSWERABLE"} or not outcome(row):
                raise ValueError(f"{key(first)}: missing outcome or invalid answerability.")
        a1_outcome, a2_outcome = outcome(first), outcome(second)
        comparisons.append({
            "record_no": int(first["record_no"]),
            "key": key(first),
            "layer": int(first["layer"]),
            "task_type": first["task_type"],
            "endpoint_family": first["endpoint_family"],
            "a1_outcome": a1_outcome,
            "a2_outcome": a2_outcome,
            "outcome_agree": a1_outcome == a2_outcome,
            "a1_basis": first["decision_basis"],
            "a2_basis": second["decision_basis"],
            "a1_answerability": first["answerability"],
            "a2_answerability": second["answerability"],
            "a1_rationale": first["short_rationale"],
            "a2_rationale": second["short_rationale"],
            "a1_rule": first["rule___constraint"],
            "a2_rule": second["rule_or_constraint"],
        })
    if {row["record_no"] for row in comparisons} != set(range(1, 255)):
        raise ValueError("Annotation record numbers must cover 1 through 254 exactly once.")
    return comparisons


def load_coordinator_decisions(data_dir: Path, comparisons: list[dict]) -> dict[int, dict]:
    rows = read_csv(data_dir / "coordinator_decisions.csv")
    decisions = {int(row["record_no"]): row for row in rows}
    expected = {
        row["record_no"] for row in comparisons
        if not row["outcome_agree"] or row["a1_answerability"] != row["a2_answerability"]
    }
    if len(rows) != len(decisions) or set(decisions) != expected:
        raise ValueError("Coordinator records must cover each independent disagreement exactly once.")
    for pair in comparisons:
        decision = decisions.get(pair["record_no"])
        if decision is None:
            continue
        for field, value in {
            "record_id": pair["key"], "task_type": pair["task_type"],
            "a1_outcome": pair["a1_outcome"], "a2_outcome": pair["a2_outcome"],
        }.items():
            if decision[field] != value:
                raise ValueError(f"{pair['key']}: coordinator record differs in {field}.")
        answerability = "UNANSWERABLE" if decision["final_outcome"] == "UNANSWERABLE" else "ANSWERABLE"
        if decision["final_answerability"] != answerability:
            raise ValueError(f"{pair['key']}: inconsistent final answerability.")
    return decisions


def wilson(successes: int, n: int) -> list[float]:
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denominator
    return [center - half, center + half]


def agreement(pairs: list[tuple[str, str]]) -> dict:
    n = len(pairs)
    matches = sum(first == second for first, second in pairs)
    first_counts, second_counts = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    # Preserve first-appearance category ordering from the original JavaScript.
    categories = list(dict.fromkeys(value for pair in pairs for value in pair))
    expected = sum(first_counts[value] / n * (second_counts[value] / n) for value in categories)
    observed = matches / n
    return {
        "n": n, "matches": matches, "agreement": observed, "expectedAgreement": expected,
        "kappa": None if expected == 1 else (observed - expected) / (1 - expected),
        "agreement95CI": wilson(matches, n),
    }


def statistics(rows: list[dict]) -> dict:
    return {
        "outcome": agreement([(row["a1_outcome"], row["a2_outcome"]) for row in rows]),
        "decisionBasis": agreement([(row["a1_basis"] or "MISSING", row["a2_basis"] or "MISSING") for row in rows]),
        "answerability": agreement([(row["a1_answerability"], row["a2_answerability"]) for row in rows]),
    }


def build_statistics(comparisons: list[dict], decisions: dict[int, dict]) -> dict:
    overall = statistics(comparisons)
    by_task = {
        task: statistics([row for row in comparisons if row["task_type"] == task])
        for task in sorted({row["task_type"] for row in comparisons})
    }
    reviewed = [row for row in comparisons if row["record_no"] in decisions]
    matches_a1 = sum(decisions[row["record_no"]]["final_outcome"] == row["a1_outcome"] for row in reviewed)
    matches_a2 = sum(decisions[row["record_no"]]["final_outcome"] == row["a2_outcome"] for row in reviewed)
    neither = sum(
        decisions[row["record_no"]]["final_outcome"] not in {row["a1_outcome"], row["a2_outcome"]}
        for row in reviewed
    )
    return {
        # Date of the preserved annotation analysis, not the date of a later rerun.
        "generated_at": "2026-08-12",
        "corpus": {"n": len(comparisons), "layers": sorted({row["layer"] for row in comparisons})},
        "pre_adjudication": {
            "primary_label": overall["outcome"],
            "answerability": overall["answerability"],
            "decision_basis": overall["decisionBasis"],
            "by_task_family": by_task,
        },
        "disposition": {
            "exact_agreements": sum(row["outcome_agree"] for row in comparisons),
            "coordinator_adjudications": len(reviewed),
            "final_match_a1_within_disagreements": matches_a1,
            "final_match_a2_within_disagreements": matches_a2,
            "final_match_neither_within_disagreements": neither,
        },
        "reporting_rule": "Reliability statistics are pre-adjudication only. Report overall exact agreement descriptively and task-family-specific reliability; retain pooled kappa for audit diagnostics only. The final label is not treated as a third independent rating.",
    }


def compare_values(actual, expected, location="result") -> None:
    """Compare recorded results, allowing only floating-point arithmetic noise."""
    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual) != set(expected):
            raise ValueError(f"{location}: fields differ.")
        for key in actual:
            compare_values(actual[key], expected[key], f"{location}.{key}")
    elif isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError(f"{location}: lengths differ.")
        for index, (first, second) in enumerate(zip(actual, expected)):
            compare_values(first, second, f"{location}[{index}]")
    elif isinstance(actual, float) or isinstance(expected, float):
        if not isinstance(actual, (int, float)) or not isinstance(expected, (int, float)):
            raise ValueError(f"{location}: value types differ.")
        if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12):
            raise ValueError(f"{location}: {actual!r} != {expected!r}.")
    elif actual != expected:
        raise ValueError(f"{location}: {actual!r} != {expected!r}.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output", type=Path, help="Output JSON; defaults to agreement_statistics.json.")
    parser.add_argument("--check", action="store_true", help="Compare with the saved JSON without writing.")
    args = parser.parse_args()
    comparisons = load_comparisons(args.data_dir)
    report = build_statistics(comparisons, load_coordinator_decisions(args.data_dir, comparisons))
    output = args.output or args.data_dir / "agreement_statistics.json"
    if args.check:
        compare_values(report, json.loads(output.read_text(encoding="utf-8")))
        print(
            f"Agreement statistics match: {len(comparisons)} pairs; "
            f"{report['pre_adjudication']['primary_label']['matches']} outcome matches; "
            f"{report['pre_adjudication']['answerability']['matches']} answerability matches; "
            f"{report['disposition']['coordinator_adjudications']} reviewed."
        )
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()

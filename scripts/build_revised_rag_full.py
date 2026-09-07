#!/usr/bin/env python3
"""Build the full-corpus revised RAG prompt package without loading labels."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from build_phase2e_prompt_package import LEAK_PATTERNS, ROOT, S026_OPTIONS, sha256_bytes, sha256_text, split_scenario_context, scrub
from build_posthoc_rag_diagnostic import (
    POLICY_CARDS,
    SYSTEM,
    case_fact_evidence,
    deduplicate_evidence,
    find_source_records,
    scope_information_sources,
    selected_source_ids,
)


DEFAULT_CASES = ROOT / "data/main/complex_cases.json"
CONDITION = "RAG_REVISED_FULL"


def build_prompt(record: dict[str, Any], operational: dict[str, Any], evidence: list[dict[str, Any]]) -> str:
    payload: dict[str, Any] = {
        "record_id": record["record_id"],
        "task_type": record["task_type"],
        "endpoint_family": record["endpoint_family"],
        "task_question": record["task_question"],
        "allowed_outcomes": record["allowed_outcomes"],
        "endpoint_policy_card": POLICY_CARDS.get(record["task_type"], []),
        "operational_context_background": operational,
        "case_specific_content": scrub(record.get("case_content") or {}),
        "retrieved_evidence": evidence,
    }
    if record["scenario_id"] == "S026":
        payload["explicit_option_definitions"] = S026_OPTIONS
    return f"{SYSTEM}\n\nINPUT\n{json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source_bytes = args.cases.read_bytes()
    records = json.loads(source_bytes)
    if len(records) != 254 or len({record["record_id"] for record in records}) != 254:
        raise SystemExit("Expected exactly 254 unique case records")

    outputs: list[dict[str, Any]] = []
    leak_hits: list[dict[str, Any]] = []
    scoped_cases: dict[str, list[str]] = {}
    for record in records:
        source_ids = selected_source_ids(record.get("case_content") or {})
        if source_ids:
            scoped_cases[record["record_id"]] = sorted(source_ids)
        scoped_context = scope_information_sources(scrub(record.get("scenario_context") or {}), source_ids)
        operational, scenario_evidence = split_scenario_context(record["scenario_id"], scoped_context)
        exact_sources = find_source_records(scoped_context, source_ids)
        source_evidence = [
            {
                "evidence_id": f"REVISED_SELECTED_SOURCE:{record['record_id']}:{source.get('id', index)}",
                "scenario_id": record["scenario_id"],
                "status": "ACTIVE_CASE_SELECTED_SOURCE",
                "authority": "SUPPLIED_SOURCE_SELECTED_BY_CASE",
                "content": source,
            }
            for index, source in enumerate(exact_sources)
        ]
        evidence = deduplicate_evidence(scenario_evidence + source_evidence + case_fact_evidence(record))
        prompt = build_prompt(record, operational, evidence)
        hits = [pattern for pattern in LEAK_PATTERNS if re.search(pattern, prompt, flags=re.IGNORECASE)]
        if hits:
            leak_hits.append({"record_id": record["record_id"], "patterns": hits})
        outputs.append({
            "run_case_id": f"{record['record_id']}::{CONDITION}",
            "record_id": record["record_id"],
            "scenario_id": record["scenario_id"],
            "case_id": record["case_id"],
            "layer": record["layer"],
            "task_type": record["task_type"],
            "endpoint_family": record["endpoint_family"],
            "allowed_outcomes": record["allowed_outcomes"],
            "condition": CONDITION,
            "evidence_ids": [item["evidence_id"] for item in evidence],
            "prompt": prompt,
        })

    if len(outputs) != 254 or leak_hits:
        raise SystemExit("Expected 254 prompts without answer cues; no output written.")
    prompt_path = args.output_dir / "prompts_rag_revised.jsonl"
    prompt_path.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in outputs), encoding="utf-8")
    print(f"Reconstructed {len(outputs)} RAG_REVISED_FULL prompts: {prompt_path}")


if __name__ == "__main__":
    main()

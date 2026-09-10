#!/usr/bin/env python3
"""Combine reconstructed Layer 1 inputs and complex-case inputs into 622 prompts."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/main"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"Missing input: {path}. Build Layer 1 first if needed.")
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer1", type=Path, default=DATA / "layer1/generated/layer1_raw_prompt_package.jsonl")
    parser.add_argument("--raw", type=Path, default=DATA / "prompts_raw.jsonl")
    parser.add_argument("--rag", type=Path, default=DATA / "prompts_rag_revised.jsonl")
    parser.add_argument("--output", type=Path, default=DATA / "prompts_main_reconstructed.jsonl")
    args = parser.parse_args()
    if args.layer1 == DATA / "layer1/generated/layer1_raw_prompt_package.jsonl":
        subprocess.run([sys.executable, str(Path(__file__).with_name("build_layer1_four_model_package.py")), "--output-dir", str(args.layer1.parent)], check=True)
    l1 = read_jsonl(args.layer1)
    raw = [r for r in read_jsonl(args.raw) if r["condition"] == "RAW"]
    rag = read_jsonl(args.rag)
    if tuple(map(len, (l1, raw, rag))) != (114, 254, 254):
        raise SystemExit("Expected 114 Layer 1, 254 RAW and 254 RAG inputs.")
    rows = [dict(r) for r in l1 + raw]
    for original in rag:
        if original["condition"] != "RAG_REVISED_FULL":
            raise SystemExit("Expected RAG_REVISED_FULL input records.")
        row = dict(original)
        row["condition"] = "RAG_REVISED"
        row["run_case_id"] = f"{row['record_id']}::RAG_REVISED"
        rows.append(row)
    for row in rows:
        row.pop("prompt_sha256", None)
    if len({r["run_case_id"] for r in rows}) != 622:
        raise SystemExit("Input positions are not unique.")
    if Counter(r["condition"] for r in rows) != {"RAW": 368, "RAG_REVISED": 254}:
        raise SystemExit("Unexpected condition counts.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows))
    print(f"Reconstructed 622 prompts: {args.output}")


if __name__ == "__main__":
    main()

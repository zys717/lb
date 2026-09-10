#!/usr/bin/env python3
"""Prepare validity-only repairs, run one repair round, or merge a new run.

Recovery uses strict JSON, 4096 tokens in rounds 1–3,
8192 in rounds 4–7, temperature 0, low reasoning, and five attempts per round.
Only --execute makes requests.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

from run_main_evaluation import PROMPTS, SETTINGS, model_command


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows))


def select_valid(run_dir: Path, model_id: str, before_round: int | None = None) -> dict[str, tuple[str, dict]]:
    original = run_dir / "original" / f"{model_id}.jsonl"
    if not original.is_file():
        raise SystemExit(f"Missing input response file: {original}")
    sources = [("official", original)]
    for directory in sorted((run_dir / "repairs").glob("round_*"), key=lambda p: int(p.name.split("_")[-1])):
        if before_round is not None and int(directory.name.split("_")[-1]) >= before_round:
            continue
        sources.extend((directory.name, p) for p in sorted((directory / "outputs").rglob(f"{model_id}.jsonl")))
    selected = {}
    for source, path in sources:
        for row in read_jsonl(path):
            key = row["run_case_id"]
            if key not in selected and row.get("status") == "OK":
                selected[key] = (source, row)
    return selected


def prepare(run_dir: Path, models: list[dict], prompts: list[dict], round_number: int) -> dict[str, Path]:
    paths = {}
    for model in models:
        model_id = model["model_id"]
        valid = select_valid(run_dir, model_id, before_round=round_number)
        missing = [r for r in prompts if r["run_case_id"] not in valid]
        if missing:
            path = run_dir / "repairs" / f"round_{round_number}" / "prompts" / f"{model_id}.jsonl"
            write_jsonl(path, missing)
            paths[model_id] = path
        print(f"{model_id}: {len(missing)} positions without a valid response")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run", "merge"))
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--prompts", type=Path, default=PROMPTS)
    parser.add_argument("--settings", type=Path, default=SETTINGS)
    parser.add_argument("--round", type=int, choices=range(1, 8))
    parser.add_argument("--output-dir", type=Path, help="Required for merge; use an empty directory.")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    prompts = read_jsonl(args.prompts)
    if len(prompts) != 622 or len({r['run_case_id'] for r in prompts}) != 622:
        raise SystemExit("Expected the complete 622-position input package.")
    models = json.loads(args.settings.read_text())["models"]
    if args.action in {"prepare", "run"}:
        if args.round is None:
            parser.error("--round is required for prepare/run")
        paths = prepare(args.run_dir, models, prompts, args.round)
        if args.action == "run":
            tokens = 4096 if args.round <= 3 else 8192
            output = args.run_dir / "repairs" / f"round_{args.round}" / "outputs"
            for model in models:
                if model["model_id"] in paths:
                    subprocess.run(model_command(model, paths[model["model_id"]], output,
                                                 tokens=tokens, strict=True, execute=args.execute, attempts=5), check=True)
        return
    if args.output_dir is None:
        parser.error("--output-dir is required for merge")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit("Merge output directory must be empty; existing responses are not overwritten.")
    combined = {}
    for model in models:
        model_id = model["model_id"]
        valid = select_valid(args.run_dir, model_id)
        missing = [r["run_case_id"] for r in prompts if r["run_case_id"] not in valid]
        if missing:
            raise SystemExit(f"{model_id}: {len(missing)} positions still lack a valid response; nothing merged.")
        rows = []
        for prompt in prompts:
            source, row = valid[prompt["run_case_id"]]
            rows.append({**row, "selected_response_source": source})
        combined[model_id] = rows
    for model_id, rows in combined.items():
        write_jsonl(args.output_dir / f"{model_id}.jsonl", rows)
        print(model_id, len(rows), dict(Counter(r["selected_response_source"] for r in rows)))


if __name__ == "__main__":
    main()

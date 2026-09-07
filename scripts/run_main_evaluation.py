#!/usr/bin/env python3
"""Run the four specified models on the 622 reconstructed inputs.

The default is an offline dry run. --execute makes API requests using a key
already set in the process environment; this program never reads .env files.
New responses are a new run, not the original current_openweight_20260826_v3.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "data/main/results/model_settings.json"
PROMPTS = ROOT / "data/main/prompts_main_reconstructed.jsonl"
RUNNER = Path(__file__).with_name("run_phase2e_evaluation.py")


def model_command(model: dict, prompts: Path, output_dir: Path, *, tokens: int = 2048,
                  strict: bool = False, execute: bool = False, attempts: int = 3) -> list[str]:
    cmd = [sys.executable, str(RUNNER), "--prompts", str(prompts),
           "--model-id", model["model_id"], "--model", model["model"],
           "--provider", "OpenRouter", "--base-url", "https://openrouter.ai/api/v1",
           "--api-key-env", "OPENROUTER_API_KEY", "--upstream-provider", model["upstream_provider"],
           "--quantization", model["quantization"], "--reasoning-effort", "low",
           "--conditions", "RAW,RAG_REVISED", "--output-dir", str(output_dir),
           "--temperature", "0", "--max-tokens", str(tokens),
           "--timeout", "180" if strict else "120", "--max-attempts", str(attempts)]
    if strict:
        cmd.append("--strict-json-schema")
    if not execute:
        cmd.append("--dry-run")
    return cmd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts", type=Path, default=PROMPTS)
    parser.add_argument("--settings", type=Path, default=SETTINGS)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.prompts.is_file():
        raise SystemExit("Missing combined prompts. Run build_main_prompts.py first.")
    rows = [json.loads(x) for x in args.prompts.read_text().splitlines() if x.strip()]
    if len(rows) != 622 or len({r["run_case_id"] for r in rows}) != 622:
        raise SystemExit("Expected exactly 622 unique main-experiment inputs.")
    for model in json.loads(args.settings.read_text())["models"]:
        subprocess.run(model_command(model, args.prompts, args.run_dir / "original", execute=args.execute), check=True)
    print("New inference run completed." if args.execute else "Offline dry run completed; no model was called.")


if __name__ == "__main__":
    main()

"""
Run a RAG-style prompt for S009/S021 and optionally call a Gemini model.

Usage examples:
  # Just print the prompt (no network call)
  python rag/run_rag_llm.py --scenario S009 --speed-mps 28.5

  # Call Gemini if google-generativeai is installed and GEMINI_API_KEY is set
  GEMINI_API_KEY=your_key python rag/run_rag_llm.py --scenario S021 --battery-percent 35
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.append(str(HERE))

from extract_constraints import extract_s009, extract_s021, load_jsonc  # type: ignore  # noqa: E402
from kg_schema import Constraint, SourceType, sample_constraints  # type: ignore  # noqa: E402
from retriever import retrieve  # type: ignore  # noqa: E402


def load_constraints() -> List[Constraint]:
    constraints: List[Constraint] = []
    constraints += extract_s009(ROOT / "scenarios" / "basic" / "S009_speed_limit.jsonc")
    constraints += extract_s021(ROOT / "scenarios" / "intermediate" / "S021_emergency_battery_dilemma.jsonc")
    constraints += [c for c in sample_constraints() if c.source_type == SourceType.REGULATION]
    return constraints


def build_rag_prompt(mission: Dict, retrieved: Dict[str, List[Constraint]]) -> str:
    ctx_lines = []
    for concept, items in retrieved.items():
        for c in items:
            ctx_lines.append(
                f"- {concept}: {c.canonical_value}{c.canonical_unit or ''} "
                f"({c.source_type.value} {c.source_ref})"
            )
    ctx = "\n".join(ctx_lines) if ctx_lines else "(no constraints found)"
    return (
        "You are a dispatch AI. Decide APPROVE or REJECT with cited constraints.\n"
        "Retrieved constraints:\n"
        f"{ctx}\n"
        f"Mission: {json.dumps(mission, ensure_ascii=False)}\n"
        "Decide and cite which constraints are satisfied/violated. Respond with JSON:\n"
        '{ "decision": "APPROVE|REJECT|CONDITIONAL|UNCERTAIN", "reasons": [...], "citations": [...] }'
    )


def call_gemini(prompt: str, model: str = "gemini-2.0-flash") -> Optional[str]:
    """
    Call Gemini if google-generativeai is available and GEMINI_API_KEY is set.
    Returns text or None on failure.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set; skipping LLM call.")
        return None
    try:
        import google.generativeai as genai
    except Exception as e:
        print(f"google-generativeai not installed ({e}); skipping LLM call.")
        return None
    try:
        genai.configure(api_key=api_key)
        client = genai.GenerativeModel(model)
        resp = client.generate_content(prompt)
        return resp.text
    except Exception as e:
        print(f"LLM call failed: {e}")
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RAG prompt for S009/S021")
    parser.add_argument("--scenario", choices=["S009", "S021"], required=True, help="Scenario id")
    parser.add_argument("--speed-mps", type=float, help="Planned speed (m/s) for S009")
    parser.add_argument("--battery-percent", type=float, help="Current battery percent for S021")
    parser.add_argument("--model", default="gemini-2.0-flash", help="Gemini model name")
    parser.add_argument("--no-call", action="store_true", help="Only print prompt, do not call LLM")
    parser.add_argument("--output", type=Path, help="Save LLM response and context to JSON file")
    parser.add_argument("--batch", action="store_true", help="Run all test_cases from scenario file and save aggregated JSON")
    return parser.parse_args()


def clean_json_text(text: str) -> str:
    """Strip markdown fences and whitespace to get raw JSON."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_+-]*", "", text, flags=re.MULTILINE).strip()
        text = re.sub(r"```$", "", text, flags=re.MULTILINE).strip()
    return text


def run_single(mission: Dict, constraints: List[Constraint], model: str, do_call: bool) -> Tuple[str, Optional[Dict]]:
    retrieved = retrieve(constraints, mission)
    prompt = build_rag_prompt(mission, retrieved)
    print("=== RAG Prompt ===")
    print(prompt)
    llm_text = None
    parsed = None
    if do_call:
        llm_text = call_gemini(prompt, model=model)
        if llm_text is not None:
            print("\n=== LLM Response ===")
            print(llm_text)
            try:
                parsed = json.loads(clean_json_text(llm_text))
            except Exception:
                parsed = None
    payload = {
        "mission": mission,
        "retrieved_constraints": {
            k: [
                {
                    "constraint_id": c.constraint_id,
                    "concept": c.concept,
                    "canonical_value": c.canonical_value,
                    "canonical_unit": c.canonical_unit,
                    "source_type": c.source_type.value,
                    "source_ref": c.source_ref,
                }
                for c in v
            ]
            for k, v in retrieved.items()
        },
        "prompt": prompt,
        "model": model,
        "llm_raw": llm_text,
        "llm_parsed": parsed,
    }
    return prompt, payload


def run_batch_s009(constraints: List[Constraint], model: str, do_call: bool) -> Dict:
    scenario_path = ROOT / "scenarios" / "basic" / "S009_speed_limit.jsonc"
    data = load_jsonc(scenario_path)
    results = []
    correct = 0
    for tc in data.get("test_cases", []):
        speed = tc.get("test_points", {}).get("target_velocity_ms")
        mission = {"aircraft_class": "light", "speed_mps": speed}
        prompt, payload = run_single(mission, constraints, model, do_call)
        expected = tc.get("expected_result", {}).get("decision")
        llm_decision = payload["llm_parsed"].get("decision") if payload.get("llm_parsed") else None
        if expected and llm_decision and str(expected).upper() == str(llm_decision).upper():
            correct += 1
        results.append(
            {
                "test_case_id": tc.get("id"),
                "description": tc.get("description"),
                "command": tc.get("command"),
                "mission": mission,
                "expected_decision": expected,
                "llm_decision": llm_decision,
                "prompt": prompt,
                "llm_raw": payload["llm_raw"],
                "llm_parsed": payload["llm_parsed"],
                "retrieved_constraints": payload["retrieved_constraints"],
            }
        )
    total = len(results)
    acc_percent = f"{(correct/total*100):.1f}%" if total else None
    return {
        "scenario": "S009_SpeedLimit",
        "scenario_type": "speed",
        "summary": {
            "total_test_cases": total,
            "llm_calls": sum(1 for r in results if r["llm_raw"]),
            "llm_accuracy": f"{correct}/{total}" if total else None,
            "llm_accuracy_percent": acc_percent,
        },
        "results": results,
    }


def main() -> None:
    args = parse_args()
    constraints = load_constraints()

    if args.batch:
        if args.scenario != "S009":
            print("Batch mode currently supported for S009 only.")
            sys.exit(1)
        agg = run_batch_s009(constraints, args.model, not args.no_call)
        if not args.output:
            print("Batch mode requires --output to save results.")
            sys.exit(1)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(agg, ensure_ascii=False, indent=2))
        print(f"\nSaved batch output to {args.output}")
        return

    # Single mission mode
    if args.scenario == "S009":
        mission = {
            "aircraft_class": "light",
            "speed_mps": args.speed_mps if args.speed_mps is not None else 28.5,
        }
    else:  # S021
        mission = {
            "aircraft_class": "multirotor",
            "mission_type": "medical",
            "battery_percent": args.battery_percent if args.battery_percent is not None else 35.0,
        }

    _, payload = run_single(mission, constraints, args.model, not args.no_call)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload.update({"scenario": args.scenario})
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"\nSaved output to {args.output}")


if __name__ == "__main__":
    main()

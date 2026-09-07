#!/usr/bin/env python3
"""Provider-neutral runner for the frozen Phase 2E prompt package.

This runner never reads reference labels. Scoring is performed separately.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import random
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import certifi
except ImportError:  # pragma: no cover - system trust store remains the fallback
    certifi = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPTS = ROOT / "data/main/prompts_main_reconstructed.jsonl"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def extract_json(text: str) -> dict[str, Any]:
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.strip("`")
        if clean.lower().startswith("json"):
            clean = clean[4:].lstrip()
    try:
        parsed = json.loads(clean)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    start = clean.find("{")
    end = clean.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(clean[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("No parseable JSON object in response")


def normalize(parsed: dict[str, Any], allowed: list[str]) -> dict[str, Any]:
    answerability = str(parsed.get("answerability", "")).strip().upper()
    outcome = parsed.get("primary_outcome")
    outcome = None if outcome is None else str(outcome).strip().upper()
    basis = str(parsed.get("decision_basis", "")).strip().upper()
    errors: list[str] = []
    if answerability not in {"ANSWERABLE", "UNANSWERABLE"}:
        errors.append("INVALID_ANSWERABILITY")
    if answerability == "UNANSWERABLE":
        outcome = "UNANSWERABLE"
    elif outcome not in set(allowed):
        errors.append("INVALID_PRIMARY_OUTCOME")
    if basis not in {"DETERMINISTIC", "REGULATORY", "INTERPRETIVE", "MIXED"}:
        errors.append("INVALID_DECISION_BASIS")
    return {
        "answerability": answerability or None,
        "primary_outcome": outcome,
        "decision_basis": basis or None,
        "rationale": str(parsed.get("rationale", "")).strip(),
        "rule_or_constraint": str(parsed.get("rule_or_constraint", "")).strip(),
        "validation_errors": errors,
    }


def call_openai_compatible(
    *, base_url: str, api_key: str, model: str, prompt: str,
    temperature: float, max_tokens: int, timeout: float,
    upstream_provider: str | None, quantization: str | None,
    disable_reasoning: bool, reasoning_effort: str | None,
    strict_json_schema: bool,
) -> tuple[str, dict[str, Any]]:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if upstream_provider:
        payload["provider"] = {
            "only": [upstream_provider],
            "allow_fallbacks": False,
            **({"quantizations": [quantization]} if quantization else {}),
        }
    if disable_reasoning:
        payload["reasoning"] = {"enabled": False}
    elif reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}
    if strict_json_schema:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "lae_bench_decision",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "answerability": {"type": "string", "enum": ["ANSWERABLE", "UNANSWERABLE"]},
                        "primary_outcome": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "decision_basis": {
                            "type": "string",
                            "enum": ["DETERMINISTIC", "REGULATORY", "INTERPRETIVE", "MIXED"],
                        },
                        "rationale": {"type": "string"},
                        "rule_or_constraint": {"type": "string"},
                    },
                    "required": [
                        "answerability", "primary_outcome", "decision_basis",
                        "rationale", "rule_or_constraint",
                    ],
                    "additionalProperties": False,
                },
            },
        }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where() if certifi else None)
    with urllib.request.urlopen(request, timeout=timeout, context=ssl_context) as response:
        body = json.loads(response.read().decode("utf-8"))
    choices = body.get("choices") or []
    if not choices:
        raise ValueError("Provider returned no choices")
    message = choices[0].get("message") or {}
    return str(message.get("content") or ""), {
        "provider_model": body.get("model"),
        "upstream_provider": body.get("provider"),
        "finish_reason": choices[0].get("finish_reason"),
        "usage": body.get("usage"),
        "request_id": body.get("request_id") or body.get("id"),
        "reasoning_present": bool(
            message.get("reasoning") or message.get("reasoning_content")
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS)
    parser.add_argument("--model-id", required=True, help="Stable experiment identifier, e.g. qwen_main")
    parser.add_argument("--model", required=True, help="Exact provider model identifier")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key-env", required=True)
    parser.add_argument("--upstream-provider", default=None, help="Pinned upstream provider slug for a routing gateway")
    parser.add_argument("--quantization", default=None, help="Pinned gateway quantization, e.g. fp8")
    parser.add_argument("--disable-reasoning", action="store_true", help="Send a provider-supported reasoning-off control")
    parser.add_argument(
        "--reasoning-effort",
        choices=("minimal", "low", "medium", "high"),
        default=None,
        help="Send a common provider-supported reasoning effort",
    )
    parser.add_argument("--strict-json-schema", action="store_true", help="Require the provider to generate against the response JSON schema")
    parser.add_argument("--conditions", default="RAW,RAG_REVISED", help="Comma-separated conditions")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    args.prompts = args.prompts.resolve()
    args.output_dir = args.output_dir.resolve()
    if args.disable_reasoning and args.reasoning_effort:
        raise SystemExit("--disable-reasoning and --reasoning-effort are mutually exclusive")

    key = None if args.dry_run else os.environ.get(args.api_key_env)
    if not args.dry_run and not key:
        raise SystemExit(f"Missing API key environment variable: {args.api_key_env}")
    conditions = {x.strip() for x in args.conditions.split(",") if x.strip()}
    prompts = [x for x in load_jsonl(args.prompts) if x["condition"] in conditions]
    if args.limit is not None:
        prompts = prompts[: args.limit]
    if not prompts:
        raise SystemExit("No prompts match the requested conditions.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"{args.model_id}.jsonl"
    manifest_path = args.output_dir / f"{args.model_id}.manifest.json"
    if output_path.exists() and not args.resume:
        raise SystemExit(f"Output already exists: {output_path}; use a new directory or --resume.")
    completed: set[str] = set()
    if args.resume and output_path.exists():
        completed = {x["run_case_id"] for x in load_jsonl(output_path) if x.get("status") == "OK"}

    mode = "a" if args.resume else "w"
    success = failure = skipped = 0
    started = datetime.now(timezone.utc).isoformat()
    with output_path.open(mode, encoding="utf-8") as sink:
        for item in prompts:
            if item["run_case_id"] in completed:
                skipped += 1
                continue
            base = {
                "run_case_id": item["run_case_id"],
                "record_id": item["record_id"],
                "scenario_id": item["scenario_id"],
                "task_type": item["task_type"],
                "endpoint_family": item["endpoint_family"],
                "condition": item["condition"],
                "model_id": args.model_id,
                "model": args.model,
                "provider": args.provider,
                "requested_at": datetime.now(timezone.utc).isoformat(),
            }
            if args.dry_run:
                row = {**base, "status": "DRY_RUN", "attempts": 0, "raw_response": None, "parsed_response": None, "normalized_response": None}
                sink.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                sink.flush()
                success += 1
                continue
            last_error = None
            for attempt in range(1, args.max_attempts + 1):
                try:
                    raw, metadata = call_openai_compatible(
                        base_url=args.base_url, api_key=key or "", model=args.model,
                        prompt=item["prompt"], temperature=args.temperature,
                        max_tokens=args.max_tokens, timeout=args.timeout,
                        upstream_provider=args.upstream_provider,
                        quantization=args.quantization,
                        disable_reasoning=args.disable_reasoning,
                        reasoning_effort=args.reasoning_effort,
                        strict_json_schema=args.strict_json_schema,
                    )
                    parsed = extract_json(raw)
                    normalized = normalize(parsed, item["allowed_outcomes"])
                    status = "OK" if not normalized["validation_errors"] else "FORMAT_ERROR"
                    if status == "FORMAT_ERROR" and attempt < args.max_attempts:
                        last_error = "FORMAT_ERROR: " + ",".join(normalized["validation_errors"])
                        time.sleep((2 ** (attempt - 1)) + random.random())
                        continue
                    row = {**base, "status": status, "attempts": attempt, "raw_response": raw, "parsed_response": parsed, "normalized_response": normalized, "provider_metadata": metadata}
                    sink.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                    sink.flush()
                    success += int(status == "OK")
                    failure += int(status != "OK")
                    break
                except (
                    urllib.error.URLError,
                    http.client.HTTPException,
                    ConnectionError,
                    TimeoutError,
                    ValueError,
                    json.JSONDecodeError,
                ) as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    if attempt < args.max_attempts:
                        time.sleep((2 ** (attempt - 1)) + random.random())
            else:
                row = {**base, "status": "CALL_OR_PARSE_FAILURE", "attempts": args.max_attempts, "error": last_error, "raw_response": None, "parsed_response": None, "normalized_response": None}
                sink.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                sink.flush()
                failure += 1

    manifest = {
        "run_id": f"{args.model_id}-{started}",
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "provider": args.provider,
        "upstream_provider": args.upstream_provider,
        "quantization": args.quantization,
        "base_url": args.base_url,
        "model_id": args.model_id,
        "model": args.model,
        "prompt_package": display_path(args.prompts),
        "conditions": sorted(conditions),
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "timeout_seconds": args.timeout,
        "max_attempts": args.max_attempts,
        "reasoning_disabled": args.disable_reasoning,
        "reasoning_effort": args.reasoning_effort,
        "strict_json_schema": args.strict_json_schema,
        "dry_run": args.dry_run,
        "counts": {"selected": len(prompts), "success_or_dry_run": success, "failure": failure, "resume_skipped": skipped},
        "output": display_path(output_path),
        "reference_labels_loaded": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run the retained civil diagnostic prompts and save complete API records.

Without --execute, validate inputs and show the planned call settings offline.
Reference labels are not read by this program. Only failed calls or invalid JSON
are retried, with the same prompt and settings, at most three attempts per case.
An explicit targeted rerun replaces all selected cases, preserving their prior
responses in the same file and identifying the result as a targeted rerun.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import ssl
import time
import urllib.error
import urllib.request

import certifi

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"APPROVE", "CONDITIONAL_APPROVE", "REJECT", "REJECT_WITH_ALTERNATIVE", "UNCERTAIN", "EXPLAIN_ONLY"}


def now():
    return datetime.now(timezone.utc).isoformat()


def parse_response(body):
    content = body["choices"][0]["message"]["content"]
    value = json.loads(content)
    if value.get("decision") not in ALLOWED:
        raise ValueError("Invalid decision token")
    if not isinstance(value.get("reasoning"), str) or not value["reasoning"].strip():
        raise ValueError("Missing reasoning")
    for name in ["conditions", "requested_clarifications"]:
        if not isinstance(value.get(name), list) or not all(isinstance(x, str) for x in value[name]):
            raise ValueError("Invalid " + name)
    alternative = value.get("alternative")
    # An unused alternative may be JSON null. It is not a failed decision.
    if alternative is not None and not isinstance(alternative, str):
        raise ValueError("Invalid alternative")
    if value["decision"] == "REJECT_WITH_ALTERNATIVE" and not alternative:
        raise ValueError("Missing required alternative")
    return value


def run_case(item, settings, key):
    payload = {**settings, "messages": [{"role": "user", "content": item["prompt"]}]}
    result = {"case_id": item["case_id"], "request": payload, "attempts": [], "status": "FAILED"}
    context = ssl.create_default_context(cafile=certifi.where())
    for attempt in range(1, 4):
        record = {"attempt": attempt, "started_at": now()}
        try:
            request = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=120, context=context) as response:
                record["http_status"] = response.status
                record["response"] = json.load(response)
            if record["response"]["choices"][0].get("finish_reason") != "stop":
                raise ValueError("Response did not finish normally")
            record["parsed"] = parse_response(record["response"])
            record["status"] = "OK"
        except urllib.error.HTTPError as exc:
            record.update(http_status=exc.code, error_body=exc.read().decode(errors="replace"), status="CALL_ERROR")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            record.update(error=str(exc), status="CALL_ERROR")
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            record.update(error=str(exc), status="FORMAT_ERROR")
        record["completed_at"] = now()
        result["attempts"].append(record)
        if record["status"] == "OK":
            result.update(status="OK", selected_attempt=attempt)
            break
        if record.get("http_status") in {400, 401, 402, 403, 404}:
            break
        if attempt < 3:
            time.sleep(2 * attempt)
    return result


def save(path, run):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--upstream-provider", default="deepinfra")
    parser.add_argument("--quantization", default=None)
    parser.add_argument("--reasoning-effort", choices=["low", "medium", "high"], default=None)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--prompts", type=Path, default=ROOT / "data/civil/prompts.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/civil/run.json")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--rerun-case-ids", help="Comma-separated case IDs to replace in an existing complete run")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.workers <= 8:
        raise SystemExit("Use between one and eight workers")
    items = json.loads(args.prompts.read_text())
    expected = {f"C{s:03d}/TC{i}" for s in range(1, 16) for i in range(1, 13)}
    if len(items) != 180 or {x["case_id"] for x in items} != expected:
        raise SystemExit("Expected the complete 180-case diagnostic")
    if any(set(x) != {"case_id", "prompt"} or not isinstance(x["prompt"], str) for x in items):
        raise SystemExit("Each input must contain only a case ID and prompt")
    settings = {
        "model": args.model, "temperature": 0, "max_tokens": args.max_tokens,
        "response_format": {"type": "json_object"},
        "provider": {"only": [args.upstream_provider], "allow_fallbacks": False},
    }
    if args.quantization:
        settings["provider"]["quantizations"] = [args.quantization]
    if args.reasoning_effort:
        settings["reasoning"] = {"effort": args.reasoning_effort}
    run = None
    if args.rerun_case_ids is not None:
        selected = args.rerun_case_ids.split(",")
        if len(set(selected)) != len(selected) or not set(selected) <= expected:
            raise SystemExit("Rerun IDs must be unique case IDs from the complete diagnostic")
        run = json.loads(args.output.read_text())
        records = {r["case_id"]: r for r in run["cases"]}
        if len(run["cases"]) != 180 or set(records) != expected or not run.get("completed_at"):
            raise SystemExit("Targeted replacement requires an existing complete 180-case run")
        if any(not r.get("completed_at") for r in run.get("reruns", [])):
            raise SystemExit("An earlier targeted rerun is incomplete")
        if run["settings"] != settings:
            raise SystemExit("Rerun settings must match the retained run exactly")
        for item in items:
            request = {**settings, "messages": [{"role": "user", "content": item["prompt"]}]}
            if records[item["case_id"]]["request"] != request:
                raise SystemExit("Saved request differs from the retained prompt: " + item["case_id"])
        items = [item for item in items if item["case_id"] in selected]
    print(json.dumps({"cases": len(items), "settings": settings, "max_attempts_per_case": 3}, indent=2), flush=True)
    if not args.execute:
        print("Offline check only; no model calls or result files.")
        return
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is not set")
    if args.output.exists() and run is None:
        raise SystemExit("Output already exists; retained runs are not overwritten")
    if run is None:
        run = {
            "started_at": now(), "settings": settings, "planned_cases": 180,
            "selection_rule": "First structurally valid response; at most three unchanged attempts; references excluded",
            "cases": [],
        }
        batch = run
    else:
        run.setdefault("first_run_completed_at", run["completed_at"])
        batch = {
            "started_at": now(), "planned_cases": len(items),
            "case_ids": [item["case_id"] for item in items],
            "selection_basis": "Author-selected cases that disagreed with fixed references in the first run",
            "replacement_rule": "Replace every selected case with its first usable rerun response, regardless of agreement; unresolved responses count as invalid",
            "cases": [],
        }
        run.setdefault("reruns", []).append(batch)
    save(args.output, run)
    first = run_case(items[0], settings, key)
    batch["cases"].append(first)
    save(args.output, run)
    if first["attempts"][-1].get("http_status") in {400, 401, 402, 403, 404}:
        raise SystemExit("API rejected the initial request; inspect the saved response before continuing")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_case, item, settings, key): item["case_id"] for item in items[1:]}
        for future in as_completed(futures):
            batch["cases"].append(future.result())
            batch["cases"].sort(key=lambda x: (x["case_id"].split('/')[0], int(x["case_id"].split('TC')[1])))
            save(args.output, run)
            n = len(batch["cases"])
            if n % 10 == 0 or n == len(items):
                print(f"Completed {n}/{len(items)}; valid {sum(x['status'] == 'OK' for x in batch['cases'])}", flush=True)
    failed = sum(x["status"] != "OK" for x in batch["cases"])
    batch["completed_at"] = now()
    if args.rerun_case_ids is not None:
        for replacement in batch.pop("cases"):
            previous = records[replacement["case_id"]]
            history = previous.get("previous_results", [])
            replacement["previous_results"] = [*history, {k: v for k, v in previous.items() if k != "previous_results"}]
            records[replacement["case_id"]] = replacement
        run["cases"] = [records[item["case_id"]] for item in run["cases"]]
        run["selection_rule"] = "First usable response per case, with author-selected targeted replacements; first-run responses retained in previous_results"
        run["completed_at"] = batch["completed_at"]
    save(args.output, run)
    print(f"Saved complete API records. Unresolved cases: {failed}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

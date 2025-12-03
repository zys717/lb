"""
Extractor for operational (SOP) constraints and regulation snippets for S021–S040.

Outputs:
- outputs/constraints_extracted.json : scenario policy snippets (SOP layer).
- outputs/regulation_chunks.json     : chunked regulation text (REGULATION layer).

Dual-layer note: scenario-derived "policy snippets" are marked as SourceType.SOP.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
if str(HERE) not in sys.path:
    sys.path.append(str(HERE))

from controlled_vocab import CONTROLLED_VOCAB  # type: ignore  # noqa: E402
from kg_schema import Constraint, SourceType, to_canonical_speed  # type: ignore  # noqa: E402


def load_jsonc(path: Path) -> dict:
    """
    Minimal JSONC loader: strips // comments and parses JSON.
    Suitable for the current scenario files that only use // comments.
    """
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"//.*", "", text)
    return json.loads(text)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    """Simple character-based chunker for regulation text."""
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    chunks: List[str] = []
    i = 0
    while i < len(text):
        chunk = text[i : i + chunk_size]
        chunks.append(chunk.strip())
        i += max(chunk_size - overlap, 1)
    return [c for c in chunks if c]


def infer_concepts(text: str) -> List[str]:
    """Lightweight concept tagging via substring match against controlled vocab synonyms."""
    lowered = text.lower()
    concepts: List[str] = []
    for item in CONTROLLED_VOCAB:
        concept = item["concept"]
        for syn in item.get("synonyms", []):
            if syn.lower() in lowered:
                concepts.append(concept)
                break
    return list(dict.fromkeys(concepts))  # dedupe while preserving order


def add_policy_snippet(
    out: List[Dict],
    file_path: Path,
    snippet: str,
    label: str,
    concepts_hint: Optional[Sequence[str]] = None,
) -> None:
    concepts = list(concepts_hint or [])
    if not concepts:
        concepts = infer_concepts(snippet)
        if not concepts:
            concepts = ["Ambiguity"]
    out.append(
        {
            "constraint_id": f"{file_path.stem}_{label}",
            "file": str(file_path),
            "concept": concepts[0],
            "concepts": concepts,
            "source_type": SourceType.SOP.value,
            "source_ref": file_path.name,
            "text": snippet,
        }
    )


def extract_parameters_from_rule(rule_id: str, params: dict, file_path: Path) -> List[Dict]:
    extracted: List[Dict] = []
    for name, body in params.items():
        if not isinstance(body, dict):
            continue
        value = body.get("value")
        unit = body.get("unit")
        description = body.get("description", "")
        concepts = infer_concepts(f"{name} {description}")
        concept = concepts[0] if concepts else "OperationalPolicy"
        entry: Dict[str, Optional[str | float]] = {
            "constraint_id": f"{file_path.stem}_{rule_id}_{name}",
            "file": str(file_path),
            "concept": concept,
            "concepts": concepts,
            "source_type": SourceType.SOP.value,
            "source_ref": file_path.name,
            "raw_value": value if isinstance(value, (int, float)) else None,
            "raw_unit": unit,
            "canonical_value": None,
            "canonical_unit": unit,
        }
        # Speed canonical conversion if obvious
        if concept == "Speed" and isinstance(value, (int, float)) and unit:
            try:
                canonical = to_canonical_speed(value, unit)
                entry["canonical_value"] = canonical["canonical_value"]  # type: ignore[index]
                entry["canonical_unit"] = canonical["canonical_unit"]  # type: ignore[index]
            except Exception:
                pass
        extracted.append(entry)
        if description:
            add_policy_snippet(extracted, file_path, description, f"{rule_id}_{name}_desc", concepts_hint=concepts)
    return extracted


def extract_scenario(file_path: Path) -> List[Dict]:
    data = load_jsonc(file_path)
    out: List[Dict] = []

    # Regulation references -> SOP snippets (policy cues for prompt grounding)
    for idx, ref in enumerate(data.get("regulation_references", []) or []):
        add_policy_snippet(out, file_path, str(ref), f"regref_{idx}", concepts_hint=["RegulationVersion"])

    # Rules parameters + descriptions
    for rule_id, rule_body in (data.get("rules") or {}).items():
        params = rule_body.get("parameters", {}) if isinstance(rule_body, dict) else {}
        if isinstance(params, dict):
            out.extend(extract_parameters_from_rule(rule_id, params, file_path))
        for key in ["description", "decision_logic", "exemptions", "policies", "policy_stack"]:
            body = rule_body.get(key) if isinstance(rule_body, dict) else None
            if isinstance(body, list):
                for idx, entry in enumerate(body):
                    if isinstance(entry, str):
                        add_policy_snippet(out, file_path, entry, f"{rule_id}_{key}_{idx}")
            elif isinstance(body, str):
                add_policy_snippet(out, file_path, body, f"{rule_id}_{key}")

    # Policy stacks in other keys
    for key in ["policy_stack", "policies"]:
        body = data.get(key)
        if isinstance(body, list):
            for idx, entry in enumerate(body):
                if isinstance(entry, str):
                    add_policy_snippet(out, file_path, entry, f"{key}_{idx}")

    # Test cases: mine structured cues (battery, expected decisions, traps)
    tcs = data.get("test_cases") or []
    if isinstance(tcs, list):
        for tc in tcs:
            if not isinstance(tc, dict):
                continue
            tc_id = tc.get("id") or tc.get("case_id") or tc.get("name") or "tc"
            # Battery percent present
            batt = tc.get("current_battery_percent") or tc.get("battery_percent")
            if isinstance(batt, (int, float)):
                out.append(
                    {
                        "constraint_id": f"{file_path.stem}_{tc_id}_battery",
                        "file": str(file_path),
                        "concept": "BatteryReserve",
                        "concepts": ["BatteryReserve"],
                        "source_type": SourceType.SOP.value,
                        "source_ref": file_path.name,
                        "raw_value": float(batt),
                        "raw_unit": "percent",
                        "canonical_value": float(batt),
                        "canonical_unit": "percent",
                        "text": f"Current battery percent in test case {tc_id}: {batt}%",
                    }
                )
            dc = tc.get("distance_calculations") or {}
            if isinstance(dc, dict):
                total_req = dc.get("total_required_percent")
                if isinstance(total_req, (int, float)):
                    out.append(
                        {
                            "constraint_id": f"{file_path.stem}_{tc_id}_battery_required",
                            "file": str(file_path),
                            "concept": "BatteryReserve",
                            "concepts": ["BatteryReserve"],
                            "source_type": SourceType.SOP.value,
                            "source_ref": file_path.name,
                            "raw_value": float(total_req),
                            "raw_unit": "percent",
                            "canonical_value": float(total_req),
                            "canonical_unit": "percent",
                            "text": f"Required percent for {tc_id}: {total_req}%",
                        }
                    )
                # Capture option/alternative details inside distance_calculations
                for k, v in dc.items():
                    if isinstance(v, dict) and k.lower().startswith("option"):
                        add_policy_snippet(
                            out,
                            file_path,
                            json.dumps({k: v}, ensure_ascii=False),
                            f"{tc_id}_{k}",
                            concepts_hint=["Priority"],
                        )
            exp_dec = tc.get("expected_decision") or tc.get("expected")
            if isinstance(exp_dec, str):
                add_policy_snippet(
                    out,
                    file_path,
                    f"Test case {tc_id} expected decision: {exp_dec}",
                    f"{tc_id}_expected_decision",
                    concepts_hint=["Priority"],
                )
            exp_reason = tc.get("expected_reason")
            if isinstance(exp_reason, str):
                add_policy_snippet(out, file_path, exp_reason, f"{tc_id}_expected_reason")
            corr = tc.get("correct_reasoning")
            if isinstance(corr, list):
                for idx, line in enumerate(corr):
                    if isinstance(line, str):
                        add_policy_snippet(out, file_path, line, f"{tc_id}_reasoning_{idx}")
            trap = tc.get("llm_trap")
            if isinstance(trap, str):
                add_policy_snippet(out, file_path, trap, f"{tc_id}_llm_trap", concepts_hint=["AdversarialPrompt"])
            mbrief = tc.get("mission_brief")
            if isinstance(mbrief, dict):
                text_parts = []
                for key, val in mbrief.items():
                    if isinstance(val, str):
                        text_parts.append(f"{key}: {val}")
                if text_parts:
                    add_policy_snippet(out, file_path, "; ".join(text_parts), f"{tc_id}_mission_brief", concepts_hint=["EmergencyEvacuation"])
            # mission alternatives/options
            if isinstance(mbrief, dict):
                opts = mbrief.get("options")
                if isinstance(opts, list):
                    for idx, opt in enumerate(opts):
                        if isinstance(opt, dict):
                            add_policy_snippet(
                                out,
                                file_path,
                                json.dumps(opt, ensure_ascii=False),
                                f"{tc_id}_option_{idx}",
                                concepts_hint=["Priority"],
                            )
                alt = mbrief.get("alternatives")
                if isinstance(alt, dict):
                    add_policy_snippet(
                        out,
                        file_path,
                        json.dumps(alt, ensure_ascii=False),
                        f"{tc_id}_alternatives",
                        concepts_hint=["Priority"],
                    )

    return out


def extract_scenarios_batch() -> List[Dict]:
    targets = sorted(
        list(ROOT.glob("scenarios/intermediate/S0[2-3][0-9]_*.jsonc"))
        + list(ROOT.glob("scenarios/advanced/S0[3-4][0-9]_*.jsonc"))
    )
    extracted: List[Dict] = []
    for path in targets:
        extracted.extend(extract_scenario(path))
    return extracted


def chunk_pdf(path: Path) -> Tuple[List[str], Optional[str]]:
    """
    Extract text from a PDF using PyPDF2 if available, otherwise pdftotext.
    Returns (chunks, error_message).
    """
    # Try PyPDF2
    try:
        import PyPDF2  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        PyPDF2 = None  # type: ignore
        py_err = f"PyPDF2 not available: {exc}"
    else:
        py_err = None
        try:
            reader = PyPDF2.PdfReader(str(path))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            text = "\n".join(pages)
            return (chunk_text(text), None)
        except Exception as exc:  # pragma: no cover - PDF parsing errors
            py_err = f"Failed to parse PDF {path.name} via PyPDF2: {exc}"

    # Fallback to pdftotext if available
    try:
        import subprocess

        tmp_txt = path.with_suffix(".tmp.txt")
        subprocess.run(["pdftotext", str(path), str(tmp_txt)], check=True, capture_output=True)
        txt = tmp_txt.read_text(encoding="utf-8", errors="ignore")
        tmp_txt.unlink(missing_ok=True)
        return (chunk_text(txt), None)
    except Exception as exc:  # pragma: no cover - external command errors
        return ([], py_err or f"Failed to parse PDF {path.name}: {exc}")


def chunk_regulations() -> List[Dict]:
    regs: List[Dict] = []
    reg_md = ROOT / "regulations" / "无人驾驶航空器飞行管理暂行条例.md"
    if reg_md.exists():
        text = reg_md.read_text(encoding="utf-8")
        for idx, chunk in enumerate(chunk_text(text)):
            regs.append(
                {
                    "chunk_id": f"CN_Interim_{idx}",
                    "file": str(reg_md),
                    "source_type": SourceType.REGULATION.value,
                    "source_ref": "CN_Interim_UAS",
                    "text": chunk,
                }
            )
    faa_pdf = ROOT / "regulations" / "14 CFR Part 107 (up to date as of 9-29-2025).pdf"
    if faa_pdf.exists():
        faa_chunks, err = chunk_pdf(faa_pdf)
        for idx, chunk in enumerate(faa_chunks):
            regs.append(
                {
                    "chunk_id": f"FAA_Part107_{idx}",
                    "file": str(faa_pdf),
                    "source_type": SourceType.REGULATION.value,
                    "source_ref": "FAA_Part_107",
                    "text": chunk,
                }
            )
        if err:
            print(f"[warn] FAA Part 107 chunking error: {err}", file=sys.stderr)
    return regs


def main() -> None:
    scenario_constraints = extract_scenarios_batch()
    out_path = HERE / "outputs" / "constraints_extracted.json"
    out_path.write_text(json.dumps(scenario_constraints, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(scenario_constraints)} scenario constraints -> {out_path}")

    reg_chunks = chunk_regulations()
    reg_path = HERE / "outputs" / "regulation_chunks.json"
    reg_path.write_text(json.dumps(reg_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(reg_chunks)} regulation chunks -> {reg_path}")


if __name__ == "__main__":
    main()

"""
Group extracted constraints by scenario id for downstream RAG retrieval.

Input: rag/outputs/constraints_extracted.json (from batch_extract.py)
Output: rag/outputs/constraints_by_scenario.json
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent


def load_extracted() -> List[Dict]:
    path = HERE / "outputs" / "constraints_extracted.json"
    return json.loads(path.read_text())


def scenario_id_from_file(file_path: str) -> str:
    # Assumes filename starts with SXXX_
    name = Path(file_path).stem
    return name.split("_")[0]


def main() -> None:
    data = load_extracted()
    grouped: Dict[str, List[Dict]] = defaultdict(list)
    for item in data:
        sid = scenario_id_from_file(item["file"])
        grouped[sid].append(item)
    out_path = HERE / "outputs" / "constraints_by_scenario.json"
    out_path.write_text(json.dumps(grouped, ensure_ascii=False, indent=2))
    print(f"Grouped {len(data)} constraints into {len(grouped)} scenarios -> {out_path}")


if __name__ == "__main__":
    main()

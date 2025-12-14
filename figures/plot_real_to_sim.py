"""
Generate two figures using real project data:
1) coverage_case_scenario_capabilities.png – Alluvial: 23 real cases (3 domains) → 49 scenarios → capability clusters.
2) coverage_capability_heatmap.png – Scenario bucket vs capability dimension (Physics/Rules/Intent/Adversarial/Operational).

Usage (avoid font cache errors):
    MPLCONFIGDIR=/tmp/mplconfig python figures/plot_real_to_sim.py
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from glob import glob
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
MAPPING_PATH = ROOT / "regulations" / "Real-to-Sim_Mapping.md"
SCENARIO_ROOT = ROOT / "scenarios"
REPORTS_DIR = ROOT / "reports"
FIG_DIR = ROOT / "figures"

# ---------------- Accuracy helpers ----------------

def layer_for_sid(sid: str) -> str:
    try:
        n = int(sid[1:])
    except Exception:
        return "Basic"
    if n <= 20:
        return "Basic"
    if n <= 30:
        return "Intermediate"
    if n <= 40:
        return "Advanced"
    return "Operational"


def parse_accuracy_from_report(path: Path) -> float | None:
    """Parse accuracy percent from report JSON. Returns percent value (0-100)."""
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    # try summary llm_accuracy_percent
    summary = data.get("summary", {})
    acc_pct = summary.get("llm_accuracy_percent") or summary.get("accuracy_percent")
    if isinstance(acc_pct, str) and acc_pct.endswith("%"):
        try:
            return float(acc_pct.strip("%"))
        except Exception:
            pass
    # try llm_accuracy "x/y"
    acc_str = summary.get("llm_accuracy")
    if isinstance(acc_str, str) and "/" in acc_str:
        try:
            num, den = acc_str.split("/")
            num = float(num)
            den = float(den)
            return (num / den * 100) if den else None
        except Exception:
            pass
    # compute from results
    results = data.get("results", [])
    if results:
        correct = 0
        total = 0
        for r in results:
            gt = None
            if isinstance(r.get("ground_truth"), dict):
                gt = r["ground_truth"].get("decision")
            gt = gt or r.get("expected_decision")
            pred = r.get("llm_decision") or (r.get("llm_result") or {}).get("decision")
            if gt and pred:
                total += 1
                if str(gt).upper() == str(pred).upper():
                    correct += 1
        if total:
            return correct / total * 100
    return None


def collect_layer_accuracies() -> Dict[str, Dict[str, float]]:
    """
    Collect average accuracies per layer for:
    - raw LLM (reports/*_LLM_VALIDATION.json)
    - RAG (reports/*_RAG_REPORT.json)
    - rule baseline (reports/*_RULE_BASELINE.json)
    """
    buckets = ["Basic", "Intermediate", "Advanced", "Operational"]
    data: Dict[str, Dict[str, List[float]]] = {
        "raw": {b: [] for b in buckets},
        "rag": {b: [] for b in buckets},
        "rule": {b: [] for b in buckets},
    }
    for path in REPORTS_DIR.glob("S0??_LLM_VALIDATION.json"):
        sid = path.stem.split("_")[0]
        layer = layer_for_sid(sid)
        acc = parse_accuracy_from_report(path)
        if acc is not None:
            data["raw"][layer].append(acc)
    for path in REPORTS_DIR.glob("S0??_RAG_REPORT.json"):
        sid = path.stem.split("_")[0]
        layer = layer_for_sid(sid)
        acc = parse_accuracy_from_report(path)
        if acc is not None:
            data["rag"][layer].append(acc)
    for path in REPORTS_DIR.glob("S0??_RULE_BASELINE.json"):
        sid = path.stem.split("_")[0]
        layer = layer_for_sid(sid)
        acc = parse_accuracy_from_report(path)
        if acc is not None:
            data["rule"][layer].append(acc)

    avg: Dict[str, Dict[str, float]] = {"raw": {}, "rag": {}, "rule": {}}
    counts: Dict[str, Dict[str, int]] = {"raw": {}, "rag": {}, "rule": {}}
    for model in ["raw", "rag", "rule"]:
        for layer in buckets:
            vals = data[model][layer]
            counts[model][layer] = len(vals)
            avg[model][layer] = sum(vals) / len(vals) if vals else 0.0
    return {"avg": avg, "counts": counts}

# ---------------- Data helpers ----------------

def parse_case_to_scenarios() -> Dict[str, Dict]:
    """Parse mapping doc to get domains, cases, and linked scenario IDs."""
    text = MAPPING_PATH.read_text(encoding="utf-8")
    sections = re.split(r"^### \*\*", text, flags=re.M)[1:]
    data: Dict[str, Dict] = {}
    for sec in sections:
        header, body = sec.split("\n", 1)
        domain_header = header.split("**")[0].strip()
        if "低空物流配送" in domain_header:
            domain = "Logistics"
        elif "低空交通运输生产作业" in domain_header:
            domain = "Industrial"
        elif "低空应急救援" in domain_header:
            domain = "Emergency"
        else:
            domain = domain_header
        cases = re.split(r"^#### 案例", body, flags=re.M)[1:]
        case_map: Dict[str, List[str]] = {}
        for c in cases:
            lines = c.strip().splitlines()
            case_id_line = lines[0] if lines else "UNKNOWN"
            case_id = f"Case {case_id_line.strip(': ')}"
            scenarios = set(re.findall(r"S0\d{2}", "\n".join(lines)))
            case_map[case_id] = sorted(scenarios)
        data[domain] = {"cases": case_map}
    return data


def load_scenario_level() -> Dict[str, str]:
    """
    Load scenario complexity_layer -> coarse layer label.
    Map to four buckets strictly by ID range:
    S001-S020: Basic
    S021-S030: Intermediate
    S031-S040: Advanced
    S041-S049: Operational
    """
    levels: Dict[str, str] = {}
    for path in glob(str(SCENARIO_ROOT / "**" / "S0??_*.jsonc"), recursive=True):
        p = Path(path)
        sid = p.name.split("_")[0]
        try:
            n = int(sid[1:])
            if n <= 20:
                levels[sid] = "Basic"
            elif n <= 30:
                levels[sid] = "Intermediate"
            elif n <= 40:
                levels[sid] = "Advanced"
            else:
                levels[sid] = "Operational"
        except Exception:
            levels[sid] = "Basic"
    return levels


def capability_tags_for_sid(sid: str) -> List[str]:
    """
    Heuristic multi-label capability tags to avoid diagonal sparsity.
    Each scenario can carry multiple capability dimensions.
    """
    try:
        n = int(sid[1:])
    except Exception:
        return ["Operational"]
    tags: List[str] = []
    if n <= 20:
        tags += ["Physics", "Rules"]
    elif n <= 30:
        tags += ["Rules", "Physics"]
    elif n <= 34:
        tags += ["Intent", "Rules"]
    elif n <= 40:
        tags += ["Adversarial", "Rules"]
    else:
        tags += ["Operational", "Rules"]
    if n in {22, 23, 24, 25}:
        tags.append("Intent")
    if n in {28, 30, 33}:
        tags.append("Operational")
    if n in {39, 40}:
        tags.append("Intent")
    if n in {41, 42, 43, 44}:
        tags.append("Physics")
    if n in {48, 49}:
        tags.append("Adversarial")
    return list(dict.fromkeys(tags))


def load_decision_counts() -> Dict[str, Counter]:
    """Aggregate decision counts from reports/*_LLM_VALIDATION.json."""
    dec_map: Dict[str, Counter] = {}
    for path in glob(str(REPORTS_DIR / "S0??_*LLM_VALIDATION.json")):
        p = Path(path)
        sid = p.stem.split("_")[0]
        try:
            data = json.loads(p.read_text())
            counter = Counter()
            for r in data.get("results", []):
                dec = (r.get("llm_result") or {}).get("decision") or r.get("llm_decision")
                if dec:
                    counter[dec.upper()] += 1
            if counter:
                dec_map[sid] = counter
        except Exception:
            continue
    return dec_map


def scenario_bucket(sid: str) -> str:
    """Group scenarios into four buckets."""
    try:
        n = int(sid[1:])
    except Exception:
        return "Other"
    if n <= 20:
        return "S001-S020"
    if n <= 30:
        return "S021-S030"
    if n <= 40:
        return "S031-S040"
    return "S041-S049"


# ---------------- Plots ----------------

def plot_case_scenario_capability_alluvial() -> None:
    """
    Aggregated alluvial: 3 case domains -> 4 scenario layers -> decision outcomes.
    Flows are counts (case->scenario unique; scenario decisions aggregated to layer).
    """
    domain_colors = {
        "Logistics": "#6c9bd2",
        "Industrial": "#d29b6c",
        "Emergency": "#6cb59b",
        "Other": "#b0b0b0",
    }
    layer_colors = {
        "Basic": "#4c8c4a",
        "Intermediate": "#6fa46f",
        "Advanced": "#9abf8f",
        "Operational": "#c6dcb5",
    }
    decision_palette = {
        "APPROVE": "#2b9348",
        "REJECT": "#c1121f",
        "CONDITIONAL_APPROVE": "#ffb703",
        "REJECT_WITH_ALTERNATIVE": "#6a4c93",
        "UNCERTAIN": "#577590",
        "EXPLAIN_ONLY": "#8d99ae",
        "OTHER": "#b0b0b0",
    }
    layers_order = ["Basic", "Intermediate", "Advanced", "Operational"]

    mapping = parse_case_to_scenarios()
    levels = load_scenario_level()

    # Domain -> Layer counts
    domain_layer = Counter()
    scenario_caps = defaultdict(list)
    for dom, info in mapping.items():
        for scens in info["cases"].values():
            for sid in scens:
                layer = levels.get(sid, "Basic")
                domain_layer[(dom, layer)] += 1
                scenario_caps[sid] = capability_tags_for_sid(sid)

    # Layer -> decision counts
    dec_counts = load_decision_counts()
    layer_decision = Counter()
    for sid, counter in dec_counts.items():
        layer = levels.get(sid, "Basic")
        for dec, cnt in counter.items():
            layer_decision[(layer, dec.upper())] += cnt

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=320)

    total_height = 12.0  # keep columns similar height

    def stack_blocks(items, x, color_map):
        y = 0.0
        pos = {}
        col_total = sum(v for _, v in items) or 1
        for label, val in items:
            h = max(0.25, (val / col_total) * total_height)
            ax.fill_between([x - 0.08, x + 0.08], [y + h, y + h], [y, y], color=color_map.get(label, "#b0b0b0"), alpha=0.5, edgecolor="none")
            pos[label] = (y, y + h)
            y += h + 0.08
        return pos

    def add_labels(pos, x, align):
        for key, (y0, y1) in pos.items():
            ax.text(x, (y0 + y1) / 2, key, ha=align, va="center", fontsize=9, weight="bold")

    domain_items = []
    for dom in ["Logistics", "Industrial", "Emergency"]:
        total = sum(v for (d, _), v in domain_layer.items() if d == dom)
        if total > 0:
            domain_items.append((dom, total))
    domain_pos = stack_blocks(domain_items, 0.0, domain_colors)

    layer_items = []
    for layer in layers_order:
        total = sum(v for (_, l), v in domain_layer.items() if l == layer)
        if total > 0:
            layer_items.append((layer, total))
    layer_pos = stack_blocks(layer_items, 2.0, layer_colors)

    # Decisions (top 6 + OTHER)
    dec_totals = Counter()
    for (_, dec), v in layer_decision.items():
        dec_totals[dec] += v
    top_decs = [d for d, _ in dec_totals.most_common(6)]
    decisions = top_decs + (["OTHER"] if len(dec_totals) > 6 else [])

    dec_items = []
    for dec in decisions:
        if dec == "OTHER":
            total = sum(v for (_, d), v in layer_decision.items() if d not in top_decs)
        else:
            total = dec_totals[dec]
        if total > 0:
            dec_items.append((dec, total))
    dec_pos = stack_blocks(dec_items, 3.8, decision_palette)

    # domain -> layer flows
    for (dom, layer), v in domain_layer.items():
        if dom in domain_pos and layer in layer_pos:
            y0, y0h = domain_pos[dom]
            y1, y1h = layer_pos[layer]
            ax.fill_between([0.08, 1.92], [y0h, y1h], [y0, y1], color=domain_colors.get(dom, "#8fb3c8"), alpha=0.5, linewidth=0)

    # layer -> decision flows
    for (layer, dec), v in layer_decision.items():
        dec_key = dec if dec in top_decs else "OTHER"
        if layer in layer_pos and dec_key in dec_pos:
            y0, y0h = layer_pos[layer]
            y1, y1h = dec_pos[dec_key]
            ax.fill_between([2.08, 3.72], [y0h, y1h], [y0, y1], color=decision_palette.get(dec_key, "#999999"), alpha=0.6, linewidth=0)

    add_labels(domain_pos, -0.18, "right")
    add_labels(layer_pos, 2.12, "left")
    add_labels(dec_pos, 3.92, "left")

    ax.axis("off")
    ax.set_xlim(-0.5, 4.2)
    ax.set_title("Case domains → Scenario layers → Decision outcomes", fontsize=12, weight="bold", pad=12)
    fig.tight_layout()
    FIG_DIR.mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / "coverage_case_scenario_capabilities.png", bbox_inches="tight")
    plt.close(fig)


def plot_capability_heatmap() -> None:
    """Heatmap from capability.md table (7 clusters x 4 layers), shown as % of layer."""
    layers = [
        "Basic",
        "Intermediate",
        "Advanced",
        "Operational",
    ]
    capabilities = [
        "Spatial & Physical Awareness",
        "Regulatory Compliance",
        "Dynamic Contingency",
        "Cognitive & Ethical Reasoning",
        "Interaction & Security",
        "Resource & Fleet Optimization",
        "Systemic Fairness & Coordination",
    ]
    # Data from capability.md table (counts)
    matrix = [
        [9, 0, 1, 0],
        [9, 3, 0, 0],
        [0, 2, 1, 2],
        [0, 5, 3, 0],
        [1, 0, 5, 1],
        [1, 0, 0, 3],
        [0, 0, 0, 3],
    ]
    # Totals per layer: 20,10,10,9
    layer_totals = [20, 10, 10, 9]

    pct_matrix = []
    for row in matrix:
        pct_row = []
        for val, total in zip(row, layer_totals):
            pct_row.append(round(val / total * 100, 1) if total else 0)
        pct_matrix.append(pct_row)

    fig, ax = plt.subplots(figsize=(7.8, 5.4), dpi=320)
    im = ax.imshow(pct_matrix, cmap="YlGnBu", vmin=0, vmax=100)
    ax.set_xticks(range(len(layers)))
    ax.set_xticklabels(layers, rotation=12)
    ax.set_yticks(range(len(capabilities)))
    ax.set_yticklabels(capabilities)
    max_val = 100
    for i, row in enumerate(pct_matrix):
        for j, pct in enumerate(row):
            text_color = "#ffffff" if pct >= max(10, max_val * 0.4) else "#0b1a20"
            ax.text(
                j,
                i,
                f"{pct:.1f}%",
                ha="center",
                va="center",
                color=text_color,
                fontsize=8,
                fontweight="bold",
            )
    ax.set_title("Capability coverage by layer (percent of layer)", fontsize=12, weight="bold")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Coverage (%)", rotation=90)
    fig.tight_layout()
    FIG_DIR.mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / "coverage_capability_heatmap.png", bbox_inches="tight")
    plt.close(fig)


def plot_layer_accuracy_comparison() -> None:
    """Grouped bars: per-layer accuracy for raw LLM, RAG, rule baseline."""
    stats = collect_layer_accuracies()
    acc = stats["avg"]
    cnt = stats["counts"]
    layers = ["Basic", "Intermediate", "Advanced", "Operational"]

    x_all = list(range(len(layers)))
    width = 0.24
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=320)

    def add_series(model_key: str, shift: float, color: str, label: str):
        xs = []
        ys = []
        for i, layer in enumerate(layers):
            if cnt[model_key].get(layer, 0) > 0:
                xs.append(i + shift)
                ys.append(acc[model_key].get(layer, 0))
        ax.bar(xs, ys, width=width, color=color, label=label)
        for xi, yi in zip(xs, ys):
            ax.text(xi, yi + 1, f"{yi:.1f}", ha="center", va="bottom", fontsize=8)

    add_series("raw", -width, "#4c78a8", "Raw LLM")
    add_series("rag", 0.0, "#f58518", "RAG")
    add_series("rule", width, "#54a24b", "Rule baseline")

    ax.set_xticks(x_all)
    ax.set_xticklabels(layers)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Accuracy (%)", fontsize=10)
    ax.set_title("Layer-wise accuracy comparison", fontsize=12, weight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    FIG_DIR.mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / "layer_accuracy_comparison.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    mpl.rcParams.update({
        "font.size": 8,
        "axes.labelcolor": "#0f0f0f",
        "axes.edgecolor": "#2f4f2f",
        "axes.facecolor": "#f8f9f6",
        "figure.facecolor": "#ffffff",
        "savefig.facecolor": "#ffffff",
        "grid.color": "#dcded6",
        "grid.linestyle": "--",
        "grid.linewidth": 0.4,
    })
    plot_case_scenario_capability_alluvial()
    plot_capability_heatmap()
    plot_layer_accuracy_comparison()
    print(f"Saved figures to: {FIG_DIR}")


if __name__ == "__main__":
    main()

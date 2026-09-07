#!/usr/bin/env python3
"""Generate the task-specific paired-gain forest plot used as Figure 2."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/main/results/task_family_paired_gain.csv"

MODEL_ORDER = [
    "qwen38_flagship",
    "glm52_flagship",
    "deepseek_v4_flash",
    "meta_muse_30b",
]
MODEL_LABELS = {
    "qwen38_flagship": "Qwen3.8",
    "glm52_flagship": "GLM-5.2",
    "deepseek_v4_flash": "DeepSeek-V4",
    "meta_muse_30b": "Muse-Glimmer",
}
MODEL_COLORS = {
    "qwen38_flagship": "#009E73",
    "glm52_flagship": "#E69F00",
    "deepseek_v4_flash": "#0072B2",
    "meta_muse_30b": "#D55E00",
}
TASKS = [
    ("PRE_FLIGHT_AUTHORIZATION", "Pre-flight authorization", 126, 15),
    ("IN_FLIGHT_CONTINGENCY", "In-flight contingency", 27, 4),
    ("RESOURCE_OR_POLICY_DECISION", "Resource or policy decision", 84, 10),
]

GRID_COLOR = "#E2E5E7"
TEXT_COLOR = "#24292D"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DATA)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = pd.read_csv(args.input)
    data = data[data["task_type"].isin(task[0] for task in TASKS)].copy()

    expected = len(TASKS) * len(MODEL_ORDER)
    if len(data) != expected:
        raise ValueError(f"Expected {expected} paired estimates, found {len(data)}")
    if data.duplicated(["task_type", "model_id"]).any():
        raise ValueError("Duplicate task--model estimates found")

    for column in ["rag_minus_raw", "ci_low", "ci_high"]:
        data[column] = 100 * data[column]

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8.0,
            "axes.labelsize": 8.2,
            "xtick.labelsize": 7.6,
            "ytick.labelsize": 7.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )

    fig, ax = plt.subplots(figsize=(7.10, 3.85), facecolor="white")
    fig.subplots_adjust(left=0.215, right=0.985, bottom=0.155, top=0.985)

    group_rows = [
        [13.4, 12.4, 11.4, 10.4],
        [7.7, 6.7, 5.7, 4.7],
        [2.0, 1.0, 0.0, -1.0],
    ]
    group_headers = [14.35, 8.65, 2.95]
    row_positions = []
    row_labels = []

    for task_index, (task_id, task_label, n_cases, n_clusters) in enumerate(TASKS):
        part = data[data["task_type"] == task_id].set_index("model_id")
        rows = group_rows[task_index]

        ax.text(
            -19.2,
            group_headers[task_index],
            f"{task_label}  ($n$ = {n_cases}; {n_clusters} scenario clusters)",
            ha="left",
            va="center",
            fontsize=8.4,
            fontweight="semibold",
            color=TEXT_COLOR,
        )

        for y, model_id in zip(rows, MODEL_ORDER):
            estimate = float(part.loc[model_id, "rag_minus_raw"])
            low = float(part.loc[model_id, "ci_low"])
            high = float(part.loc[model_id, "ci_high"])
            color = MODEL_COLORS[model_id]
            ax.errorbar(
                estimate,
                y,
                xerr=[[estimate - low], [high - estimate]],
                fmt="o",
                markersize=4.5,
                markerfacecolor=color,
                markeredgecolor=color,
                markeredgewidth=0.7,
                ecolor=color,
                elinewidth=0.9,
                capsize=2.0,
                capthick=0.8,
                zorder=3,
            )
            row_positions.append(y)
            row_labels.append(MODEL_LABELS[model_id])

    ax.axvline(0, color="#7B8388", linewidth=0.8, linestyle=(0, (3, 3)), zorder=1)
    for y in [9.55, 3.85]:
        ax.axhline(y, color=GRID_COLOR, linewidth=0.7, zorder=0)

    ax.set_xlim(-20, 70)
    ax.set_xticks([-20, 0, 20, 40, 60])
    ax.set_ylim(-1.75, 14.85)
    ax.set_yticks(row_positions)
    ax.set_yticklabels(row_labels, color=TEXT_COLOR)
    ax.set_xlabel(
        "Change in exact reference-outcome agreement (percentage points)",
        labelpad=7,
        color=TEXT_COLOR,
    )

    ax.grid(axis="x", color=GRID_COLOR, linewidth=0.55, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#777F84")
    ax.spines["bottom"].set_linewidth(0.7)
    ax.tick_params(axis="x", length=2.5, width=0.7, color="#777F84")
    ax.tick_params(axis="y", length=0, pad=6)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight", facecolor="white", dpi=600)
    print(args.output)
    plt.close(fig)


if __name__ == "__main__":
    main()

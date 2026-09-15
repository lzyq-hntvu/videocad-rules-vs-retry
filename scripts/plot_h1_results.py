#!/usr/bin/env python3
"""
H1 预实验结果图 - 退化斜率对比

更偏学术论文风格的双面板图：
1. 分层退化斜率对照
2. baseline / robust 在不同复杂度下的退化曲线

使用方法:
    python scripts/plot_h1_results.py
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from utils import COLORS as BASE_COLORS
from utils import save_figure, setup_nsfc_style

COLORS = {
    "baseline": "#6C7A89",
    "robust": "#2E5C8A",
    "low": "#B8C6D1",
    "medium": "#7FA6C9",
    "high": "#4E79A7",
    "grid": BASE_COLORS["grid"],
    "text": BASE_COLORS["text"],
    "text_secondary": BASE_COLORS["text_secondary"],
    "accent": "#E67E22",
}


def load_data():
    # 2026-09-15: data/preliminary_results.json 已隔离（非管线产物，见
    # docs/audit-2026-09-15-data-lineage-and-rng.md）。本脚本禁用，待重接到真实管线输出。
    raise SystemExit(
        f"{Path(__file__).name}: 数据源 preliminary_results.json 已撤回隔离，本脚本禁用。"
        "真实结果见 evidence/videocad/notes/h2_h3_proxy_experiment/ 与 tmp/dev_five_arm/。"
    )
    return data["h1_results"]


def _annotate_bars(ax, bars):
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.3f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            color=COLORS["text_secondary"],
        )


def plot_slope_summary(data, ax):
    overall = data["data"]["overall"]
    by_complexity = data["data"]["by_complexity"]

    categories = ["Overall", "Low", "Medium", "High"]
    baseline = [
        overall["baseline_slope"],
        by_complexity["low"]["baseline_slope"],
        by_complexity["medium"]["baseline_slope"],
        by_complexity["high"]["baseline_slope"],
    ]
    robust = [
        overall["robust_slope"],
        by_complexity["low"]["robust_slope"],
        by_complexity["medium"]["robust_slope"],
        by_complexity["high"]["robust_slope"],
    ]

    x = np.arange(len(categories))
    width = 0.34
    bars1 = ax.bar(
        x - width / 2,
        baseline,
        width,
        label="baseline",
        color=COLORS["baseline"],
        edgecolor="white",
        linewidth=1.0,
    )
    bars2 = ax.bar(
        x + width / 2,
        robust,
        width,
        label="robust",
        color=COLORS["robust"],
        edgecolor="white",
        linewidth=1.0,
    )
    _annotate_bars(ax, bars1)
    _annotate_bars(ax, bars2)

    ax.set_title("A. Slope Comparison by Complexity", loc="left", fontsize=12, fontweight="bold")
    ax.set_ylabel("Degradation Slope")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(-0.145, -0.08)
    ax.grid(axis="y", linestyle="--", alpha=0.35, color=COLORS["grid"])
    ax.legend(loc="upper right", frameon=False)
    ax.text(
        0.02,
        0.06,
        "Robust is flatter in medium/high; low remains a boundary case.",
        transform=ax.transAxes,
        fontsize=8.5,
        color=COLORS["text_secondary"],
    )


def plot_degradation_curves(data, ax):
    by_complexity = data["data"]["by_complexity"]

    curve_specs = [
        ("low", "low", COLORS["low"]),
        ("medium", "medium", COLORS["medium"]),
        ("high", "high", COLORS["high"]),
    ]

    for comp_key, label, color in curve_specs:
        comp_data = by_complexity[comp_key]

        baseline_curve = comp_data["baseline_curve"]
        eps_b = [p["epsilon"] for p in baseline_curve]
        acc_b = [p["accuracy"] for p in baseline_curve]
        ax.plot(
            eps_b,
            acc_b,
            color=color,
            linestyle="-",
            linewidth=1.8,
            alpha=0.55,
            marker="o",
            markersize=3.8,
            label=f"{label} baseline",
        )

        robust_curve = comp_data["robust_curve"]
        eps_r = [p["epsilon"] for p in robust_curve]
        acc_r = [p["accuracy"] for p in robust_curve]
        ax.plot(
            eps_r,
            acc_r,
            color=color,
            linestyle="--",
            linewidth=2.0,
            alpha=0.95,
            marker="s",
            markersize=3.8,
            label=f"{label} robust",
        )

    ax.set_title("B. Degradation Curves under Controlled Perturbation", loc="left", fontsize=12, fontweight="bold")
    ax.set_xlabel("Perturbation Level ε")
    ax.set_ylabel("Accuracy")
    ax.set_xlim(-0.01, 0.42)
    ax.set_ylim(0.58, 1.02)
    ax.grid(linestyle="--", alpha=0.35, color=COLORS["grid"])
    ax.legend(loc="lower left", ncol=2, frameon=False, fontsize=8.5)
    ax.text(
        0.98,
        0.08,
        "Dashed: robust\nSolid: baseline",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.5,
        color=COLORS["text_secondary"],
    )


def create_figure():
    setup_nsfc_style()
    data = load_data()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8), constrained_layout=True)
    plot_slope_summary(data, axes[0])
    plot_degradation_curves(data, axes[1])

    fig.suptitle(
        "Figure 5. H1 Degradation Slopes and Layered Trends",
        fontsize=14,
        fontweight="bold",
        color=COLORS["text"],
    )
    fig.text(
        0.5,
        0.01,
        "Note: The key evidence for H1 is degradation slope rather than a single best point. "
        "Robust remains flatter overall and in medium/high subsets, while low is retained as a boundary condition.",
        ha="center",
        fontsize=9,
        color=COLORS["text_secondary"],
    )
    return fig


def main():
    print("Generating H1 preliminary results figure...")
    fig = create_figure()
    save_figure(fig, "fig5_h1_degradation")
    plt.close(fig)
    print("Done!")


if __name__ == "__main__":
    main()

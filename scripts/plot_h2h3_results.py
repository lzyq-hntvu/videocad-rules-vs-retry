#!/usr/bin/env python3
"""
H2/H3 预实验结果图 - 阈值迁移与规则抑制效果

更偏学术论文风格的双面板图：
1. 不同复杂度下成功率-误差强度曲线
2. 规则约束导致的阈值迁移（dumbbell plot）

使用方法:
    python scripts/plot_h2h3_results.py
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
    "no_rule": "#7B8794",
    "min_rule": "#2E5C8A",
    "threshold": "#E67E22",
    "low": "#B8C6D1",
    "medium": "#7FA6C9",
    "high": "#4E79A7",
    "grid": BASE_COLORS["grid"],
    "text": BASE_COLORS["text"],
    "text_secondary": BASE_COLORS["text_secondary"],
}


def load_data():
    data_path = Path(__file__).parent.parent / "data" / "preliminary_results.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["h2h3_results"]


def plot_success_curves(data, ax):
    by_complexity = data["data"]
    success_threshold = data["success_threshold"]
    specs = [
        ("low", "low", COLORS["low"]),
        ("medium", "medium", COLORS["medium"]),
        ("high", "high", COLORS["high"]),
    ]

    for comp_key, label, color in specs:
        comp_data = by_complexity[comp_key]
        no_rule_curve = comp_data["curves"]["no_rule"]
        with_rule_curve = comp_data["curves"]["min_rule"]

        eps_nr = [p["epsilon"] for p in no_rule_curve]
        suc_nr = [p["success_rate"] for p in no_rule_curve]
        ax.plot(
            eps_nr,
            suc_nr,
            color=color,
            linestyle="-",
            linewidth=1.8,
            alpha=0.55,
            marker="o",
            markersize=3.5,
            label=f"{label} no_rule",
        )

        eps_wr = [p["epsilon"] for p in with_rule_curve]
        suc_wr = [p["success_rate"] for p in with_rule_curve]
        ax.plot(
            eps_wr,
            suc_wr,
            color=color,
            linestyle="--",
            linewidth=2.0,
            alpha=0.95,
            marker="s",
            markersize=3.5,
            label=f"{label} with_rule",
        )

        ax.scatter(
            [comp_data["no_rule"]["threshold_epsilon"]],
            [success_threshold],
            color=COLORS["no_rule"],
            s=28,
            zorder=4,
        )
        ax.scatter(
            [comp_data["min_rule"]["threshold_epsilon"]],
            [success_threshold],
            color=COLORS["min_rule"],
            s=28,
            zorder=4,
            marker="s",
        )

    ax.axhline(
        y=success_threshold,
        color=COLORS["threshold"],
        linestyle=":",
        linewidth=1.6,
    )
    ax.text(
        0.98,
        success_threshold + 0.015,
        "Threshold",
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="bottom",
        fontsize=8.5,
        color=COLORS["threshold"],
    )

    ax.set_title("A. Success Rate vs Error Level", loc="left", fontsize=12, fontweight="bold")
    ax.set_xlabel("Error Level ε")
    ax.set_ylabel("Success Rate")
    ax.set_xlim(-0.005, 0.085)
    ax.set_ylim(0.0, 1.03)
    ax.grid(linestyle="--", alpha=0.35, color=COLORS["grid"])
    ax.legend(loc="lower left", ncol=2, frameon=False, fontsize=8.2)
    ax.text(
        0.98,
        0.05,
        "Dashed: with_rule\nSolid: no_rule",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.5,
        color=COLORS["text_secondary"],
    )


def plot_threshold_shift(data, ax):
    by_complexity = data["data"]
    levels = ["high", "medium", "low"]
    y = np.arange(len(levels))

    no_rule = [by_complexity[level]["no_rule"]["threshold_epsilon"] for level in levels]
    with_rule = [by_complexity[level]["min_rule"]["threshold_epsilon"] for level in levels]
    lift_pct = [by_complexity[level]["threshold_lift_percent"] for level in levels]

    for idx, (n_rule, w_rule, pct) in enumerate(zip(no_rule, with_rule, lift_pct)):
        ax.plot([n_rule, w_rule], [idx, idx], color=COLORS["grid"], linewidth=2.2, zorder=1)
        ax.scatter(n_rule, idx, color=COLORS["no_rule"], s=48, zorder=3, label="no_rule" if idx == 0 else "")
        ax.scatter(
            w_rule,
            idx,
            color=COLORS["min_rule"],
            s=52,
            marker="s",
            zorder=3,
            label="with_rule" if idx == 0 else "",
        )
        ax.text(
            w_rule + 0.003,
            idx,
            f"+{pct:.0f}%",
            va="center",
            fontsize=9,
            color=COLORS["text_secondary"],
        )

    ax.set_title("B. Threshold Shift under Rule Constraints", loc="left", fontsize=12, fontweight="bold")
    ax.set_xlabel("Reliability Threshold ε*")
    ax.set_yticks(y)
    ax.set_yticklabels(levels)
    ax.set_xlim(0.0, 0.09)
    ax.grid(axis="x", linestyle="--", alpha=0.35, color=COLORS["grid"])
    ax.legend(loc="lower right", frameon=False)
    ax.text(
        0.02,
        0.06,
        "Each segment links the same complexity layer under no_rule and with_rule.",
        transform=ax.transAxes,
        fontsize=8.5,
        color=COLORS["text_secondary"],
    )


def create_figure():
    setup_nsfc_style()
    data = load_data()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8), constrained_layout=True)
    plot_success_curves(data, axes[0])
    plot_threshold_shift(data, axes[1])

    fig.suptitle(
        "Figure 6. Complexity-Related Thresholds and Rule Suppression",
        fontsize=14,
        fontweight="bold",
        color=COLORS["text"],
    )
    fig.text(
        0.5,
        0.01,
        "Note: H3 focuses on complexity-related threshold differences, while H2 asks whether rule constraints lift ε* "
        "and delay failure. The figure emphasizes threshold shift and curve shape rather than dashboard-style panels.",
        ha="center",
        fontsize=9,
        color=COLORS["text_secondary"],
    )
    return fig


def main():
    print("Generating H2/H3 preliminary results figure...")
    fig = create_figure()
    save_figure(fig, "fig6_h2h3_threshold")
    plt.close(fig)
    print("Done!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""论文图 Fig.1 / Fig.2 / Fig.4 生成（Stage 5 排版前置，纯绘图，零模拟）。

数据来源（只读，不改动任何已封存结果）：
  Fig.1  实验设计示意图 — 无数据，纯示意（四臂 × 26 点 ε 网格 × 三复杂度层，跨臂共用随机数）。
  Fig.2  success-rate vs ε 曲线 — evidence/videocad/notes/four_arm_confirm/*/curve_summary.csv，
        代表性格两个：主格 ρ=0.9/r=0.2 与交越区 ρ=0/r=0.5，三个复杂度层，四臂 + 0.5 判据线。
  Fig.4  规则类型消融 — evidence/videocad/notes/rule_ablation/{ablation_effects,eps_star}.csv，
        可测组（state consistency / legality set）柱状 + Δε*（extended 10-pt 网格，删失标注），
        不可测组（ordering / coordinate）按稿内规范以"标注空组"呈现，绝不画零高柱。

配色沿用主图 fig_eps_star_vs_rho.png（scripts/eps_star_grid_summary.py）的四臂映射，
保证全稿图间一致；线型 + marker 为次级编码（配色 CVD 校验已过，亮度带/灰基线为既定论文惯例，
以线型与直接标注补偿）。输出目录默认 tmp/paper_figures/。
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
CONFIRM = REPO / "evidence" / "videocad" / "notes" / "four_arm_confirm"
ABLATION = REPO / "evidence" / "videocad" / "notes" / "rule_ablation"

# 四臂身份映射 = 主图既定配色（全稿一致）
ARM_COLORS = {"no_rules": "#888888", "retry_selfreport": "#f4a261",
              "retry_oracle": "#e63946", "min_rules": "#2a9d8f"}
ARM_STYLES = {"no_rules": ":", "retry_selfreport": "--",
              "retry_oracle": "-", "min_rules": "-"}
ARM_MARKERS = {"no_rules": "x", "retry_selfreport": "s",
               "retry_oracle": "o", "min_rules": "D"}
ARM_LABELS = {"no_rules": "no_rules (baseline)", "retry_selfreport": "retry_selfreport",
              "retry_oracle": "retry_oracle (upper bound)", "min_rules": "min_rules"}
ARM_ORDER = ("no_rules", "retry_selfreport", "retry_oracle", "min_rules")

# 消融图（条件色，非臂色）：ε 三点用单色相浅→深梯度；正负用青/红双极
ABLATION_EPS_SHADES = {0.02: "#a8d8d1", 0.05: "#63b3a7", 0.08: "#2a9d8f"}
POS, NEG = "#2a9d8f", "#c94b4b"   # Δε* 双极（负极取深一档的红，避与柱状 ε 梯度混淆）
INK, MUTED = "#222222", "#777777"

UNTESTABLE_SENTENCE = ("These two pre-registered conditions are therefore not testable "
                       "in this study; we report them as untestable rather than as null effects.")


# ---------------------------------------------------------------- Fig.1 示意图
def fig1(out: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.6, 8.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 13.4)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#f4f7f6", ec="#2a9d8f", fs=8.8, lw=1.4):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.18",
                                     fc=fc, ec=ec, lw=lw))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=INK, linespacing=1.45)

    def arrow(x1, y1, x2, y2, style="-", color="#555555"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=14, lw=1.3, color=color,
                                     linestyle=style, shrinkA=2, shrinkB=2))

    box(1.2, 11.9, 7.6, 1.25,
        "VideoCAD action-event archive (Dataverse 11828777, MD5-verified)\n"
        "44,291 symbolic action chains · 2,131,066 events")
    box(1.2, 9.9, 7.6, 1.25,
        "Complexity stratification: low / medium / high\n"
        "600-chain confirmation set (seed 20260916, pre-registered)")
    box(1.2, 7.6, 7.6, 1.5,
        "Controlled error injection at rate ε\n"
        "26-point grid ε ∈ {0.00 … 0.50} · mixture 70% action swap / 30% status flip\n"
        "common random numbers: identical error draws across all arms")
    box(0.15, 7.6, 2.5, 1.5,
        "ρ ∈ {0, 0.5, 0.9}\nretry error-repeatability\n\nr ∈ {0.2, 0.5}  budget\nB = ⌈L(1+r)⌉\n\nk = 2  retry cap",
        fc="#fdf6ec", ec="#f4a261", fs=7.6)

    arm_y, arm_w, gap = 4.7, 2.15, 0.32
    xs = [0.55 + i * (arm_w + gap) for i in range(4)]
    arm_txt = ["no_rules\n(baseline)",
               "retry_selfreport\n(env.-reported)",
               "retry_oracle\n(upper bound,\nmain contrast)",
               "min_rules\n(stack-consistency\n+ illegal-close)"]
    for x, t in zip(xs, arm_txt):
        box(x, arm_y, arm_w, 1.7, t, fc="#ffffff", ec="#2a9d8f", fs=7.3)

    box(1.2, 2.2, 7.6, 1.35,
        "ε* per arm — injection rate at which success probability crosses 0.5\n"
        "chain-level bootstrap B = 9999 · pre-registered decision gate")
    ax.text(5.0, 1.35,
            "7.49M runs · confirmation seed 20261015 · run-once (RUN_COMPLETE marker)",
            ha="center", fontsize=8.2, color=MUTED)

    arrow(5.0, 11.9, 5.0, 11.15)
    arrow(5.0, 9.9, 5.0, 9.1)
    for x in xs:
        arrow(5.0, 7.6, x + arm_w / 2, 6.4)
        arrow(x + arm_w / 2, 4.7, 5.0, 3.55)
    # ρ/r/k 只作用于 retry 臂：虚线
    for i in (1, 2):
        arrow(2.65, 7.6, xs[i] + arm_w / 2, 6.4, style="--", color="#f4a261")

    ax.set_title("Controlled four-arm error-injection design", fontsize=11.5, pad=10)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------- Fig.2 success vs ε
def _load_curves(run_dir: Path) -> dict:
    """curve_summary.csv -> {(stratum, arm): [(ε, success_rate), ...]}"""
    data: dict[tuple[str, str], list[tuple[float, float]]] = {}
    with (run_dir / "curve_summary.csv").open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["complexity_label"] in ("low", "medium", "high"):
                data.setdefault((row["complexity_label"], row["arm"]),
                                []).append((float(row["epsilon"]),
                                            float(row["success_rate"])))
    return data

def fig2(out: Path) -> None:
    cells = [(CONFIRM / "r02_rho09", "ρ = 0.9, r = 0.2  (primary cell)"),
             (CONFIRM / "r05_rho00", "ρ = 0, r = 0.5  (transient errors, ample budget)")]
    strata = ["low", "medium", "high"]
    stratum_labels = {"low": "low complexity", "medium": "medium complexity",
                      "high": "high complexity"}
    fig, axes = plt.subplots(3, 2, figsize=(9.6, 9.2), sharex=True, sharey=True)

    for col, (run_dir, cell_title) in enumerate(cells):
        curves = _load_curves(run_dir)
        for row_i, stratum in enumerate(strata):
            ax = axes[row_i][col]
            for arm in ARM_ORDER:
                pts = sorted(curves[(stratum, arm)])
                xs, ys = zip(*pts)
                ax.plot(xs, ys, ARM_STYLES[arm], color=ARM_COLORS[arm],
                        marker=ARM_MARKERS[arm], ms=3.6, lw=1.9, label=ARM_LABELS[arm],
                        markevery=2)
            ax.axhline(0.5, color="#555555", lw=1.0, ls=(0, (5, 4)))
            ax.text(0.497, 0.515, "ε* criterion = 0.5", ha="right", va="bottom",
                    fontsize=7.4, color="#555555")
            ax.set_ylim(-0.03, 1.03)
            ax.set_xlim(-0.01, 0.51)
            ax.grid(alpha=0.25)
            ax.tick_params(labelsize=8.5)
            if row_i == 0:
                ax.set_title(cell_title, fontsize=10)
            if row_i == 2:
                ax.set_xlabel("injection rate ε", fontsize=9.5)
            if col == 0:
                ax.set_ylabel(f"{stratum_labels[stratum]}\nsuccess rate", fontsize=9.5)

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False,
               fontsize=9.3, bbox_to_anchor=(0.5, -0.005))
    fig.suptitle("Success rate vs injection rate ε — four arms under common random numbers",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0.045, 1, 0.965))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------- Fig.4 消融图
def _ablation_rows() -> tuple[dict, dict]:
    """(delta_succ[class][direction][eps] -> value, eps_star[(condition)] -> (val, flag))"""
    ds: dict[str, dict[str, dict[float, float]]] = {}
    with (ABLATION / "ablation_effects.csv").open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row["quantity"] == "delta_success_rate" and row["grid"] == "primary"
                    and row["stratum"] == "pooled" and row["epsilon"]):
                ds.setdefault(row["rule_class"], {})[row["direction"]] = \
                    ds.get(row["rule_class"], {}).get(row["direction"], {})
                ds[row["rule_class"]][row["direction"]][float(row["epsilon"])] = \
                    float(row["value"])
    es: dict[str, tuple[float | None, str]] = {}
    with (ABLATION / "eps_star.csv").open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["stratum"] == "pooled" and row["grid"] == "extended_10pt":
                es[row["condition"]] = (
                    float(row["epsilon_star"]) if row["epsilon_star"] else None,
                    row["censor_flag"])
    return ds, es

def fig4(out: Path) -> None:
    ds, es = _ablation_rows()
    no_rules_eps = es["no_rules"][0]           # 参考臂（下删失，取网格下界）
    full_eps = es["full"][0]

    # Δε*（extended 10-pt，pooled）：条件 − 参考；参考删失的记 flag
    def delta(cond: str, ref: float) -> tuple[float | None, str]:
        v, flag = es[cond]
        if v is None:
            return None, flag
        return v - ref, flag

    fig = plt.figure(figsize=(9.8, 7.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.6, 1.0], hspace=0.42, wspace=0.25,
                         left=0.09, right=0.97, top=0.90, bottom=0.07)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    axu = fig.add_subplot(gs[1, :])
    axu.axis("off")

    # ---- Panel A：三主 ε 点 Δ success rate（single 为正，LOO 为负）
    classes = ["consistency", "legal_set"]
    class_labels = ["state consistency", "legality set"]
    eps_pts = [0.02, 0.05, 0.08]
    group_w, bar_w = 0.78, 0.24
    for gi, cls in enumerate(classes):
        base = gi * 2.2
        for di, direction in enumerate(("single_vs_no_rules", "loo_vs_full")):
            x0 = base + di * (group_w + 0.30)
            for k, e in enumerate(eps_pts):
                v = ds[cls][direction][e]
                ax1.bar(x0 + k * bar_w, v, width=bar_w * 0.92,
                        color=ABLATION_EPS_SHADES[e], edgecolor="white", lw=0.8)
                ax1.text(x0 + k * bar_w, v + (0.022 if v >= 0 else -0.022),
                         f"{v:+.3f}", ha="center",
                         va="bottom" if v >= 0 else "top", fontsize=7.0, color=INK)
        ax1.text(base + group_w / 2 - 0.15, 0.72, class_labels[gi], ha="center",
                 fontsize=9.6, color=INK)
    ax1.axhline(0, color=INK, lw=1.0)
    ax1.set_ylim(-0.78, 0.82)
    ax1.set_xticks([])
    ax1.set_ylabel("Δ success rate vs reference\n(pooled, primary grid)", fontsize=9)
    ax1.set_title("A · Δ success rate at the three pre-registered ε points\n"
                  "left cluster: enabled alone (vs no_rules) · right: removed from full (LOO)",
                  fontsize=9.2)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=c, ec="white") for c in
               (ABLATION_EPS_SHADES[e] for e in eps_pts)]
    ax1.legend(handles, [f"ε = {e:g}" for e in eps_pts], frameon=False, fontsize=8.2,
               loc="lower right")
    ax1.grid(axis="y", alpha=0.25)

    # ---- Panel B：Δε*（extended 10-pt 网格）
    entries = [
        ("state consistency\nalone", delta("only_consistency", no_rules_eps)),
        ("state consistency\nLOO", delta("loo_no_consistency", full_eps)),
        ("legality set\nLOO", delta("loo_no_legal_set", full_eps)),
        ("legality set\nalone", delta("only_legal_set", no_rules_eps)),
        ("full set\n(vs no_rules)", (full_eps - no_rules_eps, es["full"][1])),
    ]
    xs = range(len(entries))
    for x, (label, (v, flag)) in zip(xs, entries):
        if v is None:
            ax2.text(x, 0.02, "censored\n(not measurable)", ha="center", va="bottom",
                     fontsize=7.6, color=MUTED, style="italic")
            continue
        ax2.bar(x, v, width=0.62, color=POS if v >= 0 else NEG,
                edgecolor="white", lw=0.8)
        ax2.text(x, v + (0.010 if v >= 0 else -0.010), f"{v:+.3f}",
                 ha="center", va="bottom" if v >= 0 else "top",
                 fontsize=8.0, color=INK)
        if "censored" in flag or x == 4:
            note = "ref. floor-censored" if x == 4 else "lower end censored"
            ax2.annotate(note, xy=(x, v), xytext=(x, v - 0.075 if v < 0 else v - 0.075),
                         ha="center", fontsize=6.8, color=MUTED, style="italic")
    ax2.axhline(0, color=INK, lw=1.0)
    ax2.set_xticks(list(xs))
    ax2.set_xticklabels([e[0] for e in entries], fontsize=8.0)
    ax2.set_ylim(-0.30, 0.27)
    ax2.set_ylabel("Δε* (pooled, exploratory\n10-point grid)", fontsize=9)
    ax2.set_title("B · Δε* on the extended grid — censored values reported, not omitted",
                  fontsize=9.2)
    ax2.grid(axis="y", alpha=0.25)

    # ---- 底部：不可测组（标注空组，不画零高柱）
    axu.add_patch(FancyBboxPatch((0.02, 0.18), 0.96, 0.72,
                                 boxstyle="round,pad=0.012", fc="#fbfbfb",
                                 ec="#bbbbbb", lw=1.1, ls=(0, (4, 3)),
                                 transform=axu.transAxes))
    axu.text(0.5, 0.88, "Not testable in this study — shown as an annotated empty group "
             "(not as zero-height bars)", ha="center", va="top", fontsize=9.6, color=INK,
             transform=axu.transAxes)
    for i, (name, sig) in enumerate([("ordering", "≡ no_rules (single) / ≡ full (LOO)"),
                                     ("coordinate", "≡ no_rules (single) / ≡ full (LOO)")]):
        xc = 0.235 + i * 0.50
        axu.add_patch(FancyBboxPatch((xc - 0.185, 0.36), 0.37, 0.34,
                                      boxstyle="round,pad=0.01", fc="white",
                                      ec="#bbbbbb", lw=1.0, ls=(0, (4, 3)),
                                      transform=axu.transAxes))
        axu.text(xc, 0.62, name, ha="center", fontsize=10, color=INK,
                 transform=axu.transAxes)
        axu.text(xc, 0.47, f"untestable · trigger count = 0\nstructural identity: {sig}",
                 ha="center", fontsize=7.8, color=MUTED, transform=axu.transAxes)
    axu.text(0.5, 0.06, f"“{UNTESTABLE_SENTENCE}”", ha="center", va="bottom",
             fontsize=8.4, color=INK, style="italic", transform=axu.transAxes)

    fig.suptitle("Rule-type ablation — the effect localizes to state consistency; "
                 "two pre-registered classes are untestable", fontsize=11.5)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description="论文图 Fig.1/Fig.2/Fig.4 生成")
    ap.add_argument("--out-dir", type=Path, default=REPO / "tmp" / "paper_figures")
    ap.add_argument("--fig", choices=["1", "2", "4", "all"], default="all")
    args = ap.parse_args()
    if args.fig in ("1", "all"):
        fig1(args.out_dir / "fig1_design_schematic.png")
        print(f"Wrote: {args.out_dir / 'fig1_design_schematic.png'}")
    if args.fig in ("2", "all"):
        fig2(args.out_dir / "fig2_success_rate_vs_epsilon.png")
        print(f"Wrote: {args.out_dir / 'fig2_success_rate_vs_epsilon.png'}")
    if args.fig in ("4", "all"):
        fig4(args.out_dir / "fig4_rule_ablation.png")
        print(f"Wrote: {args.out_dir / 'fig4_rule_ablation.png'}")


if __name__ == "__main__":
    main()

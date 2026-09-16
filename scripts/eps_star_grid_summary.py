#!/usr/bin/env python3
"""ε* 跨条件极差（正式报告量）+ ε*–ρ 主图生成。

报告量（audit §3.6 预登记，写作"不变性主张的直接度量"）：
  各臂 ε* 在 (ρ, r) 网格（3×2 = 6 格，pooled）上的极差与倍数。
  min_rules / no_rules 预期为 0（不随 ρ、r 变）；retry_oracle 预期跨约一个数量级。

主图（论文主图，森林图降为次图）：
  横轴 ρ，纵轴 ε*（pooled，判据 0.5，线性插值），每臂一条线，
  r = 0.2 / r = 0.5 两个 panel。min_rules 为水平线；retry_oracle 陡降；
  r = 0.5 panel 在 ρ≈0 附近与 min_rules 交叉。

数据：run_four_arm_experiment 输出目录（per_run_results.csv 重算 pooled ε*，
      与引擎同一插值函数）。零模拟成本，纯分析。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "evidence" / "videocad" / "scripts"))
from run_four_arm_experiment import eps_star  # noqa: E402

ARMS = ("no_rules", "retry_selfreport", "retry_oracle", "min_rules")


def load_meta(run_dir: Path) -> dict:
    s = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    return {"rho": s["inputs"]["retry_repro_prob"], "r": s["inputs"]["budget_ratio"]}


def pooled_eps(run_dir: Path, arm: str, criterion: float):
    by_eps: dict[float, list[int]] = {}
    with (run_dir / "per_run_results.csv").open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["arm"] == arm:
                by_eps.setdefault(float(row["epsilon"]), []).append(int(row["success"]))
    curve = sorted((eps, sum(v) / len(v)) for eps, v in by_eps.items())
    val, flag = eps_star(curve, criterion)
    return val, flag


def main() -> None:
    ap = argparse.ArgumentParser(description="ε* range across (ρ,r) grid + ε*–ρ main figure")
    ap.add_argument("--runs", type=Path, nargs="+", required=True)
    ap.add_argument("--criterion", type=float, default=0.5)
    ap.add_argument("--range-out", type=Path, required=True)
    ap.add_argument("--plot", type=Path, default=None)
    args = ap.parse_args()

    grid: dict[tuple[float, float], dict[str, float | None]] = {}
    for d in args.runs:
        meta = load_meta(d)
        cell: dict[str, float | None] = {}
        for arm in ARMS:
            v, _ = pooled_eps(d, arm, args.criterion)
            cell[arm] = v
        grid[(meta["rho"], meta["r"])] = cell

    # 极差表
    rows = []
    for arm in ARMS:
        vals = [(rho, r, grid[(rho, r)][arm]) for rho, r in sorted(grid)]
        defined = [(rho, r, v) for rho, r, v in vals if v is not None]
        if not defined:
            continue
        vs = [v for _, _, v in defined]
        lo, hi = min(vs), max(vs)
        rows.append({
            "arm": arm, "scope": "pooled", "n_conditions": len(grid),
            "n_defined": len(defined), "eps_star_min": round(lo, 6), "eps_star_max": round(hi, 6),
            "range": round(hi - lo, 6), "ratio_max_over_min": round(hi / lo, 3) if lo > 0 else "",
            "censored_cells": len(grid) - len(defined),
            "per_cell": "; ".join(f"ρ={rho},r={r}:{v:.4f}" if v is not None else f"ρ={rho},r={r}:>0.50"
                                  for rho, r, v in vals),
        })
    args.range_out.parent.mkdir(parents=True, exist_ok=True)
    with args.range_out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"Wrote: {args.range_out}")
    for r_ in rows:
        print(f"  {r_['arm']:16} ε* ∈ [{r_['eps_star_min']:.4f}, {r_['eps_star_max']:.4f}]"
              f"  range={r_['range']:.4f}  ratio={r_['ratio_max_over_min']}  censored={r_['censored_cells']}")

    if args.plot:
        plot_eps_rho(grid, args.plot, args.criterion)
        print(f"Plot:  {args.plot}")


def plot_eps_rho(grid, path: Path, criterion: float) -> None:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return
    colors = {"no_rules": "#888888", "retry_selfreport": "#f4a261",
              "retry_oracle": "#e63946", "min_rules": "#2a9d8f"}
    styles = {"no_rules": ":", "retry_selfreport": "--", "retry_oracle": "-", "min_rules": "-"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    for ax, r in zip(axes, (0.2, 0.5)):
        rhos = sorted({rho for rho, rr in grid if rr == r})
        for arm in ARMS:
            xs, ys = [], []
            for rho in rhos:
                v = grid.get((rho, r), {}).get(arm)
                if v is not None:
                    xs.append(rho); ys.append(v)
            ax.plot(xs, ys, styles[arm], color=colors[arm], marker="o", lw=2.2, label=arm)
        ax.set_title(f"r = {r}  (B = ceil(L·{1+r:g}))")
        ax.set_xlabel("ρ  (retry error-reproducibility)")
        ax.set_xticks(rhos)
        ax.grid(alpha=0.25)
    axes[0].set_ylabel(f"ε*  (success-criterion {criterion}, pooled)")
    axes[0].axhline(0.193, color="#2a9d8f", lw=0)  # no-op keeps legend order stable
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Threshold ε* vs error reproducibility ρ — each arm, two budget settings")
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""ε* 的链级 bootstrap 与 Δε* 检验 —— 决策门 v2 的分析实现（审计 §3.2 预登记）。

本脚本**必须先于确认集结果存在并已验证**（审计复查项 2）：分析代码若在见过答案
之后编写，即使无主观故意，也等同于事后选择分析口径。开发集验证：
    python3 scripts/bootstrap_eps_star.py --runs tmp/dev_ext_r02_rho00 \
        tmp/dev_ext_r02_rho05 tmp/dev_ext_r02_rho09 --plot tmp/dev_ext_forest_r02.png

预登记口径（audit §3.2，写死在 DEFAULT_*）：
  estimand   Δε* = ε*(min_rules) − ε*(retry_oracle)；ε* = 合并成功率曲线与判据的线性插值交点
  重抽样     链（sample_id）为单位的非参数 bootstrap，B=1003，种子显式传入并落盘
  主格       r=0.2, ρ=0.9, 三层合并 → 门：Δε* 的 95% 百分位 CI 跨 0 即停投
  次要族     r=0.2 下 3 ρ × 3 层 = 9 格，Holm 校正（bootstrap 镜像 p），全部如实报告
  敏感性族   r=0.5 对应 9 格，族内 Holm；ρ=0 处 Δε* 随 r 变号属承重发现，正文必报（§3.3）

p 值定义（bootstrap 镜像）：p = 2·min(F̂(0), 1−F̂(0))，cap 1，F̂ 为 bootstrap Δε* 的经验分布。
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "evidence" / "videocad" / "scripts"))
from run_four_arm_experiment import eps_star  # noqa: E402  （与引擎同一插值实现）

PAIR = ("min_rules", "retry_oracle")
CRITERION_DEFAULT = 0.5
B_DEFAULT = 1003
STRATA = ("low", "medium", "high")


def load_run_dir(run_dir: Path) -> tuple[dict, dict, dict]:
    """读 per_run_results.csv + summary.json → (chain_rates, meta, strata_map)。

    chain_rates[(arm, sample_id)] = {eps: mean_success_over_reps}
    strata_map[sample_id] = complexity_label
    """
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    meta = {"rho": summary["inputs"]["retry_repro_prob"],
            "budget_ratio": summary["inputs"]["budget_ratio"],
            "n_chains": summary["inputs"]["chains"]}
    acc: dict[tuple[str, str], defaultdict[float, list]] = defaultdict(lambda: defaultdict(list))
    strata_map: dict[str, str] = {}
    with (run_dir / "per_run_results.csv").open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            acc[(r["arm"], r["sample_id"])][float(r["epsilon"])].append(int(r["success"]))
            strata_map[r["sample_id"]] = r["complexity_label"]
    chain_rates = {k: {eps: sum(v) / len(v) for eps, v in eps_dict.items()}
                   for k, eps_dict in acc.items()}
    return chain_rates, meta, strata_map


def pooled_eps_star(chain_rates: dict, chains: list[str], arm: str, criterion: float):
    """给定链集合，求该臂的合并 ε*（每 ε 对链成功率再平均 → 插值）。"""
    eps_vals = sorted({eps for (a, _), d in chain_rates.items()
                       if a == arm for eps in d})
    curve = []
    for eps in eps_vals:
        rates = [chain_rates[(arm, c)][eps] for c in chains if eps in chain_rates.get((arm, c), {})]
        if rates:
            curve.append((eps, sum(rates) / len(rates)))
    val, flag = eps_star(curve, criterion)
    return val, flag, curve


def delta_eps_star(chain_rates: dict, chains: list[str], criterion: float):
    """Δε* = ε*(min_rules) − ε*(retry_oracle)；任一侧删失返回 None。"""
    m, mf, _ = pooled_eps_star(chain_rates, chains, PAIR[0], criterion)
    o, of, _ = pooled_eps_star(chain_rates, chains, PAIR[1], criterion)
    if m is None or o is None:
        return None, mf, of
    return m - o, mf, of


def bootstrap_cell(chain_rates: dict, chains: list[str], criterion: float,
                   b: int, rng: random.Random) -> tuple[float | None, list[float], int]:
    """点估计 + B 次链级重抽样。返回 (point, deltas, n_undefined)。"""
    point, _, _ = delta_eps_star(chain_rates, chains, criterion)
    deltas: list[float] = []
    n_undefined = 0
    n = len(chains)
    for _ in range(b):
        draw = [chains[rng.randrange(n)] for _ in range(n)]
        d, _, _ = delta_eps_star(chain_rates, draw, criterion)
        if d is None:
            n_undefined += 1
        else:
            deltas.append(d)
    return point, deltas, n_undefined


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm 逐步校正，输入 {cell: p}，返回 {cell: adj_p}。"""
    m = len(pvals)
    order = sorted(pvals, key=lambda k: pvals[k])
    adj: dict[str, float] = {}
    running = 0.0
    for i, k in enumerate(order):
        running = max(running, (m - i) * pvals[k])
        adj[k] = min(1.0, running)
    return adj


def main() -> None:
    ap = argparse.ArgumentParser(description="Chain-level bootstrap of Δε* (gate v2 analysis)")
    ap.add_argument("--runs", type=Path, nargs="+", required=True,
                    help="run_four_arm_experiment 输出目录（含 per_run_results.csv + summary.json）")
    ap.add_argument("--criterion", type=float, default=CRITERION_DEFAULT)
    ap.add_argument("--b", type=int, default=B_DEFAULT)
    ap.add_argument("--seed", type=int, default=20260915,
                    help="bootstrap 自身种子（与实验种子独立，记录后入补充材料）")
    ap.add_argument("--out-prefix", type=Path, default=None,
                    help="结果 CSV 前缀（默认取第一个 runs 目录的父目录）")
    ap.add_argument("--plot", type=Path, default=None, help="森林图输出路径（图 3 原料）")
    args = ap.parse_args()

    out_prefix = args.out_prefix or args.runs[0].parent / "bootstrap"
    rng = random.Random(args.seed)

    cells: list[dict] = []
    replicates: dict[str, list[float]] = {}
    for run_dir in args.runs:
        chain_rates, meta, strata_map = load_run_dir(run_dir)
        all_chains = sorted(strata_map)
        sets = {"pooled": all_chains}
        for s in STRATA:
            sets[s] = sorted(c for c in all_chains if strata_map[c] == s)
        for set_name, chains in sets.items():
            point, deltas, n_undef = bootstrap_cell(chain_rates, chains, args.criterion,
                                                    args.b, rng)
            n = len(deltas)
            if n == 0:
                lo = hi = p = None
            else:
                sd = sorted(deltas)
                lo = sd[max(0, int(0.025 * n))]
                hi = sd[min(n - 1, int(0.975 * n) + 1)]
                p = min(1.0, 2.0 * min(sum(1 for d in deltas if d <= 0.0) / n,
                                       sum(1 for d in deltas if d >= 0.0) / n))
            tag = f"r{meta['budget_ratio']}_rho{meta['rho']}_{set_name}"
            replicates[tag] = deltas
            cells.append({
                "r": meta["budget_ratio"], "rho": meta["rho"], "stratum_set": set_name,
                "n_chains": len(chains), "B_requested": args.b, "B_defined": n,
                "pct_undefined": round(n_undef / args.b, 4) if args.b else 0.0,
                "delta_eps_star_point": round(point, 6) if point is not None else "",
                "ci_lo": round(lo, 6) if lo is not None else "",
                "ci_hi": round(hi, 6) if hi is not None else "",
                "p_boot": round(p, 6) if p is not None else "",
                "family": ("primary" if (meta["budget_ratio"] == 0.2 and meta["rho"] == 0.9
                                          and set_name == "pooled")
                           else "secondary-9" if (meta["budget_ratio"] == 0.2 and set_name in STRATA)
                           else "sensitivity-r05" if meta["budget_ratio"] == 0.5
                           else "descriptive"),
                "holm_adj_p": "",
            })

    # Holm：族内校正（secondary-9 族与 sensitivity-r05 族分别处理）
    for family in ("secondary-9", "sensitivity-r05"):
        fam = [c for c in cells if c["family"] == family and c["p_boot"] != ""]
        if fam:
            adj = holm({f"{c['rho']}|{c['stratum_set']}": float(c["p_boot"]) for c in fam})
            for c in fam:
                c["holm_adj_p"] = round(adj[f"{c['rho']}|{c['stratum_set']}"], 6)

    cells.sort(key=lambda c: (c["r"], c["rho"], c["stratum_set"] != "pooled", c["stratum_set"]))
    out_csv = Path(f"{out_prefix}_results.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cells[0].keys()))
        w.writeheader(); w.writerows(cells)

    out_rep = Path(f"{out_prefix}_replicates.csv")
    with out_rep.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["replicate"] + list(replicates))
        bmax = max(len(v) for v in replicates.values())
        for i in range(bmax):
            w.writerow([i] + [v[i] if i < len(v) else "" for v in replicates.values()])

    primary = next((c for c in cells if c["family"] == "primary"), None)
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_rep} (B={args.b} replicates per cell, seed={args.seed})")
    if primary:
        verdict = "CI 跨 0 → 门触发（停投）" if (primary["ci_lo"] != "" and primary["ci_lo"] <= 0 <= primary["ci_hi"]) \
            else "CI 全正 → 门通过（继续投稿流程）" if primary["ci_lo"] != "" and primary["ci_lo"] > 0 else "无法判定"
        print(f"\n主格 (r=0.2, ρ=0.9, pooled): Δε* = {primary['delta_eps_star_point']} "
              f"95% CI [{primary['ci_lo']}, {primary['ci_hi']}] → {verdict}")
    if args.plot:
        plot_forest(cells, args.plot)
        print(f"Plot:  {args.plot}")


def plot_forest(cells: list[dict], path: Path) -> None:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return
    rows = [c for c in cells if c["stratum_set"] in STRATA and c["delta_eps_star_point"] != ""]
    rows.sort(key=lambda c: (c["r"], c["rho"], STRATA.index(c["stratum_set"])))
    colors = {"low": "#2a9d8f", "medium": "#f4a261", "high": "#e63946"}
    fig, ax = plt.subplots(figsize=(8, max(4, len(rows) * 0.32)))
    ys = list(range(len(rows)))[::-1]
    for y, c in zip(ys, rows):
        x = float(c["delta_eps_star_point"])
        lo = float(c["ci_lo"]) if c["ci_lo"] != "" else x
        hi = float(c["ci_hi"]) if c["ci_hi"] != "" else x
        ax.plot([lo, hi], [y, y], color=colors[c["stratum_set"]], lw=2)
        ax.plot(x, y, "o", color=colors[c["stratum_set"]])
        rlab = "r=.2" if c["r"] == 0.2 else "r=.5"
        ax.text(hi + 0.004, y, f"ρ={c['rho']} {rlab}", va="center", fontsize=8, color="#555555")
    ax.axvline(0, color="k", lw=1)
    for s, col in colors.items():
        ax.plot([], [], "o", color=col, label=s)
    ax.legend(title="stratum", loc="lower right")
    ax.set_yticks([])
    ax.set_xlabel("Δε* = ε*(min_rules) − ε*(retry_oracle)")
    ax.set_title("Δε* forest (chain-level bootstrap, B=%d)" % (cells[0]["B_defined"] or 0))
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()

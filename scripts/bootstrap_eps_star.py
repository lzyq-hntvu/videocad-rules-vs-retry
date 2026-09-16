#!/usr/bin/env python3
"""ε* 的链级 bootstrap 与 Δε* 检验 —— 决策门 v2 的分析实现（审计 §3.2 预登记，三段式）。

本脚本**必须先于确认集结果存在并已验证**（审计复查项 2）：分析代码若在见过答案
之后编写，即使无主观故意，也等同于事后选择分析口径。开发集验证：
    python3 scripts/bootstrap_eps_star.py --runs tmp/dev_ext_r02_rho00 \
        tmp/dev_ext_r02_rho05 tmp/dev_ext_r02_rho09 --plot tmp/dev_ext_forest_r02.png

预登记口径（audit §3.2，三段式，无歧义）：
  主检验   单一事前指定格：r=0.2, ρ=0.9, 三层合并（pooled）
           estimand Δε* = ε*(min_rules) − ε*(retry_oracle)；门：95% 百分位 CI 跨 0 即停投；不做任何校正
  次要族   r=0.2 下 3 ρ × 3 层 = 9 格，族内 Holm（bootstrap 镜像 p）；全部如实报告
  描述性   pooled @ ρ∈{0, 0.5}（主对照），仅点估计 + CI，不参与任何判定、不进族
  对照量   Δε*(retry_oracle − no_rules)：重试自身相对无干预的增量（审计复查项 1）。
           对每个 ρ 报告（pooled 与分层同出），family=control——仅点估计 + CI，
           无 Holm、不构成判定。若 ρ=0.9 下该量 ≈0，正文明写：该条件下重试已基本失效，
           主对比近似于规则 vs 无干预——这是 ρ 的机制后果，不是设计缺陷。
  敏感性族 r=0.5 对应 9 格（主对照），族内 Holm；ρ=0 处 Δε* 随 r 变号属承重发现，进正文

p 值定义（bootstrap 镜像）：p = 2·min(F̂(0), 1−F̂(0))，cap 1。
分辨率下限 2/B：B = 9999 → 2×10⁻⁴，9 格 Holm 后最小可报 ≈ 1.8×10⁻³；正文 p 小于
该值时写作 "p < 2×10⁻⁴（bootstrap 分辨率下限）"。B = 9999 使百分位点恰落次序统计量
（0.025×9999 = 249.975 → 取 250/9750 次序；脚本按 rank 取整，B 取 9999/1999/999 族）。
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
from run_four_arm_experiment import eps_star  # noqa: E402  （与引擎同一插值实现，杜绝口径分叉）

PAIRS = {
    "main": ("min_rules", "retry_oracle"),
    "control": ("retry_oracle", "no_rules"),
}
MAIN_PAIR_NAME = "main"
B_DEFAULT = 9999
STRATA = ("low", "medium", "high")


def load_run_dir(run_dir: Path) -> tuple[dict, dict, dict]:
    """读 per_run_results.csv + summary.json → (chain_rates, meta, strata_map)。"""
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
    eps_vals = sorted({eps for (a, _), d in chain_rates.items()
                       if a == arm for eps in d})
    curve = []
    for eps in eps_vals:
        rates = [chain_rates[(arm, c)][eps] for c in chains if eps in chain_rates.get((arm, c), {})]
        if rates:
            curve.append((eps, sum(rates) / len(rates)))
    val, flag = eps_star(curve, criterion)
    return val, flag


def delta_eps_star(chain_rates: dict, chains: list[str], pair: tuple[str, str], criterion: float):
    a, b = pair
    va, _ = pooled_eps_star(chain_rates, chains, a, criterion)
    vb, _ = pooled_eps_star(chain_rates, chains, b, criterion)
    if va is None or vb is None:
        return None
    return va - vb


def bootstrap_cell(chain_rates: dict, chains: list[str], pair: tuple[str, str],
                   criterion: float, b: int, rng: random.Random):
    point = delta_eps_star(chain_rates, chains, pair, criterion)
    deltas: list[float] = []
    n_undefined = 0
    n = len(chains)
    for _ in range(b):
        draw = [chains[rng.randrange(n)] for _ in range(n)]
        d = delta_eps_star(chain_rates, draw, pair, criterion)
        if d is None:
            n_undefined += 1
        else:
            deltas.append(d)
    return point, deltas, n_undefined


def holm(pvals: dict[str, float]) -> dict[str, float]:
    m = len(pvals)
    order = sorted(pvals, key=lambda k: pvals[k])
    adj: dict[str, float] = {}
    running = 0.0
    for i, k in enumerate(order):
        running = max(running, (m - i) * pvals[k])
        adj[k] = min(1.0, running)
    return adj


def main() -> None:
    ap = argparse.ArgumentParser(description="Chain-level bootstrap of Δε* (gate v2, three-tier pre-registration)")
    ap.add_argument("--runs", type=Path, nargs="+", required=True,
                    help="run_four_arm_experiment 输出目录（含 per_run_results.csv + summary.json）")
    ap.add_argument("--criterion", type=float, default=0.5)
    ap.add_argument("--b", type=int, default=B_DEFAULT)
    ap.add_argument("--seed", type=int, default=20260915,
                    help="bootstrap 自身种子（与实验种子独立，记录后入补充材料）")
    ap.add_argument("--out-prefix", type=Path, default=None)
    ap.add_argument("--plot", type=Path, default=None, help="森林图输出路径（主对照，图 3 原料）")
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

        for pair_name, pair in PAIRS.items():
            for set_name, chains in sets.items():
                point, deltas, n_undef = bootstrap_cell(chain_rates, chains, pair,
                                                        args.criterion, args.b, rng)
                n = len(deltas)
                if n == 0:
                    lo = hi = p = None
                else:
                    sd = sorted(deltas)
                    lo = sd[max(0, int(0.025 * n))]
                    hi = sd[min(n - 1, int(0.975 * n) + 1)]
                    p = min(1.0, 2.0 * min(sum(1 for d in deltas if d <= 0.0) / n,
                                           sum(1 for d in deltas if d >= 0.0) / n))
                tag = f"r{meta['budget_ratio']}_rho{meta['rho']}_{set_name}_{pair_name}"
                replicates[tag] = deltas

                if pair_name == "control":
                    family = "control"  # 对照量：仅报告，不校正、不判定
                elif meta["budget_ratio"] == 0.2 and meta["rho"] == 0.9 and set_name == "pooled":
                    family = "primary"
                elif meta["budget_ratio"] == 0.2 and set_name in STRATA:
                    family = "secondary-9"
                elif meta["budget_ratio"] == 0.5 and set_name in STRATA:
                    family = "sensitivity-r05"  # 仅 9 个分层格；pooled @ r=0.5 为描述性（§3.2③）
                else:
                    family = "descriptive"

                cells.append({
                    "pair": f"{pair[0]}-{pair[1]}",
                    "r": meta["budget_ratio"], "rho": meta["rho"], "stratum_set": set_name,
                    "n_chains": len(chains), "B_requested": args.b, "B_defined": n,
                    "pct_undefined": round(n_undef / args.b, 4) if args.b else 0.0,
                    "delta_eps_star_point": round(point, 6) if point is not None else "",
                    "ci_lo": round(lo, 6) if lo is not None else "",
                    "ci_hi": round(hi, 6) if hi is not None else "",
                    "p_boot": round(p, 6) if p is not None else "",
                    "p_floor": f"2/{args.b}",
                    "family": family,
                    "holm_adj_p": "",
                })

    # Holm：仅主对照的检验族（secondary-9 与 sensitivity-r05）；control/descriptive/primary 不参与
    for family in ("secondary-9", "sensitivity-r05"):
        fam = [c for c in cells if c["family"] == family and c["p_boot"] != ""]
        if fam:
            adj = holm({f"{c['rho']}|{c['stratum_set']}": float(c["p_boot"]) for c in fam})
            for c in fam:
                c["holm_adj_p"] = round(adj[f"{c['rho']}|{c['stratum_set']}"], 6)

    cells.sort(key=lambda c: (c["r"], c["rho"], c["stratum_set"] != "pooled",
                              STRATA.index(c["stratum_set"]) if c["stratum_set"] in STRATA else 9,
                              c["pair"]))
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
    print(f"Wrote: {out_rep} (B={args.b} per cell, seed={args.seed})")
    if primary:
        verdict = "CI 跨 0 → 门触发（停投）" if (primary["ci_lo"] != "" and primary["ci_lo"] <= 0 <= primary["ci_hi"]) \
            else "CI 全正 → 门通过（继续投稿流程）" if primary["ci_lo"] != "" and primary["ci_lo"] > 0 else "无法判定"
        print(f"\n主格 (r=0.2, ρ=0.9, pooled, main): Δε* = {primary['delta_eps_star_point']} "
              f"95% CI [{primary['ci_lo']}, {primary['ci_hi']}] → {verdict}")
    controls = [c for c in cells if c["family"] == "control" and c["stratum_set"] == "pooled"]
    for c in controls:
        print(f"对照量 (ρ={c['rho']}, r={c['r']}, pooled): Δε*(oracle−no_rules) = "
              f"{c['delta_eps_star_point']} CI [{c['ci_lo']}, {c['ci_hi']}]")
    if args.plot:
        plot_forest(cells, args.plot)
        print(f"Plot:  {args.plot}")


def plot_forest(cells: list[dict], path: Path) -> None:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return
    rows = [c for c in cells
            if c["pair"] == "-".join(PAIRS["main"]) and c["stratum_set"] in STRATA
            and c["delta_eps_star_point"] != ""]
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
    ax.set_xlabel("Δε* = ε*(min_rules) − ε*(retry_oracle)  [main pair]")
    ax.set_title("Δε* forest — chain-level bootstrap (gate v2, main pair)")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()

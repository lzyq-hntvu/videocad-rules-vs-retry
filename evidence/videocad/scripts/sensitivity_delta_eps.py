#!/usr/bin/env python3
"""敏感性族 Δε* 重算与链级 bootstrap —— 2026-09-16 申请人批准的三项补充分析之一/二。

支持两种模式（audit §3.2⑥：敏感性族，非确认集主跑，不影响门 v2 判定）：

  points     从既有 run 目录的 curve_summary.csv 在指定判据（如 0.7）下重算
             ε*（线性插值，与引擎同一 eps_star 实现），并给出主对照
             Δε* = ε*(min_rules) − ε*(retry_oracle)（pooled = 三层等权平均，
             200/200/200 等额分配下与链级 pooled 精确一致；脚本内 assert 校验）。
             不重跑引擎、不触碰任何既有文件。

  bootstrap  从既有 run 目录的 per_run_results.csv 做链级 bootstrap（重抽样单位=链，
             B 默认 9999），在指定判据下给 Δε* 点估计 + 95% 百分位 CI + bootstrap
             镜像 p。插值函数 import 自 run_four_arm_experiment（与引擎/门 v2 分析
             同一实现，杜绝口径分叉——audit §3.2 实现条款）。

CI 口径与 scripts/bootstrap_eps_star.py（门 v2 分析实现）逐字段一致：
  lo = sorted[max(0, int(0.025*n))]，hi = sorted[min(n-1, int(0.975*n)+1)]，
  p = 2·min(F̂(0), 1−F̂(0))（cap 1）。numpy 仅用于加速聚合，随机数由
  numpy.random.Generator(PCG64, seed) 产生，种子显式落盘。

申报：本脚本全部产出属敏感性族——0.7 判据为既有确认集输出的重算（新分析种子只用于
bootstrap 重抽样），k ∈ {1,3} 为引擎重跑（种子 20261017）。两者均不是确认集主跑
（种子 20261015，run-once 已封存），不进入、不影响门 v2 判定。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "evidence" / "videocad" / "scripts"))
from run_four_arm_experiment import eps_star  # noqa: E402  （与引擎同一插值实现）

MAIN_PAIR = ("min_rules", "retry_oracle")
STRATA = ("low", "medium", "high")
ARMS = ("no_rules", "retry_selfreport", "retry_oracle", "min_rules")
B_DEFAULT = 9999
SEED_DEFAULT = 20261018  # 敏感性族 bootstrap 种子（与 20260915 门 v2 种子、20261015 主跑、20261016 消融、20261017 k 重跑均不同）


def load_curve_summary(path: Path):
    """curve_summary.csv → {(arm, stratum): [(eps, rate), ...]}，并校验层间 n_runs 相等。"""
    rows = list(csv.DictReader(path.open("r", encoding="utf-8")))
    n_by = {}
    curves: dict[tuple[str, str], list[tuple[float, float]]] = {}
    for r in rows:
        key = (r["arm"], r["complexity_label"])
        curves.setdefault(key, []).append((float(r["epsilon"]), float(r["success_rate"])))
        n_by.setdefault(key, set()).add(int(r["n_runs"]))
    for key, ns in n_by.items():
        assert len(ns) == 1, f"stratum n_runs unequal for {key}: {ns}"
    base = {n for (a, _), ns in n_by.items() if a == ARMS[0] for n in ns}
    for a in ARMS:
        for s in STRATA:
            assert n_by[(a, s)] == base, f"cross-arm n_runs mismatch at {(a, s)}"
    for k in curves:
        curves[k].sort()
    return curves, base.pop()


def pooled_curve(curves, arm, strata=STRATA):
    """pooled 曲线 = 三层 success_rate 等权平均（等额分配下 = 链级 pooled）。"""
    eps_vals = [e for e, _ in curves[(arm, STRATA[0])]]
    out = []
    for e in eps_vals:
        rates = [dict(curves[(arm, s)])[e] for s in strata]
        out.append((e, sum(rates) / len(rates)))
    return out


def mode_points(args):
    pair = tuple(args.pair.split(","))
    out_rows = []
    for cs_path in args.curve_summary:
        cell = cs_path.parent.name
        curves, n_runs = load_curve_summary(cs_path)
        eps_vals = [e for e, _ in curves[(ARMS[0], STRATA[0])]]
        # assert: pooled（链级）= 三层平均 —— 由等额分配保证（n_runs_per_stratum 相等已 assert）
        for arm in ARMS:
            curves[(arm, "pooled")] = pooled_curve(curves, arm)
        for arm in ARMS:
            for s in STRATA + ("pooled",):
                val, flag = eps_star(curves[(arm, s)], args.criterion)
                out_rows.append({"cell": cell, "arm": arm, "stratum_set": s,
                                 "n_runs_per_stratum": n_runs,
                                 "criterion": args.criterion,
                                 "epsilon_star": round(val, 6) if val is not None else "",
                                 "censor_flag": flag})
        for s in STRATA + ("pooled",):
            va, fa = eps_star(curves[(pair[0], s)], args.criterion)
            vb, fb = eps_star(curves[(pair[1], s)], args.criterion)
            flag = "ok" if (fa == "ok" and fb == "ok") else f"{pair[0]}:{fa};{pair[1]}:{fb}"
            out_rows.append({"cell": cell, "arm": f"DELTA_{pair[0]}-minus-{pair[1]}",
                             "stratum_set": s, "n_runs_per_stratum": n_runs,
                             "criterion": args.criterion,
                             "epsilon_star": round(va - vb, 6) if (va is not None and vb is not None) else "",
                             "censor_flag": flag})
    out_path = args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader(); w.writerows(out_rows)
    print(f"Wrote: {out_path}  ({len(out_rows)} rows; criterion={args.criterion})")


def load_per_run(run_dir: Path):
    """per_run_results.csv → (chain_ids, strata_map, {arm: counts[n_chain, n_eps]}, eps_vals, m_reps)。"""
    import pandas as pd
    df = pd.read_csv(run_dir / "per_run_results.csv",
                     usecols=["sample_id", "complexity_label", "arm", "epsilon", "replicate", "success"])
    chain_ids = sorted(df["sample_id"].unique())
    cid = {c: i for i, c in enumerate(chain_ids)}
    strata_map = df.drop_duplicates("sample_id").set_index("sample_id")["complexity_label"].to_dict()
    eps_vals = sorted(df["epsilon"].unique())
    eidx = {e: i for i, e in enumerate(eps_vals)}
    reps = sorted(df["replicate"].unique())
    m = len(reps)
    counts = {}
    for arm in ARMS:
        sub = df[df["arm"] == arm]
        mat = np.zeros((len(chain_ids), len(eps_vals)), dtype=np.int64)
        ci = sub["sample_id"].map(cid).to_numpy()
        ei = sub["epsilon"].map(eidx).to_numpy()
        np.add.at(mat, (ci, ei), sub["success"].to_numpy(dtype=np.int64))
        counts[arm] = mat
    assert m == 20, f"unexpected replicate count {m}"
    return chain_ids, strata_map, counts, eps_vals, m


def cell_delta_bootstrap(counts, chain_idx, pair, criterion, eps_vals, m, b, rng):
    """一个格子的 Δε* bootstrap：返回 (point, deltas, n_undefined)。"""
    curves = {}
    for arm in pair:
        c = counts[arm][chain_idx]
        rates = c.sum(axis=0) / (len(chain_idx) * m)
        curves[arm] = list(zip(eps_vals, rates.tolist()))
    point_vals = {}
    for arm in pair:
        v, _ = eps_star(curves[arm], criterion)
        point_vals[arm] = v
    point = None if any(v is None for v in point_vals.values()) else point_vals[pair[0]] - point_vals[pair[1]]
    n = len(chain_idx)
    deltas = []
    n_undef = 0
    c0, c1 = counts[pair[0]], counts[pair[1]]
    for _ in range(b):
        idx = rng.integers(0, n, n)
        v0, _ = eps_star(list(zip(eps_vals, (c0[chain_idx][idx].sum(axis=0) / (n * m)).tolist())), criterion)
        v1, _ = eps_star(list(zip(eps_vals, (c1[chain_idx][idx].sum(axis=0) / (n * m)).tolist())), criterion)
        if v0 is None or v1 is None:
            n_undef += 1
        else:
            deltas.append(v0 - v1)
    return point, deltas, n_undef


def mode_bootstrap(args):
    pair = tuple(args.pair.split(","))
    rng = np.random.default_rng(args.seed)
    out_rows = []
    reps_out: dict[str, list] = {}
    for run_dir in args.runs:
        cell = run_dir.name
        chain_ids, strata_map, counts, eps_vals, m = load_per_run(run_dir)
        sets = {"pooled": np.arange(len(chain_ids))}
        for s in STRATA:
            sets[s] = np.array([i for i, c in enumerate(chain_ids) if strata_map[c] == s])
        for set_name, idx in sets.items():
            point, deltas, n_undef = cell_delta_bootstrap(counts, idx, pair, args.criterion,
                                                          eps_vals, m, args.b, rng)
            nd = len(deltas)
            if nd == 0:
                lo = hi = p = ""
            else:
                sd = sorted(deltas)
                lo = round(sd[max(0, int(0.025 * nd))], 6)
                hi = round(sd[min(nd - 1, int(0.975 * nd) + 1)], 6)
                p = round(min(1.0, 2.0 * min(sum(1 for d in deltas if d <= 0) / nd,
                                             sum(1 for d in deltas if d >= 0) / nd)), 6)
            out_rows.append({
                "cell": cell, "pair": f"{pair[0]}-{pair[1]}", "stratum_set": set_name,
                "n_chains": int(len(idx)), "criterion": args.criterion,
                "B_requested": args.b, "B_defined": nd,
                "pct_undefined": round(n_undef / args.b, 4),
                "delta_eps_star_point": round(point, 6) if point is not None else "",
                "ci_lo": lo, "ci_hi": hi, "p_boot": p, "p_floor": f"2/{args.b}",
                "bootstrap_seed": args.seed,
                "family": args.family,
            })
            reps_out[f"{cell}|{set_name}"] = deltas
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader(); w.writerows(out_rows)
    rep_path = args.out.with_name(args.out.stem + "_replicates.csv")
    with rep_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["replicate"] + list(reps_out))
        bmax = max((len(v) for v in reps_out.values()), default=0)
        for i in range(bmax):
            w.writerow([i] + [v[i] if i < len(v) else "" for v in reps_out.values()])
    print(f"Wrote: {args.out}  ({len(out_rows)} cells; B={args.b}, seed={args.seed}, criterion={args.criterion})")
    print(f"Wrote: {rep_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Sensitivity-family Δε* recompute + chain-level bootstrap (audit §3.2⑥)")
    sub = ap.add_subparsers(dest="mode", required=True)

    p1 = sub.add_parser("points", help="recompute ε* and Δε* at a given criterion from curve_summary.csv")
    p1.add_argument("--curve-summary", type=Path, nargs="+", required=True)
    p1.add_argument("--criterion", type=float, required=True)
    p1.add_argument("--pair", type=str, default=",".join(MAIN_PAIR))
    p1.add_argument("--out", type=Path, required=True)

    p2 = sub.add_parser("bootstrap", help="chain-level bootstrap of Δε* from per_run_results.csv")
    p2.add_argument("--runs", type=Path, nargs="+", required=True)
    p2.add_argument("--criterion", type=float, required=True)
    p2.add_argument("--pair", type=str, default=",".join(MAIN_PAIR))
    p2.add_argument("--b", type=int, default=B_DEFAULT)
    p2.add_argument("--seed", type=int, default=SEED_DEFAULT)
    p2.add_argument("--family", type=str, required=True,
                    help="申报标签，如 sensitivity-criterion07 / sensitivity-k（非确认集主跑）")
    p2.add_argument("--out", type=Path, required=True)

    args = ap.parse_args()
    if args.mode == "points":
        mode_points(args)
    else:
        mode_bootstrap(args)


if __name__ == "__main__":
    main()

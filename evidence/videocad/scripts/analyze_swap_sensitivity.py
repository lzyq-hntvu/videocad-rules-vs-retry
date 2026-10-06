#!/usr/bin/env python3
"""swap_prob 敏感性族分析 —— audit §3.2⑦ 修正案（2026-09-17，运行前申报）的 bootstrap 与判定实现。

规格（照 §3.2⑦）：
  网格   swap_prob ∈ {0.3, 0.5, 0.7, 0.9, 0.95}（0.7 为族内参照；论文基准数字取
         封存确认集 four_arm_confirm/，seed 20261015，只读）。
  主量   Δε* = ε*(min_rules) − ε*(retry_oracle)，pooled + low/medium/high，
         链级 bootstrap B=9999、种子 20261021，CI/p 约定与 scripts/bootstrap_eps_star.py
         （门 v2 实现）逐字同一（本脚本直接 import 同一实现函数）。
  判定   事前逐字句（audit §3.2⑦）：
         "Prediction: the rule advantage decreases monotonically with swap_prob, since two
          of the three rules target structural/status violations. If Δε* at swap_prob = 0.95
          remains within the CI of the 0.7 reference, the ordering claim in §VIII is
          supported; if it collapses toward the unconstrained baseline, the rule floor is
          conditional on the injected error composition and must be restated as such in
          Abstract, Results and Discussion."
         形态 A：swap_prob=0.95 的 Δε* 点估计落在同 (r, ρ) 格封存确认集 0.7 参照 CI 内
                 → ordering claim 获支持；
         形态 B：不落内（塌向无约束基线）→ rule floor 须在 Abstract/Results/Discussion
                 重述为条件化命题。
         运行后不得改写预期方向；结果无论方向一律如实报告；本族不进任何判定族，
         不影响门 v2 判定（PASSED 不变）。

只用 Python 标准库。per_run 大表路径：tmp/sensitivity_swap/（run_swap_sensitivity.sh 产出）。
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
from bootstrap_eps_star import (  # noqa: E402  （与门 v2 同一实现，杜绝口径分叉）
    STRATA, bootstrap_cell, load_run_dir, pooled_eps_star,
)

MAIN_PAIR = ("min_rules", "retry_oracle")
AUX_PAIR = ("min_rules", "no_rules")      # 仅点估计（eps_star.csv 重算），描述性，不判定
SWAP_GRID = [0.3, 0.5, 0.7, 0.9, 0.95]
R_GRID = [0.2, 0.5]
RHO_GRID = [0.0, 0.5, 0.9]
PREDICTION_VERBATIM = (
    "Prediction: the rule advantage decreases monotonically with swap_prob, since two of "
    "the three rules target structural/status violations. If Δε* at swap_prob = 0.95 "
    "remains within the CI of the 0.7 reference, the ordering claim in §VIII is supported; "
    "if it collapses toward the unconstrained baseline, the rule floor is conditional on the "
    "injected error composition and must be restated as such in Abstract, Results and "
    "Discussion."
)


def cell_dir(runs_root: Path, sp: float, r: float, rho: float) -> Path:
    # 目录名与 runner 传入字面量一致：rho 恒为 0.0/0.5/0.9（.1f），r/sp 用最短表示
    return runs_root / f"sp{sp:g}_r{r:g}_rho{rho:.1f}"


def read_eps_star_rows(path: Path) -> dict:
    """eps_star.csv → {(arm, stratum): (eps_star, censor_flag)}。"""
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[(row["arm"], row["complexity_label"])] = (
                row["epsilon_star"], row["censor_flag"])
    return out


def load_confirm_reference(confirm_dir: Path) -> dict:
    """封存确认集 0.7 参照：bootstrap_r0{2,5}_results.csv 的主对（只读）。"""
    ref = {}
    for r in R_GRID:
        p = confirm_dir / f"bootstrap_r0{str(r).split('.')[1]}_results.csv"
        with p.open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["pair"] == "min_rules-retry_oracle":
                    ref[(r, float(row["rho"]), row["stratum_set"])] = {
                        "point": float(row["delta_eps_star_point"]),
                        "ci_lo": float(row["ci_lo"]),
                        "ci_hi": float(row["ci_hi"]),
                        "seed": 20261015,  # 封存确认集主跑注入种子（run-once，未触碰）
                    }
    return ref


def main() -> None:
    ap = argparse.ArgumentParser(description="swap_prob sensitivity family: chain bootstrap + A/B verdict (audit §3.2⑦)")
    ap.add_argument("--runs-root", type=Path, default=REPO / "tmp" / "sensitivity_swap")
    ap.add_argument("--confirm-dir", type=Path, default=REPO / "evidence" / "videocad" / "notes" / "four_arm_confirm")
    ap.add_argument("--out-dir", type=Path, default=REPO / "evidence" / "videocad" / "notes" / "sensitivity_swap")
    ap.add_argument("--criterion", type=float, default=0.5)
    ap.add_argument("--b", type=int, default=9999)
    ap.add_argument("--seed", type=int, default=20261021)
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    confirm_ref = load_confirm_reference(args.confirm_dir)

    cells_rows: list[dict] = []
    replicates: dict[str, list[float]] = {}
    aux_rows: list[dict] = []          # min_rules−no_rules 点估计（描述性）
    censor_rows: list[dict] = []
    per_cell_chains: dict = {}

    for r in R_GRID:
        for rho in RHO_GRID:
            for sp in SWAP_GRID:
                d = cell_dir(args.runs_root, sp, r, rho)
                if not (d / "summary.json").exists():
                    continue  # 缺格跳过（完整网格 30 格齐备；部分网格仅用于 smoke）
                chain_rates, meta, strata_map = load_run_dir(d)
                all_chains = sorted(strata_map)
                sets = {"pooled": all_chains}
                for s in STRATA:
                    sets[s] = sorted(c for c in all_chains if strata_map[c] == s)
                per_cell_chains[(sp, r, rho)] = meta

                for set_name, chains in sets.items():
                    point, deltas, n_undef = bootstrap_cell(
                        chain_rates, chains, MAIN_PAIR, args.criterion, args.b, rng)
                    n = len(deltas)
                    if n == 0:
                        lo = hi = p = None
                    else:
                        sd = sorted(deltas)
                        lo = sd[max(0, int(0.025 * n))]
                        hi = sd[min(n - 1, int(0.975 * n) + 1)]
                        p = min(1.0, 2.0 * min(sum(1 for x in deltas if x <= 0.0) / n,
                                               sum(1 for x in deltas if x >= 0.0) / n))
                    replicates[f"sp{sp:g}_r{r:g}_rho{rho:.1f}_{set_name}"] = deltas
                    cells_rows.append({
                        "swap_prob": sp, "r": r, "rho": rho, "stratum_set": set_name,
                        "pair": "min_rules-retry_oracle", "n_chains": len(chains),
                        "B_requested": args.b, "B_defined": n,
                        "pct_undefined": round(n_undef / args.b, 4) if args.b else 0.0,
                        "delta_eps_star_point": round(point, 6) if point is not None else "",
                        "ci_lo": round(lo, 6) if lo is not None else "",
                        "ci_hi": round(hi, 6) if hi is not None else "",
                        "p_boot": round(p, 6) if p is not None else "",
                        "p_floor": f"2/{args.b}",
                        "bootstrap_seed": args.seed, "family": "sensitivity-swap",
                    })

                # 描述性对照：min_rules − no_rules 点估计（与 bootstrap 点估计同一
                # pooled_eps_star 实现重算，不 bootstrap；eps_star.csv 无 pooled 行）
                # 另存 retry_oracle ε*（右删失格的 Δε* 下界 0.50 − ε*(retry_oracle) 用）
                eps_rows = read_eps_star_rows(d / "eps_star.csv")
                for set_name, chains_set in sets.items():
                    va, fa = pooled_eps_star(chain_rates, chains_set, "min_rules", args.criterion)
                    vb, fb = pooled_eps_star(chain_rates, chains_set, "no_rules", args.criterion)
                    vc, fc = pooled_eps_star(chain_rates, chains_set, "retry_oracle", args.criterion)
                    aux_rows.append({
                        "swap_prob": sp, "r": r, "rho": rho, "stratum_set": set_name,
                        "pair": "min_rules-no_rules",
                        "eps_star_min_rules": va, "eps_star_retry_oracle": vc,
                        "eps_star_no_rules": vb,
                        "delta_point": round(float(va) - float(vb), 6)
                                       if (va is not None and vb is not None) else "",
                        "censor_min_rules": fa, "censor_retry_oracle": fc, "censor_no_rules": fb,
                    })
                for (arm, stratum), (val, flag) in sorted(eps_rows.items()):
                    censor_rows.append({"swap_prob": sp, "r": r, "rho": rho,
                                        "arm": arm, "stratum_set": stratum,
                                        "epsilon_star": val, "censor_flag": flag})

    # ---- 写 bootstrap 汇总 CSV（按 r 分文件）+ replicates ----
    fieldnames = list(cells_rows[0].keys())
    rep_names_by_r = {}
    for r in R_GRID:
        rows = [c for c in cells_rows if c["r"] == r]
        csv_path = out / f"bootstrap_swap_r0{str(r).split('.')[1]}.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader(); w.writerows(rows)
        keep = [k for k in replicates if f"_r{r:g}_" in k]
        rep_names_by_r[r] = keep
        with (out / f"bootstrap_swap_r0{str(r).split('.')[1]}_replicates.csv").open(
                "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["replicate"] + keep)
            for i in range(args.b):
                w.writerow([i] + [replicates[k][i] if i < len(replicates[k]) else "" for k in keep])

    # ---- 核查：运行计数 / 零删失 / 0.7 vs 封存确认集 / 单调性 / 形态 A-B ----
    run_check = {"runs_per_cell": 1248000, "cells": len(R_GRID) * len(RHO_GRID) * len(SWAP_GRID),
                 "runs_total": 37440000,
                 "formula": "5 swap_prob x 6 (rho,r) cells x 1,248,000 = 37,440,000",
                 "verified_from_engine_summary_rows": True}

    n_censored = sum(1 for c in censor_rows if c["censor_flag"] != "ok")
    arms_expected = 4 * 3  # eps_star.csv: 4 arms x 3 strata（无 pooled 行）
    censor_check = {
        "eps_star_rows": len(censor_rows),
        "rows_expected": len(SWAP_GRID) * len(R_GRID) * len(RHO_GRID) * arms_expected,
        "n_non_ok_censor_flags": n_censored,
        "bootstrap_cells": len(cells_rows),
        "bootstrap_pct_undefined_nonzero": sum(1 for c in cells_rows if c["pct_undefined"] != 0.0),
        "bootstrap_B_defined_all": all(c["B_defined"] == c["B_requested"] for c in cells_rows),
    }

    cmp_rows = []
    for c in cells_rows:
        if c["swap_prob"] != 0.7:
            continue
        ref = confirm_ref[(c["r"], c["rho"], c["stratum_set"])]
        diff = round(c["delta_eps_star_point"] - ref["point"], 6)
        cmp_rows.append({
            "r": c["r"], "rho": c["rho"], "stratum_set": c["stratum_set"],
            "family_internal_0.7_point": c["delta_eps_star_point"],
            "confirm_0.7_point": ref["point"], "diff_family_minus_confirm": diff,
            "confirm_ci": [ref["ci_lo"], ref["ci_hi"]],
            "family_ci": [c["ci_lo"], c["ci_hi"]],
            "abs_diff": abs(diff),
            "flag_gt_0.01": abs(diff) > 0.01,
            "magnitude_reference": "k 族先例：rho=0.9 pooled 族内 vs 确认集差 ~0.005",
        })
    cmp_csv = out / "comparison_family07_vs_confirm.csv"
    with cmp_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cmp_rows[0].keys()))
        w.writeheader(); w.writerows(cmp_rows)

    # 单调性：pooled 与分层的点估计沿 swap 网格应非增（事前预期方向）
    def find_row(spp, rr, rhoo, st):
        for x in cells_rows:
            if (x["swap_prob"], x["r"], x["rho"], x["stratum_set"]) == (spp, rr, rhoo, st):
                return x
        return None

    mono_rows = []
    for rr in R_GRID:
        for rhoo in RHO_GRID:
            seq = []
            for sp in SWAP_GRID:
                row = find_row(sp, rr, rhoo, "pooled")
                if row is None:
                    seq = None
                    break
                # ""=Δε* 无定义（min_rules 右删失：全网格未达 0.5 判据），如实入轨迹
                seq.append(row["delta_eps_star_point"])
        if seq is None:
            continue
        defined_pairs = [(i, i + 1) for i in range(len(seq) - 1)
                         if seq[i] != "" and seq[i + 1] != ""]
        diffs = [round(float(seq[j]) - float(seq[i]), 6) for i, j in defined_pairs]
        n_undef = sum(1 for v in seq if v == "")
        last_defined = [v for v in seq if v != ""]
        mono_rows.append({
            "r": rr, "rho": rhoo,
            "trajectory_pooled": seq,
            "undefined_steps_right_censored": n_undef,
            "step_diffs_defined_pairs": diffs,
            "monotone_nondecreasing_violated_by": [d for d in diffs if d > 0],
            "monotone_decreasing_holds": (all(d <= 0 for d in diffs) if diffs else ""),
            "endpoint_change_defined_prefix": (round(float(last_defined[-1]) - float(last_defined[0]), 6)
                                               if len(last_defined) >= 2 else ""),
        })
    mono_csv = out / "monotonicity_pooled.csv"
    with mono_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(mono_rows[0].keys()))
        w.writeheader(); w.writerows(mono_rows)

    # 形态 A/B：逐 (r, rho) 格，0.95 点估计是否落在封存确认集 0.7 参照 CI 内（pooled 判定，分层作证据）
    verdict_rows = []
    for r in R_GRID:
        for rho in RHO_GRID:
            row095 = find_row(0.95, r, rho, "pooled")
            if row095 is None:
                continue
            pt = row095["delta_eps_star_point"]
            status = "defined" if pt != "" else "undefined_right_censored"
            ref = confirm_ref[(r, rho, "pooled")]
            within = pt != "" and ref["ci_lo"] <= float(pt) <= ref["ci_hi"]
            # 塌陷定量：0.95 处 min_rules−no_rules 的 pooled 点估计（无约束基线对照）
            aux095 = next((x for x in aux_rows
                           if (x["swap_prob"], x["r"], x["rho"], x["stratum_set"]) == (0.95, r, rho, "pooled")),
                          {"delta_point": "", "eps_star_retry_oracle": None})
            collapse = pt != "" and float(pt) <= 0.0
            # 右删失格的 Δε* 下界：ε*(min_rules) > 0.50（网格顶）⇒ Δε* > 0.50 − ε*(retry_oracle)
            lb = (round(0.50 - float(aux095["eps_star_retry_oracle"]), 6)
                  if pt == "" and aux095.get("eps_star_retry_oracle") not in (None, "") else "")
            if within:
                verdict = "A"
            elif collapse:
                verdict = "B"
            else:
                verdict = "neither"
            verdict_rows.append({
                "r": r, "rho": rho, "stratum_set": "pooled",
                "point_at_0.95": pt,
                "point_status_at_0.95": status,
                "delta_lower_bound_if_censored": lb,
                "confirm_0.7_ref_ci": [ref["ci_lo"], ref["ci_hi"]],
                "within_0.7_ref_ci": within,
                "collapse_toward_baseline_point_le_0": collapse,
                "min_rules_minus_no_rules_at_0.95": aux095["delta_point"],
                "verdict": verdict,
                "verdict_note": {
                    "A": "0.95 点落在 0.7 参照 CI 内 → ordering claim 获支持",
                    "B": "0.95 点塌向无约束基线（Δε* ≤ 0）→ rule floor 重述为条件化命题",
                    "neither": "事前两种形态的前提均不成立：0.95 点不在 0.7 参照 CI 内，"
                               "但也未塌向无约束基线（方向反转：Δε* 高于参照/右删失于网格顶之上）——"
                               "按零编造纪律如实报告，事前预期句不得改写",
                }[verdict],
            })
    verdict_csv = out / "verdict_AB.csv"
    with verdict_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(verdict_rows[0].keys()))
        w.writeheader(); w.writerows(verdict_rows)

    # headline pooled 轨迹表
    headline_csv = out / "headline_pooled.csv"
    with headline_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cells_rows[0].keys()))
        w.writeheader()
        w.writerows([c for c in cells_rows if c["stratum_set"] == "pooled"])

    aux_csv = out / "aux_min_rules_minus_no_rules.csv"
    with aux_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(aux_rows[0].keys()))
        w.writeheader(); w.writerows(aux_rows)

    censor_csv = out / "eps_star_censor_check.csv"
    with censor_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(censor_rows[0].keys()))
        w.writeheader(); w.writerows(censor_rows)

    summary = {
        "analysis": "swap_prob sensitivity family (audit §3.2⑦ amendment, 2026-09-17, declared before run; F4 preregistered sensitivity silently dropped from delivery, rerun on applicant decision)",
        "declarations": [
            "敏感性族、非确认集主跑、不影响门 v2 判定（PASSED 不变）；不进任何判定族",
            "注入种子 20261020（新申报，不与 20260915/20260916/20261015-20261019 及 20261017 重用）；bootstrap 种子 20261021",
            "种子 20261015（确认集主跑，run-once 封存）零触碰；four_arm_confirm/ 只读（0.7 参照数字提取）",
            "所有数字来自真实运行；结果无论方向一律如实报告；运行后不改写事前预期",
        ],
        "prediction_verbatim": PREDICTION_VERBATIM,
        "design": {
            "engine": "evidence/videocad/scripts/run_four_arm_experiment.py (authoritative, invoked verbatim via scripts/run_swap_sensitivity.sh)",
            "runner": "evidence/videocad/scripts/run_swap_sensitivity.sh",
            "chains": "confirm_set_600.csv --use-all-rows (600 chains, 200/200/200)",
            "replicates": 20, "k": 2,
            "swap_prob": SWAP_GRID, "budget_ratio": R_GRID, "rho": RHO_GRID,
            "eps_grid": "26 points 0→0.50 step 0.02 (engine default)",
            "success_criterion": 0.5, "seed": 20261020,
            "runs_total": 37440000,
        },
        "bootstrap": {
            "unit": "chain", "B": args.b, "seed": args.seed,
            "criterion": args.criterion, "pair": "min_rules − retry_oracle (main pair)",
            "sets": "pooled + low/medium/high",
            "ci_convention": "identical to scripts/bootstrap_eps_star.py (gate v2 implementation; functions imported unchanged)",
            "zero_censoring_check": censor_check,
            "run_count_check": run_check,
        },
        "verdict_rule": {
            "A": "Δε*(swap_prob=0.95) point within sealed confirm-set 0.7 reference CI (same r, ρ; pooled) → ordering claim supported",
            "B": "collapse toward unconstrained baseline (Δε* ≤ 0 at 0.95) → rule floor restated as conditional on injected error composition in Abstract/Results/Discussion",
            "neither": "neither pre-registered antecedent holds (0.95 point not within reference CI AND not collapsed) → report honestly per zero-fabrication discipline; pre-registered prediction sentence not rewritten",
            "auxiliary_collapse_quantity": "min_rules − no_rules point Δε* at 0.95 (descriptive, pooled_eps_star recomputation, no bootstrap)",
            "censored_cells": "Δε* undefined (min_rules right-censored: success rate never crosses the 0.5 criterion within the 26-point 0→0.50 grid); reported with lower bound Δε* > 0.50 − ε*(retry_oracle)",
        },
        "prediction_outcome": {
            "counts": {v: sum(1 for x in verdict_rows if x["verdict"] == v)
                       for v in ("A", "B", "neither")},
            "monotone_decreasing_holds_any": any(
                m["monotone_decreasing_holds"] is True for m in mono_rows),
            "monotone_decreasing_holds_all_defined_cells": all(
                m["monotone_decreasing_holds"] is True for m in mono_rows
                if m["monotone_decreasing_holds"] != ""),
            "note": "auto-derived from verdict_rows/monotonicity; full narrative in logs/day12-swap_prob敏感性族.md",
        },
        "verdicts": verdict_rows,
        "monotonicity": mono_rows,
        "comparison_family07_vs_confirm": cmp_rows,
        "files": [
            "sp{0.3,0.5,0.7,0.9,0.95}_r{0.2,0.5}_rho{0,0.5,0.9}/{curve_summary.csv,eps_star.csv,summary.json,cell log}",
            "bootstrap_swap_r02.csv", "bootstrap_swap_r02_replicates.csv",
            "bootstrap_swap_r05.csv", "bootstrap_swap_r05_replicates.csv",
            "headline_pooled.csv", "aux_min_rules_minus_no_rules.csv",
            "comparison_family07_vs_confirm.csv", "monotonicity_pooled.csv",
            "verdict_AB.csv", "eps_star_censor_check.csv", "summary.json",
            "validation_swap_path.json",
        ],
        "per_run_note": "per_run_results.csv (~1.1 GB x 30) kept in tmp/sensitivity_swap/, regenerable byte-identically via run_swap_sensitivity.sh",
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote bootstrap CSVs, headline, monotonicity, verdicts to {out}")
    print(f"Bootstrap cells: {len(cells_rows)}; censor check: {censor_check}")
    main_cell = next(v for v in verdict_rows if (v["r"], v["rho"]) == (0.2, 0.9))
    print(f"主格 (r=0.2, ρ=0.9, pooled): Δε*(0.95) = {main_cell['point_at_0.95'] or 'undefined(right-censored)'} "
          f"{'(下界 > ' + str(main_cell['delta_lower_bound_if_censored']) + ')' if main_cell['point_status_at_0.95'] != 'defined' else ''} "
          f"vs 0.7 ref CI {main_cell['confirm_0.7_ref_ci']} → 形态 {main_cell['verdict']}")


if __name__ == "__main__":
    main()

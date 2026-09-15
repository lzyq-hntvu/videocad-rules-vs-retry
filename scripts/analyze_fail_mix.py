#!/usr/bin/env python3
"""按 臂 × 复杂度层 × ε 分解失败原因占比（审计 C：budget_exhausted 单独量化）。

读 run_four_arm_experiment.py 的 per_run_results.csv，输出 fail_mix.csv：
每个 (arm, label, ε) 格的 n_fail 及各失败原因计数与占比
（budget_exhausted / step_abandoned / non_empty_stack_at_end / stack_underflow / finish_mismatch）。

注意：fail_reason 记录的是**首个**失败事件（步放弃后链继续，后续原因不计），
因此 non_empty_stack_at_end 会被先行发生的 step_abandoned 遮蔽而低估；对
budget_exhausted（终止性）无影响——它正是本表要单独回答的量。
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

REASONS = ("budget_exhausted", "step_abandoned", "non_empty_stack_at_end",
           "stack_underflow", "finish_mismatch", "unexpected_stack_underflow",
           "unexpected_finish_mismatch")


def main() -> None:
    ap = argparse.ArgumentParser(description="Fail-reason mix per arm x label x epsilon")
    ap.add_argument("per_run_csv", type=Path)
    ap.add_argument("--out", type=Path, required=True, help="输出 fail_mix.csv 路径")
    args = ap.parse_args()

    acc: dict[tuple[str, str, float], defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    totals: dict[tuple[str, str, float], int] = defaultdict(int)
    with args.per_run_csv.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r["arm"], r["complexity_label"], float(r["epsilon"]))
            totals[key] += 1
            acc[key]["success" if r["success"] == "1" else (r["fail_reason"] or "unknown")] += 1

    rows = []
    for key in sorted(totals, key=lambda k: (k[0], k[1], k[2])):
        arm, label, eps = key
        n = totals[key]
        reasons = acc[key]
        n_fail = n - reasons["success"]
        row: dict[str, object] = {
            "arm": arm, "complexity_label": label, "epsilon": eps, "n_runs": n,
            "success_rate": round(reasons["success"] / n, 6), "n_fail": n_fail,
        }
        for reason in REASONS:
            c = reasons[reason]
            row[f"n_{reason}"] = c
            row[f"share_{reason}"] = round(c / n_fail, 4) if n_fail else 0.0
        row["n_other"] = n_fail - sum(reasons[r] for r in REASONS)
        rows.append(row)

    fields = ["arm", "complexity_label", "epsilon", "n_runs", "success_rate", "n_fail"]
    for reason in REASONS:
        fields += [f"n_{reason}", f"share_{reason}"]
    fields.append("n_other")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote: {args.out} ({len(rows)} rows)")


if __name__ == "__main__":
    main()

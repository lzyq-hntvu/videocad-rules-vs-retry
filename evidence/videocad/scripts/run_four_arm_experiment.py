#!/usr/bin/env python3
"""Four-arm paired error-injection experiment on VideoCAD symbolic action chains.

对应实验方案 v1 步骤一 + 2026-09-15 二轮修正案（docs/audit-2026-09-15-data-lineage-and-rng.md §二轮）：

Arms（表 A，四臂——F5 决议 C）:
  no_rules         无任何约束，误差注入后直接执行（下界）
  retry_selfreport 环境判非法（栈下溢 / finish 失配，不读 gt）才重试该步，每步至多 k 次
  retry_oracle     任一步偏离预期状态转移（attempt != gt event）即重试，每步至多 k 次
  min_rules        栈一致性收束 + 非法关闭修正（沿用本子代理实验口径，含一处 gt 修复声明，
                   属 oracle 级信息——Section III 申报，与 retry_oracle 信息等级对齐）

关于已移除的第五臂（rules_retry）：min_rules 是全覆盖修复策略——检测到的每种违规都修，
执行按构造不抛错，叠加其上的重试层恒为惰性。已实证（39,600/39,600 runs 逐 run 相同）。
论文 Section III 方法句（预登记锁死）：
  "min_rules is a total repair policy: every violation it detects, it corrects, so
   execution never raises and a retry layer placed on top is inert by construction.
   We verified this empirically (39,600/39,600 runs identical) and therefore report
   four arms rather than five."

误差相关性 ρ（--retry-repro-prob，二轮修正案 F6）:
  真实 GUI 中重试大概率复现同一误差（感知器把按钮定位错，重跑同一步会再错），旧规格
  "fresh independent draw" 把重试设成了最有利形态（ρ=0：P(步失败)=ε^(k+1)，几何收敛，
  开发集实证 retry_oracle 以 ~0.3 优势碾压 min_rules——规格缺陷，非重试的真实强度）。
  ρ = 重试复现主尝试同一误差的概率：
    ρ=0   独立重抽——对应瞬时/执行类误差（时序、竞态、点击抖动），重跑同一步换新样本，
          是 GUI 自动化中真实存在的误差类（审计 §3.4：非稻草人）
    ρ→1   确定性复现——对应可重复误差（感知类：检测器把元素定位错，重跑同一步再错），
          重试完全无效
  论文主张定稿：规则对可重复误差有价值；对瞬时误差，重试已经足够。
  每次重试：从重试流抽 u_corr；u_corr < ρ → 复现主尝试的同一事件；否则独立重抽。
  论文 headline 由"规则赢/输"升级为"重试何时够用，取决于误差的可重复性 ρ"。

随机数纪律（F2）:
  - 初始误差向量按 (chain, rep) 由 sha256 确定性导出种子预生成为定长三元组数组，
    同一 (chain, rep) 下所有臂、所有 ε 档共用（corrupt 判定 u<ε，ε 不参与抽样；
    common random numbers，跨臂 + 跨 ε 双重配对）。
  - 重试独立流 sha256(seed,"retry",chain,rep,step,attempt)：先抽 ρ 相关判定，
    再（若独立重抽）抽三元组。与主向量完全隔离，无顺序推进母发生器。

成败定义（不含 gt，F3）:
  success = 全程无步放弃、无环境错误终止、结束时栈为空。
  旧管线 cumulative mismatch-rate 判定（所有臂共用、读 gt）已移出成败路径；
  mismatch 仅作分析统计输出。oracle 通道清单见 summary.json design_notes。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from run_h2_h3_mechanism_proxy import load_events, load_selected_chains

ARMS = ("no_rules", "retry_selfreport", "retry_oracle", "min_rules")
RETRY_ARMS = ("retry_selfreport", "retry_oracle")
VALID_STATUS = ("started", "finished")


def seed_from(*parts: object) -> int:
    """由任意字段确定性导出 64 位种子（sha256，无前向顺序依赖）。"""
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8"))
        h.update(b"|")
    return int.from_bytes(h.digest()[:8], "big")


def draw_triple(rng: random.Random) -> tuple[float, float, float]:
    return (rng.random(), rng.random(), rng.random())


def build_attempt(
    event: dict,
    alt_actions: tuple[str, ...],
    triple: tuple[float, float, float],
    epsilon: float,
    swap_prob: float,
) -> dict:
    """按预生成三元组构造一次尝试。corrupt iff u<ε；swap_prob 配比可 CLI 调（申报）。"""
    status, action = event["status"], event["action"]
    u, v, w = triple
    if u < epsilon:
        if v < swap_prob:
            if alt_actions:
                action = alt_actions[int(w * len(alt_actions)) % len(alt_actions)]
        else:
            status = "finished" if status == "started" else "started"
    return {"status": status, "action": action}


def is_mismatch(attempt: dict, gt_event: dict) -> bool:
    return attempt["status"] != gt_event["status"] or attempt["action"] != gt_event["action"]


def env_would_error(stack: list[str], attempt: dict) -> bool:
    """环境自检（self-report 信号，不读 gt）：started 恒合法；finish 需栈非空且栈顶匹配。"""
    if attempt["status"] == "started":
        return False
    if not stack:
        return True
    return stack[-1] != attempt["action"]


def execute_attempt(stack: list[str], attempt: dict) -> str | None:
    """执行已通过检定的尝试；返回环境错误码或 None。"""
    if attempt["status"] == "started":
        stack.append(attempt["action"])
        return None
    if not stack:
        return "stack_underflow"
    if stack[-1] != attempt["action"]:
        return "finish_mismatch"
    stack.pop()
    return None


def min_rules_repair(attempt: dict, gt_event: dict, stack: list[str]) -> int:
    """最小规则集（沿用旧管线口径）。返回修复次数。

    ⚠ 第一处修复读取 ground truth（oracle 级信息）：本误差模型下注入器只产出
    started/finished，该分支实为死代码，但按原口径保留并在论文 Section III 申报。
    第二、三处修复不读 gt。
    """
    repaired = 0
    if attempt["status"] not in VALID_STATUS:
        attempt["status"] = gt_event["status"]  # ← 唯一读 gt 的规则
        repaired += 1
    if attempt["status"] == "finished":
        if stack and stack[-1] == attempt["action"]:
            pass
        elif stack:
            attempt["action"] = stack[-1]  # 投影到栈顶（一致性收束，不读 gt）
            repaired += 1
        else:
            attempt["status"] = "started"  # 空栈非法关闭 → 转开启（不读 gt）
            repaired += 1
    return repaired


@dataclass
class ArmResult:
    success: bool
    fail_step_idx: int | None
    fail_reason: str | None
    mismatch_count: int
    repaired_events: int
    attempts_made: int
    abandoned: bool
    budget: int
    event_count: int


def run_arm(
    arm: str,
    events: list[dict],
    plan: list[tuple[float, float, float]],
    alt_lists: list[tuple[str, ...]],
    *,
    epsilon: float,
    k: int,
    budget: int,
    chain_id: str,
    rep: int,
    seed: int,
    swap_prob: float,
    retry_repro_prob: float,
) -> ArmResult:
    L = len(events)
    stack: list[str] = []
    mismatch = 0
    repaired = 0
    attempts = 0
    abandoned = False
    first_fail_idx: int | None = None
    first_fail_reason: str | None = None

    def terminal(idx: int, reason: str) -> ArmResult:
        return ArmResult(False, idx, reason, mismatch, repaired, attempts, abandoned, budget, L)

    for i in range(L):
        primary = build_attempt(events[i], alt_lists[i], plan[i], epsilon, swap_prob)

        if arm in ("no_rules", "min_rules"):
            if attempts >= budget:
                return terminal(i, "budget_exhausted")
            attempts += 1
            if arm == "min_rules":
                repaired += min_rules_repair(primary, events[i], stack)
            err = execute_attempt(stack, primary)
            if err:
                # min_rules 修复后按构造不会触发；保留防御分支
                return terminal(i, err if arm == "no_rules" else f"unexpected_{err}")
            mismatch += int(is_mismatch(primary, events[i]))
            continue

        # 重试臂：t=0 用共享初始向量，t>=1 走独立重试流（先抽 ρ 判定，再决定是否独立重抽）
        step_done = False
        for t in range(k + 1):
            if attempts >= budget:
                return terminal(i, "budget_exhausted")
            if t == 0:
                att = dict(primary)
            else:
                rng_r = random.Random(seed_from(seed, "retry", chain_id, rep, i, t))
                if rng_r.random() < retry_repro_prob:
                    att = dict(primary)  # ρ：复现同一误差
                else:
                    att = build_attempt(events[i], alt_lists[i], draw_triple(rng_r), epsilon, swap_prob)
            if arm == "retry_oracle":
                bad = is_mismatch(att, events[i])
            else:  # retry_selfreport：环境自检
                bad = env_would_error(stack, att)
            attempts += 1
            if not bad:
                err = execute_attempt(stack, att)
                if err:  # 防御：检定通过却执行报错
                    return terminal(i, f"unexpected_{err}")
                mismatch += int(is_mismatch(att, events[i]))
                step_done = True
                break
        if not step_done:
            abandoned = True
            if first_fail_idx is None:
                first_fail_idx, first_fail_reason = i, "step_abandoned"
            # 步放弃：不施加该步，继续向下走（方案表 B）
            continue

    if stack:
        idx = L - 1
        if first_fail_idx is None:
            first_fail_idx, first_fail_reason = idx, "non_empty_stack_at_end"
        return ArmResult(False, first_fail_idx, first_fail_reason, mismatch, repaired, attempts, abandoned, budget, L)
    if abandoned:
        return ArmResult(False, first_fail_idx, first_fail_reason, mismatch, repaired, attempts, abandoned, budget, L)
    return ArmResult(True, None, None, mismatch, repaired, attempts, abandoned, budget, L)


def eps_star(curve: list[tuple[float, float]], criterion: float) -> tuple[float | None, str]:
    """线性插值求 ε*。返回 (值, 审查标记)。

    标记: ok / left_censored(最左格点已低于判据) / right_censored(全程未达判据)。
    """
    prev_eps, prev_rate = None, None
    for eps, rate in sorted(curve):
        if rate < criterion:
            if prev_eps is None:
                return float(eps), "left_censored"
            if prev_rate is None or prev_rate == rate:
                return float(eps), "ok"
            w = (prev_rate - criterion) / (prev_rate - rate)
            return prev_eps + w * (eps - prev_eps), "ok"
        prev_eps, prev_rate = eps, rate
    return None, "right_censored"


def maybe_plot(curve_rows: list[dict], out_dir: Path, rho: float) -> list[str]:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return []
    out_files: list[str] = []
    labels = ["low", "medium", "high"]
    colors = {"no_rules": "#888888", "retry_selfreport": "#f4a261",
              "retry_oracle": "#e63946", "min_rules": "#2a9d8f"}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
    for ax, label in zip(axes, labels):
        for arm in ARMS:
            rows = sorted((r for r in curve_rows if r["arm"] == arm and r["complexity_label"] == label),
                          key=lambda r: float(r["epsilon"]))
            ax.plot([float(r["epsilon"]) for r in rows], [float(r["success_rate"]) for r in rows],
                    marker="o", label=arm, color=colors[arm])
        ax.axhline(0.5, color="k", ls="--", lw=1)
        ax.set_title(f"{label}")
        ax.set_xlabel("epsilon")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("success rate")
    axes[2].legend(fontsize=8)
    fig.suptitle(f"rho = {rho}")
    fig.tight_layout()
    p = out_dir / f"four_arm_success_rate_vs_epsilon_rho{rho}.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    out_files.append(str(p))
    return out_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Four-arm paired error-injection experiment (rules vs retry, with rho)")
    parser.add_argument("--samples-csv", type=Path,
                        default=Path("evidence/videocad/notes/cad_action_multimodal_samples.csv"))
    parser.add_argument("--per-label", type=int, default=30,
                        help="每复杂度层取前 N 链（开发集口径）；与 --use-all-rows 互斥")
    parser.add_argument("--use-all-rows", action="store_true",
                        help="使用 CSV 全部行（确认集口径：CSV 即样本清单）")
    parser.add_argument("--replicates", type=int, default=20)
    parser.add_argument("--eps-list", type=str,
                        default=",".join(f"{i*0.02:.2f}" for i in range(26)),
                        help="逗号分隔的 ε 网格（默认 26 档 0→0.50；跨档共享同一组注入随机数。"
                             "⚠ 不要缩小：0.20 上限会使 min_rules 在 low/medium 层右删失，"
                             "Δε* 无法计算——审计 §3.1")
    parser.add_argument("--k", type=int, default=2, help="单步重试上限（超出即放弃该步）")
    parser.add_argument("--budget-ratio", type=float, default=0.2, help="预算 B = ceil(L*(1+r)) 的 r")
    parser.add_argument("--swap-prob", type=float, default=0.7, help="误差注入动作替换配比（其余为状态翻转）")
    parser.add_argument("--retry-repro-prob", type=float, default=0.0,
                        help="ρ：重试复现主尝试同一误差的概率（0=独立重抽，对重试最有利；1=重试无效）")
    parser.add_argument("--seed", type=int, default=20260226)
    parser.add_argument("--success-criterion", type=float, default=0.5, help="ε* 主判据（0.7 作敏感性分析）")
    parser.add_argument("--arms", type=str, default=",".join(ARMS))
    parser.add_argument("--out-dir", type=Path, default=Path("tmp/four_arm_experiment"))
    args = parser.parse_args()

    eps_values = sorted({float(x) for x in args.eps_list.split(",")})
    arms = tuple(a.strip() for a in args.arms.split(",") if a.strip())
    for a in arms:
        if a not in ARMS:
            raise ValueError(f"unknown arm: {a}")

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.use_all_rows:
        # plumbing 修正（2026-09-16）："use all rows" 不再按 sample_group 过滤——
        # 确认集清单的 sample_group 为 confirm_set_600，过滤会导致零行静默崩溃。
        # 仅要求复杂度标签与动作链路径存在；对开发集 CSV（全为 random_stratified_overlap）行为不变。
        rows = []
        with args.samples_csv.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("complexity_label") and row.get("action_json_path"):
                    rows.append(row)
    else:
        rows = load_selected_chains(args.samples_csv, args.per_label)

    chains = []
    global_vocab: set[str] = set()
    for row in rows:
        events = load_events(Path(row["action_json_path"]))
        global_vocab.update(e["action"] for e in events)
        chains.append({"sample_id": row["sample_id"], "complexity_label": row["complexity_label"],
                       "events": events})
    vocab_sorted = sorted(global_vocab)

    plans: dict[tuple[str, int], list[tuple[float, float, float]]] = {}
    alt_cache: dict[str, list[tuple[str, ...]]] = {}
    for chain in chains:
        sid = chain["sample_id"]
        alt_cache[sid] = tuple(
            tuple(a for a in vocab_sorted if a != ev["action"]) for ev in chain["events"]
        )
        for rep in range(args.replicates):
            rng = random.Random(seed_from(args.seed, "inj", sid, rep))
            plans[(sid, rep)] = [draw_triple(rng) for _ in chain["events"]]

    curve_acc = defaultdict(lambda: {"n": 0, "success": 0, "fail_ratio_sum": 0.0, "mismatch_sum": 0.0,
                                     "repaired_sum": 0, "attempts_sum": 0, "abandoned": 0})
    per_run_rows = []
    reason_counter: Counter = Counter()

    for epsilon in eps_values:
        for chain in chains:
            sid = chain["sample_id"]
            label = chain["complexity_label"]
            L = len(chain["events"])
            budget = math.ceil(L * (1 + args.budget_ratio))
            for rep in range(args.replicates):
                plan = plans[(sid, rep)]
                for arm in arms:
                    r = run_arm(arm, chain["events"], plan, alt_cache[sid], epsilon=epsilon,
                                k=args.k, budget=budget, chain_id=sid, rep=rep,
                                seed=args.seed, swap_prob=args.swap_prob,
                                retry_repro_prob=args.retry_repro_prob)
                    fail_idx = r.fail_step_idx if r.fail_step_idx is not None else L - 1
                    fail_ratio = (fail_idx + 1) / L if L else 0.0
                    key = (arm, label, epsilon)
                    acc = curve_acc[key]
                    acc["n"] += 1
                    acc["success"] += int(r.success)
                    acc["fail_ratio_sum"] += fail_ratio
                    acc["mismatch_sum"] += r.mismatch_count / L if L else 0.0
                    acc["repaired_sum"] += r.repaired_events
                    acc["attempts_sum"] += r.attempts_made
                    acc["abandoned"] += int(r.abandoned)
                    if r.fail_reason:
                        reason_counter[(label, arm, r.fail_reason)] += 1
                    per_run_rows.append({
                        "sample_id": sid, "complexity_label": label, "arm": arm,
                        "epsilon": epsilon, "replicate": rep,
                        "success": int(r.success),
                        "fail_step_idx": r.fail_step_idx if r.fail_step_idx is not None else "",
                        "fail_reason": r.fail_reason or "",
                        "fail_step_ratio": round(fail_ratio, 6),
                        "mismatch_count": r.mismatch_count,
                        "mismatch_rate": round(r.mismatch_count / L, 6) if L else 0.0,
                        "repaired_events": r.repaired_events,
                        "attempts_made": r.attempts_made,
                        "abandoned": int(r.abandoned),
                        "budget": r.budget,
                        "event_count": L,
                    })

    curve_rows = []
    for (arm, label, epsilon), acc in sorted(curve_acc.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
        n = acc["n"]
        curve_rows.append({
            "arm": arm, "complexity_label": label, "epsilon": epsilon, "n_runs": n,
            "success_rate": round(acc["success"] / n, 6),
            "mean_fail_step_ratio": round(acc["fail_ratio_sum"] / n, 6),
            "mean_mismatch_rate": round(acc["mismatch_sum"] / n, 6),
            "mean_repaired_events": round(acc["repaired_sum"] / n, 6),
            "mean_attempts": round(acc["attempts_sum"] / n, 4),
            "abandon_rate": round(acc["abandoned"] / n, 6),
        })

    eps_rows = []
    for arm in arms:
        for label in ("low", "medium", "high"):
            curve = [(float(r["epsilon"]), float(r["success_rate"]))
                     for r in curve_rows if r["arm"] == arm and r["complexity_label"] == label]
            val, flag = eps_star(curve, args.success_criterion)
            eps_rows.append({"arm": arm, "complexity_label": label,
                             "epsilon_star": round(val, 6) if val is not None else "",
                             "censor_flag": flag, "criterion": args.success_criterion})

    with (out_dir / "curve_summary.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(curve_rows[0].keys()))
        w.writeheader(); w.writerows(curve_rows)
    with (out_dir / "per_run_results.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per_run_rows[0].keys()))
        w.writeheader(); w.writerows(per_run_rows)
    with (out_dir / "eps_star.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(eps_rows[0].keys()))
        w.writeheader(); w.writerows(eps_rows)

    plots = maybe_plot(curve_rows, out_dir, args.retry_repro_prob)

    summary = {
        "experiment": "four_arm_paired_error_injection (rules vs retry with rho, plan v1 step 1 + 2nd-round amendment)",
        "design_notes": {
            "arms": {
                "no_rules": "无任何约束/重试；环境错误即整链失败",
                "retry_selfreport": "环境自检（栈下溢/finish失配，不读gt）触发重试，每步至多k次",
                "retry_oracle": "attempt != gt event 即重试（完美失败检测），每步至多k次",
                "min_rules": "栈一致性收束+非法关闭修正（沿用旧管线口径；含一处gt修复属oracle级信息，Section III申报）",
            },
            "withdrawn_arm": ("rules_retry removed (F5=C): min_rules is a total repair policy: every "
                              "violation it detects, it corrects, so execution never raises and a retry "
                              "layer placed on top is inert by construction. Verified empirically "
                              "(39,600/39,600 runs identical); four arms reported."),
            "success_definition": "无步放弃 + 无环境错误终止 + 结束时栈为空；不含任何gt判定（旧管线mismatch_rate阈值判定已移出成败路径，仅作分析量）",
            "budget": "B = ceil(L*(1+r))，每次尝试（含未通过检定与ρ复现的重试）计1，规则检查不计；各臂同B",
            "retry_abandon": "单步k+1次尝试均未通过检定 → 该步放弃（不施加），链记abandoned，继续向下走",
            "retry_error_correlation": {
                "rho": args.retry_repro_prob,
                "definition": "重试复现主尝试同一误差的概率；u_corr<ρ 复现，否则独立重抽（重试流确定性）",
                "grid": [0.0, 0.5, 0.9],
                "interpretation": ("ρ=0 瞬时/执行类误差（时序、竞态、点击抖动），重试独立重抽；"
                                   "ρ→1 可重复误差（感知类），重试失效。"
                                   "论文主张：规则对可重复误差有价值；对瞬时误差，预算充足时重试已经足够"
                                   "（ρ=0 结论必须与 r 条件同引，audit §3.3/§3.4）。"),
            },
            "injection": {"per_event_probability": "epsilon", "action_swap_prob": args.swap_prob,
                           "status_flip_prob": round(1 - args.swap_prob, 6)},
            "rng": {
                "primary": "sha256(seed,'inj',chain_id,rep) 预生成定长三元组数组；全臂、全ε档共用（corrupt判定 u<epsilon，ε不参与抽样）",
                "retry": "sha256(seed,'retry',chain_id,rep,step,attempt)：先抽ρ相关判定，再独立重抽三元组",
                "note": "无顺序推进母发生器；增删臂/调整循环顺序/改ρ网格不改变任何已有结果",
            },
            "oracle_channels": [
                "min_rules 修复①: 非法status恢复gt（本误差模型下为死代码）",
                "retry_oracle 判定: attempt与gt逐事件比较",
                "（已移除）旧管线全臂共用的 cumulative mismatch-rate>threshold 判死",
            ],
        },
        "inputs": {
            "samples_csv": str(args.samples_csv), "use_all_rows": args.use_all_rows,
            "per_label": None if args.use_all_rows else args.per_label,
            "chains": len(chains), "replicates": args.replicates,
            "eps_list": eps_values, "k": args.k, "budget_ratio": args.budget_ratio,
            "swap_prob": args.swap_prob, "retry_repro_prob": args.retry_repro_prob,
            "seed": args.seed, "success_criterion": args.success_criterion, "arms": arms,
        },
        "chain_distribution": dict(Counter(c["complexity_label"] for c in chains)),
        "fail_reasons": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in reason_counter.items()},
        "plots": plots,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote: {out_dir}/curve_summary.csv  ({len(curve_rows)} rows)")
    print(f"Wrote: {out_dir}/per_run_results.csv  ({len(per_run_rows)} runs)")
    print(f"Wrote: {out_dir}/eps_star.csv")
    print(f"Wrote: {out_dir}/summary.json")
    for p in plots:
        print(f"Plot:  {p}")


if __name__ == "__main__":
    main()

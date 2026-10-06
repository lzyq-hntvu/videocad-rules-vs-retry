#!/usr/bin/env python3
"""规则类型消融实验（实验方案 v1 步骤三，表 D/E）——9 消融条件 + no_rules 参照臂。

设计规格（2026-09-16 用户批准执行）：
  条件（10 个，全部无重试——ρ/k 不适用，见 summary.json no_retry 声明）：
    4 单独启用  {legal_set} {order} {consistency} {coordinate}
    4 留一法    全集∖{legal_set} ∖{order} ∖{consistency} ∖{coordinate}
    1 全集      ≡ 引擎 min_rules 语义（逐语义等价，见下）
    1 no_rules  Δ 的基线
  ε 网格（并集 10 点一次跑全，输出逐行标注 primary/exploratory）：
    PRIMARY   = {0.02, 0.05, 0.08}   —— plan v1 表 D/E 预登记 3 点（保预登记一致性）
    EXTENDED  = {0.10,0.14,0.18,0.22,0.26,0.30,0.34} —— exploratory 扩展区
  样本：confirm_set_600.csv 全 600 链（--use-all-rows 语义）；replicates 20；
        budget-ratio 0.2（B = ceil(L*1.2)，无重试下恒不约束，保留同口径）；
        swap-prob 0.7；种子 20261016。
  运行量：10 条件 × 600 链 × 10 ε × 20 rep = 1,200,000 runs。

四类规则的操作性定义（proposal 文本出处 + 引擎原语映射）
----------------------------------------------------------
proposal 出处（~/projects/archived/nsfc-general-2026/docs/，grep "合法集"）：
  · 1.3-科学问题与研究假设-评审版定稿候选-Day10.md §1.3.4：
      "最小规则集可包括动作类型合法集约束、局部顺序约束与坐标/落点合法性约束等"；
      规则"主要来自 GUI 任务链可观测的动作合法性统计与任务语法（动作类型可达性、
      局部顺序一致性、状态前后条件）……其作用边界是限制非法状态扩散"。
  · 研究内容与关键科学问题-WP1-WP2-WP3-评审版草稿-Day10.md:76：
      "规则类型（动作合法集、顺序约束、状态一致性约束、坐标/区域约束）"。
  · 申报书正文总稿-V1.md:111：
      "规则来源限定为 GUI 任务中的合法动作集合、状态机一致性、栈/窗口约束和坐标落点一致性"。

引擎（evidence/videocad/scripts/run_four_arm_experiment.py @ git b42ce3dd）
  min_rules_repair 含三处修复原语，归属如下（必须明示）：
    R1  status ∉ {started,finished} → 恢复 gt.status   【合法集】
        状态字母表合法集修复；读 gt（oracle 级信息，Section III 申报口径沿用）。
        本误差模型下注入器只产出 started/finished → 死代码（fire 数=0，实测验证）。
    R3  status == finished 且栈空 → 转 started          【合法集】
        状态条件合法集：空栈态的合法状态集 = {started}，finished 在集合外；
        修复把尝试收束回合法集，即 proposal 的"限制非法状态扩散"（防栈下溢）。
    R2  status == finished 且栈顶 ≠ attempt.action → 投影到栈顶 【一致性】
        栈一致性收束（引擎/审计/方案原文命名）：finish 的状态前后条件——
        被关闭元素必须是当前打开元素；同时把候选动作压缩到栈顶 1 个。
    顺序（order）：min_rules 在符号链上【无】独立的顺序修复原语。LIFO 关闭次序
        纪律已内嵌于 R2 的栈顶投影，不可分离成独立可开关的修复代码路径——按规格
        如实记录：only_order 预期 ≡ no_rules、loo_no_order ≡ full（构造性退化，
        与 F5 rules_retry 退化的软版本同性质），这是可报告的范围发现，不编造语义。
    坐标（coordinate）：坐标是图像侧概念，符号动作链上【无对应物】——按规格如实
        记录：only_coordinate 预期 ≡ no_rules、loo_no_coordinate ≡ full（vacuous）。

全集 ≡ min_rules 的结构保证
----------------------------------------------------------
本脚本【导入】引擎原语（seed_from/draw_triple/build_attempt/is_mismatch/
execute_attempt/eps_star/min_rules_repair/run_arm/VALID_STATUS，以及
run_h2_h3_mechanism_proxy.load_events），不复制引擎逻辑。两个源模块均有
main-guard，import 无副作用（与 scripts/bootstrap_eps_star.py 同一导入先例）。
全集修复路径 = [repair_legal_set, repair_order, repair_consistency,
repair_coordinate] 依序施加，已对全部可达状态空间（status×action×gt×栈内容）
穷举验证与 min_rules_repair 逐字段（attempt 终值 + repaired 计数）相等；
运行后再做 ≥100 个 (chain,ε,rep) 三元组对引擎 run_arm("min_rules") /
run_arm("no_rules") 的逐 run 比对（验证 a/b，结果入 summary.json）。

配对 RNG（audit F2 复刻）
----------------------------------------------------------
初始误差向量 sha256(seed,"inj",chain_id,rep) 预生成定长三元组数组；corrupt 判定
u<ε，ε 不参与抽样；同一 (chain,rep) 全条件、全 ε 档共用（跨条件 + 跨 ε 双重配对）。
无重试 → 无重试流。无顺序推进母发生器 → 增删条件/调整循环顺序不改变任何已有结果。

种子 20261016（与主跑批 20261015 错开一日）
----------------------------------------------------------
主确认集种子 20261015 已按预登记锁定且"只运行一次"，不得复用/重跑；本消融是
新实验，取相邻次日 20261016 以保持血缘可读（day+1），并避免任何"重跑确认集"
的解释空间。F2 设计下换种子只等价于独立重复抽样，结果差异应在抽样噪声内。

ε 网格理由（日志同步声明）
----------------------------------------------------------
主口径 3 点源自 plan v1 时代（当时依据的是被 F1 撤回的伪造 JSON 世界观
ε*≤0.08——"假 JSON 世界观第三次咬伤的受害者"）；为保预登记一致性 3 点保留并
如实报（其上 Δε* 预计全删失，报告为 censored，不省略）；扩展区按 audit §3.1
先例（网格上限必须盖住真实 ε*，开发集 min_rules 分层 ε* 最高 0.3259 → 顶端
0.34 防删失），用户 2026-09-16 批准。
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evidence" / "videocad" / "scripts"))

from run_four_arm_experiment import (  # noqa: E402  （导入而非复制：与引擎同一修复代码路径）
    VALID_STATUS,
    build_attempt,
    draw_triple,
    eps_star,
    execute_attempt,
    is_mismatch,
    min_rules_repair,
    run_arm,
    seed_from,
)
from run_h2_h3_mechanism_proxy import load_events  # noqa: E402

RULE_CLASSES = ("legal_set", "order", "consistency", "coordinate")

PRIMARY_EPS = (0.02, 0.05, 0.08)
EXTENDED_EPS = (0.10, 0.14, 0.18, 0.22, 0.26, 0.30, 0.34)
DEFAULT_EPS_LIST = "0.02,0.05,0.08,0.10,0.14,0.18,0.22,0.26,0.30,0.34"

# 条件定义：condition_id -> 启用的规则类（依施加顺序）
CONDITIONS: dict[str, tuple[str, ...]] = {
    "no_rules": (),
    "only_legal_set": ("legal_set",),
    "only_order": ("order",),
    "only_consistency": ("consistency",),
    "only_coordinate": ("coordinate",),
    "loo_no_legal_set": ("order", "consistency", "coordinate"),
    "loo_no_order": ("legal_set", "consistency", "coordinate"),
    "loo_no_consistency": ("legal_set", "order", "coordinate"),
    "loo_no_coordinate": ("legal_set", "order", "consistency"),
    "full": ("legal_set", "order", "consistency", "coordinate"),
}

STRATA = ("low", "medium", "high")


# ---------------------------------------------------------------- 规则类修复原语
def repair_legal_set(attempt: dict, gt_event: dict, stack: list[str], stats: dict | None = None) -> int:
    """【合法集】R1（状态字母表合法集，死代码，读 gt）+ R3（状态条件合法集：空栈禁关闭）。

    返回修复次数（与引擎 min_rules_repair 的计数口径一致）；
    stats 可选，用于分计 R1/R3 触发数（fire 数统计，不影响修复语义）。
    """
    r = 0
    if attempt["status"] not in VALID_STATUS:
        attempt["status"] = gt_event["status"]  # R1：唯一读 gt 的原语（oracle 通道，申报）
        r += 1
        if stats is not None:
            stats["r1"] = stats.get("r1", 0) + 1
    if attempt["status"] == "finished" and not stack:
        attempt["status"] = "started"  # R3：空栈态合法集 = {started}
        r += 1
        if stats is not None:
            stats["r3"] = stats.get("r3", 0) + 1
    return r


def repair_order(attempt: dict, gt_event: dict, stack: list[str]) -> int:
    """【顺序】符号链上无独立修复原语（LIFO 纪律内嵌于一致性投影，不可分离）——vacuous。"""
    return 0


def repair_consistency(attempt: dict, gt_event: dict, stack: list[str]) -> int:
    """【一致性】R2 栈一致性收束：finish 投影到当前打开元素（状态前后条件）。"""
    if attempt["status"] == "finished" and stack and stack[-1] != attempt["action"]:
        attempt["action"] = stack[-1]
        return 1
    return 0


def repair_coordinate(attempt: dict, gt_event: dict, stack: list[str]) -> int:
    """【坐标】图像侧概念，符号动作链上无对应物——vacuous。"""
    return 0


REPAIR_FNS = {
    "legal_set": repair_legal_set,
    "order": repair_order,
    "consistency": repair_consistency,
    "coordinate": repair_coordinate,
}


# ---------------------------------------------------------------- 单条件执行器
def run_condition(
    events: list[dict],
    plan: list[tuple[float, float, float]],
    alt_lists: list[tuple[str, ...]],
    enabled: tuple[str, ...],
    *,
    epsilon: float,
    budget: int,
    swap_prob: float,
) -> dict:
    """无重试单条件执行。镜像引擎 run_arm 的 no_rules/min_rules 分支（同一代码语义）。

    返回 dict: success/fail_step_idx/fail_reason/mismatch_count/repaired_events/
    attempts_made/budget/event_count/triggers（各类触发步数）/r1_fires/r3_fires。
    """
    L = len(events)
    stack: list[str] = []
    mismatch = 0
    repaired = 0
    attempts = 0
    triggers = {c: 0 for c in RULE_CLASSES}
    r1_fires = 0
    r3_fires = 0
    first_fail_idx: int | None = None
    first_fail_reason: str | None = None
    repair_seq = [(c, REPAIR_FNS[c]) for c in enabled]

    def terminal(idx: int, reason: str) -> dict:
        return {"success": False, "fail_step_idx": idx, "fail_reason": reason,
                "mismatch_count": mismatch, "repaired_events": repaired,
                "attempts_made": attempts, "budget": budget, "event_count": L,
                "triggers": triggers, "r1_fires": r1_fires, "r3_fires": r3_fires}

    for i in range(L):
        primary = build_attempt(events[i], alt_lists[i], plan[i], epsilon, swap_prob)
        if attempts >= budget:
            return terminal(i, "budget_exhausted")
        attempts += 1
        if repair_seq:
            ls_stats: dict = {}
            for cls, fn in repair_seq:
                if cls == "legal_set":
                    n = fn(primary, events[i], stack, ls_stats)
                else:
                    n = fn(primary, events[i], stack)
                if n:
                    repaired += n
                    triggers[cls] += 1
            r1_fires += ls_stats.get("r1", 0)
            r3_fires += ls_stats.get("r3", 0)
        err = execute_attempt(stack, primary)
        if err:
            # 与引擎同口径：无修复臂报原生错误名；有修复臂按构造不应触发 → unexpected_ 前缀
            return terminal(i, err if not repair_seq else f"unexpected_{err}")
        mismatch += int(is_mismatch(primary, events[i]))

    if stack:
        idx = L - 1
        if first_fail_idx is None:
            first_fail_idx, first_fail_reason = idx, "non_empty_stack_at_end"
        return {"success": False, "fail_step_idx": first_fail_idx, "fail_reason": first_fail_reason,
                "mismatch_count": mismatch, "repaired_events": repaired,
                "attempts_made": attempts, "budget": budget, "event_count": L,
                "triggers": triggers, "r1_fires": r1_fires, "r3_fires": r3_fires}
    return {"success": True, "fail_step_idx": None, "fail_reason": None,
            "mismatch_count": mismatch, "repaired_events": repaired,
            "attempts_made": attempts, "budget": budget, "event_count": L,
            "triggers": triggers, "r1_fires": r1_fires, "r3_fires": r3_fires}


# ---------------------------------------------------------------- 验证 a/b
def run_validation(chains: list[dict], plans: dict, alt_cache: dict, args, n_val: int) -> dict:
    """全集 ≡ 引擎 min_rules、no_rules ≡ 引擎 no_rules：随机 (chain,ε,rep) 三元组逐字段比对。"""
    rng = random.Random(seed_from(args.seed, "validate"))
    eps_values = sorted({float(x) for x in args.eps_list.split(",")})
    result = {"n_triples_requested": n_val,
              "full_vs_min_rules": {"compared": 0, "mismatches": 0, "fields": ["success", "fail_reason", "attempts_made", "mismatch_count", "repaired_events"]},
              "no_rules_vs_engine": {"compared": 0, "mismatches": 0, "fields": ["success", "fail_reason", "attempts_made", "mismatch_count", "repaired_events"]}}
    seen: set = set()
    while result["full_vs_min_rules"]["compared"] + result["no_rules_vs_engine"]["compared"] < 2 * n_val:
        ci = rng.randrange(len(chains))
        rep = rng.randrange(args.replicates)
        eps = eps_values[rng.randrange(len(eps_values))]
        key = (ci, eps, rep)
        if key in seen:
            continue
        seen.add(key)
        chain = chains[ci]
        sid, L = chain["sample_id"], len(chain["events"])
        budget = math.ceil(L * (1 + args.budget_ratio))
        common = dict(epsilon=eps, k=args.k, budget=budget, chain_id=sid, rep=rep,
                      seed=args.seed, swap_prob=args.swap_prob, retry_repro_prob=0.0)
        for tag, engine_arm, enabled in (
            ("full_vs_min_rules", "min_rules", CONDITIONS["full"]),
            ("no_rules_vs_engine", "no_rules", CONDITIONS["no_rules"]),
        ):
            eng = run_arm(engine_arm, chain["events"], plans[(sid, rep)], alt_cache[sid], **common)
            mine = run_condition(chain["events"], plans[(sid, rep)], alt_cache[sid], enabled,
                                 epsilon=eps, budget=budget, swap_prob=args.swap_prob)
            eng_f = {"success": eng.success, "fail_reason": eng.fail_reason,
                     "attempts_made": eng.attempts_made, "mismatch_count": eng.mismatch_count,
                     "repaired_events": eng.repaired_events}
            mine_f = {k: mine[k] for k in eng_f}
            rec = result[tag]
            rec["compared"] += 1
            if eng_f != mine_f:
                rec["mismatches"] += 1
                rec.setdefault("examples", []).append(
                    {"sample_id": sid, "epsilon": eps, "replicate": rep, "engine": eng_f, "ablation": mine_f})
        if len(seen) > 50 * n_val:  # 防御：三元组空间远大于 n_val，不会触发
            break
    return result


# ---------------------------------------------------------------- 主流程
def main() -> None:
    t0 = time.time()
    ap = argparse.ArgumentParser(description="Rule-type ablation (plan v1 step 3, 9 conditions + no_rules, no retry)")
    ap.add_argument("--samples-csv", type=Path,
                    default=REPO_ROOT / "evidence/videocad/notes/confirm_set_600.csv")
    ap.add_argument("--replicates", type=int, default=20)
    ap.add_argument("--eps-list", type=str, default=DEFAULT_EPS_LIST,
                    help="并集网格（primary 3 点 + exploratory 7 点；跨档共享同一组注入随机数）")
    ap.add_argument("--budget-ratio", type=float, default=0.2)
    ap.add_argument("--swap-prob", type=float, default=0.7)
    ap.add_argument("--k", type=int, default=2, help="（无重试下不适用；仅为引擎 run_arm 验证接口保留）")
    ap.add_argument("--seed", type=int, default=20261016,
                    help="消融运行种子（与确认集主跑批 20261015 错开一日，理由见 docstring/summary）")
    ap.add_argument("--success-criterion", type=float, default=0.5)
    ap.add_argument("--n-validate", type=int, default=150, help="验证 a/b 各自比对的 (chain,ε,rep) 三元组数")
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT / "evidence/videocad/notes/rule_ablation")
    args = ap.parse_args()

    eps_values = sorted({float(x) for x in args.eps_list.split(",")})
    primary_set = {round(e, 6) for e in PRIMARY_EPS}
    for e in PRIMARY_EPS:
        if round(e, 6) not in {round(x, 6) for x in eps_values}:
            raise ValueError(f"primary ε {e} 不在网格内")
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- 样本装载（引擎 --use-all-rows 语义：仅要求 label 与链路径存在） ---
    rows = []
    with args.samples_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("complexity_label") and row.get("action_json_path"):
                rows.append(row)
    chains = []
    global_vocab: set[str] = set()
    for row in rows:
        events = load_events(REPO_ROOT / row["action_json_path"])
        global_vocab.update(e["action"] for e in events)
        chains.append({"sample_id": row["sample_id"], "complexity_label": row["complexity_label"],
                       "events": events})
    vocab_sorted = sorted(global_vocab)
    vocab_size = len(vocab_sorted)

    alt_cache: dict[str, list[tuple[str, ...]]] = {}
    plans: dict[tuple[str, int], list[tuple[float, float, float]]] = {}
    for chain in chains:
        sid = chain["sample_id"]
        alt_cache[sid] = tuple(
            tuple(a for a in vocab_sorted if a != ev["action"]) for ev in chain["events"]
        )
        for rep in range(args.replicates):
            rng = random.Random(seed_from(args.seed, "inj", sid, rep))
            plans[(sid, rep)] = [draw_triple(rng) for _ in chain["events"]]

    # --- 验证 a/b（先于主跑，失败即中止） ---
    val = run_validation(chains, plans, alt_cache, args, args.n_validate)
    for tag in ("full_vs_min_rules", "no_rules_vs_engine"):
        if val[tag]["mismatches"] != 0:
            raise SystemExit(f"验证失败：{tag} 存在不等三元组，中止运行。详情：{val[tag].get('examples')}")

    # --- 主跑（F2 配对：eps → chain → rep → condition，注入向量与循环顺序无关） ---
    curve_acc: dict[tuple, dict] = defaultdict(lambda: {
        "n": 0, "success": 0, "fail_ratio_all_sum": 0.0, "fail_ratios_failed": [],
        "mismatch_sum": 0.0, "repaired_sum": 0, "attempts_sum": 0,
        "steps": 0, "trig": {c: 0 for c in RULE_CLASSES}})
    reason_counter: Counter = Counter()
    r1_total = r3_total = 0
    n_runs = 0

    per_run_path = out_dir / "per_run_results.csv"
    per_run_fields = ["sample_id", "complexity_label", "condition", "epsilon", "grid", "replicate",
                      "success", "fail_step_idx", "fail_reason", "fail_step_ratio",
                      "mismatch_count", "mismatch_rate", "repaired_events", "attempts_made",
                      "abandoned", "budget", "event_count",
                      "trig_legal_set", "trig_order", "trig_consistency", "trig_coordinate"]
    f_per = per_run_path.open("w", encoding="utf-8", newline="")
    w_per = csv.DictWriter(f_per, fieldnames=per_run_fields)
    w_per.writeheader()

    for epsilon in eps_values:
        grid_tag = "primary" if round(epsilon, 6) in primary_set else "exploratory"
        for chain in chains:
            sid = chain["sample_id"]
            label = chain["complexity_label"]
            events = chain["events"]
            L = len(events)
            budget = math.ceil(L * (1 + args.budget_ratio))
            for rep in range(args.replicates):
                plan = plans[(sid, rep)]
                for cond, enabled in CONDITIONS.items():
                    r = run_condition(events, plan, alt_cache[sid], enabled,
                                      epsilon=epsilon, budget=budget, swap_prob=args.swap_prob)
                    fail_idx = r["fail_step_idx"] if r["fail_step_idx"] is not None else L - 1
                    fail_ratio = (fail_idx + 1) / L if L else 0.0
                    n_runs += 1
                    acc = curve_acc[(cond, label, epsilon)]
                    acc["n"] += 1
                    acc["success"] += int(r["success"])
                    acc["fail_ratio_all_sum"] += fail_ratio  # 引擎口径（含成功 run 记 1.0）
                    if not r["success"]:
                        acc["fail_ratios_failed"].append(fail_ratio)  # 表 E 口径：仅失败 run
                    acc["mismatch_sum"] += r["mismatch_count"] / L if L else 0.0
                    acc["repaired_sum"] += r["repaired_events"]
                    acc["attempts_sum"] += r["attempts_made"]
                    acc["steps"] += L
                    for c in RULE_CLASSES:
                        acc["trig"][c] += r["triggers"][c]
                    if r["fail_reason"]:
                        reason_counter[(label, cond, r["fail_reason"])] += 1
                    r1_total += r["r1_fires"]
                    r3_total += r["r3_fires"]
                    w_per.writerow({
                        "sample_id": sid, "complexity_label": label, "condition": cond,
                        "epsilon": epsilon, "grid": grid_tag, "replicate": rep,
                        "success": int(r["success"]),
                        "fail_step_idx": r["fail_step_idx"] if r["fail_step_idx"] is not None else "",
                        "fail_reason": r["fail_reason"] or "",
                        "fail_step_ratio": round(fail_ratio, 6),
                        "mismatch_count": r["mismatch_count"],
                        "mismatch_rate": round(r["mismatch_count"] / L, 6) if L else 0.0,
                        "repaired_events": r["repaired_events"],
                        "attempts_made": r["attempts_made"],
                        "abandoned": 0,
                        "budget": r["budget"], "event_count": L,
                        "trig_legal_set": r["triggers"]["legal_set"],
                        "trig_order": r["triggers"]["order"],
                        "trig_consistency": r["triggers"]["consistency"],
                        "trig_coordinate": r["triggers"]["coordinate"],
                    })
    f_per.close()
    elapsed = time.time() - t0

    # --- 聚合 1：curve_summary.csv ---
    curve_rows = []
    for (cond, label, epsilon), acc in sorted(curve_acc.items(),
                                              key=lambda x: (x[0][0], x[0][1], x[0][2])):
        n = acc["n"]
        frf = acc["fail_ratios_failed"]
        row = {
            "condition": cond, "complexity_label": label, "epsilon": epsilon,
            "grid": "primary" if round(epsilon, 6) in primary_set else "exploratory",
            "n_runs": n,
            "success_rate": round(acc["success"] / n, 6),
            "n_fail": n - acc["success"],
            "mean_fail_step_ratio_failed": round(sum(frf) / len(frf), 6) if frf else "",
            "median_fail_step_ratio_failed": round(statistics.median(frf), 6) if frf else "",
            "mean_fail_step_ratio_all": round(acc["fail_ratio_all_sum"] / n, 6),  # 引擎口径
            "mean_mismatch_rate": round(acc["mismatch_sum"] / n, 6),
            "mean_repaired_events": round(acc["repaired_sum"] / n, 6),
            "mean_attempts": round(acc["attempts_sum"] / n, 4),
            "n_steps": acc["steps"],
        }
        for c in RULE_CLASSES:
            row[f"trig_{c}"] = acc["trig"][c]
            row[f"trig_rate_{c}"] = round(acc["trig"][c] / acc["steps"], 6) if acc["steps"] else 0.0
        curve_rows.append(row)

    with (out_dir / "curve_summary.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(curve_rows[0].keys()))
        w.writeheader(); w.writerows(curve_rows)

    # --- 聚合 2：覆盖率/收缩比（coverage_contraction.csv） ---
    cc_rows = []
    for cond in CONDITIONS:
        for c in RULE_CLASSES:
            enabled = int(c in CONDITIONS[cond])
            # 按 ε 行（跨层跨 rep 汇总）
            for epsilon in eps_values:
                steps = sum(curve_acc[(cond, lb, epsilon)]["steps"] for lb in STRATA)
                trig = sum(curve_acc[(cond, lb, epsilon)]["trig"][c] for lb in STRATA)
                cc_rows.append({
                    "condition": cond, "rule_class": c, "epsilon": epsilon,
                    "grid": "primary" if round(epsilon, 6) in primary_set else "exploratory",
                    "enabled": enabled, "n_steps": steps, "n_triggered": trig,
                    "trigger_rate": round(trig / steps, 6) if steps else 0.0,
                    "contraction": contraction_for_class(c, vocab_size) if trig else "",
                    "vacuous": "",  # 汇总行后统一填
                })
            steps_all = sum(curve_acc[(cond, lb, e)]["steps"] for lb in STRATA for e in eps_values)
            trig_all = sum(curve_acc[(cond, lb, e)]["trig"][c] for lb in STRATA for e in eps_values)
            cc_rows.append({
                "condition": cond, "rule_class": c, "epsilon": "ALL", "grid": "all",
                "enabled": enabled, "n_steps": steps_all, "n_triggered": trig_all,
                "trigger_rate": round(trig_all / steps_all, 6) if steps_all else 0.0,
                "contraction": contraction_for_class(c, vocab_size) if trig_all else "",
                "vacuous": "",
            })
    # vacuous 判定（验证 d）：在启用该类的条件中触发数恒为 0
    vacuous_classes = []
    for c in RULE_CLASSES:
        fired = any(r["n_triggered"] > 0 for r in cc_rows
                    if r["rule_class"] == c and r["enabled"] == 1)
        if not fired:
            vacuous_classes.append(c)
    for r in cc_rows:
        r["vacuous"] = int(r["rule_class"] in vacuous_classes)
    with (out_dir / "coverage_contraction.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cc_rows[0].keys()))
        w.writeheader(); w.writerows(cc_rows)

    # --- 聚合 3：ε*（eps_star.csv） ---
    def rate_lookup(cond: str, stratum: str, epsilon: float) -> float:
        if stratum == "pooled":
            tot = sum(curve_acc[(cond, lb, epsilon)]["n"] for lb in STRATA)
            suc = sum(curve_acc[(cond, lb, epsilon)]["success"] for lb in STRATA)
            return suc / tot
        acc = curve_acc[(cond, stratum, epsilon)]
        return acc["success"] / acc["n"]

    eps_rows = []
    for grid_name, grid_eps in (("primary", [e for e in eps_values if round(e, 6) in primary_set]),
                                ("extended_10pt", eps_values)):
        for cond in CONDITIONS:
            for stratum in (*STRATA, "pooled"):
                curve = [(e, rate_lookup(cond, stratum, e)) for e in grid_eps]
                v, flag = eps_star(curve, args.success_criterion)
                eps_rows.append({
                    "condition": cond, "stratum": stratum, "grid": grid_name,
                    "n_grid_points": len(grid_eps), "criterion": args.success_criterion,
                    "epsilon_star": round(v, 6) if v is not None else "",
                    "censor_flag": flag,
                })
    with (out_dir / "eps_star.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(eps_rows[0].keys()))
        w.writeheader(); w.writerows(eps_rows)

    # --- 聚合 4：边际贡献两方向（ablation_effects.csv，长表） ---
    effect_rows = []
    for eps in eps_values:
        grid_tag = "primary" if round(eps, 6) in primary_set else "exploratory"
        for stratum in (*STRATA, "pooled"):
            # Δ成功率
            for cond in CONDITIONS:
                if cond == "no_rules":
                    continue
                if cond.startswith("only_"):
                    direction, cls, ref = "single_vs_no_rules", cond[5:], "no_rules"
                elif cond.startswith("loo_no_"):
                    direction, cls, ref = "loo_vs_full", cond[7:], "full"
                else:  # full：补充口径（规则整体效应），不属两个预登记方向
                    direction, cls, ref = "full_vs_no_rules(supp)", "all", "no_rules"
                d = rate_lookup(cond, stratum, eps) - rate_lookup(ref, stratum, eps)
                effect_rows.append({
                    "direction": direction, "rule_class": cls, "condition": cond,
                    "reference": ref, "quantity": "delta_success_rate",
                    "stratum": stratum, "epsilon": eps, "grid": grid_tag,
                    "value": round(d, 6), "censor_flag": "",
                })
            # Δ失败位置（仅失败 run 的首次失败归一化步位；mean/median）
            for cond in CONDITIONS:
                if cond == "no_rules":
                    continue
                if cond.startswith("only_"):
                    direction, cls, ref = "single_vs_no_rules", cond[5:], "no_rules"
                elif cond.startswith("loo_no_"):
                    direction, cls, ref = "loo_vs_full", cond[7:], "full"
                else:
                    direction, cls, ref = "full_vs_no_rules(supp)", "all", "no_rules"
                for stat_name, stat_fn in (("mean", lambda v: round(sum(v) / len(v), 6)),
                                           ("median", lambda v: round(statistics.median(v), 6))):
                    def get(cond_, eps_):
                        if stratum == "pooled":
                            vs = [v for lb in STRATA
                                  for v in curve_acc[(cond_, lb, eps_)]["fail_ratios_failed"]]
                        else:
                            vs = curve_acc[(cond_, stratum, eps_)]["fail_ratios_failed"]
                        return stat_fn(vs) if vs else None
                    a, b = get(cond, eps), get(ref, eps)
                    effect_rows.append({
                        "direction": direction, "rule_class": cls, "condition": cond,
                        "reference": ref, "quantity": f"delta_fail_pos_{stat_name}",
                        "stratum": stratum, "epsilon": eps, "grid": grid_tag,
                        "value": round(a - b, 6) if (a is not None and b is not None) else "",
                        "censor_flag": "undefined(no failed runs on one side)" if (a is None or b is None) else "",
                    })
    # Δε*（两档网格 × 分层 + pooled）
    eps_lookup = {(r["condition"], r["stratum"], r["grid"]): r for r in eps_rows}
    for grid_name in ("primary", "extended_10pt"):
        for cond in CONDITIONS:
            if cond == "no_rules":
                continue
            if cond.startswith("only_"):
                direction, cls, ref = "single_vs_no_rules", cond[5:], "no_rules"
            elif cond.startswith("loo_no_"):
                direction, cls, ref = "loo_vs_full", cond[7:], "full"
            else:
                direction, cls, ref = "full_vs_no_rules(supp)", "all", "no_rules"
            for stratum in (*STRATA, "pooled"):
                rc, rr = eps_lookup[(cond, stratum, grid_name)], eps_lookup[(ref, stratum, grid_name)]
                if rc["epsilon_star"] == "" or rr["epsilon_star"] == "":
                    d, cflag = "", "undefined(right_censored on one side)"
                else:
                    d = round(float(rc["epsilon_star"]) - float(rr["epsilon_star"]), 6)
                    cflag = "ok" if rc["censor_flag"] == "ok" and rr["censor_flag"] == "ok" else \
                        f"cond:{rc['censor_flag']}|ref:{rr['censor_flag']}"
                effect_rows.append({
                    "direction": direction, "rule_class": cls, "condition": cond,
                    "reference": ref, "quantity": "delta_eps_star",
                    "stratum": stratum, "epsilon": "", "grid": grid_name,
                    "value": d, "censor_flag": cflag,
                })
    with (out_dir / "ablation_effects.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(effect_rows[0].keys()))
        w.writeheader(); w.writerows(effect_rows)

    # --- 验证 c：单调性（每个 ε × 层：full 成功率 ≥ 任一留一） ---
    mono_violations = []
    for eps in eps_values:
        for stratum in (*STRATA, "pooled"):
            rf = rate_lookup("full", stratum, eps)
            for cond in CONDITIONS:
                if cond.startswith("loo_no_"):
                    rl = rate_lookup(cond, stratum, eps)
                    if rl > rf + 1e-12:
                        mono_violations.append({"epsilon": eps, "stratum": stratum,
                                                "condition": cond, "rate_loo": rl, "rate_full": rf})
    # --- 验证 d 的补充：构造性退化实证（only_order/only_coordinate ≡ no_rules；loo_no_order/loo_no_coordinate ≡ full） ---
    degen_checks = {}
    for a_cond, b_cond in (("only_order", "no_rules"), ("only_coordinate", "no_rules"),
                           ("loo_no_order", "full"), ("loo_no_coordinate", "full")):
        same = all(
            curve_acc[(a_cond, lb, e)]["success"] == curve_acc[(b_cond, lb, e)]["success"]
            for lb in STRATA for e in eps_values)
        degen_checks[f"{a_cond}_==_{b_cond}"] = bool(same)

    # --- summary.json ---
    expected_runs = len(CONDITIONS) * len(chains) * len(eps_values) * args.replicates
    summary = {
        "experiment": "rule_type_ablation (plan v1 step 3, table D/E; 9 ablation conditions + no_rules reference arm)",
        "script": "scripts/run_rule_ablation.py",
        "engine_source": {
            "file": "evidence/videocad/scripts/run_four_arm_experiment.py",
            "git_sha": "b42ce3dddf4a30833832b77ccae94b93c8c8b888",
            "reuse_mode": "import (not copied): seed_from/draw_triple/build_attempt/is_mismatch/execute_attempt/min_rules_repair/run_arm/eps_star/VALID_STATUS + load_events; both source modules main-guarded, import side-effect free",
        },
        "inputs": {
            "samples_csv": str(args.samples_csv), "use_all_rows": True,
            "chains": len(chains), "replicates": args.replicates,
            "eps_list": eps_values, "budget_ratio": args.budget_ratio,
            "swap_prob": args.swap_prob, "seed": args.seed,
            "success_criterion": args.success_criterion,
            "conditions": {c: list(en) for c, en in CONDITIONS.items()},
            "vocab_size": vocab_size, "vocab_sorted": vocab_sorted,
        },
        "no_retry": {
            "declared": "全部 10 条件均为无重试修复条件；ρ/k 不适用（无重试流）。",
            "budget": "B = ceil(L*(1+0.2)) 与引擎同口径；无重试下 attempts=L ≤ B，预算恒不约束。",
        },
        "seed_rationale": {
            "seed": args.seed,
            "confirm_main_seed": 20261015,
            "rationale": ("主确认集种子 20261015 已预登记且只运行一次，不得复用；本消融为新实验，"
                          "取相邻次日 20261016 保持血缘可读并避免任何'重跑确认集'的解释空间；"
                          "F2 配对设计下换种子仅等价于独立重复抽样。"),
        },
        "grid": {
            "primary": list(PRIMARY_EPS),
            "extended_exploratory": list(EXTENDED_EPS),
            "rationale": ("主口径 3 点为 plan v1 表 D/E 预登记点（plan v1 时代依据的是被 F1 撤回的"
                          "伪造 JSON 世界观 ε*≤0.08——假 JSON 世界观第三次咬伤的受害者）；为保预登记"
                          "一致性保留并如实报（其上 Δε* 预计全删失，报告为 censored）。扩展区按 "
                          "audit §3.1 先例（网格上限须盖住真实 ε*：开发集 min_rules 分层 ε* 最高 "
                          "0.3259 → 顶端 0.34 防删失），用户 2026-09-16 批准。"),
        },
        "rule_class_mapping": {
            "legal_set": {
                "engine_primitives": ["R1 状态字母表合法集修复（读 gt，oracle 通道申报；本误差模型下死代码）",
                                       "R3 非法关闭修正：空栈 finished → started（状态条件合法集，不读 gt）"],
                "proposal_basis": "动作类型合法集约束 / 限制非法状态扩散（1.3-科学问题 §1.3.4；申报书正文总稿-V1.md:111）",
            },
            "order": {
                "engine_primitives": [],
                "proposal_basis": "局部顺序约束（1.3-科学问题 §1.3.4；研究内容 WP1-WP2-WP3:76）",
                "note": ("符号链上无独立修复原语：LIFO 关闭次序纪律内嵌于一致性收束的栈顶投影，"
                          "不可分离为独立可开关代码路径 → only_order ≡ no_rules、loo_no_order ≡ full"
                          "（构造性退化，如实报告为范围发现）。"),
            },
            "consistency": {
                "engine_primitives": ["R2 栈一致性收束：finish 投影到栈顶（状态前后条件，不读 gt）"],
                "proposal_basis": "状态一致性约束 / 状态前后条件 / 状态机一致性（研究内容:76；1.3 §1.3.4）",
            },
            "coordinate": {
                "engine_primitives": [],
                "proposal_basis": "坐标/落点合法性约束（1.3 §1.3.4；申报书正文总稿:111）",
                "note": "坐标是图像侧概念，符号动作链上无对应物 → only_coordinate ≡ no_rules、loo_no_coordinate ≡ full（vacuous，如实报告）。",
            },
            "oracle_channels": [
                "legal_set R1：非法 status 恢复 gt（本误差模型下死代码；沿引引擎 Section III 申报口径）",
            ],
        },
        "metric_definitions": {
            "success": "无环境错误终止 + 结束栈空（无重试 → 无步放弃）；零 gt，与引擎 F3 口径一致",
            "delta_success_rate": "single 方向 = rate(only_X) − rate(no_rules)；loo 方向 = rate(loo_no_X) − rate(full)；full_vs_no_rules 为补充口径",
            "delta_eps_star": "ε* 用引擎导入的同一 eps_star 线性插值（判据 0.5）；分层（low/medium/high）+ pooled；两档网格各报；删失如实标",
            "fail_position": "首次失败归一化步位 (fail_step_idx+1)/L，仅统计失败 run（成功 run 不进入 mean/median）；Δ = 条件 − 参照",
            "fail_position_ks_vs_no_rules": {
                "status": "skipped",
                "reason": ("表 E 的 Δ失败位置以 mean/median 落实已足够支撑图 4 与正文表述；KS 为分布级"
                            "补充检验，不进入任何预登记判定，为控制本步实现面与运行面按规格声明省略。"),
            },
            "coverage": ("每类规则在每条件中被触发的步比例 = 触发步数 / 总步数（跨该条件全部 run 求和）；"
                          "触发 = 该步修复函数改变了 attempt（含阻止错误：R2 投影与 R3 转 started 均同时"
                          "改变尝试并阻止相应环境错误，二者同事件计一次）"),
            "contraction": {
                "definition": "触发步上候选空间被压缩的比例 = 1 − |约束后可行集| / |约束前可行集|（按规则所约束的维度计）",
                "consistency": ("动作维度：finish 尝试的候选动作集 = 全词表（|V| 个，含被注入替换后的任意动作）"
                                 "→ 投影到栈顶 1 个 → 收缩比 = 1 − 1/|V|（|V| = 全局动作词表，逐触发步恒定）"),
                "legal_set": ("状态维度：空栈态候选状态集 {started, finished} → 合法集 {started} → 收缩比 = 0.5"
                               "（R1 若触发同属状态维度，同为 0.5；实测 R1 触发数见 r1_total_fires，预期 0）"),
                "order/coordinate": "vacuous（无修复原语，候选空间未被约束）→ 留空",
                "note": "引擎候选集是隐式的，以上为本次消融的操作化定义，随 summary.json 申报。",
            },
        },
        "run_counts": {
            "expected": expected_runs,
            "formula": f"{len(CONDITIONS)} conditions x {len(chains)} chains x {len(eps_values)} eps x {args.replicates} reps",
            "actual": n_runs,
            "match": n_runs == expected_runs,
        },
        "validation": {
            "a_full_equals_engine_min_rules": val["full_vs_min_rules"],
            "b_no_rules_equals_engine": val["no_rules_vs_engine"],
            "c_monotonicity_full_ge_loo": {"checked_cells": len(eps_values) * 4, "violations": mono_violations},
            "d_vacuous_classes": vacuous_classes,
            "d_degeneracy_empirical": degen_checks,
            "e_run_count": {"expected": expected_runs, "actual": n_runs, "match": n_runs == expected_runs},
            "r1_total_fires": r1_total,
            "r3_total_fires": r3_total,
        },
        "chain_distribution": dict(Counter(c["complexity_label"] for c in chains)),
        "fail_reasons": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in sorted(reason_counter.items())},
        "elapsed_seconds": round(elapsed, 1),
        "outputs": ["per_run_results.csv", "curve_summary.csv", "eps_star.csv",
                     "ablation_effects.csv", "coverage_contraction.csv", "summary.json"],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                           encoding="utf-8")

    print(f"Wrote: {per_run_path}  ({n_runs} runs)")
    print(f"Wrote: {out_dir}/curve_summary.csv  ({len(curve_rows)} rows)")
    print(f"Wrote: {out_dir}/eps_star.csv  ({len(eps_rows)} rows)")
    print(f"Wrote: {out_dir}/ablation_effects.csv  ({len(effect_rows)} rows)")
    print(f"Wrote: {out_dir}/coverage_contraction.csv  ({len(cc_rows)} rows)")
    print(f"Wrote: {out_dir}/summary.json")
    print(f"\n验证 a) 全集 vs 引擎 min_rules：{val['full_vs_min_rules']['compared']} 三元组，"
          f"{val['full_vs_min_rules']['mismatches']} 处不等")
    print(f"验证 b) no_rules vs 引擎 no_rules：{val['no_rules_vs_engine']['compared']} 三元组，"
          f"{val['no_rules_vs_engine']['mismatches']} 处不等")
    print(f"验证 c) 单调性 full ≥ LOO：{len(eps_values) * 4} 格，{len(mono_violations)} 处违反")
    print(f"验证 d) vacuous 类：{vacuous_classes or '无'}；构造性退化实证：{degen_checks}")
    print(f"验证 e) 运行计数：{n_runs} / 预期 {expected_runs}（{'一致' if n_runs == expected_runs else '不一致!'}）")
    print(f"R1 死代码触发数（预期 0）：{r1_total}；R3 触发数：{r3_total}")
    print(f"实测耗时：{elapsed:.1f}s（{n_runs} runs，{n_runs / max(elapsed, 1e-9) * 1000:.0f} runs/s）")


def contraction_for_class(cls: str, vocab_size: int) -> float:
    """触发步的收缩比（操作化定义见 summary.json metric_definitions.contraction）。"""
    if cls == "consistency":
        return round(1 - 1 / vocab_size, 6)   # 动作维度：|V| → 1
    if cls == "legal_set":
        return 0.5                             # 状态维度：{started, finished} → {started}
    return ""                                  # order/coordinate：vacuous


if __name__ == "__main__":
    main()

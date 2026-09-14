#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


VALID_STATUS = ("started", "finished")


@dataclass
class RunResult:
    success: bool
    fail_step_idx: int | None
    fail_reason: str | None
    mismatch_count: int
    total_events: int
    repaired_events: int


def load_selected_chains(samples_csv: Path, per_label: int) -> list[dict]:
    rows = []
    by_label = {"low": [], "medium": [], "high": []}
    with samples_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("sample_group") != "random_stratified_overlap":
                continue
            label = row["complexity_label"]
            if label in by_label:
                by_label[label].append(row)

    for label in ("low", "medium", "high"):
        label_rows = by_label[label][:per_label]
        if len(label_rows) < per_label:
            raise ValueError(f"Not enough rows for {label}: {len(label_rows)} < {per_label}")
        rows.extend(label_rows)
    return rows


def load_events(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"JSON root is not list: {path}")
    events = []
    for e in data:
        if not isinstance(e, dict):
            raise ValueError(f"Non-dict event in {path}")
        events.append(
            {
                "status": e["status"],
                "action": e["action"],
            }
        )
    return events


def perturb_events(
    events: list[dict],
    epsilon: float,
    rng: random.Random,
    action_vocab: list[str],
) -> list[dict]:
    out = []
    for e in events:
        status = e["status"]
        action = e["action"]
        if rng.random() < epsilon:
            if rng.random() < 0.7:
                candidates = [a for a in action_vocab if a != action]
                if candidates:
                    action = rng.choice(candidates)
            else:
                status = "finished" if status == "started" else "started"
        out.append({"status": status, "action": action})
    return out


def simulate_chain(
    gt_events: list[dict],
    noisy_events: list[dict],
    *,
    use_rules: bool,
    mismatch_rate_threshold: float,
) -> RunResult:
    stack: list[str] = []
    mismatch_count = 0
    repaired_events = 0

    def fail(idx: int, reason: str) -> RunResult:
        return RunResult(
            success=False,
            fail_step_idx=idx,
            fail_reason=reason,
            mismatch_count=mismatch_count,
            total_events=len(gt_events),
            repaired_events=repaired_events,
        )

    for idx, (gt, obs_in) in enumerate(zip(gt_events, noisy_events)):
        obs = {"status": obs_in["status"], "action": obs_in["action"]}

        if use_rules:
            # Minimal rule set: enforce stack-consistent finishes and avoid underflow.
            if obs["status"] not in VALID_STATUS:
                obs["status"] = gt["status"]
                repaired_events += 1

            if obs["status"] == "finished":
                if stack and stack[-1] == obs["action"]:
                    pass
                elif stack:
                    # Project mismatched finish to the currently open action to prevent cascade.
                    obs["action"] = stack[-1]
                    repaired_events += 1
                else:
                    # Prevent underflow by converting illegal finish into a start.
                    obs["status"] = "started"
                    repaired_events += 1
            elif obs["status"] == "started":
                pass
        else:
            if obs["status"] not in VALID_STATUS:
                return fail(idx, "invalid_status")

        # Execute event against symbolic stack.
        if obs["status"] == "started":
            stack.append(obs["action"])
        else:  # finished
            if not stack:
                return fail(idx, "stack_underflow")
            if stack[-1] != obs["action"]:
                return fail(idx, "finish_mismatch")
            stack.pop()

        if obs["status"] != gt["status"] or obs["action"] != gt["action"]:
            mismatch_count += 1

        mismatch_rate = mismatch_count / (idx + 1)
        if mismatch_rate > mismatch_rate_threshold:
            return fail(idx, "mismatch_rate_threshold")

    if stack:
        return fail(len(gt_events) - 1, "non_empty_stack_at_end")

    return RunResult(
        success=True,
        fail_step_idx=None,
        fail_reason=None,
        mismatch_count=mismatch_count,
        total_events=len(gt_events),
        repaired_events=repaired_events,
    )


def estimate_threshold(rows: list[dict], *, success_key: str, eps_key: str) -> float | None:
    # first epsilon where success < 0.5
    ordered = sorted(rows, key=lambda r: float(r[eps_key]))
    for r in ordered:
        if float(r[success_key]) < 0.5:
            return float(r[eps_key])
    return None


def maybe_plot(curve_rows: list[dict], out_dir: Path) -> list[str]:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return []

    out_files: list[str] = []
    labels = ["low", "medium", "high"]
    modes = [("no_rules", "No Rules"), ("with_rules", "With Rules")]

    # Plot 1: success rate vs epsilon
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, (mode_key, mode_title) in zip(axes, modes):
        for label in labels:
            rows = [r for r in curve_rows if r["rule_mode"] == mode_key and r["complexity_label"] == label]
            rows = sorted(rows, key=lambda r: float(r["epsilon"]))
            ax.plot(
                [float(r["epsilon"]) for r in rows],
                [float(r["success_rate"]) for r in rows],
                marker="o",
                label=label,
            )
        ax.set_title(mode_title)
        ax.set_xlabel("epsilon (error injection rate)")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("success rate")
    axes[1].legend()
    fig.tight_layout()
    p1 = out_dir / "h3_h2_success_rate_vs_epsilon.png"
    fig.savefig(p1, dpi=160)
    plt.close(fig)
    out_files.append(str(p1))

    # Plot 2: mean fail-step ratio vs epsilon (1.0 means survive full chain)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, (mode_key, mode_title) in zip(axes, modes):
        for label in labels:
            rows = [r for r in curve_rows if r["rule_mode"] == mode_key and r["complexity_label"] == label]
            rows = sorted(rows, key=lambda r: float(r["epsilon"]))
            ax.plot(
                [float(r["epsilon"]) for r in rows],
                [float(r["mean_fail_step_ratio"]) for r in rows],
                marker="o",
                label=label,
            )
        ax.set_title(mode_title)
        ax.set_xlabel("epsilon (error injection rate)")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("mean fail-step ratio")
    axes[1].legend()
    fig.tight_layout()
    p2 = out_dir / "h3_h2_fail_step_ratio_vs_epsilon.png"
    fig.savefig(p2, dpi=160)
    plt.close(fig)
    out_files.append(str(p2))

    return out_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Run H2/H3 mechanism proxy experiment (error injection + rule suppression)")
    parser.add_argument(
        "--samples-csv",
        type=Path,
        default=Path("evidence/videocad/notes/cad_action_multimodal_samples.csv"),
    )
    parser.add_argument("--per-label", type=int, default=30, help="Chains per complexity label from random_stratified_overlap")
    parser.add_argument("--replicates", type=int, default=40)
    parser.add_argument("--eps-start", type=float, default=0.0)
    parser.add_argument("--eps-stop", type=float, default=0.20)
    parser.add_argument("--eps-step", type=float, default=0.02)
    parser.add_argument("--mismatch-threshold", type=float, default=0.12)
    parser.add_argument("--seed", type=int, default=20260226)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("evidence/videocad/notes/h2_h3_proxy_experiment"),
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    selected_rows = load_selected_chains(args.samples_csv, args.per_label)
    chains = []
    action_vocab_set = set()
    for row in selected_rows:
        p = Path(row["action_json_path"])
        events = load_events(p)
        for e in events:
            action_vocab_set.add(e["action"])
        chains.append(
            {
                "sample_id": row["sample_id"],
                "complexity_label": row["complexity_label"],
                "event_count": len(events),
                "events": events,
            }
        )

    action_vocab = sorted(action_vocab_set)
    eps_values = []
    e = args.eps_start
    while e <= args.eps_stop + 1e-9:
        eps_values.append(round(e, 6))
        e += args.eps_step

    rng_master = random.Random(args.seed)
    curve_acc = defaultdict(lambda: {"n_runs": 0, "success": 0, "fail_step_ratio_sum": 0.0, "repaired_sum": 0, "mismatch_rate_sum": 0.0})
    per_run_rows = []
    fail_reason_counter = Counter()

    for epsilon in eps_values:
        for chain in chains:
            for rep in range(args.replicates):
                rep_seed = rng_master.randint(0, 2**31 - 1)
                rng = random.Random(rep_seed)
                noisy = perturb_events(chain["events"], epsilon, rng, action_vocab)

                for rule_mode in ("no_rules", "with_rules"):
                    result = simulate_chain(
                        chain["events"],
                        noisy,
                        use_rules=(rule_mode == "with_rules"),
                        mismatch_rate_threshold=args.mismatch_threshold,
                    )

                    fail_idx = result.fail_step_idx if result.fail_step_idx is not None else (result.total_events - 1)
                    fail_step_ratio = (fail_idx + 1) / result.total_events if result.total_events else 0.0
                    mismatch_rate = (result.mismatch_count / result.total_events) if result.total_events else 0.0

                    k = (chain["complexity_label"], rule_mode, epsilon)
                    acc = curve_acc[k]
                    acc["n_runs"] += 1
                    acc["success"] += 1 if result.success else 0
                    acc["fail_step_ratio_sum"] += fail_step_ratio
                    acc["repaired_sum"] += result.repaired_events
                    acc["mismatch_rate_sum"] += mismatch_rate
                    if result.fail_reason:
                        fail_reason_counter[(chain["complexity_label"], rule_mode, result.fail_reason)] += 1

                    per_run_rows.append(
                        {
                            "sample_id": chain["sample_id"],
                            "complexity_label": chain["complexity_label"],
                            "rule_mode": rule_mode,
                            "epsilon": epsilon,
                            "replicate": rep,
                            "success": int(result.success),
                            "fail_step_idx": result.fail_step_idx if result.fail_step_idx is not None else "",
                            "fail_reason": result.fail_reason or "",
                            "fail_step_ratio": round(fail_step_ratio, 6),
                            "mismatch_count": result.mismatch_count,
                            "mismatch_rate": round(mismatch_rate, 6),
                            "repaired_events": result.repaired_events,
                            "event_count": result.total_events,
                        }
                    )

    curve_rows = []
    for (label, rule_mode, epsilon), acc in sorted(curve_acc.items(), key=lambda x: (x[0][1], x[0][0], x[0][2])):
        n = acc["n_runs"]
        curve_rows.append(
            {
                "complexity_label": label,
                "rule_mode": rule_mode,
                "epsilon": epsilon,
                "n_runs": n,
                "success_rate": round(acc["success"] / n, 6),
                "mean_fail_step_ratio": round(acc["fail_step_ratio_sum"] / n, 6),
                "mean_mismatch_rate": round(acc["mismatch_rate_sum"] / n, 6),
                "mean_repaired_events": round(acc["repaired_sum"] / n, 6),
            }
        )

    curve_csv = out_dir / "curve_summary.csv"
    with curve_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(curve_rows[0].keys()))
        writer.writeheader()
        writer.writerows(curve_rows)

    per_run_csv = out_dir / "per_run_results.csv"
    with per_run_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(per_run_rows[0].keys()))
        writer.writeheader()
        writer.writerows(per_run_rows)

    threshold_summary = {}
    for rule_mode in ("no_rules", "with_rules"):
        threshold_summary[rule_mode] = {}
        for label in ("low", "medium", "high"):
            subset = [r for r in curve_rows if r["rule_mode"] == rule_mode and r["complexity_label"] == label]
            threshold_summary[rule_mode][label] = {
                "epsilon_star_success_lt_0_5": estimate_threshold(subset, success_key="success_rate", eps_key="epsilon")
            }

    fail_reason_summary = defaultdict(Counter)
    for (label, rule_mode, reason), count in fail_reason_counter.items():
        fail_reason_summary[(label, rule_mode)][reason] += count

    plots = maybe_plot(curve_rows, out_dir)

    summary = {
        "experiment": "H2/H3 mechanism proxy (symbolic chain error injection + rule suppression)",
        "design_notes": {
            "proxy_level": "event-level symbolic action chain (no GUI bounding boxes yet)",
            "epsilon_definition": "per-event corruption probability",
            "corruption_types": {"action_swap": 0.7, "status_flip": 0.3},
            "success_definition": "syntactically valid chain completed and cumulative mismatch-rate <= threshold",
            "rule_mode_with_rules": [
                "enforce stack-consistent finish actions",
                "convert underflow finish to started to avoid illegal close",
            ],
            "mismatch_rate_threshold": args.mismatch_threshold,
        },
        "inputs": {
            "samples_csv": str(args.samples_csv),
            "selected_per_label": args.per_label,
            "selected_chain_count": len(chains),
            "replicates_per_chain_per_epsilon": args.replicates,
            "epsilon_values": eps_values,
            "seed": args.seed,
            "action_vocab": action_vocab,
        },
        "selected_chain_distribution": dict(Counter(c["complexity_label"] for c in chains)),
        "selected_chain_event_count_stats": {
            "min": min(c["event_count"] for c in chains),
            "max": max(c["event_count"] for c in chains),
            "mean": round(sum(c["event_count"] for c in chains) / len(chains), 4),
        },
        "threshold_summary": threshold_summary,
        "fail_reason_summary": {
            f"{label}|{rule_mode}": dict(counter)
            for (label, rule_mode), counter in fail_reason_summary.items()
        },
        "outputs": {
            "curve_summary_csv": str(curve_csv),
            "per_run_results_csv": str(per_run_csv),
            "plots": plots,
        },
    }

    summary_json = out_dir / "summary.json"
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote: {curve_csv}")
    print(f"Wrote: {per_run_csv}")
    print(f"Wrote: {summary_json}")
    if plots:
        print("Plots:")
        for p in plots:
            print(f"  {p}")


if __name__ == "__main__":
    main()

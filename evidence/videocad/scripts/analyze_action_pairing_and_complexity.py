#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median


def percentile(sorted_values: list[float], p: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (len(sorted_values) - 1) * p
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return float(sorted_values[lo])
    frac = rank - lo
    return float(sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac)


def summarize_num(values: list[float]) -> dict:
    if not values:
        return {}
    s = sorted(values)
    return {
        "count": len(values),
        "min": s[0],
        "max": s[-1],
        "mean": round(float(mean(values)), 4),
        "median": round(float(median(values)), 4),
        "p90": round(float(percentile(s, 0.90) or 0.0), 4),
        "p95": round(float(percentile(s, 0.95) or 0.0), 4),
        "p99": round(float(percentile(s, 0.99) or 0.0), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pair started/finished actions and compute complexity metrics for VideoCAD action_json"
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing action_json/*.json")
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("evidence/videocad/notes/action_json_pairing_summary.json"),
    )
    parser.add_argument(
        "--top-files-output",
        type=Path,
        default=Path("evidence/videocad/notes/action_json_top_complex_files.csv"),
    )
    parser.add_argument("--top-n", type=int, default=100)
    args = parser.parse_args()

    files = sorted(args.input_dir.glob("*.json"))

    # Global aggregates
    file_count = 0
    invalid_files: list[str] = []
    files_with_pairing_issues = 0
    files_with_strict_nesting_mismatch = 0
    files_with_non_monotonic_ts = 0

    global_action_started = Counter()
    global_action_finished = Counter()
    pair_count_by_action = Counter()
    pair_duration_ms_by_action: dict[str, list[float]] = defaultdict(list)

    unmatched_start_by_action = Counter()
    unmatched_finish_by_action = Counter()

    strict_mismatch_total = 0
    strict_underflow_total = 0
    loose_negative_duration_pairs = 0

    per_file_event_counts: list[float] = []
    per_file_pair_counts: list[float] = []
    per_file_unique_actions: list[float] = []
    per_file_span_ms: list[float] = []
    per_file_max_nesting_depth: list[float] = []
    per_file_pairing_completion_rate: list[float] = []

    issue_examples: list[dict] = []
    file_metric_rows: list[dict] = []

    for fp in files:
        file_count += 1
        try:
            events = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            invalid_files.append(f"{fp.name}: {exc}")
            continue

        if not isinstance(events, list):
            invalid_files.append(f"{fp.name}: root_not_list")
            continue

        action_stacks: dict[str, list[float]] = defaultdict(list)
        strict_stack: list[str] = []

        file_started = Counter()
        file_finished = Counter()
        file_pair_count = 0
        file_unmatched_finish = Counter()
        file_pairing_issue = False
        file_strict_mismatch = False
        file_strict_mismatch_count = 0
        file_strict_underflow_count = 0
        file_non_monotonic_ts = False
        file_max_depth = 0
        ts_values: list[float] = []
        prev_ts = None
        unique_actions = set()

        for idx, event in enumerate(events):
            if not isinstance(event, dict):
                file_pairing_issue = True
                if len(issue_examples) < 12:
                    issue_examples.append(
                        {
                            "file": fp.name,
                            "event_index": idx,
                            "issue": "non_dict_event",
                            "value_type": type(event).__name__,
                        }
                    )
                continue

            action = event.get("action")
            status = event.get("status")
            ts = event.get("timestamp")

            if isinstance(ts, (int, float)):
                tsf = float(ts)
                ts_values.append(tsf)
                if prev_ts is not None and tsf < prev_ts:
                    file_non_monotonic_ts = True
                prev_ts = tsf
            else:
                tsf = None

            if not isinstance(action, str) or not isinstance(status, str):
                file_pairing_issue = True
                if len(issue_examples) < 12:
                    issue_examples.append(
                        {
                            "file": fp.name,
                            "event_index": idx,
                            "issue": "missing_action_or_status",
                            "event": event,
                        }
                    )
                continue

            unique_actions.add(action)
            if status == "started":
                file_started[action] += 1
                global_action_started[action] += 1

                if tsf is not None:
                    action_stacks[action].append(tsf)
                else:
                    action_stacks[action].append(float("nan"))

                strict_stack.append(action)
                file_max_depth = max(file_max_depth, len(strict_stack))

            elif status == "finished":
                file_finished[action] += 1
                global_action_finished[action] += 1

                if action_stacks[action]:
                    start_ts = action_stacks[action].pop()
                    if tsf is not None and not math.isnan(start_ts):
                        duration = tsf - start_ts
                        if duration < 0:
                            loose_negative_duration_pairs += 1
                            file_pairing_issue = True
                        else:
                            pair_duration_ms_by_action[action].append(duration)
                        pair_count_by_action[action] += 1
                        file_pair_count += 1
                    else:
                        pair_count_by_action[action] += 1
                        file_pair_count += 1
                else:
                    file_unmatched_finish[action] += 1
                    unmatched_finish_by_action[action] += 1
                    file_pairing_issue = True

                if not strict_stack:
                    strict_underflow_total += 1
                    file_strict_underflow_count += 1
                    file_strict_mismatch = True
                elif strict_stack[-1] == action:
                    strict_stack.pop()
                else:
                    strict_mismatch_total += 1
                    file_strict_mismatch_count += 1
                    file_strict_mismatch = True
                    # Self-heal to continue depth tracking and avoid cascade noise.
                    try:
                        reverse_idx = strict_stack[::-1].index(action)
                    except ValueError:
                        strict_underflow_total += 1
                        file_strict_underflow_count += 1
                    else:
                        idx_from_start = len(strict_stack) - 1 - reverse_idx
                        strict_stack.pop(idx_from_start)
            else:
                file_pairing_issue = True
                if len(issue_examples) < 12:
                    issue_examples.append(
                        {
                            "file": fp.name,
                            "event_index": idx,
                            "issue": "unknown_status",
                            "status": status,
                            "action": action,
                        }
                    )

        # Remaining starts are unmatched starts
        file_unmatched_start = Counter()
        for action, stack in action_stacks.items():
            if stack:
                file_unmatched_start[action] += len(stack)
                unmatched_start_by_action[action] += len(stack)
                file_pairing_issue = True

        if strict_stack:
            # Residual opens already counted as unmatched starts above; mark strict mismatch for reporting.
            file_strict_mismatch = True

        if file_pairing_issue:
            files_with_pairing_issues += 1
        if file_strict_mismatch:
            files_with_strict_nesting_mismatch += 1
        if file_non_monotonic_ts:
            files_with_non_monotonic_ts += 1

        event_count = len(events)
        span_ms = max(ts_values) - min(ts_values) if ts_values else 0.0
        started_total = sum(file_started.values())
        finished_total = sum(file_finished.values())
        pairable_upper_bound = min(started_total, finished_total) if (started_total or finished_total) else 0
        completion_rate = (file_pair_count / pairable_upper_bound) if pairable_upper_bound else 1.0

        per_file_event_counts.append(float(event_count))
        per_file_pair_counts.append(float(file_pair_count))
        per_file_unique_actions.append(float(len(unique_actions)))
        per_file_span_ms.append(float(span_ms))
        per_file_max_nesting_depth.append(float(file_max_depth))
        per_file_pairing_completion_rate.append(float(completion_rate))

        row = {
            "file": fp.name,
            "event_count": event_count,
            "pair_count": file_pair_count,
            "unique_action_count": len(unique_actions),
            "span_ms": round(float(span_ms), 4),
            "max_nesting_depth": file_max_depth,
            "started_total": started_total,
            "finished_total": finished_total,
            "unmatched_start_total": sum(file_unmatched_start.values()),
            "unmatched_finish_total": sum(file_unmatched_finish.values()),
            "strict_mismatch_count": file_strict_mismatch_count,
            "strict_underflow_count": file_strict_underflow_count,
            "pairing_completion_rate": round(float(completion_rate), 6),
            "has_pairing_issue": int(file_pairing_issue),
        }
        file_metric_rows.append(row)

        if file_pairing_issue and len(issue_examples) < 12:
            issue_examples.append(
                {
                    "file": fp.name,
                    "issue": "file_pairing_issue_summary",
                    "unmatched_start_total": row["unmatched_start_total"],
                    "unmatched_finish_total": row["unmatched_finish_total"],
                    "strict_mismatch_count": file_strict_mismatch_count,
                    "strict_underflow_count": file_strict_underflow_count,
                }
            )

    action_duration_stats = {}
    total_paired_actions = 0
    total_duration_ms = 0.0
    for action, durations in sorted(pair_duration_ms_by_action.items()):
        total_paired_actions += len(durations)
        total_duration_ms += sum(durations)
        action_duration_stats[action] = summarize_num(durations)

    # Sort "complex" files by size/depth/span.
    file_metric_rows_sorted = sorted(
        file_metric_rows,
        key=lambda r: (
            r["event_count"],
            r["max_nesting_depth"],
            r["unique_action_count"],
            r["span_ms"],
        ),
        reverse=True,
    )
    top_rows = file_metric_rows_sorted[: args.top_n]

    args.top_files_output.parent.mkdir(parents=True, exist_ok=True)
    with args.top_files_output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(top_rows[0].keys()) if top_rows else ["file"])
        writer.writeheader()
        if top_rows:
            writer.writerows(top_rows)

    summary = {
        "input_dir": str(args.input_dir),
        "file_count": file_count,
        "invalid_files": invalid_files,
        "files_with_pairing_issues": files_with_pairing_issues,
        "files_with_strict_nesting_mismatch": files_with_strict_nesting_mismatch,
        "files_with_non_monotonic_ts": files_with_non_monotonic_ts,
        "strict_mismatch_total": strict_mismatch_total,
        "strict_underflow_total": strict_underflow_total,
        "loose_negative_duration_pairs": loose_negative_duration_pairs,
        "global_action_started": dict(global_action_started.most_common()),
        "global_action_finished": dict(global_action_finished.most_common()),
        "pair_count_by_action": dict(pair_count_by_action.most_common()),
        "unmatched_start_by_action": dict(unmatched_start_by_action.most_common()),
        "unmatched_finish_by_action": dict(unmatched_finish_by_action.most_common()),
        "action_duration_ms_stats": action_duration_stats,
        "total_paired_actions_with_duration": total_paired_actions,
        "mean_paired_action_duration_ms_overall": round(
            (total_duration_ms / total_paired_actions) if total_paired_actions else 0.0, 4
        ),
        "per_file_event_count_stats": summarize_num(per_file_event_counts),
        "per_file_pair_count_stats": summarize_num(per_file_pair_counts),
        "per_file_unique_action_count_stats": summarize_num(per_file_unique_actions),
        "per_file_span_ms_stats": summarize_num(per_file_span_ms),
        "per_file_max_nesting_depth_stats": summarize_num(per_file_max_nesting_depth),
        "per_file_pairing_completion_rate_stats": summarize_num(per_file_pairing_completion_rate),
        "issue_examples": issue_examples,
        "top_complex_files_csv": str(args.top_files_output),
        "top_n": args.top_n,
    }

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote summary: {args.summary_output}")
    print(f"Wrote top files CSV: {args.top_files_output}")
    print(
        "files=%d pairing_issue_files=%d strict_mismatch_files=%d paired_actions=%d"
        % (
            summary["file_count"],
            summary["files_with_pairing_issues"],
            summary["files_with_strict_nesting_mismatch"],
            summary["total_paired_actions_with_duration"],
        )
    )


if __name__ == "__main__":
    main()

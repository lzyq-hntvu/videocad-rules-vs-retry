#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, median


def percentile(sorted_values: list[int | float], p: float) -> float | None:
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


def summarize_numeric(values: list[int | float]) -> dict:
    if not values:
        return {}
    sorted_values = sorted(values)
    return {
        "count": len(values),
        "min": sorted_values[0],
        "max": sorted_values[-1],
        "mean": round(mean(values), 4),
        "median": round(float(median(values)), 4),
        "p50": round(percentile(sorted_values, 0.50) or 0.0, 4),
        "p90": round(percentile(sorted_values, 0.90) or 0.0, 4),
        "p95": round(percentile(sorted_values, 0.95) or 0.0, 4),
        "p99": round(percentile(sorted_values, 0.99) or 0.0, 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect VideoCAD action_json files")
    parser.add_argument("input_dir", type=Path, help="Directory containing action_json/*.json")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/videocad/notes/action_json_summary.json"),
        help="Output JSON summary path",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=30,
        help="Top-k action labels to keep",
    )
    args = parser.parse_args()

    json_files = sorted(args.input_dir.glob("*.json"))

    key_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    action_counter: Counter[str] = Counter()
    action_status_counter: Counter[str] = Counter()
    per_file_event_counts: list[int] = []
    per_file_duration_ms: list[float] = []
    invalid_files: list[str] = []
    non_list_files: list[str] = []
    empty_files: list[str] = []
    monotonic_violation_files: list[str] = []
    missing_key_examples: list[dict] = []
    file_examples: list[dict] = []

    total_events = 0
    files_with_non_dict_event = 0

    for idx, fp in enumerate(json_files):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            invalid_files.append(f"{fp.name}: {exc}")
            continue

        if not isinstance(data, list):
            non_list_files.append(fp.name)
            continue

        if not data:
            empty_files.append(fp.name)
            per_file_event_counts.append(0)
            continue

        timestamps: list[float] = []
        prev_ts = None
        monotonic_violation = False
        bad_event_in_file = False

        for event_i, event in enumerate(data):
            if not isinstance(event, dict):
                bad_event_in_file = True
                continue

            total_events += 1
            key_counter.update(event.keys())

            ts = event.get("timestamp")
            if isinstance(ts, (int, float)):
                timestamps.append(float(ts))
                if prev_ts is not None and ts < prev_ts:
                    monotonic_violation = True
                prev_ts = float(ts)

            status = event.get("status")
            if isinstance(status, str):
                status_counter[status] += 1

            action = event.get("action")
            if isinstance(action, str):
                action_counter[action] += 1

            if isinstance(status, str) and isinstance(action, str):
                action_status_counter[f"{status} | {action}"] += 1

            if len(missing_key_examples) < 10:
                missing = [k for k in ("timestamp", "status", "action") if k not in event]
                if missing:
                    missing_key_examples.append(
                        {"file": fp.name, "event_index": event_i, "missing_keys": missing}
                    )

        if bad_event_in_file:
            files_with_non_dict_event += 1

        if monotonic_violation:
            monotonic_violation_files.append(fp.name)

        per_file_event_counts.append(len(data))
        if timestamps:
            per_file_duration_ms.append(max(timestamps) - min(timestamps))

        if len(file_examples) < 5:
            file_examples.append(
                {
                    "file": fp.name,
                    "event_count": len(data),
                    "first_event": data[0] if isinstance(data[0], dict) else type(data[0]).__name__,
                    "last_event": data[-1] if isinstance(data[-1], dict) else type(data[-1]).__name__,
                }
            )

    summary = {
        "input_dir": str(args.input_dir),
        "file_count": len(json_files),
        "total_events": total_events,
        "invalid_files": invalid_files,
        "non_list_files": non_list_files,
        "empty_files_count": len(empty_files),
        "empty_files_examples": empty_files[:10],
        "files_with_non_dict_event": files_with_non_dict_event,
        "monotonic_timestamp_violation_count": len(monotonic_violation_files),
        "monotonic_timestamp_violation_examples": monotonic_violation_files[:10],
        "missing_key_examples": missing_key_examples,
        "per_file_event_count_stats": summarize_numeric(per_file_event_counts),
        "per_file_duration_ms_stats": summarize_numeric(per_file_duration_ms),
        "event_keys_frequency": dict(key_counter.most_common()),
        "status_distribution": dict(status_counter.most_common()),
        "status_unique_count": len(status_counter),
        "action_unique_count": len(action_counter),
        "top_actions": dict(action_counter.most_common(args.top_k)),
        "top_action_status_pairs": dict(action_status_counter.most_common(args.top_k)),
        "sample_files": file_examples,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote summary to {args.output}")
    print(f"Files: {summary['file_count']}, events: {summary['total_events']}")


if __name__ == "__main__":
    main()

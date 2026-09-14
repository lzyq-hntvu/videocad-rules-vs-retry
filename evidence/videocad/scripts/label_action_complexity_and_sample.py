#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter
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


def summarize(values: list[float]) -> dict:
    if not values:
        return {}
    s = sorted(values)
    return {
        "count": len(values),
        "min": s[0],
        "max": s[-1],
        "mean": round(float(mean(values)), 4),
        "median": round(float(median(values)), 4),
        "p33": round(float(percentile(s, 0.33) or 0.0), 4),
        "p50": round(float(percentile(s, 0.50) or 0.0), 4),
        "p67": round(float(percentile(s, 0.67) or 0.0), 4),
        "p90": round(float(percentile(s, 0.90) or 0.0), 4),
        "p95": round(float(percentile(s, 0.95) or 0.0), 4),
        "p99": round(float(percentile(s, 0.99) or 0.0), 4),
    }


def minmax_norm(x: float, x_min: float, x_max: float) -> float:
    if x_max <= x_min:
        return 0.0
    return (x - x_min) / (x_max - x_min)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build file-level complexity labels and sample sets for VideoCAD action_json"
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing action_json/*.json")
    parser.add_argument(
        "--metrics-csv",
        type=Path,
        default=Path("evidence/videocad/notes/action_json_file_complexity_metrics.csv"),
    )
    parser.add_argument(
        "--samples-csv",
        type=Path,
        default=Path("evidence/videocad/notes/action_json_complexity_samples.csv"),
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=Path("evidence/videocad/notes/action_json_complexity_label_summary.json"),
    )
    parser.add_argument(
        "--sample-per-label",
        type=int,
        default=40,
        help="Random sample size per label (low/medium/high)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260226,
    )
    args = parser.parse_args()

    json_files = sorted(args.input_dir.glob("*.json"))
    rows: list[dict] = []
    invalid_files: list[str] = []

    for fp in json_files:
        try:
            events = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            invalid_files.append(f"{fp.name}: {exc}")
            continue
        if not isinstance(events, list):
            invalid_files.append(f"{fp.name}: root_not_list")
            continue

        ts_values: list[float] = []
        unique_actions = set()
        status_counter = Counter()
        action_counter = Counter()

        for event in events:
            if not isinstance(event, dict):
                continue
            ts = event.get("timestamp")
            st = event.get("status")
            act = event.get("action")
            if isinstance(ts, (int, float)):
                ts_values.append(float(ts))
            if isinstance(st, str):
                status_counter[st] += 1
            if isinstance(act, str):
                unique_actions.add(act)
                action_counter[act] += 1

        span_ms = (max(ts_values) - min(ts_values)) if ts_values else 0.0
        pair_count = status_counter.get("started", 0)
        event_count = len(events)
        extrusion_pairs = action_counter.get("Performing Extrusion", 0) / 2
        line_pairs = action_counter.get("Drawing Line", 0) / 2
        sketch_pairs = action_counter.get("Drawing Sketch", 0) / 2
        curve_pairs = action_counter.get("Drawing Curve", 0) / 2

        rows.append(
            {
                "file": fp.name,
                "event_count": event_count,
                "pair_count": pair_count,
                "unique_action_count": len(unique_actions),
                "span_ms": round(float(span_ms), 4),
                "extrusion_pair_count": int(extrusion_pairs),
                "line_pair_count": int(line_pairs),
                "sketch_pair_count": int(sketch_pairs),
                "curve_pair_count": int(curve_pairs),
            }
        )

    if not rows:
        raise SystemExit("No valid rows parsed")

    pair_vals = [float(r["pair_count"]) for r in rows]
    span_vals = [float(r["span_ms"]) for r in rows]
    unique_vals = [float(r["unique_action_count"]) for r in rows]
    extrude_vals = [float(r["extrusion_pair_count"]) for r in rows]

    pair_min, pair_max = min(pair_vals), max(pair_vals)
    span_min, span_max = min(span_vals), max(span_vals)
    uniq_min, uniq_max = min(unique_vals), max(unique_vals)
    ext_min, ext_max = min(extrude_vals), max(extrude_vals)

    for r in rows:
        n_pair = minmax_norm(float(r["pair_count"]), pair_min, pair_max)
        n_span = minmax_norm(float(r["span_ms"]), span_min, span_max)
        n_uniq = minmax_norm(float(r["unique_action_count"]), uniq_min, uniq_max)
        n_ext = minmax_norm(float(r["extrusion_pair_count"]), ext_min, ext_max)
        # Pair count and span dominate. Unique actions and extrusion count help separate same-length sequences.
        score = 0.40 * n_pair + 0.35 * n_span + 0.15 * n_uniq + 0.10 * n_ext
        r["complexity_score"] = round(score, 6)

    sorted_scores = sorted(float(r["complexity_score"]) for r in rows)
    q33 = float(percentile(sorted_scores, 0.33) or 0.0)
    q67 = float(percentile(sorted_scores, 0.67) or 0.0)

    label_counts = Counter()
    for r in rows:
        s = float(r["complexity_score"])
        if s <= q33:
            label = "low"
        elif s <= q67:
            label = "medium"
        else:
            label = "high"
        r["complexity_label"] = label
        label_counts[label] += 1

    rows_sorted = sorted(
        rows,
        key=lambda r: (
            float(r["complexity_score"]),
            int(r["pair_count"]),
            float(r["span_ms"]),
            int(r["unique_action_count"]),
        ),
        reverse=True,
    )

    args.metrics_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.metrics_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_sorted[0].keys()))
        writer.writeheader()
        writer.writerows(rows_sorted)

    rng = random.Random(args.seed)
    by_label: dict[str, list[dict]] = {"low": [], "medium": [], "high": []}
    for r in rows_sorted:
        by_label[r["complexity_label"]].append(r)

    sample_rows: list[dict] = []
    for label in ("low", "medium", "high"):
        label_rows = by_label[label]
        sample_n = min(args.sample_per_label, len(label_rows))
        chosen = rng.sample(label_rows, sample_n) if sample_n else []
        chosen_sorted = sorted(chosen, key=lambda r: (r["file"]))
        for r in chosen_sorted:
            sample_rows.append(
                {
                    "sample_group": "random_stratified",
                    "complexity_label": label,
                    **r,
                }
            )

    # Add deterministic "extremes" for reviewable mini-benchmark construction.
    for label in ("high", "medium", "low"):
        for r in by_label[label][:10]:
            sample_rows.append(
                {
                    "sample_group": f"top10_by_score_{label}",
                    "complexity_label": label,
                    **r,
                }
            )

    sample_fieldnames = list(sample_rows[0].keys()) if sample_rows else [
        "sample_group",
        "complexity_label",
        "file",
    ]
    with args.samples_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sample_fieldnames)
        writer.writeheader()
        writer.writerows(sample_rows)

    summary = {
        "input_dir": str(args.input_dir),
        "file_count": len(rows),
        "invalid_files": invalid_files,
        "label_definition": {
            "score_formula": "0.40*norm(pair_count)+0.35*norm(span_ms)+0.15*norm(unique_action_count)+0.10*norm(extrusion_pair_count)",
            "thresholds": {"low_max_q33": round(q33, 6), "medium_max_q67": round(q67, 6)},
            "tertiles_based_on": "complexity_score",
        },
        "label_counts": dict(label_counts),
        "metrics_stats": {
            "event_count": summarize([float(r["event_count"]) for r in rows]),
            "pair_count": summarize([float(r["pair_count"]) for r in rows]),
            "unique_action_count": summarize([float(r["unique_action_count"]) for r in rows]),
            "span_ms": summarize([float(r["span_ms"]) for r in rows]),
            "extrusion_pair_count": summarize([float(r["extrusion_pair_count"]) for r in rows]),
            "complexity_score": summarize([float(r["complexity_score"]) for r in rows]),
        },
        "sample_output": {
            "sample_per_label_random": args.sample_per_label,
            "random_seed": args.seed,
            "samples_csv": str(args.samples_csv),
            "total_sample_rows": len(sample_rows),
        },
        "top10_high_examples": by_label["high"][:10],
        "top10_low_examples": list(reversed(by_label["low"][-10:])),
    }

    args.summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote metrics CSV: {args.metrics_csv}")
    print(f"Wrote samples CSV: {args.samples_csv}")
    print(f"Wrote summary JSON: {args.summary_json}")
    print(f"files={len(rows)} labels={dict(label_counts)} sample_rows={len(sample_rows)}")


if __name__ == "__main__":
    main()

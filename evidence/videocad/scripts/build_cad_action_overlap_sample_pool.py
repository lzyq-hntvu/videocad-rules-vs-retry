#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path


def parse_paths(raw: str) -> list[str]:
    if not raw:
        return []
    return [p.strip() for p in raw.split("|") if p.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build multimodal (CAD image + action_json) sample pool from overlap IDs"
    )
    parser.add_argument(
        "--overlap-csv",
        type=Path,
        default=Path("evidence/videocad/notes/cad_action_overlap_samples.csv"),
    )
    parser.add_argument(
        "--complexity-csv",
        type=Path,
        default=Path("evidence/videocad/notes/action_json_file_complexity_metrics.csv"),
    )
    parser.add_argument(
        "--action-dir",
        type=Path,
        default=Path("evidence/videocad/samples/dataverse/action_json_unpacked/action_json"),
    )
    parser.add_argument(
        "--merged-csv",
        type=Path,
        default=Path("evidence/videocad/notes/cad_action_overlap_enriched.csv"),
    )
    parser.add_argument(
        "--samples-csv",
        type=Path,
        default=Path("evidence/videocad/notes/cad_action_multimodal_samples.csv"),
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=Path("evidence/videocad/notes/cad_action_multimodal_sample_pool_summary.json"),
    )
    parser.add_argument("--sample-per-label", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260226)
    args = parser.parse_args()

    complexity_by_id: dict[str, dict] = {}
    with args.complexity_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            sample_id = row["file"].replace(".json", "")
            complexity_by_id[sample_id] = row

    overlap_rows_raw = []
    with args.overlap_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            overlap_rows_raw.append(row)

    merged_rows: list[dict] = []
    missing_complexity_ids: list[str] = []
    missing_action_file_ids: list[str] = []

    for row in overlap_rows_raw:
        sample_id = row["sample_id"]
        cx = complexity_by_id.get(sample_id)
        if not cx:
            missing_complexity_ids.append(sample_id)
            continue

        action_path = args.action_dir / f"{sample_id}.json"
        if not action_path.exists():
            missing_action_file_ids.append(sample_id)
            continue

        image_paths = parse_paths(row.get("example_image_paths", ""))
        view_indices = sorted(
            {
                p.rsplit("_", 1)[-1].replace(".png", "")
                for p in image_paths
                if "_" in p and p.endswith(".png")
            }
        )

        merged_rows.append(
            {
                "sample_id": sample_id,
                "action_json_file": cx["file"],
                "action_json_path": str(action_path),
                "image_count_in_cad": int(row["image_count_in_cad"]),
                "example_image_paths": " | ".join(image_paths),
                "example_view_indices": ",".join(view_indices),
                "event_count": int(cx["event_count"]),
                "pair_count": int(cx["pair_count"]),
                "unique_action_count": int(cx["unique_action_count"]),
                "span_ms": float(cx["span_ms"]),
                "extrusion_pair_count": int(cx["extrusion_pair_count"]),
                "complexity_score": float(cx["complexity_score"]),
                "complexity_label": cx["complexity_label"],
            }
        )

    merged_rows_sorted = sorted(
        merged_rows,
        key=lambda r: (r["complexity_score"], r["pair_count"], r["span_ms"]),
        reverse=True,
    )

    args.merged_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.merged_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(merged_rows_sorted[0].keys()))
        writer.writeheader()
        writer.writerows(merged_rows_sorted)

    by_label: dict[str, list[dict]] = {"low": [], "medium": [], "high": []}
    for r in merged_rows_sorted:
        by_label[r["complexity_label"]].append(r)

    rng = random.Random(args.seed)
    sample_rows: list[dict] = []
    for label in ("low", "medium", "high"):
        rows = by_label[label]
        n = min(args.sample_per_label, len(rows))
        chosen = rng.sample(rows, n) if n else []
        for r in sorted(chosen, key=lambda x: x["sample_id"]):
            sample_rows.append({"sample_group": "random_stratified_overlap", **r})

    for label in ("high", "medium", "low"):
        for r in by_label[label][:15]:
            sample_rows.append({"sample_group": f"top15_overlap_{label}", **r})

    with args.samples_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(sample_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_rows)

    label_counts = Counter(r["complexity_label"] for r in merged_rows)
    image_count_dist = Counter(int(r["image_count_in_cad"]) for r in merged_rows)
    view_token_counts = Counter(len([v for v in r["example_view_indices"].split(",") if v]) for r in merged_rows)

    summary = {
        "input_files": {
            "overlap_csv": str(args.overlap_csv),
            "complexity_csv": str(args.complexity_csv),
            "action_dir": str(args.action_dir),
        },
        "merged_row_count": len(merged_rows),
        "missing_complexity_ids_count": len(missing_complexity_ids),
        "missing_complexity_ids_examples": missing_complexity_ids[:20],
        "missing_action_file_ids_count": len(missing_action_file_ids),
        "missing_action_file_ids_examples": missing_action_file_ids[:20],
        "label_distribution_on_overlap_subset": dict(label_counts),
        "image_count_in_cad_distribution": dict(sorted(image_count_dist.items())),
        "example_view_count_distribution_from_csv": dict(sorted(view_token_counts.items())),
        "outputs": {
            "merged_csv": str(args.merged_csv),
            "samples_csv": str(args.samples_csv),
            "summary_json": str(args.summary_json),
            "sample_per_label_random": args.sample_per_label,
            "random_seed": args.seed,
            "sample_row_count": len(sample_rows),
        },
        "examples": {
            "top_high_first5": by_label["high"][:5],
            "top_low_first5": by_label["low"][:5],
        },
    }
    args.summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote merged CSV: {args.merged_csv}")
    print(f"Wrote samples CSV: {args.samples_csv}")
    print(f"Wrote summary JSON: {args.summary_json}")
    print(f"merged={len(merged_rows)} labels={dict(label_counts)} sample_rows={len(sample_rows)}")


if __name__ == "__main__":
    main()

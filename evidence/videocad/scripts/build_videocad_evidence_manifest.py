#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


KEY_FILES = [
    "evidence/videocad/logs/day1-连通与下载验证.md",
    "evidence/videocad/logs/day2-action_json下载与字段探查.md",
    "evidence/videocad/logs/day3-动作配对与复杂度指标.md",
    "evidence/videocad/logs/day4-复杂度标签与分层抽样.md",
    "evidence/videocad/logs/day5-cad_imgs结构与映射探查.md",
    "evidence/videocad/logs/day6-联动样本池与脚本线索.md",
    "evidence/videocad/notes/action_json_summary.json",
    "evidence/videocad/notes/action_json_pairing_summary.json",
    "evidence/videocad/notes/action_json_complexity_label_summary.json",
    "evidence/videocad/notes/cad_imgs_mapping_probe_summary.json",
    "evidence/videocad/notes/cad_action_multimodal_sample_pool_summary.json",
    "evidence/videocad/notes/action_json_file_complexity_metrics.csv",
    "evidence/videocad/notes/action_json_complexity_samples.csv",
    "evidence/videocad/notes/cad_action_overlap_samples.csv",
    "evidence/videocad/notes/cad_action_overlap_enriched.csv",
    "evidence/videocad/notes/cad_action_multimodal_samples.csv",
    "evidence/videocad/samples/dataverse/action_json.zip",
    "evidence/videocad/samples/dataverse/cad_imgs.zip",
    "evidence/videocad/samples/dataverse/qa.json",
    "evidence/videocad/notes/sources/harvard_dataverse_metadata.json",
    "evidence/videocad/notes/sources/VideoCAD_README.md",
    "evidence/videocad/notes/sources/generate_dataset.py",
]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build evidence manifest for VideoCAD 7-day validation")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/videocad/notes/证据台账清单-Day7.json"),
    )
    args = parser.parse_args()

    day2 = load_json("evidence/videocad/notes/action_json_summary.json")
    day3 = load_json("evidence/videocad/notes/action_json_pairing_summary.json")
    day4 = load_json("evidence/videocad/notes/action_json_complexity_label_summary.json")
    day5 = load_json("evidence/videocad/notes/cad_imgs_mapping_probe_summary.json")
    day6 = load_json("evidence/videocad/notes/cad_action_multimodal_sample_pool_summary.json")

    manifest_files = []
    missing = []
    for p_str in KEY_FILES:
        p = Path(p_str)
        if not p.exists():
            missing.append(p_str)
            continue
        stat = p.stat()
        manifest_files.append(
            {
                "path": p_str,
                "size_bytes": stat.st_size,
                "mtime_epoch": int(stat.st_mtime),
                "sha256": sha256_file(p),
            }
        )

    summary = {
        "project": "VideoCAD 7天落地验证",
        "generated_date": "2026-02-26",
        "day_range": "Day1-Day6",
        "core_metrics": {
            "action_json": {
                "file_count": day2["file_count"],
                "event_count": day2["total_events"],
                "action_unique_count": day2["action_unique_count"],
                "status_distribution": day2["status_distribution"],
            },
            "pairing": {
                "paired_action_segments": day3["total_paired_actions_with_duration"],
                "pairing_issue_files": day3["files_with_pairing_issues"],
                "strict_nesting_mismatch_files": day3["files_with_strict_nesting_mismatch"],
                "negative_duration_pairs": day3["loose_negative_duration_pairs"],
            },
            "complexity_labels_all_action_json": day4["label_counts"],
            "cad_imgs": {
                "cad_image_file_count": day5["cad_listing"]["file_count"],
                "cad_unique_sample_ids": day5["cad_image_naming_pattern"]["unique_sample_id_count"],
                "action_json_overlap_count": day5["action_json_overlap"]["overlap_count"],
                "qa_exact_path_hits_in_cad_zip": day5["qa_json_path_probe"]["qa_exact_path_hits_in_cad_zip"],
            },
            "multimodal_overlap_pool": {
                "merged_overlap_samples": day6["merged_row_count"],
                "label_distribution": day6["label_distribution_on_overlap_subset"],
                "sample_rows_exported": day6["outputs"]["sample_row_count"],
            },
        },
        "key_files": manifest_files,
        "missing_key_files": missing,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote manifest to {args.output}")
    print(f"key_files={len(manifest_files)} missing={len(missing)}")


if __name__ == "__main__":
    main()

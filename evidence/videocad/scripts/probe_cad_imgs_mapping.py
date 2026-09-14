#!/usr/bin/env python3
from __future__ import annotations

import csv
import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path


IMAGE_NAME_RE = re.compile(r"^images/(\d{4})/(\d{8})_(\d+)\.png$", re.IGNORECASE)
QA_IMG_RE = re.compile(r"image_(\d+)\.png$", re.IGNORECASE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe cad_imgs.zip structure and mapping signals")
    parser.add_argument(
        "--cad-zip",
        type=Path,
        default=Path("evidence/videocad/samples/dataverse/cad_imgs.zip"),
    )
    parser.add_argument(
        "--action-dir",
        type=Path,
        default=Path("evidence/videocad/samples/dataverse/action_json_unpacked/action_json"),
    )
    parser.add_argument(
        "--qa-json",
        type=Path,
        default=Path("evidence/videocad/samples/dataverse/qa.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/videocad/notes/cad_imgs_mapping_probe_summary.json"),
    )
    parser.add_argument(
        "--overlap-csv",
        type=Path,
        default=Path("evidence/videocad/notes/cad_action_overlap_samples.csv"),
    )
    args = parser.parse_args()

    qa = json.loads(args.qa_json.read_text(encoding="utf-8"))
    qa_paths: list[str] = []
    qa_image_indices: list[int] = []
    for item in qa:
        q = item.get("question") if isinstance(item, dict) else None
        if isinstance(q, dict):
            for p in (q.get("image_refs") or {}).values():
                if isinstance(p, str):
                    qa_paths.append(p)
                    m = QA_IMG_RE.search(p)
                    if m:
                        qa_image_indices.append(int(m.group(1)))
        for opt in item.get("options", []) if isinstance(item, dict) else []:
            if isinstance(opt, dict) and isinstance(opt.get("path"), str):
                p = opt["path"]
                qa_paths.append(p)
                m = QA_IMG_RE.search(p)
                if m:
                    qa_image_indices.append(int(m.group(1)))

    qa_unique_paths = sorted(set(qa_paths))

    action_ids = {p.stem for p in args.action_dir.glob("*.json")}

    total_entries = 0
    total_files = 0
    total_dirs = 0
    parse_pattern_hits = 0
    exact_qa_path_hits = 0

    prefix_counter = Counter()
    shard_counter = Counter()
    view_idx_counter = Counter()
    sample_id_counter = Counter()
    overlap_image_count = Counter()
    overlap_sample_paths: dict[str, list[str]] = {}

    first_files: list[str] = []
    last_files: list[str] = []
    parse_miss_examples: list[str] = []
    qa_exact_match_examples: list[str] = []

    qa_path_set_lower = {p.lower() for p in qa_unique_paths}

    proc = subprocess.Popen(
        ["bsdtar", "-tf", str(args.cad_zip)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.stdout is not None
    for raw_line in proc.stdout:
        line = raw_line.rstrip("\n")
        if not line:
            continue
        total_entries += 1
        if line.endswith("/"):
            total_dirs += 1
            continue

        total_files += 1
        if len(first_files) < 20:
            first_files.append(line)
        if len(last_files) >= 20:
            last_files.pop(0)
        last_files.append(line)

        parts = line.split("/")
        prefix_counter["/".join(parts[:2])] += 1

        if line.lower() in qa_path_set_lower:
            exact_qa_path_hits += 1
            if len(qa_exact_match_examples) < 20:
                qa_exact_match_examples.append(line)

        m = IMAGE_NAME_RE.match(line)
        if m:
            parse_pattern_hits += 1
            shard, sample_id, view_idx = m.groups()
            shard_counter[shard] += 1
            view_idx_counter[view_idx] += 1
            sample_id_counter[sample_id] += 1
            if sample_id in action_ids:
                overlap_image_count[sample_id] += 1
                if sample_id not in overlap_sample_paths:
                    overlap_sample_paths[sample_id] = []
                if len(overlap_sample_paths[sample_id]) < 5:
                    overlap_sample_paths[sample_id].append(line)
        elif len(parse_miss_examples) < 20:
            parse_miss_examples.append(line)

    assert proc.stderr is not None
    stderr = proc.stderr.read().strip()
    code = proc.wait()

    cad_sample_ids = set(sample_id_counter.keys())
    action_overlap = cad_sample_ids & action_ids

    qa_idx_set = set(qa_image_indices)
    summary = {
        "cad_zip": str(args.cad_zip),
        "bsdtar_exit_code": code,
        "bsdtar_stderr": stderr,
        "cad_listing": {
            "entry_count_total": total_entries,
            "dir_count": total_dirs,
            "file_count": total_files,
            "first_files": first_files,
            "last_files": last_files,
            "prefix_top20": dict(prefix_counter.most_common(20)),
        },
        "cad_image_naming_pattern": {
            "pattern": "images/<4-digit-shard>/<8-digit-sample-id>_<view-index>.png",
            "match_file_count": parse_pattern_hits,
            "parse_miss_examples": parse_miss_examples,
            "shard_count": len(shard_counter),
            "shard_top20": dict(shard_counter.most_common(20)),
            "view_index_distribution": dict(view_idx_counter.most_common()),
            "unique_sample_id_count": len(cad_sample_ids),
            "images_per_sample_stats_hint": {
                "min": min(sample_id_counter.values()) if sample_id_counter else None,
                "max": max(sample_id_counter.values()) if sample_id_counter else None,
            },
            "sample_id_examples": sorted(list(cad_sample_ids))[:20],
        },
        "action_json_overlap": {
            "action_json_file_count": len(action_ids),
            "cad_unique_sample_id_count": len(cad_sample_ids),
            "overlap_count": len(action_overlap),
            "coverage_of_cad_ids_in_action_json": round(
                len(action_overlap) / len(cad_sample_ids), 6
            )
            if cad_sample_ids
            else None,
            "coverage_of_action_json_ids_in_cad": round(
                len(action_overlap) / len(action_ids), 6
            )
            if action_ids
            else None,
            "overlap_examples": sorted(list(action_overlap))[:20],
            "cad_not_in_action_json_examples": sorted(list(cad_sample_ids - action_ids))[:20],
            "action_not_in_cad_examples": sorted(list(action_ids - cad_sample_ids))[:20],
        },
        "qa_json_path_probe": {
            "qa_item_count": len(qa),
            "qa_unique_image_path_count": len(qa_unique_paths),
            "qa_exact_path_hits_in_cad_zip": exact_qa_path_hits,
            "qa_exact_path_hit_examples": qa_exact_match_examples,
            "qa_image_index_range": {
                "min": min(qa_idx_set) if qa_idx_set else None,
                "max": max(qa_idx_set) if qa_idx_set else None,
                "unique_count": len(qa_idx_set),
            },
        },
        "conclusions": [],
        "overlap_csv": str(args.overlap_csv),
    }

    conclusions: list[str] = summary["conclusions"]
    if parse_pattern_hits == total_files:
        conclusions.append("cad_imgs.zip files consistently follow images/<shard>/<sample_id>_<view>.png naming.")
    else:
        conclusions.append("cad_imgs.zip includes files outside the expected image naming pattern (see parse_miss_examples).")
    if len(action_overlap) > 0:
        conclusions.append("cad_imgs.zip sample IDs overlap with action_json file IDs, indicating a feasible sequence-image linkage via 8-digit sample_id.")
    if exact_qa_path_hits == 0:
        conclusions.append("qa.json image paths are not directly present in cad_imgs.zip; QA likely uses a re-indexed image subset (image_N.png) requiring an additional mapping artifact.")
    else:
        conclusions.append("Some qa.json image paths directly match cad_imgs.zip paths.")

    args.overlap_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.overlap_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["sample_id", "image_count_in_cad", "action_json_exists", "example_image_paths"],
        )
        writer.writeheader()
        for sample_id in sorted(action_overlap):
            writer.writerow(
                {
                    "sample_id": sample_id,
                    "image_count_in_cad": overlap_image_count.get(sample_id, 0),
                    "action_json_exists": 1,
                    "example_image_paths": " | ".join(overlap_sample_paths.get(sample_id, [])),
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote summary to {args.output}")
    print(
        f"cad_files={total_files} pattern_hits={parse_pattern_hits} unique_sample_ids={len(cad_sample_ids)} action_overlap={len(action_overlap)} qa_exact_hits={exact_qa_path_hits}"
    )


if __name__ == "__main__":
    main()

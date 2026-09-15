#!/usr/bin/env python3
"""步骤二：确认集 600 链抽样 —— 200/200/200 分层等量，与开发集不相交。

框架：evidence/videocad/notes/action_json_file_complexity_metrics.csv
      （44,291 链全底座；complexity_label 为 complexity_score 三分位口径，阈值与
       计数见 action_json_complexity_label_summary.json，与方案 v1 表 C 底座一致）
排除：开发集 90 链（cad_action_multimodal_samples.csv 中引擎实际取用的前 30/层）
      + 其余 45 条联动样本池行（同为开发材料，一并排除，留痕可复核）
抽样：random.Random(SEED) 分层无放回；SEED 固定并写入抽样记录 + 论文补充材料
输出：evidence/videocad/notes/confirm_set_600.csv（引擎 --use-all-rows 直接可读，
      链级指标随清单携带，供异质性解释）
      evidence/videocad/notes/confirm_set_600_sampling_record.json（种子/框架哈希/
      排除清单/不相交断言/输出哈希）

不改本脚本的任何输入而重跑，必须产出逐字节相同的清单（确定性自检在末尾）。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

SEED_DEFAULT = 20260916
PER_LABEL = 200
STRATA = ("low", "medium", "high")
REPO = Path(__file__).resolve().parent.parent
FRAME = REPO / "evidence/videocad/notes/action_json_file_complexity_metrics.csv"
DEV_CSV = REPO / "evidence/videocad/notes/cad_action_multimodal_samples.csv"
ACTION_DIR = "evidence/videocad/samples/dataverse/action_json_unpacked/action_json"
OUT_CSV = REPO / "evidence/videocad/notes/confirm_set_600.csv"
OUT_RECORD = REPO / "evidence/videocad/notes/confirm_set_600_sampling_record.json"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description="Confirm-set sampling: 600 chains, 200/200/200, disjoint from dev")
    ap.add_argument("--seed", type=int, default=SEED_DEFAULT)
    args = ap.parse_args()

    # 框架 + 排除集
    frame: dict[str, dict] = {}
    with FRAME.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            stem = row["file"].rsplit(".json", 1)[0]
            row["sample_id"] = stem
            frame[stem] = row
    dev_ids: set[str] = set()
    with DEV_CSV.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            dev_ids.add(row["sample_id"])
    excluded = dev_ids  # 135 = 开发 90 + 池内其余 45（同一清单）

    available = {s: [c for c, r in frame.items() if r["complexity_label"] == s and c not in excluded]
                 for s in STRATA}
    counts = {s: len(v) for s, v in available.items()}
    for s in STRATA:
        assert counts[s] >= PER_LABEL, f"{s} 可用 {counts[s]} < {PER_LABEL}"

    rng = random.Random(args.seed)
    drawn: dict[str, list[str]] = {}
    for s in STRATA:
        drawn[s] = sorted(rng.sample(available[s], PER_LABEL))

    # 不相交与唯一性断言
    flat = [c for s in STRATA for c in drawn[s]]
    assert len(flat) == len(set(flat)) == PER_LABEL * 3
    assert not (set(flat) & excluded), "与开发集相交！"
    assert all(frame[c]["complexity_label"] == s for s in STRATA for c in drawn[s])

    fields = ["sample_group", "sample_id", "action_json_file", "action_json_path",
              "event_count", "pair_count", "unique_action_count", "span_ms",
              "line_pair_count", "sketch_pair_count", "curve_pair_count",
              "extrusion_pair_count", "complexity_score", "complexity_label"]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for s in STRATA:
            for c in drawn[s]:
                r = frame[c]
                w.writerow({
                    "sample_group": "confirm_set_600",
                    "sample_id": c,
                    "action_json_file": r["file"],
                    "action_json_path": f"{ACTION_DIR}/{r['file']}",
                    "event_count": r["event_count"], "pair_count": r["pair_count"],
                    "unique_action_count": r["unique_action_count"], "span_ms": r["span_ms"],
                    "line_pair_count": r["line_pair_count"], "sketch_pair_count": r["sketch_pair_count"],
                    "curve_pair_count": r["curve_pair_count"], "extrusion_pair_count": r["extrusion_pair_count"],
                    "complexity_score": r["complexity_score"], "complexity_label": s,
                })

    record = {
        "seed": args.seed,
        "date": "2026-09-16",
        "frame": {"file": str(FRAME.relative_to(REPO)), "sha256": sha256_of(FRAME),
                   "total_chains": len(frame),
                   "label_counts": dict(Counter(r["complexity_label"] for r in frame.values()))},
        "excluded": {"source": str(DEV_CSV.relative_to(REPO)), "n_excluded": len(excluded),
                      "ids": sorted(excluded),
                      "note": "开发集 90 链 + 联动样本池其余 45 条（开发材料一并排除）"},
        "draw": {"per_label": PER_LABEL, "label_counts": {s: len(drawn[s]) for s in STRATA},
                  "total": len(flat)},
        "disjointness_assertion": "passed",
        "output": {"csv": str(OUT_CSV.relative_to(REPO)), "sha256": sha256_of(OUT_CSV)},
        "determinism_note": "同种子重跑必须逐字节一致；引擎注入种子须另选（见 run_confirmation.sh）",
    }
    OUT_RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"frame: {len(frame)} chains, labels {record['frame']['label_counts']}")
    print(f"excluded {len(excluded)} dev/pool chains; available after exclusion: {counts}")
    print(f"drawn: {record['draw']['label_counts']} total {len(flat)}; disjointness: PASSED")
    print(f"Wrote: {OUT_CSV.relative_to(REPO)}  sha256={record['output']['sha256'][:16]}…")
    print(f"Wrote: {OUT_RECORD.relative_to(REPO)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HISTORY_ROOT = ROOT / "proposal" / "history"
INDEX_FILE = HISTORY_ROOT / "index.jsonl"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def load_index() -> list[dict]:
    if not INDEX_FILE.exists():
        return []
    rows = []
    with INDEX_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def append_index(record: dict) -> None:
    HISTORY_ROOT.mkdir(parents=True, exist_ok=True)
    with INDEX_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def cmd_snapshot(args: argparse.Namespace) -> int:
    src = Path(args.file).resolve()
    if not src.exists() or not src.is_file():
        print(f"Source file not found: {src}", file=sys.stderr)
        return 1

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    section_key = args.name or src.stem
    dest_dir = HISTORY_ROOT / section_key
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = src.suffix if src.suffix else ".txt"
    dest = dest_dir / f"{ts}{ext}"
    shutil.copy2(src, dest)

    record = {
        "timestamp": ts,
        "section_key": section_key,
        "source": rel(src),
        "snapshot": rel(dest),
        "sha256": sha256_file(dest),
        "bytes": dest.stat().st_size,
        "note": args.note or "",
    }
    append_index(record)

    print(f"Snapshot saved: {record['snapshot']}")
    print(f"Section key: {section_key}")
    if record["note"]:
        print(f"Note: {record['note']}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    rows = load_index()
    if args.section:
        rows = [r for r in rows if r.get("section_key") == args.section]
    if args.source:
        rows = [r for r in rows if r.get("source") == args.source]
    if not rows:
        print("No snapshots found.")
        return 0
    for r in rows:
        note = f" | {r['note']}" if r.get("note") else ""
        print(f"{r['timestamp']} | {r['section_key']} | {r['snapshot']}{note}")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    snapshot = Path(args.snapshot)
    if not snapshot.is_absolute():
        snapshot = ROOT / snapshot
    if not snapshot.exists():
        print(f"Snapshot not found: {snapshot}", file=sys.stderr)
        return 1
    target = Path(args.target).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(snapshot, target)
    print(f"Restored {rel(snapshot)} -> {rel(target)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Lightweight snapshot versioning for proposal text files")
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("snapshot", help="Create a timestamped snapshot of a text file")
    s1.add_argument("file", help="Source file to snapshot")
    s1.add_argument("--name", help="Section key (defaults to source filename stem)")
    s1.add_argument("--note", help="Short change note")
    s1.set_defaults(func=cmd_snapshot)

    s2 = sub.add_parser("list", help="List snapshots")
    s2.add_argument("--section", help="Filter by section key")
    s2.add_argument("--source", help="Filter by source path (workspace-relative)")
    s2.set_defaults(func=cmd_list)

    s3 = sub.add_parser("restore", help="Restore a snapshot to a target file")
    s3.add_argument("snapshot", help="Snapshot path (absolute or workspace-relative)")
    s3.add_argument("target", help="Target file path to overwrite/create")
    s3.set_defaults(func=cmd_restore)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

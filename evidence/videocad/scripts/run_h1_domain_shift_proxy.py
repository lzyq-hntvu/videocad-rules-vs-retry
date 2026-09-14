#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def parse_example_paths(s: str) -> list[str]:
    return [p.strip() for p in (s or "").split("|") if p.strip()]


def choose_image_path(example_paths: list[str]) -> str:
    for p in example_paths:
        if p.endswith("_0.png"):
            return p
    return example_paths[0]


def stream_image_from_cad_zip(cad_zip: Path, internal_path: str) -> Image.Image:
    # bsdtar returns non-zero for this ZIP, but often writes valid stdout before failing.
    proc = subprocess.run(
        ["bsdtar", "-xOf", str(cad_zip), internal_path],
        capture_output=True,
    )
    if not proc.stdout:
        raise RuntimeError(f"Failed extracting {internal_path}: rc={proc.returncode}, err={proc.stderr[:200]!r}")
    try:
        im = Image.open(io.BytesIO(proc.stdout))
        im.load()
        return im.convert("RGB")
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Decode failed for {internal_path}: {e}") from e


def ensure_cached_image(cad_zip: Path, cache_dir: Path, internal_path: str) -> Path:
    out = cache_dir / internal_path
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 0:
        return out
    im = stream_image_from_cad_zip(cad_zip, internal_path)
    im.save(out)
    return out


def batch_extract_to_cache(cad_zip: Path, cache_dir: Path, internal_paths: list[str]) -> dict:
    missing = []
    for p in internal_paths:
        target = cache_dir / p
        if not target.exists() or target.stat().st_size == 0:
            missing.append(p)
    if not missing:
        return {"requested": len(internal_paths), "batch_missing_before": 0, "batch_present_after": len(internal_paths), "bsdtar_returncode": 0}

    cache_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["bsdtar", "-xf", str(cad_zip), "-C", str(cache_dir), *missing]
    proc = subprocess.run(cmd, capture_output=True)

    present_after = 0
    for p in internal_paths:
        t = cache_dir / p
        if t.exists() and t.stat().st_size > 0:
            present_after += 1
    return {
        "requested": len(internal_paths),
        "batch_missing_before": len(missing),
        "batch_present_after": present_after,
        "bsdtar_returncode": proc.returncode,
        "bsdtar_stderr_head": proc.stderr[:200].decode("utf-8", errors="replace"),
    }


def load_rgb(path: Path) -> Image.Image:
    im = Image.open(path)
    im.load()
    return im.convert("RGB")


def grayscale_array(im: Image.Image, size: tuple[int, int]) -> np.ndarray:
    g = im.convert("L").resize(size, Image.Resampling.BILINEAR)
    arr = np.asarray(g, dtype=np.float32) / 255.0
    return arr


def l2norm(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n <= 1e-12:
        return v
    return v / n


def pool_mean(arr: np.ndarray, out_h: int, out_w: int) -> np.ndarray:
    h, w = arr.shape
    # Trim to divisible size for simple reshape pooling
    hh = (h // out_h) * out_h
    ww = (w // out_w) * out_w
    arr = arr[:hh, :ww]
    if hh == 0 or ww == 0:
        return np.zeros((out_h, out_w), dtype=np.float32)
    sh = hh // out_h
    sw = ww // out_w
    return arr.reshape(out_h, sh, out_w, sw).mean(axis=(1, 3))


def baseline_descriptor(im: Image.Image) -> np.ndarray:
    # Deliberately simple/brittle baseline: raw grayscale appearance only.
    arr = grayscale_array(im, (64, 64))
    vec = arr.reshape(-1).astype(np.float32)
    return l2norm(vec)


def robust_descriptor(im: Image.Image) -> np.ndarray:
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g)
    g = ImageOps.equalize(g)
    arr = np.asarray(g.resize((96, 96), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0

    # Intensity branch (coarse pooled) with photometric normalization
    inten = pool_mean(arr, 12, 12)
    inten = (inten - float(inten.mean())) / (float(inten.std()) + 1e-6)

    # Gradient magnitude branch (robust to brightness shift)
    gy, gx = np.gradient(arr)
    grad = np.sqrt(gx * gx + gy * gy)
    grad = grad / (grad.mean() + 1e-6)
    grad_p = pool_mean(grad, 12, 12)

    # Global histogram branch (equalized grayscale)
    hist, _ = np.histogram(arr, bins=16, range=(0.0, 1.0), density=True)
    hist = hist.astype(np.float32)

    # Fine normalized appearance branch to preserve identity under mild shifts
    fine = np.asarray(g.resize((48, 48), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
    fine = (fine - float(fine.mean())) / (float(fine.std()) + 1e-6)

    vec = np.concatenate([fine.reshape(-1), inten.reshape(-1), grad_p.reshape(-1), hist], axis=0).astype(np.float32)
    vec = vec - vec.mean()
    return l2norm(vec)


def perturb_controlled_domain_shift(im: Image.Image, strength: int, rng: random.Random) -> Image.Image:
    if strength <= 0:
        return im.copy()

    out = im.copy()
    w, h = out.size

    # Brightness / contrast jitter grows with strength
    b_factor = 1.0 + rng.uniform(-0.06, 0.06) * strength
    c_factor = 1.0 + rng.uniform(-0.08, 0.08) * strength
    out = ImageEnhance.Brightness(out).enhance(max(0.2, b_factor))
    out = ImageEnhance.Contrast(out).enhance(max(0.2, c_factor))

    # Small blur for mid/high strength
    if strength >= 2:
        radius = 0.35 * (strength - 1) + rng.uniform(0.0, 0.25)
        out = out.filter(ImageFilter.GaussianBlur(radius=radius))

    # Scale jitter + pad/crop back to original size (simulated resolution/layout shift)
    scale = 1.0 + rng.uniform(-0.03, 0.03) * strength
    new_w = max(64, int(round(w * scale)))
    new_h = max(64, int(round(h * scale)))
    resized = out.resize((new_w, new_h), Image.Resampling.BILINEAR)
    canvas = Image.new("RGB", (w, h), (127, 127, 127))
    # center with random offset if larger/smaller
    offset_x = (w - new_w) // 2 + int(rng.uniform(-2, 2) * strength)
    offset_y = (h - new_h) // 2 + int(rng.uniform(-2, 2) * strength)
    if new_w >= w and new_h >= h:
        crop_x = max(0, (new_w - w) // 2 - offset_x)
        crop_y = max(0, (new_h - h) // 2 - offset_y)
        out = resized.crop((crop_x, crop_y, crop_x + w, crop_y + h))
    else:
        canvas.paste(resized, (offset_x, offset_y))
        out = canvas

    # Add one rectangular occlusion patch at higher strengths
    if strength >= 3:
        arr = np.asarray(out, dtype=np.uint8).copy()
        frac = 0.03 * strength + rng.uniform(0.0, 0.02)
        occ_w = max(8, int(w * frac))
        occ_h = max(8, int(h * frac))
        x0 = rng.randint(0, max(0, w - occ_w))
        y0 = rng.randint(0, max(0, h - occ_h))
        fill = int(rng.uniform(0, 255))
        arr[y0 : y0 + occ_h, x0 : x0 + occ_w, :] = fill
        out = Image.fromarray(arr, mode="RGB")

    # Add mild Gaussian noise
    arr = np.asarray(out, dtype=np.float32)
    sigma = 2.0 * strength
    noise = rng.normalvariate  # alias
    # Vectorized-ish by numpy random from deterministic seed not easy with python RNG;
    # use NumPy RNG seeded from python RNG for repeatability.
    np_rng = np.random.default_rng(rng.randint(0, 2**32 - 1))
    arr = arr + np_rng.normal(0.0, sigma, size=arr.shape)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")


def cosine_scores(query: np.ndarray, gallery: np.ndarray) -> np.ndarray:
    return gallery @ query


def rank_of_target(scores: np.ndarray, target_idx: int) -> int:
    # 1-based rank
    order = np.argsort(-scores)
    pos = int(np.where(order == target_idx)[0][0])
    return pos + 1


def line_slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    x = np.asarray(xs, dtype=np.float32)
    y = np.asarray(ys, dtype=np.float32)
    x_mean = x.mean()
    y_mean = y.mean()
    denom = float(((x - x_mean) ** 2).sum())
    if denom <= 1e-12:
        return 0.0
    num = float(((x - x_mean) * (y - y_mean)).sum())
    return num / denom


def maybe_plot(summary_rows: list[dict], out_dir: Path) -> list[str]:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return []
    out_files = []
    for metric in ("top1_acc", "mrr"):
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for method in ("baseline", "robust"):
            rows = [r for r in summary_rows if r["subset"] == "all" and r["method"] == method]
            rows = sorted(rows, key=lambda r: int(r["strength"]))
            ax.plot(
                [int(r["strength"]) for r in rows],
                [float(r[metric]) for r in rows],
                marker="o",
                label=method,
            )
        ax.set_xlabel("controlled domain shift strength")
        ax.set_ylabel(metric)
        ax.set_ylim(0.0, 1.05)
        ax.grid(alpha=0.25)
        ax.legend()
        fig.tight_layout()
        p = out_dir / f"h1_proxy_{metric}_vs_shift.png"
        fig.savefig(p, dpi=160)
        plt.close(fig)
        out_files.append(str(p))

    # By complexity label for top1
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, label in zip(axes, ("low", "medium", "high")):
        for method in ("baseline", "robust"):
            rows = [r for r in summary_rows if r["subset"] == label and r["method"] == method]
            rows = sorted(rows, key=lambda r: int(r["strength"]))
            ax.plot([int(r["strength"]) for r in rows], [float(r["top1_acc"]) for r in rows], marker="o", label=method)
        ax.set_title(label)
        ax.set_xlabel("shift strength")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("top1_acc")
    axes[-1].legend()
    fig.tight_layout()
    p = out_dir / "h1_proxy_top1_by_complexity.png"
    fig.savefig(p, dpi=160)
    plt.close(fig)
    out_files.append(str(p))
    return out_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Run H1 proxy experiment: controlled domain shift robustness (retrieval proxy)")
    parser.add_argument(
        "--enriched-csv",
        type=Path,
        default=Path("evidence/videocad/notes/cad_action_overlap_enriched.csv"),
    )
    parser.add_argument(
        "--cad-zip",
        type=Path,
        default=Path("evidence/videocad/samples/dataverse/cad_imgs.zip"),
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("evidence/videocad/notes/h1_proxy_experiment/cache_images"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("evidence/videocad/notes/h1_proxy_experiment"),
    )
    parser.add_argument("--per-label", type=int, default=100, help="Sample count per complexity label")
    parser.add_argument("--replicates", type=int, default=3, help="Perturbation replicates per image and strength")
    parser.add_argument("--max-strength", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260226)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(args.enriched_csv.open("r", encoding="utf-8", newline="")))
    by_label = {"low": [], "medium": [], "high": []}
    for r in rows:
        label = r["complexity_label"]
        if label in by_label:
            by_label[label].append(r)

    rng = random.Random(args.seed)
    selected: list[dict] = []
    for label in ("low", "medium", "high"):
        pool = by_label[label]
        if len(pool) < args.per_label:
            raise ValueError(f"Not enough rows for {label}: {len(pool)}")
        chosen = rng.sample(pool, args.per_label)
        for r in chosen:
            paths = parse_example_paths(r["example_image_paths"])
            img_path = choose_image_path(paths)
            selected.append(
                {
                    "sample_id": r["sample_id"],
                    "complexity_label": label,
                    "image_path_in_zip": img_path,
                    "action_json_file": r["action_json_file"],
                    "complexity_score": float(r["complexity_score"]),
                }
            )

    # Batch extract selected images first (much faster than per-image bsdtar).
    batch_extract_info = batch_extract_to_cache(
        args.cad_zip, args.cache_dir, [x["image_path_in_zip"] for x in selected]
    )

    # Cache and load images (fallback to per-image extraction for any misses)
    images: list[Image.Image] = []
    for item in selected:
        cached = ensure_cached_image(args.cad_zip, args.cache_dir, item["image_path_in_zip"])
        item["cached_image_path"] = str(cached)
        images.append(load_rgb(cached))

    # Build gallery descriptors
    gallery_baseline = np.stack([baseline_descriptor(im) for im in images], axis=0)
    gallery_robust = np.stack([robust_descriptor(im) for im in images], axis=0)

    per_query_rows = []
    agg = defaultdict(lambda: {"n": 0, "top1": 0, "rr_sum": 0.0})

    strengths = list(range(args.max_strength + 1))
    for idx, (item, im) in enumerate(zip(selected, images)):
        label = item["complexity_label"]
        for strength in strengths:
            for rep in range(args.replicates):
                rng_q = random.Random((args.seed * 1000003 + idx * 97 + strength * 13 + rep) & 0xFFFFFFFF)
                q_img = perturb_controlled_domain_shift(im, strength, rng_q)
                q_base = baseline_descriptor(q_img)
                q_rob = robust_descriptor(q_img)

                for method, q_vec, gallery in (
                    ("baseline", q_base, gallery_baseline),
                    ("robust", q_rob, gallery_robust),
                ):
                    scores = cosine_scores(q_vec, gallery)
                    rnk = rank_of_target(scores, idx)
                    top1 = 1 if rnk == 1 else 0
                    rr = 1.0 / rnk
                    per_query_rows.append(
                        {
                            "sample_id": item["sample_id"],
                            "complexity_label": label,
                            "method": method,
                            "strength": strength,
                            "replicate": rep,
                            "top1": top1,
                            "rank": rnk,
                            "rr": round(rr, 6),
                        }
                    )
                    for subset in ("all", label):
                        k = (subset, method, strength)
                        agg[k]["n"] += 1
                        agg[k]["top1"] += top1
                        agg[k]["rr_sum"] += rr

    summary_rows = []
    for (subset, method, strength), a in sorted(agg.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
        n = a["n"]
        summary_rows.append(
            {
                "subset": subset,
                "method": method,
                "strength": strength,
                "n_queries": n,
                "top1_acc": round(a["top1"] / n, 6),
                "mrr": round(a["rr_sum"] / n, 6),
            }
        )

    # Degradation slopes (overall and per label)
    slope_rows = []
    for subset in ("all", "low", "medium", "high"):
        for method in ("baseline", "robust"):
            ss = [r for r in summary_rows if r["subset"] == subset and r["method"] == method]
            ss = sorted(ss, key=lambda r: int(r["strength"]))
            xs = [int(r["strength"]) for r in ss]
            for metric in ("top1_acc", "mrr"):
                ys = [float(r[metric]) for r in ss]
                slope_rows.append(
                    {
                        "subset": subset,
                        "method": method,
                        "metric": metric,
                        "slope_per_strength": round(line_slope(xs, ys), 6),
                        "delta_0_to_max": round(ys[-1] - ys[0], 6),
                    }
                )

    summary_csv = out_dir / "summary_curve.csv"
    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    per_query_csv = out_dir / "per_query_results.csv"
    with per_query_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(per_query_rows[0].keys()))
        writer.writeheader()
        writer.writerows(per_query_rows)

    slopes_csv = out_dir / "degradation_slopes.csv"
    with slopes_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(slope_rows[0].keys()))
        writer.writeheader()
        writer.writerows(slope_rows)

    plots = maybe_plot(summary_rows, out_dir)

    # Compact result comparison for H1 narrative
    def get_metric(subset: str, method: str, strength: int, metric: str) -> float:
        for r in summary_rows:
            if r["subset"] == subset and r["method"] == method and int(r["strength"]) == strength:
                return float(r[metric])
        raise KeyError((subset, method, strength, metric))

    h1_compact = {}
    for subset in ("all", "low", "medium", "high"):
        h1_compact[subset] = {
            "top1_acc_strength0": {
                "baseline": get_metric(subset, "baseline", 0, "top1_acc"),
                "robust": get_metric(subset, "robust", 0, "top1_acc"),
            },
            "top1_acc_strength_max": {
                "baseline": get_metric(subset, "baseline", args.max_strength, "top1_acc"),
                "robust": get_metric(subset, "robust", args.max_strength, "top1_acc"),
            },
        }

    meta_selected_csv = out_dir / "selected_images.csv"
    with meta_selected_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(selected[0].keys()))
        writer.writeheader()
        writer.writerows(selected)

    summary_json = out_dir / "summary.json"
    summary = {
        "experiment": "H1 proxy: controlled domain shift robustness via image retrieval/matching proxy",
        "design_notes": {
            "proxy_task": "retrieve original CAD image under controlled domain shift perturbations",
            "baseline_descriptor": "raw grayscale 64x64 flattened normalized",
            "robust_descriptor": "autocontrast+equalized grayscale, pooled intensity + gradient magnitude + histogram",
            "domain_shift": "controlled composite perturbation (brightness/contrast, blur, scale jitter, occlusion, noise)",
            "claim_boundary": "proxy evidence for robustness trend; not GUI element detection/localization benchmark",
        },
        "inputs": {
            "enriched_csv": str(args.enriched_csv),
            "cad_zip": str(args.cad_zip),
            "sample_per_label": args.per_label,
            "total_images": len(selected),
            "replicates_per_strength": args.replicates,
            "strength_values": strengths,
            "seed": args.seed,
        },
        "selected_distribution": dict(Counter(x["complexity_label"] for x in selected)),
        "batch_extract_info": batch_extract_info,
        "h1_compact_comparison": h1_compact,
        "outputs": {
            "selected_images_csv": str(meta_selected_csv),
            "summary_curve_csv": str(summary_csv),
            "degradation_slopes_csv": str(slopes_csv),
            "per_query_results_csv": str(per_query_csv),
            "plots": plots,
            "cache_dir": str(args.cache_dir),
        },
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote: {meta_selected_csv}")
    print(f"Wrote: {summary_csv}")
    print(f"Wrote: {slopes_csv}")
    print(f"Wrote: {per_query_csv}")
    print(f"Wrote: {summary_json}")
    if plots:
        print("Plots:")
        for p in plots:
            print(f"  {p}")


if __name__ == "__main__":
    main()

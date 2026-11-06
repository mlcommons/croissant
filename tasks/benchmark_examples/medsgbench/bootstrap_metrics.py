"""Bootstrap 95% confidence intervals on MedSG-Bench predictions.

Reads per-sample IoU and hit@0.5 from the immutable run snapshot``
and produces 1000-iteration percentile-bootstrap 95% CIs per cell.

This script is local-only: it makes no API calls, loads no model, and does
not modify any file inside the run snapshot. The user-specified rule
"skip metrics that require new API calls (e.g. LLM-as-a-judge)" is
vacuously satisfied for MedSG-Bench Task 6, whose only metrics are
geometric (xyxy IoU and the IoU>=0.5 threshold).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import numpy as np


# Map pipeline label -> subpath under <run>/. Reflects the layout where
# ct2code lives inside paper2ct2code/ (the PDF -> CT -> code workflow) and
# paper2code is at the run root (the direct PDF -> code workflow).
PIPELINES = (
    ("paper2code", "paper2code"),
    ("ct2code",    "paper2ct2code/ct2code"),
)
MODELS = ("3b", "7b", "32b", "72b")
DEFAULT_RUN_ID = "cbd063f9_2026-05-05T08-54Z"


def load_cell(jsonl_path: pathlib.Path) -> tuple[np.ndarray, np.ndarray]:
    iou_vals: list[float] = []
    hit_vals: list[float] = []
    with jsonl_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            v = r.get("iou")
            iou_vals.append(0.0 if v is None else float(v))
            hit_vals.append(1.0 if r.get("hit@0.5") else 0.0)
    return np.asarray(iou_vals, dtype=np.float64), np.asarray(hit_vals, dtype=np.float64)


def bootstrap_mean_ci(values: np.ndarray, n_iter: int,
                      rng: np.random.Generator) -> tuple[float, float, float]:
    n = len(values)
    idx = rng.integers(0, n, size=(n_iter, n))
    means = values[idx].mean(axis=1)
    point = float(values.mean())
    lo, hi = np.percentile(means, [2.5, 97.5])
    return point, float(lo), float(hi)


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--run", type=pathlib.Path,
                   default=here / "runs" / DEFAULT_RUN_ID,
                   help="path to the immutable run snapshot directory")
    p.add_argument("--n-bootstrap", type=int, default=1000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", type=pathlib.Path, default=None,
                   help="JSON output path (default: analysis/<run-id>/bootstrap.json)")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    run_dir: pathlib.Path = args.run
    if not run_dir.is_dir():
        print(f"error: --run path does not exist: {run_dir}", file=sys.stderr)
        return 2

    out_path = args.out or (here / "analysis" / run_dir.name / "bootstrap.json")
    rng = np.random.default_rng(args.seed)

    if not args.quiet:
        header = (f"{'pipeline':>11}  {'model':>5}  {'n':>5}  "
                  f"{'IoU mean [2.5%, 97.5%] (pct)':<32}  "
                  f"{'Acc@0.5 mean [2.5%, 97.5%] (pct)':<34}")
        print(header)
        print("-" * len(header))

    cells: list[dict] = []
    t0 = time.time()
    for pipeline, subpath in PIPELINES:
        for size in MODELS:
            jl = run_dir / subpath / "raw_outputs" / f"outputs_task6_qwen2.5-vl-{size}.jsonl"
            if not jl.is_file():
                if not args.quiet:
                    print(f"  [skip] {pipeline}/{size}: no jsonl at {jl}")
                continue
            iou_arr, hit_arr = load_cell(jl)
            n = len(iou_arr)
            if n < 100:
                raise RuntimeError(f"cell {pipeline}/{size} has only {n} rows; refusing to bootstrap")
            iou_mean, iou_lo, iou_hi = bootstrap_mean_ci(iou_arr, args.n_bootstrap, rng)
            acc_mean, acc_lo, acc_hi = bootstrap_mean_ci(hit_arr, args.n_bootstrap, rng)
            cells.append({
                "pipeline": pipeline,
                "model": size,
                "n": n,
                "iou_pct":         {"mean": iou_mean * 100, "lo": iou_lo * 100, "hi": iou_hi * 100},
                "acc_at_0_5_pct":  {"mean": acc_mean * 100, "lo": acc_lo * 100, "hi": acc_hi * 100},
            })
            if not args.quiet:
                print(f"{pipeline:>11}  {size:>5}  {n:>5}  "
                      f"{iou_mean*100:6.2f} [{iou_lo*100:6.2f}, {iou_hi*100:6.2f}]            "
                      f"{acc_mean*100:6.2f} [{acc_lo*100:6.2f}, {acc_hi*100:6.2f}]")
    dt = time.time() - t0

    payload = {
        "run": run_dir.name,
        "n_bootstrap": args.n_bootstrap,
        "seed": args.seed,
        "metric_keys": ["iou", "hit_at_0_5"],
        "metrics_skipped_api_dependent": [],
        "metrics_skipped_api_dependent_note":
            "MedSG-Bench Task 6 uses only geometric metrics (xyxy IoU and "
            "the IoU>=0.5 threshold). No LLM-as-a-judge metrics are present "
            "in this benchmark; the skip-API-dependent-metrics rule is "
            "vacuously satisfied.",
        "cells": cells,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n")
    if not args.quiet:
        print(f"\nwrote {out_path}  ({dt:.2f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

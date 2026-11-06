"""Aggregate raw per-sample predictions into a filled TaskSolution JSON-LD.

See ../../paper2code/generate_jsonld.py for full documentation. This module
is a copy kept here so that paper2ct2code/ct2code/ remains a self-contained
workflow snapshot.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean


def aggregate(raw_path: Path) -> dict:
    iou_vals: list[float] = []
    hit_vals: list[bool] = []
    with raw_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            v = r.get("iou")
            iou_vals.append(0.0 if v is None else float(v))
            hit_vals.append(bool(r.get("hit@0.5")))
    n = len(iou_vals)
    if n == 0:
        raise RuntimeError(f"no rows in {raw_path}")
    return {
        "n": n,
        "iou_pct": round(100 * mean(iou_vals), 2),
        "acc_at_0_5_pct": round(100 * mean(hit_vals), 2),
    }


def patch_skeleton(skeleton: dict, metrics: dict, model: str) -> dict:
    out = dict(skeleton)
    out["croissant:evaluation"] = {
        "@type": "croissant:EvaluationTask",
        "@id": f"{out.get('@id', 'http://example.org/medsg-bench_solution')}#evaluation_run",
        "croissant:evaluatedSolution": {"@id": out.get("@id")},
        "croissant:evaluationResults": [
            {
                "@type": "croissant:EvaluationResult",
                "croissant:metric": "IoU (xyxy mean)",
                "croissant:value": metrics["iou_pct"],
                "croissant:unit": "percent",
            },
            {
                "@type": "croissant:EvaluationResult",
                "croissant:metric": "Acc@0.5",
                "croissant:value": metrics["acc_at_0_5_pct"],
                "croissant:unit": "percent",
            },
        ],
        "croissant:numInstances": metrics["n"],
        "croissant:executedOnModel": model,
    }
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--model", required=True, help="3b | 7b | 32b | 72b")
    p.add_argument("--raw", required=True, type=Path)
    p.add_argument("--skeleton", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()

    metrics = aggregate(args.raw)
    skeleton = json.loads(args.skeleton.read_text())
    filled = patch_skeleton(skeleton, metrics, model=f"qwen2.5-vl-{args.model}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(filled, indent=2) + "\n")
    print(f"wrote {args.out}  IoU={metrics['iou_pct']}%  Acc@0.5={metrics['acc_at_0_5_pct']}%  n={metrics['n']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

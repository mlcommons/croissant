"""paper2code pipeline driver.

CLI:
    python -m paper2code.run_inference --model 3b|7b|32b --task 6 --n 1000 \
        --out outputs/qwen3b_task6_paper2code.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

# Ensure the repo root is on sys.path so `import src.*` works regardless of cwd.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from src.data_local import LocalSample, load_local_subset
from src.metrics import iou as iou_xyxy
from src.qwen_loader import get_or_load_model, MODEL_PATHS
# Paper-only inference: prompt + parser are LOCAL to this pipeline, not shared.
from .inference import predict_bbox_batch as _qwen_batch


@dataclass
class Prediction:
    sample_id: str
    task_id: int
    pred_bbox: tuple | None
    raw_response: str
    backend: str
    latency_s: float


def _make_predict(model_size: str, batch_size: int = 4):
    """Return a function that takes a list[LocalSample] and emits list[Prediction]."""
    def _fn(batch: list[LocalSample]) -> list[Prediction]:
        model, processor, device = get_or_load_model(model_size)
        results = _qwen_batch(batch, model, processor, device)
        out: list[Prediction] = []
        for s, r in zip(batch, results):
            out.append(Prediction(
                sample_id=s.sample_id,
                task_id=s.task_id,
                pred_bbox=r["pred_bbox"],
                raw_response=r["raw_response"],
                backend=f"qwen2.5-vl-{model_size}",
                latency_s=r["latency_s"],
            ))
        return out
    return _fn


BACKENDS = {
    "qwen3b":  _make_predict("3b"),
    "qwen7b":  _make_predict("7b"),
    "qwen32b": _make_predict("32b"),
    "qwen72b": _make_predict("72b"),
}


def run(samples: list[LocalSample], backend: str,
        batch_size: int = 4) -> list[Prediction]:
    fn = BACKENDS[backend]
    out: list[Prediction] = []
    t0 = time.time()
    for i in range(0, len(samples), batch_size):
        batch = samples[i: i + batch_size]
        try:
            preds = fn(batch)
        except Exception as e:
            err = f"ERROR: {type(e).__name__}: {e}"
            print(f"[paper2code] batch {i} failed: {err}", file=sys.stderr)
            preds = [Prediction(s.sample_id, s.task_id, None, err, backend, 0.0)
                     for s in batch]
        out.extend(preds)
        done = len(out)
        if done % 25 == 0 or done >= len(samples):
            elapsed = time.time() - t0
            rate = done / elapsed if elapsed > 0 else 0.0
            print(f"[paper2code] {done}/{len(samples)} rate={rate:.2f}/s",
                  file=sys.stderr)
    return out


def evaluate(samples: list[LocalSample], preds: list[Prediction]) -> dict:
    by_id = {p.sample_id: p for p in preds}
    rows = []
    for s in samples:
        p = by_id.get(s.sample_id)
        pb = list(p.pred_bbox) if p and p.pred_bbox else None
        gt = list(s.gt_bbox)
        s_iou = iou_xyxy(pb, gt) if pb is not None else 0.0
        rows.append({
            "sample_id": s.sample_id,
            "task_id": s.task_id,
            "n_images": len(s.image_paths),
            "gt_bbox": gt,
            "pred_bbox": pb,
            "raw_response": (p.raw_response[:300] if p else "")[:300],
            "latency_s": round(p.latency_s if p else 0.0, 3),
            "iou": round(s_iou, 6),
            "hit@0.5": s_iou >= 0.5,
        })
    n = len(rows)
    if n == 0:
        return {"n": 0, "iou_pct": 0.0, "acc_at_0_5_pct": 0.0, "rows": []}
    iou_mean = sum(r["iou"] for r in rows) / n
    acc05 = sum(1 for r in rows if r["hit@0.5"]) / n
    return {
        "n": n,
        "iou_pct": round(100 * iou_mean, 2),
        "acc_at_0_5_pct": round(100 * acc05, 2),
        "mean_iou": iou_mean,
        "acc_at_0_5": acc05,
        "rows": rows,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=["3b", "7b", "32b", "72b"], required=True)
    p.add_argument("--task", type=int, default=6)
    p.add_argument("--n", type=int, default=1000)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    print(f"[paper2code] model={args.model} task={args.task} n={args.n} bs={args.batch_size}",
          file=sys.stderr)
    samples = load_local_subset(args.task, limit=args.n)
    print(f"[paper2code] loaded {len(samples)} samples", file=sys.stderr)

    backend = f"qwen{args.model}"
    t_eval = time.time()
    preds = run(samples, backend=backend, batch_size=args.batch_size)
    eval_secs = time.time() - t_eval
    metrics = evaluate(samples, preds)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "pipeline": "paper2code",
        "model": args.model,
        "model_path": MODEL_PATHS[args.model],
        "task_id": args.task,
        **{k: v for k, v in metrics.items() if k != "rows"},
        "total_eval_seconds": round(eval_secs, 1),
        "batch_size": args.batch_size,
        "per_sample": metrics["rows"],
    }
    args.out.write_text(json.dumps(payload, indent=2))
    print(f"[paper2code] wrote {args.out} iou={metrics['iou_pct']}% "
          f"acc05={metrics['acc_at_0_5_pct']}%", file=sys.stderr)


if __name__ == "__main__":
    main()

"""ct2code pipeline driver.

CLI:
    python -m ct2code.pipeline --model 3b|7b|32b --task 6 --n 1000 \
        --out outputs/qwen3b_task6_ct2code.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from src.data_local import LocalSample, load_local_subset
from src.metrics import iou as iou_xyxy
from src.qwen_loader import get_or_load_model, MODEL_PATHS
# CT-only inference: prompt + parser are LOCAL to this pipeline, not shared.
from .inference import predict_bbox_batch as _qwen_batch


class BasePredictor:
    name = "base"

    def predict_batch(self, batch: List[LocalSample]) -> List[dict]:
        raise NotImplementedError


class QwenVLPredictor(BasePredictor):
    """Class-style wrapper around ct2code.inference.predict_bbox_batch.

    Loads model lazily on first batch via the shared get_or_load_model cache,
    so multiple QwenVLPredictor instances of the same size in one process
    share GPU memory.
    """

    def __init__(self, model_size: str):
        self.model_size = model_size
        self.name = f"qwen2.5-vl-{model_size}"
        self._loaded = None

    def _ensure(self):
        if self._loaded is None:
            self._loaded = get_or_load_model(self.model_size)
        return self._loaded

    def predict_batch(self, batch: List[LocalSample]) -> List[dict]:
        model, processor, device = self._ensure()
        return _qwen_batch(batch, model, processor, device)


def evaluate_local(samples: List[LocalSample], predictor: BasePredictor,
                   batch_size: int = 4) -> dict:
    """Iterate samples in batches, predict, score IoU, return summary dict."""
    rows = []
    t0 = time.time()
    for i in range(0, len(samples), batch_size):
        batch = samples[i: i + batch_size]
        try:
            results = predictor.predict_batch(batch)
        except Exception as e:
            err = f"ERROR: {type(e).__name__}: {e}"
            print(f"[ct2code] batch {i} failed: {err}", file=sys.stderr)
            results = [{"pred_bbox": None, "raw_response": err,
                        "latency_s": 0.0, "model": predictor.name}
                       for _ in batch]
        for s, r in zip(batch, results):
            gt = list(s.gt_bbox)
            pred = list(r["pred_bbox"]) if r["pred_bbox"] else None
            s_iou = iou_xyxy(pred, gt) if pred is not None else 0.0
            rows.append({
                "sample_id": s.sample_id,
                "task_id": s.task_id,
                "n_images": len(s.image_paths),
                "gold": gt,
                "pred": pred,
                "raw_response": (r["raw_response"] or "")[:300],
                "latency_s": round(r["latency_s"], 3),
                "iou": round(s_iou, 6),
                "hit@0.5": s_iou >= 0.5,
            })
        done = len(rows)
        if done % 25 == 0 or done >= len(samples):
            elapsed = time.time() - t0
            rate = done / elapsed if elapsed > 0 else 0.0
            print(f"[ct2code] {done}/{len(samples)} rate={rate:.2f}/s",
                  file=sys.stderr)
    n = len(rows)
    if n == 0:
        return {"n": 0, "iou_pct": 0.0, "acc_at_0_5_pct": 0.0, "per_sample": []}
    mean_iou = sum(r["iou"] for r in rows) / n
    acc05 = sum(1 for r in rows if r["hit@0.5"]) / n
    return {
        "n": n,
        "mean_iou": mean_iou,
        "acc_at_0_5": acc05,
        "iou_pct": round(100 * mean_iou, 2),
        "acc_at_0_5_pct": round(100 * acc05, 2),
        "per_sample": rows,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=["3b", "7b", "32b", "72b"], required=True)
    p.add_argument("--task", type=int, default=6)
    p.add_argument("--n", type=int, default=1000)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    samples = load_local_subset(args.task, limit=args.n)
    print(f"[ct2code] task={args.task} n={len(samples)} model={args.model} "
          f"bs={args.batch_size}", file=sys.stderr)

    predictor = QwenVLPredictor(model_size=args.model)
    t_eval = time.time()
    metrics = evaluate_local(samples, predictor, batch_size=args.batch_size)
    eval_secs = time.time() - t_eval

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "pipeline": "ct2code",
        "model": args.model,
        "model_path": MODEL_PATHS[args.model],
        "task_id": args.task,
        "predictor": predictor.name,
        "n": metrics["n"],
        "mean_iou": metrics["mean_iou"],
        "acc_at_0_5": metrics["acc_at_0_5"],
        "iou_pct": metrics["iou_pct"],
        "acc_at_0_5_pct": metrics["acc_at_0_5_pct"],
        "total_eval_seconds": round(eval_secs, 1),
        "batch_size": args.batch_size,
        "per_sample": metrics["per_sample"],
    }
    args.out.write_text(json.dumps(payload, indent=2))
    print(f"[ct2code] wrote {args.out} iou={metrics['iou_pct']}% "
          f"acc05={metrics['acc_at_0_5_pct']}%", file=sys.stderr)


if __name__ == "__main__":
    main()

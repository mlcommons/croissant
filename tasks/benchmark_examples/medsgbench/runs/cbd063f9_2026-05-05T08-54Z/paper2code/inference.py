"""paper2code inference path.
"""

from __future__ import annotations

import re
import time
from typing import Tuple

import torch

from src.data_local import LocalSample
from src.vision_process import process_vision_info

# format_qwen_2_5 from prompts.py (k=1 contamination bundle). Identical
# to ct2code's PROMPT_FORMAT - both pipelines receive the same suffix
# from the same prompts.py.
PROMPT_FORMAT = (
    " Output only the coordinates. Format: (x1,y1),(x2,y2). "
    "Strictly follow this format. No additional text or explanation."
)

# LENIENT: try the explicit tuple first (paper Sec 5.2 names the format),
# then fall back to four bare integers anywhere in the response (paper
# Sec 5.2 hedges that "different model families use different
# coordinate normalizations").
_BBOX_RX_TUPLE = re.compile(
    r"\(?\s*(\d+\.?\d*)\s*[,，]\s*(\d+\.?\d*)\s*\)?\s*[,，]?\s*"
    r"\(?\s*(\d+\.?\d*)\s*[,，]\s*(\d+\.?\d*)\s*\)?"
)
_BBOX_RX_FALLBACK = re.compile(
    r"(-?\d+\.?\d*)[ ,，]+(-?\d+\.?\d*)[ ,，]+(-?\d+\.?\d*)[ ,，]+(-?\d+\.?\d*)"
)


def _extract_bbox(text: str) -> Tuple[int, int, int, int] | None:
    if not text:
        return None
    m = _BBOX_RX_TUPLE.search(text)
    if not m:
        m = _BBOX_RX_FALLBACK.search(text)
    if not m:
        return None
    try:
        x1, y1, x2, y2 = (int(round(float(m.group(i)))) for i in range(1, 5))
    except (ValueError, OverflowError):
        return None
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1, y1, x2, y2)


def build_messages(sample: LocalSample) -> list[dict]:
    """Single user turn: images then question + format suffix from k=1.

    Same structure as ct2code; the prompt content is fixed by k=1
    (format_qwen_2_5 from prompts.py) so both pipelines build messages
    identically. Differentiation lives only in _extract_bbox.
    """
    content: list[dict] = []
    for p in sample.image_paths:
        content.append({"type": "image", "image": str(p)})
    content.append({"type": "text", "text": sample.question + PROMPT_FORMAT})
    return [{"role": "user", "content": content}]


def predict_bbox_batch(samples: list[LocalSample], model, processor, device,
                       max_new_tokens: int = 128) -> list[dict]:
    msgs_list = [build_messages(s) for s in samples]
    texts = [
        processor.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
        for m in msgs_list
    ]

    all_images: list = []
    all_videos: list = []
    for msgs in msgs_list:
        imgs, vids = process_vision_info(msgs)
        if imgs:
            all_images.extend(imgs)
        if vids:
            all_videos.extend(vids)

    inputs = processor(
        text=texts,
        images=all_images if all_images else None,
        videos=all_videos if all_videos else None,
        padding=True,
        return_tensors="pt",
    ).to(device)

    t0 = time.time()
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False,
        )
    dt = time.time() - t0

    trimmed = [out_ids[len(in_ids):]
               for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
    responses = processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )
    name = getattr(model, "name_or_path", "qwen2.5-vl")
    out: list[dict] = []
    for r in responses:
        text = (r or "").strip()
        out.append({
            "pred_bbox": _extract_bbox(text),
            "raw_response": text,
            "latency_s": dt / max(1, len(samples)),
            "batch_size": len(samples),
            "batch_latency_s": dt,
            "model": name,
            "pipeline": "paper2code",
        })
    return out


def predict_bbox(sample: LocalSample, model, processor, device,
                 max_new_tokens: int = 128) -> dict:
    return predict_bbox_batch([sample], model, processor, device,
                              max_new_tokens=max_new_tokens)[0]

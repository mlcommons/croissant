#!/usr/bin/env python3
"""
RISEBench evaluation pipeline for Gemini-2.0-Flash-Experimental.

Inference  : Gemini-2.0-Flash-Exp  (google-genai SDK, native image-in / image-out)
Judge      : GPT-4.1               (openai SDK, LMM-as-a-Judge)
Dataset    : RISEBench-360         (HuggingFace: PhoenixZ/RISEBench)

Usage
-----
    # full pipeline (inference + evaluation)
    python run_eval.py

    # only run inference (generate edited images)
    python run_eval.py --skip-eval

    # only run evaluation (score existing outputs)
    python run_eval.py --skip-inference

    # control parallelism for the judge phase
    python run_eval.py --nproc 8

    # ── Proof-of-concept: one sample, use pre-built output from GitHub ──
    # Downloads input image, reference image, and the model's existing output
    # directly from the RISEBench GitHub repo — no dataset clone required.
    python run_eval.py --sample logical_reasoning_1 --skip-inference --use-github-output

Environment variables
---------------------
    GOOGLE_API_KEY   — Gemini API key
    OPENAI_API_KEY   — OpenAI API key (for GPT-4.1 judge)

Output layout (relative to this script)
----------------------------------------
    outputs/
        images/
            temporal_reasoning/<index>.png
            causal_reasoning/<index>.png
            spatial_reasoning/<index>.png
            logical_reasoning/<index>.png
        gemini-2.0-flash-exp.pkl          # cached raw judge responses
        gemini-2.0-flash-exp_scores.csv   # per-sample scores + accuracy
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import pickle
import re
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm

# ─── Google Gemini (inference) ───────────────────────────────────────────────
from google import genai
from google.genai import types as gtypes

# ─── OpenAI (judge) ──────────────────────────────────────────────────────────
from openai import OpenAI

# ─── Paths ───────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "outputs"
HF_DATA_DIR = SCRIPT_DIR / "hf_data"   # downloaded dataset lives here

MODEL_NAME = "gemini-2.0-flash-exp"
JUDGE_MODEL = "gpt-4.1"
NPROC = 4                               # parallel judge threads (override with --nproc)

# ─── Judge prompts (verbatim from RISEBench/utils.py) ────────────────────────

PROMPT_CONSIST = """You are a highly skilled image evaluator. You will receive two images (an original image and a modified image) along with a specific modification instruction. The second image is known to have been altered based on this instruction, starting from the first image. Your task is to evaluate whether the two images maintain consistency in aspects not related to the given instruction.

## Task
Evaluate the consistency between the images according to the following scale (1 to 5):

- **5 (Perfect Consistency)**: Apart from changes explicitly required by the instruction, all other details (e.g., personal features, clothing, background, layout, colors, positions of objects) are completely identical between the two images.

- **4 (Minor Differences)**: Apart from changes explicitly required by the instruction, the second image is mostly consistent with the original image but contains a minor discrepancy (such as a missing minor personal feature, accessory, or tattoo).

- **3 (Noticeable Differences)**: Apart from changes explicitly required by the instruction, the second image has one significant difference from the original (such as a noticeable alteration in a person's appearance like hair or skin color, or a significant change in background environment).

- **2 (Significant Differences)**: Apart from changes explicitly required by the instruction, the second image has two or more significant differences or multiple noticeable inconsistencies (such as simultaneous changes in both personal appearance and background environment).

- **1 (Severe Differences)**: Apart from changes explicitly required by the instruction, nearly all key details (e.g., gender, major appearance features, background environment, or scene layout) significantly differ from the original image, clearly deviating from the original.

Note: When assigning scores, only consider details unrelated to the instruction. Changes explicitly requested by the instruction should NOT be regarded as inconsistencies.

## Input

**Instruction:** {instruct}

## Output Format

Provide a detailed, step-by-step explanation of your scoring process. Conclude clearly with the final score, formatted as:

**Final Score:** **1-5**"""

PROMPT_REASONING = """You are an expert image evaluator. For each task, you will be provided with:

1. An **instruction** describing how an image should be modified.
2. A **ground-truth textual description** that represents the intended result of the modification.
3. An **output image** generated by an assistant.

Your task is to assess the output image based on the following evaluation dimension:

## Evaluation Dimension: Alignment Between Image and Reference Description
Assess how accurately the output image aligns with the visual content described in the reference description, considering the context of the instruction.

**Scoring Criteria:**
- **5**: The image completely matches the description, accurately reflecting every detail and degree.
- **4**: The image mostly matches the description, with minor discrepancies.
- **3**: The image partially matches the description but contains differences or lacks some details.
- **2**: The image contains noticeable difference. Important details are missed or clearly inaccurate.
- **1**: The image fails to follow the instruction and does not correspond to the description at all.

## Input
**Instruction**  {instruct}
**GroundTruth Description:** {reference}

## Output Format

Provide a detailed, step-by-step explanation of your scoring process. Conclude clearly with the final score, formatted as:

**Final Score:** **X**
"""

PROMPT_REASONING_W_INPUT = """You are an expert image evaluator. For each task, you will be provided with:

1. An original image.
2. An **instruction** describing how an image should be modified.
3. A **ground-truth textual description** that represents the intended result of the modification.
4. An **output image** generated by an assistant.

Your task is to assess the output image based on the following evaluation dimension:

## Evaluation Dimension: Alignment Between Image and Reference Description
Assess how accurately the output image aligns with the visual content described in the reference description, considering the context of the instruction.

**Scoring Criteria:**
- **5**: The image completely matches the description, accurately reflecting every detail and degree.
- **4**: The image mostly matches the description, with minor discrepancies.
- **3**: The image partially matches the description but contains differences or lacks some details.
- **2**: The image contains noticeable difference. Important details are missed or clearly inaccurate.
- **1**: The image fails to follow the instruction and does not correspond to the description at all.

## Input
**Instruction**  {instruct}
**GroundTruth Description:** {reference}

## Output Format

Provide a detailed, step-by-step explanation of your scoring process. Conclude clearly with the final score, formatted as:

**Final Score:** **X**
"""

PROMPT_GENERATION = """You are an expert image evaluator. For each task, you will be provided with an **output image** generated by an assistant.

Your task is to independently assess the image along the following dimension and assign an integer score from **1 to 5**:

### Evaluation Dimension: Realism and Generation Quality

Assess the overall visual realism and generation fidelity of the image. Consider the image's clarity, natural appearance, and compliance with physical plausibility and real-world constraints.

**Scoring Guidelines:**

- **5** The image is sharp, visually coherent, and all elements appear highly realistic and physically plausible.
- **4** The image is clear, with most elements appearing realistic; minor details may show slight unreality.
- **3** The image is mostly clear, but some significant elements appear unrealistic or physically implausible.
- **2** The image is noticeably blurry or contains major unrealistic components or visual distortions.
- **1** The image is extremely blurry, incoherent, or severely unrealistic; realism is nearly absent.

## Output Format

After the evaluation, conclude clearly with the final score, formatted as:

**Final Score:** **X**
"""

PROMPT_SPATIAL_REF = """You are an expert image evaluator. For each task, you will be provided with:

1. An **instruction** describing how an image should be modified.
2. A **ground-truth textual description** that represents the intended result of the modification.
3. An **output image** generated by an assistant.

Your task is to assess the output image based on the following evaluation dimension:

## Evaluation Dimension: Alignment Between Image and Reference Description
Assess how accurately the output image aligns with the visual content described in the reference description, considering the context of the instruction.

**Scoring Criteria:**
- **5**: The image completely matches the description, accurately reflecting every detail and degree.
- **4**: The image mostly matches the description, with minor discrepancies.
- **3**: The image partially matches the description but contains differences or lacks some details.
- **2**: The image contains noticeable difference. Important details are missed or clearly inaccurate.
- **1**: The image fails to follow the instruction and is entirely unrelated to the description.

## Input
**Instruction**  {instruct}
**GroundTruth Description:** {reference}

## Output Format

Conclude clearly with the final score, formatted as:

**Final Score:** **X**"""

PROMPT_SPATIAL_REF_IMG = """You are an expert image evaluator. For each task, you will be provided with:

1. An **instruction** describing how an image should be modified.
2. A **reference image** that represents the intended result of the modification.
3. An **output image** generated by an assistant.

Your task is to assess the output image based on the following evaluation dimension:

## Evaluation Dimension: Alignment Between Output Image and reference Image
Assess how accurately the output image aligns with the reference image, considering the context of the instruction.

**Scoring Criteria:**
- **5**: The image completely matches the reference image and fully follows the instruction.
- **4**: The image mostly matches the reference image, with minor discrepancies.
- **3**: The image partially matches the reference image but contains differences or lacks some details.
- **2**: The image contains noticeable difference. Important details are missed or clearly inaccurate.
- **1**: The image fails to follow the instruction and is entirely unrelated to the reference image.

## Input
**Instruction**  {instruct}

## Output Format

Conclude clearly with the final score, formatted as:

**Final Score:** **X**"""

PROMPT_SPATIAL_REF_W_INPUT = """You are an expert image evaluator. For each task, you will be provided with:

1. An original image.
2. An **instruction** describing how the original image should be modified.
3. A **ground-truth textual description** that represents the intended result of the modification.
4. An **output image** generated by an assistant.

Your task is to assess the output image based on the following evaluation dimension:

## Evaluation Dimension: Alignment Between Image and Reference Description
Assess how accurately the output image aligns with the reference description based on the original image, considering the context of the instruction.

**Scoring Criteria:**
- **5**: The image completely matches the description, accurately reflecting every detail and degree.
- **4**: The image mostly matches the description, with minor discrepancies.
- **3**: The image partially matches the description but contains differences or lacks some details.
- **2**: The image contains noticeable difference. Important details are missed or clearly inaccurate.
- **1**: The image fails to follow the instruction and is entirely unrelated to the description.

## Input
**Instruction**  {instruct}
**GroundTruth Description:** {reference}

## Output Format

Conclude clearly with the final score, formatted as:

**Final Score:** **X**"""

PROMPT_SPATIAL_QUAL = """You are a highly skilled image evaluator. Given an image, your task is to assess and determine its clarity and distortion, and then provide a score (an integer between 1 and 5) based on the following criteria:

## Task Requirements:

Determine whether the image has blurriness, distortion, visual defects, or physical inaccuracies.

Assign an appropriate score to the image based on the above criteria, considering its overall quality and detail integrity.

## Scoring Criteria:

- **5 points**: The image is very clear, with complete details, and no noticeable distortion or blurriness. All elements conform to physical laws.
- **4 points**: The image is clear, with only minor blurriness, and no noticeable distortion.
- **3 points**: The image has areas with clarity issues, such as slight blurriness or distortion. Some elements are physically incorrect.
- **2 points**: The image has noticeable blurriness or distortion, with significant detail loss, or lacks physical accuracy.
- **1 point**: The image is severely blurry or distorted, making it difficult to recognize its content, with serious degradation in visual quality, almost unusable.

Do not penalize the image for being rendered in 3D.

## Output Format

Provide a clear conclusion with the final score, formatted as follows:

**Final Score:** **1-5**

where X represents the score."""

PROMPT_SPATIAL_CONS = """You are a precise and analytical image consistency evaluator.

You will be given:
- **Image A**: the original image.
- **Image B**: a modified version of Image A.
- **Instruction**: a directive describing the intended modification to Image A to produce Image B.

Your task is to **evaluate how consistent Image B remains with Image A in all aspects *except* those explicitly changed by the instruction.** You must **ignore the instructed changes** and **only assess unintended differences**.

## Evaluation Scale (1 to 5):

- **5** Perfect Consistency
  All elements not related to the instruction are visually identical between Image A and Image B (e.g., style, background, object positions, colors, shapes). No unintended change is present.
- **4** Minor Difference
  One small unintended change is present (e.g., a slight color variation or minor object shape shift), but overall the image remains highly consistent.
- **3** Noticeable Difference
  One major or a few minor unintended changes are present (e.g., an object's shape, color, or background differs noticeably, or style has shifted slightly).
- **2** Significant Inconsistency
  Two or more significant differences unrelated to the instruction (e.g., changes in both object details and background or style), reducing overall fidelity.
- **1** Severe Inconsistency
  Major unintended changes dominate the image (e.g., altered visual style, scene layout, or appearance), clearly breaking consistency with Image A.

> Note: To receive a score of 5, the modified image must be visually identical to the original in every unaffected aspect. If the background in the original is vague (e.g., plain white), and Image B is also similar, you may disregard background consistency. If a blue diamond shape appears in the bottom-left corner of Image 2, ignore it; it is a watermark.

## Input
**Instruction:** {instruct}

## Output Format
After evaluation, conclude with:

**Final Score:** **1-5**
"""

PROMPT_LOGICAL_CONS_ANS = """**You are a highly skilled image evaluator.** Given an image with logical problem, you will receive:

1. **Image 1**: The original image.
2. **Image 2**: A generated image from an assistant model.
3. **Problem Description**
4. **Reference Answer**

## Evaluation Task

* Compare Image 2 against Image 1 in terms of visual style, environment, and composition.
* Score each comparison as **1** (consistent) or **0** (inconsistent).

## Consistency Criteria (score 1 if true):

* Color palette, line weight, font/handwriting style, arrangement, and background setting closely match.
* Only the problem's solution differs (e.g., added or removed marks), or color brightness is slightly lighter/darker.
* Image 2 is derived by overlaying a pattern onto Image 1 without altering style or layout.
* **If a blue diamond shape appears in the bottom-left corner of Image 2, ignore it; it is a watermark.**

## Inconsistency Example (score 0):

* Image 1 shows a quadrilateral with unequal edges and arbitrary angles, but Image 2 depicts a perfect square with equal edges and right angles.

## Inputs
**Problem Description**:
{instruct}
**Reference Answer**:
{reference}

## Output
You should provide a step-by-step explanation of how you arrived at the score and conclude in the format:

**Final Score**: **X**
"""

PROMPT_LOGICAL_CONS = """**You are a highly skilled image evaluator.** Given an image with logical problem, you will receive:

1. **Image 1**: The original image.
2. **Image 2**: A generated image answer from an assistant model.
3. **Problem Description**

## Evaluation Task

* Judge the appearance consistency between Image 1 and Image 2.
* Score each comparison as **1** (consistent) or **0** (inconsistent).

## Consistency Criteria (score 1 if true):

* Color palette, line weight, font/handwriting style, arrangement, and background setting closely match.
* Only the problem's solution differs (e.g., added or removed marks), or color brightness is slightly lighter/darker.
* Image 2 is derived by overlaying a pattern onto Image 1 without altering style or layout.
* **If a blue diamond shape appears in the bottom-left corner of Image 2, ignore it; it is a watermark.**

## Inconsistency Example (score 0):

* Image 1 shows a quadrilateral with unequal edges and arbitrary angles, but Image 2 depicts a perfect square with equal edges and right angles.
* Image 2 contains severe blur and distortion.

## Inputs
**Problem Description**:
{instruct}

## Output
Conclude in the format:

**Final Score**: **X**
"""

PROMPT_LOGICAL_TXT = """**You are a highly skilled image evaluator.** Given an image with logical problem, you will receive:

1. **Image**: A generated image answer from an assistant model.
2. **Reference Answer**

## Task
Assign a binary score (0 or 1) for **Logical Correctness**:
- **1** if the Generated Image accurately implements the Reference Answer.
- **0** otherwise.

## Requirements
- The original image is not given and do not imagine the original image, just determine whether the generated image matches the reference answer.
- **If the given image contains more content than reference answer, give score 0.**

## Inputs
**Reference Answer**:
{reference}

## Output
You should provide a step-by-step explanation of how you arrived at the score and conclude in the format:

**Final Score**: **X**
"""

PROMPT_LOGICAL_IMG = """**You are a highly skilled image evaluator.** Given a logical problem, you will receive:

1. **Problem Description**
2. **Image 1**: A reference ground-truth image answer that correctly solves the problem.
3. **Image 2**: A generated image answer from an assistant model.

## Logical Correctness (0/1)
Determine whether the content of *Image 2* solves the problem in the same way as *Image 1* does.

### Scoring rules:
- Score **1** if *Image 2* exactly matches *Image 1* in terms of problem-solving logic and visual outcome.
- Score **0** if there are any differences that affect the correctness of the solution.

## Problem Description
{instruct}

## Output
Conclude in the format:

**Final Score**: **X**
"""

PROMPT_LOGICAL_IMG_WO_Q = """**You are a highly skilled image evaluator.** You will receive:

1. **Image 1**: An image represents the correct answer.
2. **Image 2**: A generated image that is claimed to solve the problem.

## Task
Determine whether Image 1 and Image 2 are the same. Give 1 when same and 0 when not same. Do not consider size and background.
DO NOT GIVE 1 WHEN IMAGE 2 CONTAINS MORE CONTENT THAN IMAGE 1.
WHEN IMAGE 2 IS A PUZZLE AND IMAGE 1 IS NOT AN ANSWER, GIVE 0.

## Output
Provide your explanation and give score in the format:

**Final Score**: **X**
"""


# ─── Dataset helpers ─────────────────────────────────────────────────────────

def download_dataset() -> None:
    """Download RISEBench-360 from HuggingFace if not already present."""
    # Accept if any of these marker files exist
    markers = [
        HF_DATA_DIR / "data" / "data_total.json",
        HF_DATA_DIR / "data_total.json",
    ]
    if any(m.exists() for m in markers):
        print(f"Dataset already present at {HF_DATA_DIR}")
        return

    HF_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("Downloading RISEBench-360 from HuggingFace (PhoenixZ/RISEBench)…")
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id="PhoenixZ/RISEBench",
            repo_type="dataset",
            local_dir=str(HF_DATA_DIR),
            ignore_patterns=["*.git*", ".git*"],
        )
        print("Download complete.")
        return
    except Exception as exc:
        print(f"HuggingFace download failed ({exc}); falling back to GitHub clone…")

    ret = os.system(
        f'git clone --depth 1 https://github.com/PhoenixZ810/RISEBench.git "{HF_DATA_DIR}"'
    )
    if ret != 0:
        raise RuntimeError("Failed to clone RISEBench from GitHub.")
    print("GitHub clone complete.")


def find_data_json() -> Path:
    """Locate data_total.json (or data_360.json) inside the downloaded dataset."""
    candidates = [
        HF_DATA_DIR / "data" / "data_total.json",
        HF_DATA_DIR / "data" / "data_360.json",
        HF_DATA_DIR / "data_total.json",
        HF_DATA_DIR / "data_360.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        f"Could not find benchmark data JSON in {HF_DATA_DIR}. "
        "Expected data/data_total.json or data/data_360.json."
    )


def find_image_base() -> Path:
    """Return the directory that contains at least one *_reasoning_images/ folder."""
    cat_dirs = [
        "temporal_reasoning_images",
        "causal_reasoning_images",
        "spatial_reasoning_images",
        "logical_reasoning_images",
    ]
    for candidate in [HF_DATA_DIR / "data", HF_DATA_DIR]:
        if any((candidate / d).exists() for d in cat_dirs):
            return candidate
    raise FileNotFoundError(
        f"Could not find category image folders under {HF_DATA_DIR}."
    )


# ─── GitHub single-sample helpers ────────────────────────────────────────────

_GITHUB_RAW = "https://raw.githubusercontent.com/PhoenixZ810/RISEBench/main"

def _download_url(url: str, dest: Path) -> None:
    """Download *url* to *dest*, creating parent dirs as needed. No-op if dest exists."""
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {url}")
    urllib.request.urlretrieve(url, dest)


def prepare_sample_from_github(item: dict, use_github_output: bool) -> None:
    """
    For a single sample, fetch all required files from GitHub raw URLs:
      • input image  → hf_data/data/<image>
      • reference image (if any) → hf_data/data/<reference_img>
      • pre-built output image (when use_github_output=True)
            → outputs/images/<category>/<index>.png
    The data_total.json itself is also fetched into hf_data/data/ if absent.
    """
    data_dir = HF_DATA_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Fetch data_total.json so find_data_json() works even without a full clone
    _download_url(
        f"{_GITHUB_RAW}/data/data_total.json",
        data_dir / "data_total.json",
    )

    # Input image
    _download_url(
        f"{_GITHUB_RAW}/data/{item['image']}",
        data_dir / item["image"],
    )

    # Reference image (used by logical_reasoning with reference_img)
    ref_img = item.get("reference_img")
    if ref_img and pd.notna(ref_img):
        _download_url(
            f"{_GITHUB_RAW}/data/{ref_img}",
            data_dir / ref_img,
        )

    # Pre-built output image from the repo's gemini2 outputs
    if use_github_output:
        category = item["category"]
        index    = item["index"]
        out_path = OUTPUT_DIR / "images" / category / f"{index}.png"
        _download_url(
            f"{_GITHUB_RAW}/outputs/gemini2/images/{category}/{index}.png",
            out_path,
        )


# ─── Inference ───────────────────────────────────────────────────────────────

def _mime_for(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    return {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/jpeg")


def gemini_generate(client: genai.Client, image_path: Path, instruction: str) -> bytes | None:
    """
    Call Gemini-2.0-Flash-Exp with an input image + instruction.
    Returns the raw bytes of the generated output image, or None on failure.
    """
    with open(image_path, "rb") as fh:
        img_bytes = fh.read()
    mime = _mime_for(image_path)

    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    gtypes.Part.from_bytes(data=img_bytes, mime_type=mime),
                    gtypes.Part.from_text(text=instruction),
                ],
                config=gtypes.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )
            for part in response.candidates[0].content.parts:
                if getattr(part, "inline_data", None) is not None:
                    if part.inline_data.mime_type.startswith("image/"):
                        return part.inline_data.data
            print(f"    Warning: no image part in Gemini response (attempt {attempt})")
        except Exception as exc:
            print(f"    Gemini error (attempt {attempt}/3): {exc}")
            time.sleep(5 * attempt)
    return None


def run_inference(data: list[dict], image_base: Path) -> None:
    """
    Run Gemini-2.0-Flash-Exp on every sample in *data*, saving output images to
    OUTPUT_DIR/images/{category}/{index}.png.  Already-completed samples are skipped.
    """
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    todo = []
    for item in data:
        out_path = OUTPUT_DIR / "images" / item["category"] / f"{item['index']}.png"
        if not out_path.exists():
            todo.append(item)

    print(f"  {len(data) - len(todo)} already done, {len(todo)} remaining.")

    for item in tqdm(todo, desc="Inference"):
        index = item["index"]
        category = item["category"]
        out_dir = OUTPUT_DIR / "images" / category
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{index}.png"

        img_path = image_base / item["image"]
        if not img_path.exists():
            print(f"  [SKIP] missing input image: {img_path}")
            continue

        img_bytes = gemini_generate(client, img_path, item["instruction"])
        if img_bytes is None:
            print(f"  [FAIL] inference failed for {index}")
            continue

        out_path.write_bytes(img_bytes)


# ─── Evaluation helpers ───────────────────────────────────────────────────────

def _encode_image_b64(path: str | Path, size: int = 768) -> str:
    img = Image.open(path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((size, size))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def gpt_call(client: OpenAI, messages: list[dict]) -> str:
    """
    Send a multi-modal message list to GPT-4.1.
    Each element is {"type": "text"|"image", "value": str}.
    Returns the response text, or "" on repeated failure.
    """
    content: list[dict] = []
    for msg in messages:
        if msg["type"] == "text":
            content.append({"type": "text", "text": msg["value"]})
        elif msg["type"] == "image":
            b64 = _encode_image_b64(msg["value"])
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"},
            })

    for attempt in range(1, 6):
        try:
            resp = client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[{"role": "user", "content": content}],
                max_tokens=1024,
                temperature=0,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            print(f"    GPT-4.1 error (attempt {attempt}/5): {exc}")
            time.sleep(3 * attempt)
    return ""


def _find_output_image(index: str, category: str) -> Path | None:
    out_dir = OUTPUT_DIR / "images" / category
    for ext in ("png", "jpg", "jpeg"):
        p = out_dir / f"{index}.{ext}"
        if p.exists():
            return p
    return None


def eval_one(item: dict, image_base: Path, client: OpenAI) -> dict:
    """
    Run the GPT-4.1 judge on one sample.
    Returns a dict with keys: judge1, judge2, and (for non-logical) judge3.
    """
    index = item["index"]
    category = item["category"]
    instruction = item["instruction"]

    out_img = _find_output_image(index, category)
    if out_img is None:
        raise FileNotFoundError(f"No output image for {index}")

    img2 = str(out_img)
    img1 = str(image_base / item["image"])   # default: original input

    judge_rea_needs_img1 = False

    # ── Build per-dimension prompts depending on category ────────────────────
    if category in ("temporal_reasoning", "causal_reasoning"):
        reference = item.get("reference", "")
        reasoning_img = item.get("reasoning_img")
        if reasoning_img is not None and pd.notna(reasoning_img):
            judge_rea_needs_img1 = True
            prompt_rea = PROMPT_REASONING_W_INPUT.format(instruct=instruction, reference=reference)
        else:
            prompt_rea = PROMPT_REASONING.format(instruct=instruction, reference=reference)
        prompt_cons = PROMPT_CONSIST.format(instruct=instruction)
        prompt_qua = PROMPT_GENERATION

    elif category == "spatial_reasoning":
        reference_img = item.get("reference_img")
        reasoning_img = item.get("reasoning_img")
        reference = item.get("reference", "")
        if reference_img is not None and pd.notna(reference_img):
            judge_rea_needs_img1 = True
            img1 = str(image_base / reference_img)
            prompt_rea = PROMPT_SPATIAL_REF_IMG.format(instruct=instruction)
        elif reasoning_img is not None and pd.notna(reasoning_img):
            judge_rea_needs_img1 = True
            prompt_rea = PROMPT_SPATIAL_REF_W_INPUT.format(instruct=instruction, reference=reference)
        else:
            prompt_rea = PROMPT_SPATIAL_REF.format(instruct=instruction, reference=reference)
        prompt_cons = PROMPT_SPATIAL_CONS.format(instruct=instruction)
        prompt_qua = PROMPT_SPATIAL_QUAL

    elif category == "logical_reasoning":
        reference_txt = item.get("reference_txt")
        reference_img = item.get("reference_img")
        if reference_txt is not None and pd.notna(reference_txt):
            prompt_cons = PROMPT_LOGICAL_CONS_ANS.format(instruct=instruction, reference=reference_txt)
            prompt_rea = PROMPT_LOGICAL_TXT.format(instruct=instruction, reference=reference_txt)
        elif reference_img is not None and pd.notna(reference_img):
            judge_rea_needs_img1 = True
            img1 = str(image_base / reference_img)
            prompt_cons = PROMPT_LOGICAL_CONS.format(instruct=instruction)
            reasoning_wo_ins = item.get("reasoning_wo_ins")
            if reasoning_wo_ins is not None and pd.notna(reasoning_wo_ins):
                prompt_rea = PROMPT_LOGICAL_IMG_WO_Q
            else:
                prompt_rea = PROMPT_LOGICAL_IMG.format(instruct=instruction)
        else:
            # Fallback: treat like reference_txt with empty reference
            prompt_cons = PROMPT_LOGICAL_CONS.format(instruct=instruction)
            prompt_rea = PROMPT_LOGICAL_TXT.format(instruct=instruction, reference="")
    else:
        raise ValueError(f"Unknown category: {category}")

    result: dict = {}

    # Judge 1 — Appearance Consistency (skipped when consistency_free is set)
    consistency_free = item.get("consistency_free")
    if consistency_free is not None and pd.notna(consistency_free):
        result["judge1"] = None
    else:
        result["judge1"] = gpt_call(client, [
            {"type": "text",  "value": prompt_cons},
            {"type": "image", "value": img1},
            {"type": "image", "value": img2},
        ])

    # Judge 2 — Instruction Reasoning
    if judge_rea_needs_img1:
        msgs_rea = [
            {"type": "text",  "value": prompt_rea},
            {"type": "image", "value": img1},
            {"type": "image", "value": img2},
        ]
    else:
        msgs_rea = [
            {"type": "text",  "value": prompt_rea},
            {"type": "image", "value": img2},
        ]
    result["judge2"] = gpt_call(client, msgs_rea)

    # Judge 3 — Visual Plausibility (temporal / causal / spatial only)
    if category != "logical_reasoning":
        result["judge3"] = gpt_call(client, [
            {"type": "text",  "value": prompt_qua},
            {"type": "image", "value": img2},
        ])

    return result


def run_evaluation(data: list[dict], image_base: Path, nproc: int) -> dict:
    """
    Run GPT-4.1 judge on all samples.  Results are cached in a .pkl file so
    interrupted runs resume from where they left off.
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    cache_file = OUTPUT_DIR / f"{MODEL_NAME}.pkl"
    cache_lock = threading.Lock()

    cached: dict = {}
    if cache_file.exists():
        with open(cache_file, "rb") as fh:
            cached = pickle.load(fh)

    pending = [item for item in data if item["index"] not in cached]
    print(f"  {len(cached)} already evaluated, {len(pending)} remaining.")

    def _save():
        with open(cache_file, "wb") as fh:
            pickle.dump(cached, fh)

    with ThreadPoolExecutor(max_workers=nproc) as executor:
        futures = {
            executor.submit(eval_one, item, image_base, client): item["index"]
            for item in pending
        }
        for future in tqdm(as_completed(futures), total=len(futures), desc="Evaluation"):
            idx = futures[future]
            try:
                result = future.result()
                with cache_lock:
                    cached[idx] = result
                    _save()
            except Exception as exc:
                print(f"  [ERROR] {idx}: {exc}")

    return cached


# ─── Score extraction & metric computation ────────────────────────────────────

def extract_score(text: str) -> list[int] | None:
    """Return a list of integers parsed after 'Final Score:' in *text*."""
    for pattern in (
        r"\*?\*?Final Score\*?\*?:?\s*([\d*\s,\n]*)",
        r"\*?\*?Final Scores\*?\*?:?\s*([\d*\s,\n]*)",
    ):
        for match in re.findall(pattern, text, re.IGNORECASE):
            nums = re.findall(r"\d+", match.replace("\n", " "))
            if nums:
                return list(map(int, nums))
    return None


def _parse_scores(judge: dict, category: str) -> tuple[int | None, int | None, int | None]:
    """
    Parse raw judge responses into (ApprConsistency, Reasoning, VisualPlausibility).
    Logical reasoning uses binary (0/1) scoring mapped to (1 or 5).
    """
    j1 = judge.get("judge1")
    j2 = judge.get("judge2", "")
    j3 = judge.get("judge3")

    if category == "logical_reasoning":
        s1 = extract_score(j1) if j1 else None
        s2 = extract_score(j2) if j2 else None
        if s1 and s2:
            ac = 4 * min(s1[0], 1) + 1   # 0→1, 1→5
            r  = 4 * min(s2[0], 1) + 1
        else:
            ac = r = None
        return ac, r, None
    else:
        # j1 may be None when consistency_free
        s1 = extract_score(j1) if j1 else None
        s2 = extract_score(j2) if j2 else None
        s3 = extract_score(j3) if j3 else None
        ac = s1[0] if s1 else (None if j1 is not None else None)
        r  = s2[0] if s2 else None
        vp = s3[0] if s3 else None
        return ac, r, vp


def _is_complete(row: pd.Series) -> int:
    """Return 1 if the sample is 'successful' (all applicable scores == 5)."""
    category = row["category"]
    r  = row.get("Reasoning")
    ac = row.get("ApprConsistency")
    vp = row.get("VisualPlausibility")
    is_free = pd.notna(row.get("consistency_free"))

    if r is None:
        return 0

    if category in ("temporal_reasoning", "causal_reasoning", "spatial_reasoning"):
        if is_free:
            return 1 if r == 5 and vp == 5 else 0
        return 1 if ac == 5 and r == 5 and vp == 5 else 0
    elif category == "logical_reasoning":
        if ac is None:
            return 0
        return 1 if ac == 5 and r == 5 else 0
    return 0


def compute_metrics(data: list[dict], results: dict) -> pd.DataFrame:
    df = pd.DataFrame(data)
    ac_list, rea_list, vp_list = [], [], []

    for _, row in df.iterrows():
        judge = results.get(row["index"], {})
        ac, r, vp = _parse_scores(judge, row["category"])
        ac_list.append(ac)
        rea_list.append(r)
        vp_list.append(vp)

    df["ApprConsistency"]  = ac_list
    df["Reasoning"]        = rea_list
    df["VisualPlausibility"] = vp_list
    df["complete"]         = df.apply(_is_complete, axis=1)
    return df


def print_results(df: pd.DataFrame) -> None:
    CATEGORY_LABELS = {
        "temporal_reasoning": "Temporal",
        "causal_reasoning":   "Causal",
        "spatial_reasoning":  "Spatial",
        "logical_reasoning":  "Logical",
    }
    print()
    print(f"{'Subtask':<12}  {'Accuracy':>10}  {'Success / Total':>16}")
    print("-" * 44)

    total_ok = 0
    total_n  = 0
    for cat, label in CATEGORY_LABELS.items():
        sub = df[df["category"] == cat]
        n   = len(sub)
        ok  = int(sub["complete"].sum())
        acc = ok / n * 100 if n else 0.0
        total_ok += ok
        total_n  += n
        print(f"  {label:<10}  {acc:>8.1f}%  {ok:>6} / {n:<6}")

    overall = total_ok / total_n * 100 if total_n else 0.0
    print("-" * 44)
    print(f"  {'Overall':<10}  {overall:>8.1f}%  {total_ok:>6} / {total_n:<6}")
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    global HF_DATA_DIR, MODEL_NAME  # declared here so all references below are valid

    parser = argparse.ArgumentParser(
        description="RISEBench evaluation: Gemini-2.0-Flash-Experimental + GPT-4.1 Judge"
    )
    parser.add_argument(
        "--skip-inference", action="store_true",
        help="Skip the inference phase (assume outputs already exist).",
    )
    parser.add_argument(
        "--skip-eval", action="store_true",
        help="Skip the evaluation phase (only run inference).",
    )
    parser.add_argument(
        "--nproc", type=int, default=NPROC,
        help=f"Parallel threads for the GPT-4.1 judge (default: {NPROC}).",
    )
    parser.add_argument(
        "--data-dir", type=str, default=None,
        help="Path to an already-downloaded RISEBench dataset directory.",
    )
    parser.add_argument(
        "--sample", type=str, default=None,
        help=(
            "Comma-separated list of sample indices to process, e.g. "
            "'logical_reasoning_1' or 'temporal_reasoning_3,causal_reasoning_7'. "
            "When set, only those samples are run (good for quick proof-of-concept)."
        ),
    )
    parser.add_argument(
        "--model", type=str, default=MODEL_NAME,
        help=(
            f"Gemini model to use for inference (default: {MODEL_NAME}). "
            "Override when the default has been retired, e.g. "
            "--model gemini-2.5-flash-image"
        ),
    )
    parser.add_argument(
        "--use-github-output", action="store_true",
        help=(
            "When combined with --sample and --skip-inference, download the "
            "pre-built output image(s) from the RISEBench GitHub repo instead "
            "of running Gemini inference.  Requires no API keys for the "
            "inference phase."
        ),
    )
    args = parser.parse_args()

    # Allow caller to override the inference model and dataset directory
    MODEL_NAME = args.model
    if args.data_dir:
        HF_DATA_DIR = Path(args.data_dir)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Dataset ──────────────────────────────────────────────────────────
    # In single-sample / proof-of-concept mode we fetch only what we need from
    # GitHub instead of cloning the whole dataset.
    sample_indices: set[str] = set()
    if args.sample:
        sample_indices = {s.strip() for s in args.sample.split(",") if s.strip()}

    # Step 1: ensure the data JSON exists locally
    if sample_indices:
        # Fetch only data_total.json from GitHub (no full clone needed)
        (HF_DATA_DIR / "data").mkdir(parents=True, exist_ok=True)
        _download_url(
            f"{_GITHUB_RAW}/data/data_total.json",
            HF_DATA_DIR / "data" / "data_total.json",
        )
    else:
        download_dataset()

    data_json = find_data_json()

    with open(data_json) as fh:
        raw_data: list[dict] = json.load(fh)

    # Step 2: filter to requested samples and download their images from GitHub
    if sample_indices:
        data = [item for item in raw_data if item["index"] in sample_indices]
        missing = sample_indices - {item["index"] for item in data}
        if missing:
            raise ValueError(f"Sample index(es) not found in dataset: {missing}")
        print(f"Samples: {len(data)} (filtered from {len(raw_data)})")
        for item in data:
            prepare_sample_from_github(item, use_github_output=args.use_github_output)
    else:
        data = raw_data
        print(f"Samples: {len(data)}")

    # Step 3: locate image base dir (must come after images are downloaded)
    image_base = find_image_base()
    print(f"Data   : {data_json}")
    print(f"Images : {image_base}")

    # ── 2. Inference ────────────────────────────────────────────────────────
    if not args.skip_inference:
        print("\n=== Phase 1 — Inference (Gemini-2.0-Flash-Exp) ===")
        run_inference(data, image_base)

    # ── 3. Evaluation ───────────────────────────────────────────────────────
    if not args.skip_eval:
        print("\n=== Phase 2 — Evaluation (GPT-4.1 Judge) ===")
        results = run_evaluation(data, image_base, nproc=args.nproc)
    else:
        cache_file = OUTPUT_DIR / f"{MODEL_NAME}.pkl"
        if cache_file.exists():
            with open(cache_file, "rb") as fh:
                results = pickle.load(fh)
        else:
            print("No cached evaluation results found; re-running evaluation.")
            results = run_evaluation(data, image_base, nproc=args.nproc)

    # ── 4. Metrics ──────────────────────────────────────────────────────────
    print("\n=== Results ===")
    df = compute_metrics(data, results)
    print_results(df)

    scores_csv = OUTPUT_DIR / f"{MODEL_NAME}_scores.csv"
    df.to_csv(scores_csv, index=False)
    print(f"Detailed scores saved to {scores_csv}")


if __name__ == "__main__":
    main()

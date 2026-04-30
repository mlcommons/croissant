#!/usr/bin/env python3
"""
Evaluate Gemini 2.5 Pro on CoRe Lite — Control Dependency (pairwise trace) subtask.

Runs up to 500 instances from CoRe Lite in parallel, computes F1 and Correct
Trace Rate, saves raw responses to ./raw_outputs/gemini-2-5-pro/ (next to this
script), and updates ./core_solution_gemini-2-5-pro.jsonld with the computed
metrics.

Usage (run from this directory):
    GEMINI_API_KEY=<key> python core_implementation_gemini-2-5-pro.py

Expected (paper Table 4, CoRe Lite, Control Dependency, gemini-2.5-pro-preview-05-06):
    F1  = 92.49 %
    CT  = 92.26 %

Note: this script targets the stable `gemini-2.5-pro` endpoint, not the
`gemini-2.5-pro-preview-05-06` endpoint used in the paper, so numbers are
not directly comparable.
"""

import asyncio
import json
import os
import re
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from google import genai
from google.genai import types

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent
OUTPUT_DIR    = SCRIPT_DIR / "raw_outputs" / "gemini-2-5-pro"
RESPONSES_FILE = OUTPUT_DIR / "control_dep_trace.jsonl"
METRICS_FILE  = OUTPUT_DIR / "control_dep_trace_metrics.json"
SOLUTION_FILE = SCRIPT_DIR / "core_solution_gemini-2-5-pro.jsonld"
ANNOTATION_CACHE_DIR = OUTPUT_DIR / "_annotation_cache"

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_ID       = "gemini-2.5-pro"
DATASET_URL    = "https://huggingface.co/datasets/lt-asset/CoRe/resolve/main/data.jsonl"
LITE_JSON_URL  = "https://raw.githubusercontent.com/CoReBench/CoRe/main/lite.json"
ANNOT_BASE_URL = "https://raw.githubusercontent.com/CoReBench/CoRe/main/raw_annotation"
MAX_INSTANCES  = 500
MAX_RETRIES    = 3
MAX_TOKENS     = 2048
CONCURRENCY    = 8   # parallel Gemini calls; tune down if hitting rate limits

FALLBACK_PROMPT = (
    "Your previous response could not be parsed correctly. "
    "Please re-read the prompt and ensure your answer strictly follows the "
    "required JSON format enclosed with ```<your response here>```. "
    "Ensure that your JSON is valid and matches the specification. Try again:"
)


# ── Gemini setup ──────────────────────────────────────────────────────────────
def _init_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY not set. Export it in your shell before running."
        )
    return genai.Client(api_key=api_key)


# ── Data loading ──────────────────────────────────────────────────────────────
def _fetch_url(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CoRe-eval/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _load_lite_ids() -> set:
    print("  Fetching lite.json from GitHub…")
    data = json.loads(_fetch_url(LITE_JSON_URL))
    ctrl = data["control"]
    ids = set(ctrl.get("C", [])) | set(ctrl.get("Java", [])) | set(ctrl.get("Python", []))
    print(f"  Loaded {len(ids)} CoRe Lite control_dep IDs")
    return ids


def load_instances() -> list[dict]:
    print("Loading dataset from HuggingFace (raw JSONL)…")
    raw = _fetch_url(DATASET_URL, timeout=120)
    lines = raw.decode().splitlines()
    print(f"  Total lines: {len(lines)}")

    lite_ids = _load_lite_ids()

    instances: list[dict] = []
    for line in lines:
        if not line.strip():
            continue
        item = json.loads(line)
        if not item["task_id"].startswith("control_"):
            continue
        if item.get("category", "") != "trace":
            continue
        if item["task_id"] not in lite_ids:
            continue
        instances.append(item)

    print(f"  Found {len(instances)} control_dep trace instances in CoRe Lite")

    if len(instances) > MAX_INSTANCES:
        import random
        random.seed(42)
        instances = random.sample(instances, MAX_INSTANCES)
        print(f"  Sampled {MAX_INSTANCES} instances")

    return instances


# ── Annotation / trace validation ─────────────────────────────────────────────
_annot_cache_lock = threading.Lock()
_annot_mem_cache: dict[str, Optional[dict]] = {}


def _load_annotation(label_file: str, language: str) -> Optional[dict]:
    key = f"{language}/{label_file}"
    with _annot_cache_lock:
        if key in _annot_mem_cache:
            return _annot_mem_cache[key]

    cache_path = ANNOTATION_CACHE_DIR / language / label_file
    result: Optional[dict] = None
    if cache_path.exists():
        with open(cache_path) as f:
            result = yaml.safe_load(f)
    else:
        url = f"{ANNOT_BASE_URL}/{language}/label/{label_file}"
        try:
            content = _fetch_url(url, timeout=15).decode()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(content)
            result = yaml.safe_load(content)
        except Exception as exc:
            print(f"\n    WARNING: could not load annotation {label_file}: {exc}")

    with _annot_cache_lock:
        _annot_mem_cache[key] = result
    return result


def _build_direct_ctrl_edges(annotation: dict) -> set[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    variables = annotation.get("variables") or {}
    for var_key, var_data in variables.items():
        if not var_data:
            continue
        parts = var_key.strip().split()
        if len(parts) < 2:
            continue
        try:
            dst_line = int(parts[-1])
        except ValueError:
            continue
        controldep = var_data.get("controldep") or []
        if not isinstance(controldep, list):
            continue
        for entry in controldep:
            if not isinstance(entry, str):
                continue
            ep = entry.strip().split()
            if len(ep) < 2:
                continue
            try:
                src_line = int(ep[-1])
            except ValueError:
                continue
            if src_line != dst_line:
                edges.add((src_line, dst_line))
    return edges


def check_trace_correct(pred_trace: list, instance: dict) -> bool:
    if not pred_trace or len(pred_trace) < 2:
        return False
    src = instance.get("src")
    dst = instance.get("dst")
    try:
        if int(pred_trace[0]) != int(src) or int(pred_trace[-1]) != int(dst):
            return False
    except (TypeError, ValueError):
        return False
    annotation = _load_annotation(instance["label_file"], instance["language"])
    if annotation is None:
        return False
    dep_edges = _build_direct_ctrl_edges(annotation)
    for i in range(len(pred_trace) - 1):
        try:
            edge = (int(pred_trace[i]), int(pred_trace[i + 1]))
        except (TypeError, ValueError):
            return False
        if edge not in dep_edges:
            return False
    return True


# ── Response parsing ──────────────────────────────────────────────────────────
def _parse_response(text: str) -> Optional[dict]:
    patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{"ControlDependence".*?\})',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _extract_pred_label(parsed: Optional[dict]) -> bool:
    if parsed is None:
        return False
    val = parsed.get("ControlDependence")
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() == "true"
    return False


def _extract_pred_trace(parsed: Optional[dict]) -> list:
    if parsed is None:
        return []
    trace = parsed.get("Trace", [])
    return trace if isinstance(trace, list) else []


# ── Async Gemini querying ─────────────────────────────────────────────────────
async def query_gemini_async(
    client: genai.Client,
    prompt_text: str,
    task_id: str,
    sem: asyncio.Semaphore,
) -> tuple[Optional[str], Optional[dict], bool]:
    """Returns (raw_text, parsed_dict, api_failed)."""
    gen_cfg = types.GenerateContentConfig(temperature=0, max_output_tokens=MAX_TOKENS)
    raw_text: Optional[str] = None

    async with sem:
        chat = client.aio.chats.create(model=MODEL_ID, config=gen_cfg)
        for attempt in range(MAX_RETRIES):
            msg = prompt_text if attempt == 0 else FALLBACK_PROMPT
            try:
                response = await chat.send_message(msg)
                raw_text = response.text
                parsed = _parse_response(raw_text)
                if parsed is not None:
                    return raw_text, parsed, False
                # parse failure → retry with fallback prompt in same chat session
            except Exception as exc:
                wait = min(2 ** attempt, 30)
                print(f"\n  [{task_id}] API err (attempt {attempt+1}): {exc} — retrying in {wait}s")
                await asyncio.sleep(wait)

    return raw_text, None, (raw_text is None)


# ── Metrics ───────────────────────────────────────────────────────────────────
def compute_metrics(results: list[dict]) -> dict:
    tp = fp = fn = tn = 0
    correct_traces = total_pred_pos = api_failures = 0

    for r in results:
        pred, true = r["pred_label"], r["label"]
        if r.get("api_failed"):
            api_failures += 1
        if pred and true:
            tp += 1
        elif pred:
            fp += 1
        elif true:
            fn += 1
        else:
            tn += 1
        if pred:
            total_pred_pos += 1
            if r.get("trace_correct", False):
                correct_traces += 1

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    ct   = correct_traces / total_pred_pos if total_pred_pos > 0 else 0.0

    return {
        "f1":               round(f1 * 100, 2),
        "precision":        round(prec * 100, 2),
        "recall":           round(rec * 100, 2),
        "ct":               round(ct * 100, 2),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "correct_traces":   correct_traces,
        "total_pred_pos":   total_pred_pos,
        "n_instances":      len(results),
        "n_parse_failures": sum(1 for r in results if not r["parse_success"]),
        "n_api_failures":   api_failures,
    }


# ── Incremental I/O ───────────────────────────────────────────────────────────
_write_lock = threading.Lock()


def load_done(path: Path) -> dict:
    """Only count instances with a valid response as done; failures get re-queued."""
    done: dict = {}
    if path.exists():
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    if not r.get("api_failed") and r.get("parse_success"):
                        done[r["task_id"]] = r
    return done


def append_result(path: Path, result: dict):
    with _write_lock:
        with open(path, "a") as f:
            f.write(json.dumps(result) + "\n")


# ── TaskSolution update ───────────────────────────────────────────────────────
def update_solution_file(metrics: dict, run_ts: str):
    with open(SOLUTION_FILE) as f:
        solution = json.load(f)

    ctrl_id = "http://example.org/core-benchmark_solution_gemini-2-5-pro#control_dependency_sol"
    for subtask in solution.get("croissant:subTask", []):
        if subtask.get("@id") != ctrl_id:
            continue
        for result in subtask["croissant:evaluation"]["croissant:evaluationResults"]:
            m = result.get("croissant:metric", "")
            if m == "F1 Score":
                result["croissant:value"] = str(metrics["f1"])
                result["croissant:computedAt"] = run_ts
            elif m == "Correct Trace Rate":
                result["croissant:value"] = str(metrics["ct"])
                result["croissant:computedAt"] = run_ts
        subtask["croissant:output"]["schema:contentUrl"] = str(
            RESPONSES_FILE.relative_to(SCRIPT_DIR)
        )
        break

    exec_cfg = solution.get("croissant:execution", {})
    exec_cfg["croissant:runTimestamp"]  = run_ts
    exec_cfg["croissant:modelId"]       = MODEL_ID
    exec_cfg["croissant:instanceCount"] = metrics["n_instances"]

    with open(SOLUTION_FILE, "w") as f:
        json.dump(solution, f, indent=2)
    print(f"TaskSolution updated: {SOLUTION_FILE}")


# ── Async worker ──────────────────────────────────────────────────────────────
async def process_instance(
    client: genai.Client,
    inst: dict,
    idx: int,
    total: int,
    sem: asyncio.Semaphore,
    results: list,
) -> None:
    task_id = inst["task_id"]
    label   = bool(inst["groundtruth"])

    raw_text, parsed, api_failed = await query_gemini_async(
        client, inst["prompt"], task_id, sem
    )

    pred_label    = _extract_pred_label(parsed)
    pred_trace    = _extract_pred_trace(parsed) if pred_label else []
    trace_correct = check_trace_correct(pred_trace, inst) if pred_label else False

    result = {
        "task_id":       task_id,
        "label":         label,
        "pred_label":    pred_label,
        "pred_trace":    pred_trace,
        "trace_correct": trace_correct,
        "raw_response":  raw_text,
        "parse_success": parsed is not None,
        "api_failed":    api_failed,
        "timestamp":     datetime.now(timezone.utc).isoformat(),
    }
    append_result(RESPONSES_FILE, result)
    results.append(result)

    status = "API_FAIL" if api_failed else ("parse_fail" if parsed is None else
             ("✓" if pred_label == label else "✗"))
    trace_sym = f"trace={'✓' if trace_correct else '✗'}" if pred_label else "trace=N/A"
    print(f"[{idx:>3}/{total}] {task_id[:60]}  pred={pred_label} {status}  {trace_sym}")


# ── Main ──────────────────────────────────────────────────────────────────────
async def async_main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATION_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    client    = _init_client()
    instances = load_instances()
    if not instances:
        print("No instances found.")
        return

    print("\nDataset fields:", list(instances[0].keys()))
    print(f"Example — task_id={instances[0]['task_id']}  "
          f"src={instances[0]['src']}  dst={instances[0]['dst']}  "
          f"groundtruth={instances[0]['groundtruth']}")

    done    = load_done(RESPONSES_FILE)
    results = list(done.values())
    todo    = [inst for inst in instances if inst["task_id"] not in done]
    print(f"\nAlready done: {len(done)} / {len(instances)}  ({len(todo)} remaining)")
    print(f"Running with CONCURRENCY={CONCURRENCY}\n")

    sem = asyncio.Semaphore(CONCURRENCY)
    total = len(todo)
    tasks = [
        process_instance(client, inst, idx, total, sem, results)
        for idx, inst in enumerate(todo, 1)
    ]
    await asyncio.gather(*tasks)

    metrics = compute_metrics(results)
    run_ts  = datetime.now(timezone.utc).isoformat()

    print(f"\n{'='*60}")
    print(f"Results  ({metrics['n_instances']} instances,  "
          f"{metrics['n_parse_failures']} parse failures,  "
          f"{metrics['n_api_failures']} API failures)")
    print(f"  Precision : {metrics['precision']:.2f} %")
    print(f"  Recall    : {metrics['recall']:.2f} %")
    print(f"  F1 Score  : {metrics['f1']:.2f} %   (paper: 92.49 %)")
    print(f"  CT Rate   : {metrics['ct']:.2f} %   (paper: 92.26 %)")
    print(f"  TP/FP/FN/TN : {metrics['tp']}/{metrics['fp']}/{metrics['fn']}/{metrics['tn']}")
    print(f"  Correct traces : {metrics['correct_traces']} / {metrics['total_pred_pos']}")
    print(f"{'='*60}\n")

    with open(METRICS_FILE, "w") as f:
        json.dump({
            "model":         MODEL_ID,
            "task":          "control_dependency_trace",
            "run_timestamp": run_ts,
            "metrics":       metrics,
            "expected_f1":   92.49,
            "expected_ct":   92.26,
        }, f, indent=2)
    print(f"Metrics saved: {METRICS_FILE}")

    update_solution_file(metrics, run_ts)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Prepare and finalize AbsenceBench ablation runs.

This script supports two conditions:
  - paper_only: prompts follow Appendix A wording from the paper.
  - ct_only: prompts are derived only from TaskProblem-level semantics.

Workflow:
  1) prepare prompts JSONL files for each condition/domain
  2) collect model raw responses (written externally into responses/*.jsonl)
  3) finalize metrics, bootstrap CIs, solution JSON-LD, and manifest
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from datasets import load_dataset

RUN_ROOT = Path(__file__).resolve().parent.parent
DATASET_ID = "harveyfin/AbsenceBench"
DATASET_SPLIT = "validation"
DOMAINS = ("poetry", "numerical", "github_prs")

DEFAULT_MODEL = "claude-4-sonnet"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_PER_SUBSET = 20
DEFAULT_BOOTSTRAP_ITERS = 1000
DEFAULT_BOOTSTRAP_SEED = 42


PAPER_PROMPT_TEMPLATES: dict[str, dict[str, str]] = {
    "poetry": {
        "system": (
            "You are helping a student practice memorizing poems. The student"
            " will recite a poem, but they may have missed some lines. Your"
            " task is to identify exactly which lines are missing from their"
            " recitation. List only the missing lines, nothing else."
        ),
        "user": (
            "Here is the complete original poem:\n{original}\n\nNow, here is"
            " my recitation which may be missing some lines:\n{modified}\n\n"
            "What lines did I miss? Please list only the missing lines,"
            " nothing else."
        ),
    },
    "numerical": {
        "system": (
            "You are helping a student practice reciting sequences. The"
            " student will recite a sequence, but they may have missed some"
            " numbers. Your task is to identify exactly which numbers are"
            " missing from their recitation. List only the missing numbers,"
            " nothing else."
        ),
        "user": (
            "Here is a sequence of numbers:\n{original}\n\nNow, here is my"
            " recitation of the sequence which may be missing some"
            " numbers:\n{modified}\n\nWhat numbers did I miss? Please list"
            " only the missing numbers, nothing else."
        ),
    },
    "github_prs": {
        "system": (
            "You are helping a software developer determine if their merge of"
            " a pull request was successful. The developer had to edit the"
            " commit history and just wants to make sure that they have not"
            " changed what will be merged. They will list the changed lines."
            " Your job is to figure out if they have missed any insertions or"
            " deletions from the original merge. Only pay attention to the"
            " insertions and deletions (ignore the context of the diff)."
        ),
        "user": (
            "Here is the complete original diff:\n{original}\n\nAnd here is"
            " the merge diff after the developer fixed the commit"
            " history:\n{modified}\n\nWhat changed lines (insertions or"
            " deletions) present in the original diff are missing in the"
            " merge diff (if any)? List only the missing changed lines,"
            " nothing else."
        ),
    },
}


CT_ONLY_PROMPT_TEMPLATES: dict[str, dict[str, str]] = {
    "poetry": {
        "system": (
            "You solve omission-detection tasks. Given an original text and a"
            " modified text, output only the omitted elements, one per line."
        ),
        "user": (
            "Subtask: poetry omission detection.\n\nOriginal context:\n{original}"
            "\n\nModified context:\n{modified}\n\nReturn only the missing lines"
            " from the original context, one per line, with no commentary."
        ),
    },
    "numerical": {
        "system": (
            "You solve omission-detection tasks. Given an original text and a"
            " modified text, output only the omitted elements, one per line."
        ),
        "user": (
            "Subtask: numerical omission detection.\n\nOriginal context:\n{original}"
            "\n\nModified context:\n{modified}\n\nReturn only the missing numbers"
            " from the original context, one per line, with no commentary."
        ),
    },
    "github_prs": {
        "system": (
            "You solve omission-detection tasks. Given an original text and a"
            " modified text, output only the omitted elements, one per line."
        ),
        "user": (
            "Subtask: GitHub PR diff omission detection.\n\nOriginal context:\n{original}"
            "\n\nModified context:\n{modified}\n\nReturn only changed lines from"
            " the original context that are missing in the modified context,"
            " one per line, with no commentary."
        ),
    },
}


def utc_now_iso() -> str:
  return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def model_slug(model: str) -> str:
  return model.lower().replace(".", "-").replace(" ", "-")


def parse_predictions(raw: str) -> list[str]:
  return [line.strip() for line in raw.splitlines() if line.strip()]


def normalize(s: str) -> str:
  return s.strip()


def per_instance_metrics(gold: list[str], pred: list[str]) -> dict[str, float | int]:
  gold_norm = [normalize(g) for g in gold if normalize(g)]
  pred_norm = [normalize(p) for p in pred if normalize(p)]

  gold_pool = list(gold_norm)
  tp = 0
  for p in pred_norm:
    if p in gold_pool:
      tp += 1
      gold_pool.remove(p)
  fp = len(pred_norm) - tp
  fn = len(gold_norm) - tp
  exact_match = int(sorted(gold_norm) == sorted(pred_norm))
  return {"tp": tp, "fp": fp, "fn": fn, "exact_match": exact_match}


def aggregate(metrics_per_instance: list[dict[str, float | int]]) -> dict[str, float]:
  if not metrics_per_instance:
    return {"f1": 0.0, "precision": 0.0, "recall": 0.0, "exact_match_rate": 0.0, "n": 0}
  tp = sum(m["tp"] for m in metrics_per_instance)
  fp = sum(m["fp"] for m in metrics_per_instance)
  fn = sum(m["fn"] for m in metrics_per_instance)
  prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
  rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
  f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
  em = sum(m["exact_match"] for m in metrics_per_instance) / len(metrics_per_instance)
  return {
      "f1": f1,
      "precision": prec,
      "recall": rec,
      "exact_match_rate": em,
      "n": len(metrics_per_instance),
  }


def percentile(values: list[float], q: float) -> float:
  if not values:
    return 0.0
  vals = sorted(values)
  if len(vals) == 1:
    return vals[0]
  pos = q * (len(vals) - 1)
  lo = int(math.floor(pos))
  hi = int(math.ceil(pos))
  if lo == hi:
    return vals[lo]
  frac = pos - lo
  return vals[lo] * (1.0 - frac) + vals[hi] * frac


def bootstrap_summary(
    metrics_per_instance: list[dict[str, float | int]],
    iters: int,
    seed: int,
) -> dict[str, Any]:
  if not metrics_per_instance:
    return {
        "iters": iters,
        "seed": seed,
        "mean": {"f1": 0.0, "exact_match_rate": 0.0},
        "ci95": {"f1": [0.0, 0.0], "exact_match_rate": [0.0, 0.0]},
    }

  rng = random.Random(seed)
  n = len(metrics_per_instance)
  f1_vals: list[float] = []
  em_vals: list[float] = []
  for _ in range(iters):
    sample = [metrics_per_instance[rng.randrange(n)] for _ in range(n)]
    agg = aggregate(sample)
    f1_vals.append(agg["f1"])
    em_vals.append(agg["exact_match_rate"])

  return {
      "iters": iters,
      "seed": seed,
      "mean": {
          "f1": sum(f1_vals) / len(f1_vals),
          "exact_match_rate": sum(em_vals) / len(em_vals),
      },
      "ci95": {
          "f1": [percentile(f1_vals, 0.025), percentile(f1_vals, 0.975)],
          "exact_match_rate": [percentile(em_vals, 0.025), percentile(em_vals, 0.975)],
      },
  }


def condition_templates(condition: str) -> dict[str, dict[str, str]]:
  if condition == "paper_only":
    return PAPER_PROMPT_TEMPLATES
  if condition == "ct_only":
    return CT_ONLY_PROMPT_TEMPLATES
  raise ValueError(f"Unsupported condition: {condition}")


def build_messages(
    condition: str,
    domain: str,
    original: str,
    modified: str,
) -> tuple[str, str]:
  tmpl = condition_templates(condition)[domain]
  system = tmpl["system"]
  user = tmpl["user"].format(original=original, modified=modified)
  return system, user


def read_jsonl(path: Path) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  with open(path) as f:
    for line in f:
      if line.strip():
        rows.append(json.loads(line))
  return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
  with open(path, "w") as f:
    for row in rows:
      f.write(json.dumps(row) + "\n")


def load_subset(domain: str, max_per_subset: int) -> list[dict[str, Any]]:
  ds = load_dataset(DATASET_ID, domain, split=DATASET_SPLIT)
  if max_per_subset and max_per_subset > 0:
    ds = ds.select(range(min(max_per_subset, len(ds))))
  return list(ds)


def update_solution_file(
    solution_path: Path,
    model: str,
    temperature: float,
    max_tokens: int,
    per_domain: dict[str, dict[str, float]],
    overall: dict[str, float],
) -> None:
  with open(solution_path) as f:
    sol = json.load(f)

  exec_id = f"{sol['@id']}#execution"
  impl_id = f"{sol['@id']}#implementation"

  hyperparameters = [
      {
          "@type": "schema:PropertyValue",
          "schema:name": "model",
          "schema:value": model,
      },
      {
          "@type": "schema:PropertyValue",
          "schema:name": "temperature",
          "schema:value": temperature,
      },
      {
          "@type": "schema:PropertyValue",
          "schema:name": "max_tokens",
          "schema:value": max_tokens,
      },
      {
          "@type": "schema:PropertyValue",
          "schema:name": "instances_per_subset",
          "schema:value": int(overall["n"] / max(len(per_domain), 1)),
      },
  ]
  sol["croissant:execution"] = {
      "@type": "croissant:ExecutionConfig",
      "@id": exec_id,
      "croissant:hyperparameter": hyperparameters,
  }
  sol["croissant:implementation"] = {
      "@type": "schema:SoftwareApplication",
      "@id": impl_id,
      "schema:name": f"Cursor subagent runner - {model}",
  }

  domain_to_subproblem_id = {
      "poetry": "http://example.org/absencebench#poetry",
      "numerical": "http://example.org/absencebench#numerical",
      "github_prs": "http://example.org/absencebench#github_prs",
  }
  for sub in sol.get("croissant:subTask", []):
    based_on = sub.get("schema:isBasedOn", {}).get("@id", "")
    domain = next(
        (d for d, pid in domain_to_subproblem_id.items() if pid == based_on),
        None,
    )
    if domain is None or domain not in per_domain:
      continue
    sub["croissant:execution"] = {"@id": exec_id}
    sub["croissant:implementation"] = {"@id": impl_id}
    metrics = per_domain[domain]
    eval_block = sub.setdefault("croissant:evaluation", {})
    eval_block["croissant:evaluationResults"] = [
        {
            "@type": "croissant:EvaluationResult",
            "croissant:metric": "F1-Score",
            "croissant:value": f"{metrics['f1']*100:.2f}",
            "schema:description": (
                f"Micro F1-score on {int(metrics['n'])} instances of the"
                f" {domain} subtask."
            ),
        },
        {
            "@type": "croissant:EvaluationResult",
            "croissant:metric": "Exact Match",
            "croissant:value": f"{metrics['exact_match_rate']*100:.2f}",
            "schema:description": (
                f"Per-instance exact-match rate on {int(metrics['n'])}"
                f" instances of the {domain} subtask."
            ),
        },
    ]

  top_eval = sol.setdefault("croissant:evaluation", {})
  top_eval["croissant:evaluationResults"] = [
      {
          "@type": "croissant:EvaluationResult",
          "croissant:metric": "F1-Score",
          "croissant:value": f"{overall['f1']*100:.2f}",
          "schema:description": (
              "Overall (pooled) Micro F1-score across all"
              f" {int(overall['n'])} evaluated instances across the 3"
              " subtasks."
          ),
      },
      {
          "@type": "croissant:EvaluationResult",
          "croissant:metric": "Exact Match",
          "croissant:value": f"{overall['exact_match_rate']*100:.2f}",
          "schema:description": (
              "Overall per-instance exact-match rate across all"
              f" {int(overall['n'])} evaluated instances."
          ),
      },
  ]

  with open(solution_path, "w") as f:
    json.dump(sol, f, indent=2)
    f.write("\n")


def prepare_condition(condition: str, max_per_subset: int) -> None:
  cond_dir = RUN_ROOT / condition
  prompts_dir = cond_dir / "prompts"
  prompts_dir.mkdir(parents=True, exist_ok=True)

  domain_counts: dict[str, int] = {}
  for domain in DOMAINS:
    rows: list[dict[str, Any]] = []
    for ex in load_subset(domain, max_per_subset):
      iid = int(ex["id"])
      system, user = build_messages(condition, domain, ex["original_context"], ex["modified_context"])
      rows.append(
          {
              "id": iid,
              "domain": domain,
              "system": system,
              "user": user,
          }
      )
    out_path = prompts_dir / f"prompts_{domain}.jsonl"
    write_jsonl(out_path, rows)
    domain_counts[domain] = len(rows)

  manifest = {
      "prepared_utc": utc_now_iso(),
      "condition": condition,
      "prompt_source": "paper_appendix_a" if condition == "paper_only" else "ct_only_generic",
      "dataset": {
          "id": DATASET_ID,
          "split": DATASET_SPLIT,
          "max_per_subset": max_per_subset,
      },
      "domain_counts": domain_counts,
      "paths": {
          "prompts_dir": str(prompts_dir.relative_to(RUN_ROOT)),
      },
  }
  with open(prompts_dir / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")


def finalize_condition(
    condition: str,
    max_per_subset: int,
    model: str,
    temperature: float,
    max_tokens: int,
    bootstrap_iters: int,
    bootstrap_seed: int,
) -> None:
  cond_dir = RUN_ROOT / condition
  responses_dir = cond_dir / "responses"
  output_dir = cond_dir / "raw_outputs" / model_slug(model)
  output_dir.mkdir(parents=True, exist_ok=True)

  all_metrics: list[dict[str, float | int]] = []
  all_instance_ids: dict[str, list[int]] = {}
  per_domain_agg: dict[str, dict[str, float]] = {}
  per_domain_bootstrap: dict[str, dict[str, Any]] = {}

  for domain in DOMAINS:
    response_path = responses_dir / f"responses_{domain}.jsonl"
    if not response_path.exists():
      raise FileNotFoundError(f"Missing responses file: {response_path}")
    response_rows = read_jsonl(response_path)
    response_by_id = {int(row["id"]): row.get("raw_response", "") for row in response_rows}

    records: list[dict[str, Any]] = []
    domain_metrics: list[dict[str, float | int]] = []
    ids: list[int] = []
    for ex in load_subset(domain, max_per_subset):
      iid = int(ex["id"])
      if iid not in response_by_id:
        raise ValueError(
            f"Missing response for {condition}/{domain} id={iid}"
        )
      raw = response_by_id[iid]
      gold = list(ex["omitted_context"]) or []
      pred = parse_predictions(raw)
      metrics = per_instance_metrics(gold, pred)
      rec = {
          "id": iid,
          "domain": domain,
          "gold": gold,
          "pred": pred,
          "raw_response": raw,
          "metrics": metrics,
          "model": model,
          "ts": time.time(),
      }
      records.append(rec)
      domain_metrics.append(metrics)
      all_metrics.append(metrics)
      ids.append(iid)

    write_jsonl(output_dir / f"outputs_{domain}.jsonl", records)
    per_domain_agg[domain] = aggregate(domain_metrics)
    per_domain_bootstrap[domain] = bootstrap_summary(
        domain_metrics, bootstrap_iters, bootstrap_seed
    )
    all_instance_ids[domain] = ids

  overall_agg = aggregate(all_metrics)
  overall_bootstrap = bootstrap_summary(all_metrics, bootstrap_iters, bootstrap_seed)

  solution_path = cond_dir / "absencebench_claude-4-sonnet_solution.jsonld"
  update_solution_file(
      solution_path=solution_path,
      model=model,
      temperature=temperature,
      max_tokens=max_tokens,
      per_domain=per_domain_agg,
      overall=overall_agg,
  )

  bootstrap_path = output_dir / "bootstrap_metrics.json"
  bootstrap_obj = {
      "condition": condition,
      "iters": bootstrap_iters,
      "seed": bootstrap_seed,
      "per_domain": per_domain_bootstrap,
      "overall": overall_bootstrap,
  }
  with open(bootstrap_path, "w") as f:
    json.dump(bootstrap_obj, f, indent=2)
    f.write("\n")

  def pct(x: float) -> float:
    return round(x * 100.0, 2)

  metrics_summary: dict[str, dict[str, float]] = {}
  for domain, agg in per_domain_agg.items():
    metrics_summary[domain] = {
        "f1": pct(agg["f1"]),
        "precision": pct(agg["precision"]),
        "recall": pct(agg["recall"]),
        "exact_match_rate": pct(agg["exact_match_rate"]),
        "n": int(agg["n"]),
    }
  metrics_summary["overall"] = {
      "f1": pct(overall_agg["f1"]),
      "precision": pct(overall_agg["precision"]),
      "recall": pct(overall_agg["recall"]),
      "exact_match_rate": pct(overall_agg["exact_match_rate"]),
      "n": int(overall_agg["n"]),
  }

  manifest = {
      "version": "1.0.0",
      "skill": "ct2code",
      "run_id": RUN_ROOT.name,
      "condition": condition,
      "run_kind": "ablation_subset",
      "run_kind_note": (
          f"Ablation condition {condition}; first {max_per_subset} instances per"
          " subtask in validation split; responses collected via Cursor subagents."
      ),
      "created_utc": utc_now_iso(),
      "model": model,
      "runner_type": "cursor-subagent",
      "hyperparameters": {
          "temperature": temperature,
          "max_tokens": max_tokens,
          "instances_per_subset": max_per_subset,
      },
      "dataset": {
          "huggingface_id": DATASET_ID,
          "split": DATASET_SPLIT,
          "configs": list(DOMAINS),
          "instances_used": all_instance_ids,
      },
      "paths_relative_to_condition_dir": {
          "solution": "absencebench_claude-4-sonnet_solution.jsonld",
          "raw_outputs_dir": f"raw_outputs/{model_slug(model)}",
          "bootstrap_metrics": f"raw_outputs/{model_slug(model)}/bootstrap_metrics.json",
      },
      "metrics_summary": metrics_summary,
      "bootstrap": {
          "iters": bootstrap_iters,
          "seed": bootstrap_seed,
          "overall_f1_mean_pct": pct(overall_bootstrap["mean"]["f1"]),
          "overall_f1_ci95_pct": [
              pct(overall_bootstrap["ci95"]["f1"][0]),
              pct(overall_bootstrap["ci95"]["f1"][1]),
          ],
          "overall_em_mean_pct": pct(overall_bootstrap["mean"]["exact_match_rate"]),
          "overall_em_ci95_pct": [
              pct(overall_bootstrap["ci95"]["exact_match_rate"][0]),
              pct(overall_bootstrap["ci95"]["exact_match_rate"][1]),
          ],
      },
  }
  with open(output_dir / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")


def parse_args() -> argparse.Namespace:
  p = argparse.ArgumentParser(description=__doc__)
  sub = p.add_subparsers(dest="command", required=True)

  p_prepare = sub.add_parser("prepare", help="Build prompt files for a condition.")
  p_prepare.add_argument("--condition", choices=["paper_only", "ct_only"], required=True)
  p_prepare.add_argument("--max-per-subset", type=int, default=DEFAULT_MAX_PER_SUBSET)

  p_finalize = sub.add_parser(
      "finalize",
      help="Ingest responses and compute outputs/metrics/bootstrap for a condition.",
  )
  p_finalize.add_argument("--condition", choices=["paper_only", "ct_only"], required=True)
  p_finalize.add_argument("--max-per-subset", type=int, default=DEFAULT_MAX_PER_SUBSET)
  p_finalize.add_argument("--model", default=DEFAULT_MODEL)
  p_finalize.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
  p_finalize.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
  p_finalize.add_argument("--bootstrap-iters", type=int, default=DEFAULT_BOOTSTRAP_ITERS)
  p_finalize.add_argument("--bootstrap-seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)
  return p.parse_args()


def main() -> int:
  args = parse_args()
  if args.command == "prepare":
    prepare_condition(args.condition, args.max_per_subset)
    return 0
  if args.command == "finalize":
    finalize_condition(
        condition=args.condition,
        max_per_subset=args.max_per_subset,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        bootstrap_iters=args.bootstrap_iters,
        bootstrap_seed=args.bootstrap_seed,
    )
    return 0
  raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
  raise SystemExit(main())

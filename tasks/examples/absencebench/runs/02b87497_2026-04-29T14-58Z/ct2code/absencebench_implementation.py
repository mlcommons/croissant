"""AbsenceBench baseline implementation: Anthropic Claude Sonnet.

Generated following Leo's `tasks/SKILL_ct2code.md` runbook on the
`absencebench_problem.jsonld` TaskProblem in this directory.

Pipeline for each of the 3 subtasks (poetry, numerical, github_prs):
  1. Load the corresponding subset of `harveyfin/AbsenceBench` from HuggingFace.
  2. For each instance, build the paper's exact default prompt template
     (Fu et al. 2025, Table 6) and call the Anthropic Messages API.
  3. Parse the response by splitting on newlines, stripping whitespace.
  4. Compute micro-F1 (per-element) and exact-match (per-instance) versus
     `omitted_context`, the ground-truth list of removed elements.
  5. Save raw outputs (predictions + gold + per-instance metrics) to JSONL.

After running across all subtasks, the script updates the TaskSolution JSON-LD
file (`absencebench_<model_slug>_solution.jsonld`) by populating its
`croissant:execution` block with the model + hyperparameters used and each
sub-solution's `croissant:evaluation.croissant:evaluationResults` with the
measured F1-Score and Exact Match values, plus an overall result on the root.

Incremental execution: if a per-subset outputs JSONL already contains
predictions for a given instance id, that instance is skipped.

Environment:
  ANTHROPIC_API_KEY must be set for live runs.

Usage:
  # Dry run, 5 instances per subset (no real cost beyond a handful of API calls):
  python absencebench_implementation.py --dry-run

  # Specify how many per subset:
  python absencebench_implementation.py --max-per-subset 5

  # Full evaluation (~3.3K API calls; expensive!):
  python absencebench_implementation.py --max-per-subset 0

  # Pick a different Sonnet:
  python absencebench_implementation.py --dry-run --model claude-sonnet-4-5

  # Test the parsing/metrics path without API calls (returns empty predictions):
  python absencebench_implementation.py --dry-run --no-api
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from datasets import load_dataset

HERE = Path(__file__).resolve().parent

DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.0

DOMAINS = ("poetry", "numerical", "github_prs")

PROMPT_TEMPLATES: dict[str, dict[str, str]] = {
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


def parse_args() -> argparse.Namespace:
  p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
  p.add_argument("--model", default=DEFAULT_MODEL)
  p.add_argument(
      "--max-per-subset",
      type=int,
      default=None,
      help=(
          "Cap instances per subtask. 0 means full dataset. Defaults to 5"
          " when --dry-run is set, else 0 (full)."
      ),
  )
  p.add_argument("--dry-run", action="store_true")
  p.add_argument(
      "--no-api",
      action="store_true",
      help=(
          "Skip API calls; return empty predictions. Useful to test the"
          " plumbing without spending tokens."
      ),
  )
  p.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
  p.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
  p.add_argument(
      "--solution-file",
      default=None,
      help=(
          "Path to write/update the TaskSolution JSON-LD. Default:"
          " absencebench_<model_slug>_solution.jsonld in this directory."
      ),
  )
  args = p.parse_args()
  if args.max_per_subset is None:
    args.max_per_subset = 5 if args.dry_run else 0
  return args


def model_slug(model: str) -> str:
  return model.lower().replace(".", "-").replace(" ", "-")


def build_messages(domain: str, original: str, modified: str) -> tuple[str, list[dict[str, str]]]:
  tmpl = PROMPT_TEMPLATES[domain]
  user = tmpl["user"].format(original=original, modified=modified)
  return tmpl["system"], [{"role": "user", "content": user}]


def call_claude(client: Any, model: str, system: str, messages: list[dict[str, str]],
                max_tokens: int, temperature: float) -> str:
  resp = client.messages.create(
      model=model,
      max_tokens=max_tokens,
      temperature=temperature,
      system=system,
      messages=messages,
  )
  parts: list[str] = []
  for block in resp.content:
    if getattr(block, "type", None) == "text":
      parts.append(block.text)
  return "".join(parts)


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


def load_existing_predictions(path: Path) -> dict[int, dict[str, Any]]:
  if not path.exists():
    return {}
  out: dict[int, dict[str, Any]] = {}
  with open(path) as f:
    for line in f:
      if not line.strip():
        continue
      obj = json.loads(line)
      out[int(obj["id"])] = obj
  return out


def append_prediction(path: Path, record: dict[str, Any]) -> None:
  with open(path, "a") as f:
    f.write(json.dumps(record) + "\n")


def run_subset(
    domain: str,
    model: str,
    client: Any,
    max_n: int,
    max_tokens: int,
    temperature: float,
    use_api: bool,
    output_dir: Path,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
  ds = load_dataset("harveyfin/AbsenceBench", domain, split="validation")
  if max_n and max_n > 0:
    ds = ds.select(range(min(max_n, len(ds))))

  out_path = output_dir / f"outputs_{domain}.jsonl"
  existing = load_existing_predictions(out_path)
  records: list[dict[str, Any]] = list(existing.values())

  for ex in ds:
    iid = int(ex["id"])
    if iid in existing:
      continue
    gold = list(ex["omitted_context"]) or []
    if use_api:
      system, messages = build_messages(domain, ex["original_context"], ex["modified_context"])
      try:
        raw = call_claude(client, model, system, messages, max_tokens, temperature)
      except Exception as e:
        print(f"  [{domain}#{iid}] API error: {type(e).__name__}: {e}", flush=True)
        raw = ""
    else:
      raw = ""
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
    append_prediction(out_path, rec)
    records.append(rec)
    print(
        f"  [{domain}#{iid}] gold={len(gold)} pred={len(pred)} tp={metrics['tp']}"
        f" fp={metrics['fp']} fn={metrics['fn']} em={metrics['exact_match']}",
        flush=True,
    )

  agg = aggregate([r["metrics"] for r in records])
  print(
      f"[{domain}] n={agg['n']} F1={agg['f1']*100:.2f} P={agg['precision']*100:.2f}"
      f" R={agg['recall']*100:.2f} EM={agg['exact_match_rate']*100:.2f}",
      flush=True,
  )
  return agg, records


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
      "schema:name": f"Anthropic Messages API - {model}",
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
  print(f"Wrote updated solution to {solution_path}")


def make_anthropic_client(use_api: bool) -> Any:
  if not use_api:
    return None
  if not os.environ.get("ANTHROPIC_API_KEY"):
    print(
        "ERROR: ANTHROPIC_API_KEY not set. Set it or pass --no-api to test"
        " the parsing path with empty predictions.",
        file=sys.stderr,
    )
    sys.exit(2)
  import anthropic

  return anthropic.Anthropic()


def main() -> int:
  args = parse_args()
  print(
      f"Model: {args.model} | dry_run={args.dry_run} | max_per_subset="
      f"{args.max_per_subset} | use_api={not args.no_api}"
  )
  client = make_anthropic_client(use_api=not args.no_api)

  output_dir = HERE / "raw_outputs" / model_slug(args.model)
  output_dir.mkdir(parents=True, exist_ok=True)

  per_domain: dict[str, dict[str, float]] = {}
  pooled: list[dict[str, float | int]] = []
  for domain in DOMAINS:
    print(f"\n=== {domain} ===")
    agg, records = run_subset(
        domain=domain,
        model=args.model,
        client=client,
        max_n=args.max_per_subset,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        use_api=not args.no_api,
        output_dir=output_dir,
    )
    per_domain[domain] = agg
    pooled.extend(r["metrics"] for r in records)
  overall = aggregate(pooled)
  print(
      f"\n=== OVERALL === n={overall['n']} F1={overall['f1']*100:.2f}"
      f" P={overall['precision']*100:.2f} R={overall['recall']*100:.2f}"
      f" EM={overall['exact_match_rate']*100:.2f}"
  )

  solution_path = (
      Path(args.solution_file)
      if args.solution_file
      else HERE / f"absencebench_{model_slug(args.model)}_solution.jsonld"
  )
  if not solution_path.exists():
    print(
        f"ERROR: solution skeleton not found at {solution_path}. Generate it"
        " first.",
        file=sys.stderr,
    )
    return 2
  update_solution_file(
      solution_path=solution_path,
      model=args.model,
      temperature=args.temperature,
      max_tokens=args.max_tokens,
      per_domain=per_domain,
      overall=overall,
  )
  return 0


if __name__ == "__main__":
  raise SystemExit(main())

#!/usr/bin/env python3
"""Split, merge, and validate chunked AbsenceBench response files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

RUN_ROOT = Path(__file__).resolve().parent.parent
DOMAINS = ("poetry", "numerical", "github_prs")
CONDITIONS = ("ct_only", "paper_only")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
  out: list[dict[str, Any]] = []
  with open(path) as f:
    for line in f:
      if line.strip():
        out.append(json.loads(line))
  return out


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with open(path, "w") as f:
    for row in rows:
      f.write(json.dumps(row) + "\n")


def split_chunks(condition: str, domain: str, chunk_size: int) -> None:
  src = RUN_ROOT / condition / "prompts" / f"prompts_{domain}.jsonl"
  rows = read_jsonl(src)
  out_dir = RUN_ROOT / condition / "chunks"
  out_dir.mkdir(parents=True, exist_ok=True)
  for i in range(0, len(rows), chunk_size):
    chunk = rows[i:i + chunk_size]
    idx = i // chunk_size
    out = out_dir / f"prompts_{domain}_chunk_{idx:03d}.jsonl"
    write_jsonl(out, chunk)


def merge_chunks(condition: str, domain: str) -> None:
  chunk_dir = RUN_ROOT / condition / "chunk_responses"
  pattern = re.compile(rf"^responses_{re.escape(domain)}_chunk_(\d{{3}})\.jsonl$")
  files: list[tuple[int, Path]] = []
  for p in chunk_dir.glob(f"responses_{domain}_chunk_*.jsonl"):
    m = pattern.match(p.name)
    if m:
      files.append((int(m.group(1)), p))
  files.sort()
  merged: list[dict[str, Any]] = []
  for _, p in files:
    merged.extend(read_jsonl(p))
  out = RUN_ROOT / condition / "responses" / f"responses_{domain}.jsonl"
  write_jsonl(out, merged)


def _has_bad_text(domain: str, raw: str) -> bool:
  text = raw.strip()
  if not text:
    return False

  bad_prefixes = (
      "This looks like a good bug fix!",
      "Poetry is a literary art form",
      "Here is the complete original poem:",
  )
  return any(text.startswith(p) for p in bad_prefixes)


def validate(condition: str, domain: str, strict_text_checks: bool) -> None:
  prompts = read_jsonl(RUN_ROOT / condition / "prompts" / f"prompts_{domain}.jsonl")
  responses = read_jsonl(RUN_ROOT / condition / "responses" / f"responses_{domain}.jsonl")

  if len(prompts) != len(responses):
    raise ValueError(
        f"{condition}/{domain}: row-count mismatch prompts={len(prompts)} responses={len(responses)}"
    )

  p_ids = [int(r["id"]) for r in prompts]
  r_ids = [int(r["id"]) for r in responses]
  if p_ids != r_ids:
    raise ValueError(f"{condition}/{domain}: id order mismatch between prompts and responses")

  bad_rows = 0
  for row in responses:
    raw = row.get("raw_response", "")
    if not isinstance(raw, str):
      raise ValueError(f"{condition}/{domain}: non-string raw_response for id={row.get('id')}")
    if strict_text_checks and _has_bad_text(domain, raw):
      bad_rows += 1

  if strict_text_checks and bad_rows > 0:
    raise ValueError(
        f"{condition}/{domain}: found {bad_rows} rows with banned generic-format markers"
    )


def parse_args() -> argparse.Namespace:
  p = argparse.ArgumentParser(description=__doc__)
  sub = p.add_subparsers(dest="cmd", required=True)

  p_split = sub.add_parser("split")
  p_split.add_argument("--condition", choices=CONDITIONS, required=True)
  p_split.add_argument("--domain", choices=DOMAINS, required=True)
  p_split.add_argument("--chunk-size", type=int, default=80)

  p_merge = sub.add_parser("merge")
  p_merge.add_argument("--condition", choices=CONDITIONS, required=True)
  p_merge.add_argument("--domain", choices=DOMAINS, required=True)

  p_validate = sub.add_parser("validate")
  p_validate.add_argument("--condition", choices=CONDITIONS, required=True)
  p_validate.add_argument("--domain", choices=DOMAINS, required=True)
  p_validate.add_argument("--strict-text-checks", action="store_true")

  return p.parse_args()


def main() -> int:
  args = parse_args()
  if args.cmd == "split":
    split_chunks(args.condition, args.domain, args.chunk_size)
    return 0
  if args.cmd == "merge":
    merge_chunks(args.condition, args.domain)
    return 0
  if args.cmd == "validate":
    validate(args.condition, args.domain, args.strict_text_checks)
    return 0
  raise ValueError(f"Unsupported command: {args.cmd}")


if __name__ == "__main__":
  raise SystemExit(main())

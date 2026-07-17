# AbsenceBench Croissant Tasks Example

This directory holds Croissant Tasks artifacts for **AbsenceBench** (Fu et al. 2025, [arXiv:2506.11440](https://arxiv.org/abs/2506.11440)) — a benchmark that asks LLMs to identify intentionally omitted information from a document, given access to both the original and the modified version.

This example is the first in `tasks/benchmark_examples/` that exercises **both** of Leo's runbooks end-to-end:

- `tasks/SKILL_pdf2ct.md`: paper PDF → Croissant Tasks `TaskProblem` (+ paper-reported `TaskSolution`s, summary, validation report).
- `tasks/SKILL_ct2code.md`: `TaskProblem` + a baseline spec → implementation code + populated `TaskSolution` + per-instance raw outputs + run manifest.

## Layout convention: snapshot per run

Unlike `mmlu/` and `xlsum/` (which are flat), this example treats each end-to-end execution of `pdf2ct → ct2code` as an immutable snapshot. Each run lives under `runs/<parent_commit>_<utc_timestamp>/`, contains everything needed to audit and reproduce that specific run, and is never modified after creation.

```
runs/<parent_commit>_<utc_timestamp>/
├── README.md             ← per-run TL;DR, results, layout, reproduction, run nuances (model, N, runner type, etc.)
├── pdf2ct/               ← outputs of SKILL_pdf2ct (TaskProblem + paper-reported solutions + meta)
├── ct2code/              ← outputs of SKILL_ct2code (impl + populated solution + raw outputs + manifest + prompts)
└── infra/                ← workaround / helper scripts scoped to this run
```

The directory naming convention `<parent_commit>_<utc_timestamp>` decomposes as:

- `<parent_commit>`: short SHA of the upstream commit the run was performed against. Tells anyone reading the dir name which versions of the SKILLs / shapes / framework underpin the snapshot.
- `<utc_timestamp>`: ISO 8601 UTC, `YYYY-MM-DDTHH-MMZ` (filesystem-safe — colon replaced with hyphen). The `Z` is the Zulu / UTC marker.

The kind of run (dry-run vs full eval, N-per-subset, model, runner type) is documented in each run's `README.md` and `ct2code/raw_outputs/<model>/manifest.json` rather than encoded in the path. A new run never overwrites or modifies an existing run's files.

## Runs in this directory

| Run | Started | Parent commit | Stage status | Headline overall F1 |
|---|---|---|---|---:|
| [`02b87497_2026-04-29T14-58Z`](runs/02b87497_2026-04-29T14-58Z/) | 2026-04-29 | `02b87497` (Leo: ct2code skill + updated pdf2ct skill) | pdf2ct: complete; ct2code: 5-instance/subset dry-run on `claude-4-sonnet` via Cursor subagent. SHACL: SKIPPED (validator state per docs of the time). | 65.98 |
| [`02b87497_2026-04-30T08-03Z`](runs/02b87497_2026-04-30T08-03Z/) | 2026-04-30 | `02b87497` (same as above) | pdf2ct: complete; ct2code: fresh 5-instance/subset dry-run on `claude-4-sonnet` via Cursor subagent. SHACL: actually RAN; FAIL on all 4 with two known shape bugs (verbatim output captured). Reproducibility comparison vs the 2026-04-29 run: numerical 5/5 deterministic, poetry/github_prs 1/5 deterministic. | 61.79 |

The two runs share parent commit, prompts (byte-identical), model, and hyperparameters — so the metric delta (`-4 F1` overall) is purely run-to-run nondeterminism in the Cursor-subagent invocation of `claude-4-sonnet` at "T=0". Numerical sequences are deterministic-friendly; longer free-form outputs (poetry, github_prs) are not. See [`runs/02b87497_2026-04-30T08-03Z/README.md`](runs/02b87497_2026-04-30T08-03Z/README.md) for the per-instance breakdown.

## Quick navigation

- The most recent run's full report: [`runs/02b87497_2026-04-30T08-03Z/README.md`](runs/02b87497_2026-04-30T08-03Z/README.md).
- The TaskProblem (definition of the benchmark, latest snapshot): [`runs/02b87497_2026-04-30T08-03Z/pdf2ct/absencebench_problem.jsonld`](runs/02b87497_2026-04-30T08-03Z/pdf2ct/absencebench_problem.jsonld).
- The implementation script (latest): [`runs/02b87497_2026-04-30T08-03Z/ct2code/absencebench_implementation.py`](runs/02b87497_2026-04-30T08-03Z/ct2code/absencebench_implementation.py).

## A note on the snapshot convention vs. `mmlu/` and `xlsum/`

The flat layout used by `mmlu/` and `xlsum/` is fine for examples that won't be re-run as the framework evolves. AbsenceBench is the first example built end-to-end after both `pdf2ct` and `ct2code` were available, and we expect to iterate (more baselines, full evals, paper updates), so we adopt the snapshot layout. If Leo prefers, this can be flattened back to match the existing examples — every file maps cleanly to its flat-layout location.

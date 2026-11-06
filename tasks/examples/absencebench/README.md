# AbsenceBench Croissant Tasks Example

This directory holds Croissant Tasks artifacts for **AbsenceBench** (Fu et al. 2025, [arXiv:2506.11440](https://arxiv.org/abs/2506.11440)) — a benchmark that asks LLMs to identify intentionally omitted information from a document, given access to both the original and the modified version.

This example is the first in `tasks/examples/` that exercises **both** runbooks end-to-end:

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
| [`02b87497_2026-04-29T14-58Z`](runs/02b87497_2026-04-29T14-58Z/) | 2026-04-29 | `02b87497` (ct2code skill + updated pdf2ct skill) | pdf2ct: complete; ct2code: 5-instance/subset dry-run on `claude-4-sonnet` via Cursor subagent. SHACL: SKIPPED (validator state per docs of the time). | 65.98 |
| [`02b87497_2026-04-30T08-03Z`](runs/02b87497_2026-04-30T08-03Z/) | 2026-04-30 | `02b87497` (same as above) | pdf2ct: complete; ct2code: fresh 5-instance/subset dry-run on `claude-4-sonnet` via Cursor subagent. SHACL: actually RAN; FAIL on all 4 with two known shape bugs (verbatim output captured). Reproducibility comparison vs the 2026-04-29 run: numerical 5/5 deterministic, poetry/github_prs 1/5 deterministic. | 61.79 |
| [`9763f55a_2026-05-06T10-00Z`](runs/9763f55a_2026-05-06T10-00Z/) | 2026-05-06 | `9763f55a` (latest upstream `mmlu_example`) | input ablation snapshot: `ct_only` vs `paper_only`, each on 20 instances/subtask (`n=60`) with `claude-4-sonnet`; includes bootstrap CIs (`N=1000`) from saved outputs. | 68.64 (`ct_only`), 94.59 (`paper_only`) |
| [`9763f55a_2026-05-06T10-14Z`](runs/9763f55a_2026-05-06T10-14Z/) | 2026-05-06 | `9763f55a` (latest upstream `mmlu_example`) | full-scope (`n=0`) ablation snapshot with strict condition-isolated workers and bootstrap CIs (`N=1000`) over all 3278 validation examples per condition. Caveat: instruction collapse on long-context prompts degrades response fidelity; see run README quality note. | 58.61 (`ct_only`), 71.26 (`paper_only`) |
| [`9763f55a_2026-05-06T10-24Z`](runs/9763f55a_2026-05-06T10-24Z/) | 2026-05-06 | `9763f55a` (latest upstream `mmlu_example`) | full-scope (`n=0`) ablation rerun with chunked workers + explicit QA gates (count/id alignment + generic-output guard), then bootstrap CIs (`N=1000`) on corrected merged outputs. | 91.58 (`ct_only`), 96.06 (`paper_only`) |

The first two runs share parent commit, prompts (byte-identical), model, and hyperparameters — so the metric delta (`-4 F1` overall) is purely run-to-run nondeterminism in the Cursor-subagent invocation of `claude-4-sonnet` at "T=0". Numerical sequences are deterministic-friendly; longer free-form outputs (poetry, github_prs) are not. See [`runs/02b87497_2026-04-30T08-03Z/README.md`](runs/02b87497_2026-04-30T08-03Z/README.md) for the per-instance breakdown.

The `9763f55a_2026-05-06T10-00Z` run adds clean small-scope ablation evidence (`ct_only` vs `paper_only`) and bootstrap confidence intervals. The follow-up `9763f55a_2026-05-06T10-14Z` run scales to full validation scope (`n=0`) under strict condition isolation, but exposes instruction-collapse failure modes. The `9763f55a_2026-05-06T10-24Z` rerun applies chunked worker execution plus explicit QA gates to address that failure mode while keeping the same ablation scope and isolation policy.

## Quick navigation

- The most recent run's full report: [`runs/9763f55a_2026-05-06T10-24Z/README.md`](runs/9763f55a_2026-05-06T10-24Z/README.md).
- The TaskProblem (definition of the benchmark, latest snapshot): [`runs/9763f55a_2026-05-06T10-24Z/pdf2ct/absencebench_problem.jsonld`](runs/9763f55a_2026-05-06T10-24Z/pdf2ct/absencebench_problem.jsonld).
- The ablation pipeline script (latest): [`runs/9763f55a_2026-05-06T10-24Z/infra/ablation_pipeline.py`](runs/9763f55a_2026-05-06T10-24Z/infra/ablation_pipeline.py).

## A note on the snapshot convention vs. `mmlu/` and `xlsum/`

The flat layout used by `mmlu/` and `xlsum/` is fine for examples that won't be re-run as the framework evolves. AbsenceBench is the first example built end-to-end after both `pdf2ct` and `ct2code` were available, and we expect to iterate (more baselines, full evals, paper updates), so we adopt the snapshot layout. If maintainers prefer, this can be flattened back to match the existing examples — every file maps cleanly to its flat-layout location.

# AbsenceBench run: `02b87497_2026-04-30T08-03Z`

Self-contained snapshot of one end-to-end `pdf2ct → ct2code` execution against AbsenceBench (Fu et al. 2025, [arXiv:2506.11440](https://arxiv.org/abs/2506.11440)).

This is a **reproducibility-comparison run** against the previous snapshot at [`02b87497_2026-04-29T14-58Z`](../02b87497_2026-04-29T14-58Z/) — same parent commit, same prompts, same model, same hyperparameters, fresh execution. Headline finding: Cursor subagents at `claude-4-sonnet` are **not strictly deterministic** on non-trivial outputs even at `temperature=0` (8 of 15 instances produced different raw responses across the two runs). Numerical responses are deterministic; poetry and github_prs are not.

## TL;DR

- **Parent commit**: `02b87497` (Leo: "add - ct2code skill + updated pdf2ct skill") — same as previous run; upstream/mmlu_example has not advanced.
- **Started**: 2026-04-30 08:03 UTC.
- **Run kind**: dry-run, first 5 instances of the validation split per subtask = 15 LLM calls total. Pipeline reproducibility check.
- **Baseline**: `claude-4-sonnet` invoked via 15 fresh Cursor subagents, `temperature=0`, `max_tokens=4096`, paper Appendix A default prompt templates. **Same 15 prompt files (byte-identical) as the previous run.**
- **pdf2ct stage**: `tasks/validator.py` was **actually run** end-to-end this time (see `pdf2ct/shacl_run.txt`); previous run had marked it SKIPPED. All four JSON-LDs FAIL with one of two known shape bugs (Bug A on Problem, Bug B on Solutions). Both match items on the team's known-issue list (RISEBench agent analysis, Slack 2026-04-29: Changes 2 and 4). Structural-check via `infra/_structural_check.py` PASS on all four files.
- **Spec modifications**: NONE. Per team guidance, this run deliberately does NOT modify `tasks/croissant-tasks.ttl` or `tasks/croissant-tasks-shapes.ttl`.
- **Headline numbers** (5 instances per subtask, micro-F1 / per-instance exact-match rate, Δ vs previous run):

  | Subtask | This run F1 | Previous F1 | Δ F1 | This run EM | Paper Table 3 (claude-3-7-sonnet, no thinking) |
  |---|---:|---:|---:|---:|---:|
  | poetry | 75.92 | 85.35 | -9.43 | 20.00 | 73.5 |
  | numerical | 100.00 | 100.00 | 0.00 | 100.00 | 91.4 |
  | github_prs | 10.61 | 9.77 | +0.84 | 0.00 | 35.7 |
  | **overall** | **61.79** | **65.98** | **-4.19** | **40.00** | **66.9 (avg)** |

## Reproducibility comparison vs previous run

The interesting question of this run was: at `temperature=0`, with byte-identical prompts and the same model slug, does Cursor's subagent give us bit-exact reproducibility?

**Answer: no, only on simple deterministic-friendly tasks.**

| Domain | Per-instance raw_response identical to previous run | Notes |
|---|---|---|
| numerical | **5 / 5** (100% deterministic) | Sequence completion is converged behaviour; single-token-ish outputs. |
| poetry | **1 / 5** | The chatty-poetry instance #2 went from 82 to 132 predicted lines, costing precision (88.2 → 66.4 F1). |
| github_prs | **1 / 5** | Diff-line counts shifted by ±1-4 between runs. |

So aggregate metric variance of ±5-10 F1 between runs at the same scope is real and expected. **Single dry-run numbers should not be over-interpreted.** Use multiple runs and report variance, or run the full eval where N=3,278 averages out small per-instance perturbations.

A complete per-instance breakdown (gold size, old/new predicted size, raw_response identity, old/new F1) lives in `ct2code/raw_outputs/claude-4-sonnet/manifest.json` under `comparison_to_previous_run.per_instance_response_identity`.

## Layout under this directory

```
02b87497_2026-04-30T08-03Z/
├── README.md                                                    ← you are here
│
├── pdf2ct/                                                       ← outputs of SKILL_pdf2ct
│   ├── absencebench_problem.jsonld                              ← THE TaskProblem (definition of AbsenceBench)
│   ├── absencebench_solution_claude-3-7-sonnet.jsonld           ← paper Table 3, claude-3-7-sonnet, no thinking
│   ├── absencebench_solution_claude-3-7-sonnet-thinking.jsonld  ← paper Table 3, claude-3-7-sonnet, thinking
│   ├── summary.md                                                ← extraction confidence, caveats (per pdf2ct §8)
│   ├── validation_report.json                                    ← per-file json/RDF/SHACL/structural status (per pdf2ct §9)
│   └── shacl_run.txt                                             ← captured pyshacl output for each of our 4 JSON-LDs
│
├── ct2code/                                                      ← outputs of SKILL_ct2code
│   ├── absencebench_implementation.py                            ← generated baseline runner (unchanged from previous run)
│   ├── absencebench_claude-4-sonnet_solution.jsonld              ← populated TaskSolution from this run's measurements
│   ├── prompts/                                                  ← exact prompts shown to each subagent (15 files; byte-identical to previous run)
│   │   ├── poetry_0.txt … poetry_4.txt
│   │   ├── numerical_0.txt … numerical_4.txt
│   │   └── github_prs_0.txt … github_prs_4.txt
│   └── raw_outputs/claude-4-sonnet/
│       ├── manifest.json                                         ← run metadata + comparison_to_previous_run section
│       ├── outputs_poetry.jsonl                                  ← per-instance: id, gold, pred, raw_response, metrics
│       ├── outputs_numerical.jsonl
│       └── outputs_github_prs.jsonl
│
└── infra/
    └── _structural_check.py                                      ← rdflib-only validator (workaround, see below)
```

## Validator status

`tasks/validator.py` was actually **run end-to-end** this time on all four JSON-LDs in this run; verbatim output captured in `pdf2ct/shacl_run.txt`. Result: all four FAIL.

| Bug | Where | pyshacl error | Affects (this run) | Matches RISEBench analysis | Also fails on Leo's testdata |
|---|---|---|---|---|---|
| **A** | `TaskProblemShape` "must have at least one Spec" — outer `sh:property` whose body is `sh:or` of alternatives has no outer `sh:path` | `'exists but is not a well-formed SHACL PropertyShape'` | `pdf2ct/absencebench_problem.jsonld` | "Change 2: Fix TaskProblemShape spec constraint" | yes — `testdata/valid_problem.jsonld` FAIL |
| **B** | `EvaluationTaskShape` `croissant:evaluatedSolution` — `sh:qualifiedMinCount 1` without corresponding `sh:qualifiedValueShape` | `'QualifiedValueShapeConstraintComponent must have at least one sh:qualifiedValueShape predicate'` | All three TaskSolutions | "Change 4: Fix evaluatedSolution cardinality" | yes — `testdata/valid_evaluation_task.jsonld` FAIL |

Validator passes on simpler shapes — `testdata/valid_solution.jsonld`, `testdata/direct_task.jsonld`, `testdata/valid_solution_subtasks_all_concrete.jsonld` all PASS — confirming the bugs are scoped to the two specific shapes our files happen to exercise, not universal.

Suggested fixes (also in `pdf2ct/validation_report.json` `upstream_issues`):

- **Bug A**: lift the `sh:or` out of the inner `sh:property` to NodeShape level, with each alternative being a full `sh:property` carrying its own `sh:path`, `sh:class`, and `sh:minCount 1`.
- **Bug B**: replace `sh:qualifiedMinCount 1` with `sh:minCount 1` + `sh:maxCount 1` (the cardinality the constraint actually wants is "exactly 1", not a qualified-shape count).

**This run deliberately does NOT modify the spec files** (`tasks/croissant-tasks.ttl` or `tasks/croissant-tasks-shapes.ttl`), per the team guidance in the 2026-04-29 Slack thread. Workaround: `infra/_structural_check.py` (rdflib-only) — all four JSON-LDs PASS it.

## Reproducing this run

### Path 1 — via Anthropic API (fresh run on any machine)

```bash
# From the repo root
pip install -e tasks/                                              # gets pyshacl, rdflib, datasets, evaluate, nltk, pillow, pycocotools
pip install anthropic                                              # solution-specific
export ANTHROPIC_API_KEY=...

# Snapshot a new run dir based on this one's structure:
NEW_RUN="$(git rev-parse --short HEAD)_$(date -u +%Y-%m-%dT%H-%MZ)"
NEW_DIR="tasks/benchmark_examples/absencebench/runs/$NEW_RUN"
cp -r tasks/benchmark_examples/absencebench/runs/02b87497_2026-04-30T08-03Z "$NEW_DIR"
rm -rf "$NEW_DIR/ct2code/raw_outputs/claude-4-sonnet" "$NEW_DIR/ct2code/prompts"
sed -i 's/PENDING/PENDING/g' "$NEW_DIR/ct2code/absencebench_claude-4-sonnet_solution.jsonld"

# Run the implementation in-place:
cd "$NEW_DIR/ct2code"
python absencebench_implementation.py --dry-run                    # 5 per subset
# or for a full eval (~3,278 LLM calls; expensive):
# python absencebench_implementation.py --max-per-subset 0
```

### Path 2 — via Cursor subagents (the path used to populate the committed snapshot)

This is how the committed `claude-4-sonnet` results were produced; it avoids needing a local Anthropic API key by using Cursor's subagent infrastructure. Same procedure as for the previous run — see `runs/02b87497_2026-04-29T14-58Z/README.md` § "Reproducing this run · Path 2" for the canonical recipe.

## Out of scope for this run / known caveats

- **Run-to-run nondeterminism**: documented above. Don't read into ±5-10 F1 deltas at n=5; do a full eval if you want stable numbers.
- Only 2 of the paper's 16 Table 3 baselines materialized as paper-reported solutions (claude-3-7-sonnet ±thinking). Adding the remaining 14 is mechanical.
- HF dataset `validation` split sums to 3,278 across the three configs; the paper text claims 4,302 instances. Worth a sanity-check with the authors.
- Hyperparameter coverage in paper-reported solutions is sparse — model name, context length, API provider, thinking on/off only. Temperature and max-tokens are not stated in paper main text or appendix; omitted.
- The github_prs F1 of 10.6 is still an artefact of n=5 + the model emitting diff context lines as predictions. Run with larger n (or a smarter post-parser that strips empty `+`-only / brace-only lines before scoring) to get a meaningful number for that domain.

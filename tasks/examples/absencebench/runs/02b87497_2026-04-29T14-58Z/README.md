# AbsenceBench run: `02b87497_2026-04-29T14-58Z`

Self-contained snapshot of one end-to-end `pdf2ct → ct2code` execution against AbsenceBench (Fu et al. 2025, [arXiv:2506.11440](https://arxiv.org/abs/2506.11440)).

## TL;DR

- **Parent commit**: `02b87497` (Leo: "add - ct2code skill + updated pdf2ct skill").
- **Started**: 2026-04-29 14:58 UTC.
- **Run kind**: dry-run, first 5 instances of the validation split per subtask = 15 LLM calls total. This is a pipeline sanity check, not a benchmark result.
- **Baseline**: `claude-4-sonnet` invoked via 15 Cursor subagents (one per instance), `temperature=0`, `max_tokens=4096`, paper Appendix A default prompt templates.
- **pdf2ct stage**: complete. Authored TaskProblem, two paper-reported TaskSolutions (claude-3-7-sonnet ±thinking), `summary.md`, `validation_report.json`. SHACL conformance was SKIPPED because two known shape bugs in `tasks/croissant-tasks-shapes.ttl` block the paths our files exercise (Bug A on TaskProblems, Bug B on TaskSolutions-with-EvaluationTasks; see "Validator status" below). Structural-check via `infra/_structural_check.py` PASSED on all four files.
- **Spec modifications**: NONE. Per team guidance in the 2026-04-29 Slack thread, this run deliberately does NOT modify `tasks/croissant-tasks.ttl` or `tasks/croissant-tasks-shapes.ttl`.
- **ct2code stage**: complete. Generated `absencebench_implementation.py`, ran it against `claude-4-sonnet` via 15 Cursor subagents (one per instance), wrote per-instance predictions to `ct2code/raw_outputs/claude-4-sonnet/outputs_<domain>.jsonl`, populated `absencebench_claude-4-sonnet_solution.jsonld`.
- **Headline numbers** (5 instances per subtask, micro-F1 / per-instance exact-match rate):

  | Subtask | F1 | Exact Match | Paper Table 3 (claude-3-7-sonnet, no thinking) |
  |---|---:|---:|---:|
  | poetry | 85.35 | 20.00 | 73.5 |
  | numerical | 100.00 | 100.00 | 91.4 |
  | github_prs | 9.77 | 0.00 | 35.7 |
  | **overall** | **65.98** | **40.00** | **66.9 (avg)** |

  github_prs collapses on n=5 because the model emits diff context lines (`+`-only markers, brace-only lines) that aren't in the gold, tanking precision. Don't read into the number — n=5 is too small.

## Layout under this directory

```
02b87497_2026-04-29T14-58Z/
├── README.md                                                    ← you are here
│
├── pdf2ct/                                                       ← outputs of SKILL_pdf2ct
│   ├── absencebench_problem.jsonld                              ← THE TaskProblem (definition of AbsenceBench)
│   ├── absencebench_solution_claude-3-7-sonnet.jsonld           ← paper Table 3, claude-3-7-sonnet, no thinking
│   ├── absencebench_solution_claude-3-7-sonnet-thinking.jsonld  ← paper Table 3, claude-3-7-sonnet, thinking
│   ├── summary.md                                                ← extraction confidence, caveats (per pdf2ct §8)
│   └── validation_report.json                                    ← per-file json/RDF/SHACL/structural status (per pdf2ct §9)
│
├── ct2code/                                                      ← outputs of SKILL_ct2code
│   ├── absencebench_implementation.py                            ← generated baseline runner
│   ├── absencebench_claude-4-sonnet_solution.jsonld              ← populated TaskSolution from this run
│   ├── prompts/                                                  ← exact prompts shown to each subagent (15 files)
│   │   ├── poetry_0.txt … poetry_4.txt
│   │   ├── numerical_0.txt … numerical_4.txt
│   │   └── github_prs_0.txt … github_prs_4.txt
│   └── raw_outputs/claude-4-sonnet/
│       ├── manifest.json                                         ← run metadata (model, hyperparams, dataset rev, paper-vs-run, agent_transcript path)
│       ├── outputs_poetry.jsonl                                  ← per-instance: id, gold, pred, raw_response, metrics
│       ├── outputs_numerical.jsonl
│       └── outputs_github_prs.jsonl
│
└── infra/
    └── _structural_check.py                                      ← rdflib-only validator (workaround, see below)
```

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
cp -r tasks/benchmark_examples/absencebench/runs/02b87497_2026-04-29T14-58Z "$NEW_DIR"
rm -rf "$NEW_DIR/ct2code/raw_outputs/claude-4-sonnet" "$NEW_DIR/ct2code/prompts"
sed -i 's/PENDING/PENDING/g' "$NEW_DIR/ct2code/absencebench_claude-4-sonnet_solution.jsonld"  # reset the populated solution to placeholders if desired

# Run the implementation in-place:
cd "$NEW_DIR/ct2code"
python absencebench_implementation.py --dry-run                    # 5 per subset
# or for a full eval (~3,278 LLM calls; expensive):
# python absencebench_implementation.py --max-per-subset 0
```

### Path 2 — via Cursor subagents (the path used to populate the committed snapshot)

This is how the committed `claude-4-sonnet` results were produced; it avoids needing a local Anthropic API key by using Cursor's subagent infrastructure.

1. Build per-instance prompt files using the paper Appendix A default templates wrapped in a roleplay preamble — equivalent code lives in `absencebench_implementation.py:build_messages()`. The 15 prompt files are committed under `ct2code/prompts/` for audit.
2. For each prompt file, launch a Cursor subagent (`subagent_type=generalPurpose`, `model=claude-4-sonnet`) with the task: "read `prompts/<domain>_<id>.txt` and write your literal model output to a per-instance response file". Subagent IDs are session-scoped and not archived; the response text lives as the `raw_response` field in `ct2code/raw_outputs/claude-4-sonnet/outputs_<domain>.jsonl`.
3. Compute per-instance metrics by calling `per_instance_metrics()` and `aggregate()` from `absencebench_implementation.py`, append to `outputs_<domain>.jsonl`, then call `update_solution_file()` to populate `absencebench_claude-4-sonnet_solution.jsonld`.

## Metric chain (auditable end-to-end)

```
gold (HF dataset)              ┐
predict (LLM via subagent)     ┘  → outputs_<domain>.jsonl: {id, gold, pred, raw_response, metrics}
                                                              │
                       per_instance_metrics(gold, pred)        │
                       (multiset-intersection TP/FP/FN, EM)    │
                                                               │
                       aggregate({tp, fp, fn, em})             ▼
                       (micro-precision/recall/F1, EM-rate)   solution.jsonld croissant:evaluationResults
```

Anyone can re-derive the F1 / EM values stored in `absencebench_claude-4-sonnet_solution.jsonld` from `outputs_*.jsonl` by re-running the two pure functions in `absencebench_implementation.py` against the stored `gold` / `pred` fields. No hidden state.

## Validator status

SHACL validation against the current upstream (`02b87497`) is blocked on the paths our files exercise by **two distinct shape bugs in `tasks/croissant-tasks-shapes.ttl`**. Both match items on the team's known-issue list, as surfaced by the agent in the RISEBench experiment (Slack thread on 2026-04-29).

| Bug | Where | pyshacl error | Affects | Matches RISEBench analysis |
|---|---|---|---|---|
| **A** | `TaskProblemShape` "must have at least one Spec" — outer `sh:property` whose body is `sh:or` of alternatives has no outer `sh:path` | `'exists but is not a well-formed SHACL PropertyShape'` | All TaskProblems, including our `pdf2ct/absencebench_problem.jsonld` and Leo's own `tasks/testdata/valid_problem.jsonld` | "Change 2: Fix TaskProblemShape spec constraint" |
| **B** | `EvaluationTaskShape` `croissant:evaluatedSolution` — `sh:qualifiedMinCount 1` without corresponding `sh:qualifiedValueShape` | `'QualifiedValueShapeConstraintComponent must have at least one sh:qualifiedValueShape predicate'` | All TaskSolutions in this run (each carries `EvaluationTask` children) | "Change 4: Fix evaluatedSolution cardinality" |

Suggested fixes (also recorded in `pdf2ct/validation_report.json` `upstream_issues`):

- **Bug A**: lift the `sh:or` out of the inner `sh:property` to NodeShape level, with each alternative being a full `sh:property` carrying its own `sh:path`, `sh:class`, and `sh:minCount 1`.
- **Bug B**: replace `sh:qualifiedMinCount 1` with `sh:minCount 1` + `sh:maxCount 1` (the cardinality the constraint actually wants is "exactly 1", not a qualified-shape count).

Validator state on simpler inputs is healthier than yesterday: `tasks/testdata/valid_solution.jsonld` and `tasks/testdata/direct_task.jsonld` now PASS. So Leo's recent shape updates did land — just not on the two shapes our files exercise.

**This run deliberately does NOT modify the spec files** (`tasks/croissant-tasks.ttl` or `tasks/croissant-tasks-shapes.ttl`), per the team guidance in the 2026-04-29 Slack thread. Workaround: `infra/_structural_check.py` (rdflib-only) verifies each JSON-LD parses, has the expected types, includes required references, and that no Specs leak into Solutions. All four JSON-LD files pass it.

## Out of scope for this run / known caveats

- Only 2 of the paper's 16 Table 3 baselines materialized as paper-reported solutions (claude-3-7-sonnet ±thinking). Adding the remaining 14 (gemini-2-5-flash ±thinking, gpt-4-1, gpt-4o, o3-mini, llama-4-maverick, etc.) is mechanical — same template, different numbers.
- HF dataset `validation` split sums to 3,278 across the three configs; the paper text claims 4,302 instances. The discrepancy may be perturbation/placeholder splits not exposed via headline configs; worth a sanity-check with the authors.
- Hyperparameter coverage in paper-reported solutions is sparse — model name, context length, API provider, thinking on/off only. Temperature and max-tokens are not stated in paper main text or appendix; omitted.
- The github_prs F1 of 9.77 is an artefact of n=5 + the model emitting diff context lines as predictions. Run with larger n (or a smarter post-parser that strips empty `+`-only / brace-only lines before scoring) to get a meaningful number for that domain.

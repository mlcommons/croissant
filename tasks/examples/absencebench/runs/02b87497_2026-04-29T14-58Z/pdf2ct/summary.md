# pdf2ct summary: AbsenceBench

This file is the `summary.md` artifact required by `tasks/SKILL_pdf2ct.md` Step 8 — an executive summary of what was extracted from the paper to produce the TaskProblem and the paper-reported TaskSolutions in this directory.

## Overview

- **Date**: 2026-04-29
- **Paper**: AbsenceBench: Language Models Can't Tell What's Missing (Fu, Shrivastava, Moore, West, Tan, Holtzman; 2025)
- **OpenReview**: <https://openreview.net/pdf?id=pmLMrqhIpb>
- **arXiv**: <https://arxiv.org/abs/2506.11440>
- **Code**: <https://github.com/harvey-fin/absence-bench>
- **Dataset**: <https://huggingface.co/datasets/harveyfin/AbsenceBench> (CC-BY-SA 4.0)
- **`@id` base**: `http://example.org/absencebench_problem` and `http://example.org/absencebench#<subtask_slug>` (matching the convention used in `mmlu_problem.jsonld` and `xlsum_problem.jsonld`)

## TaskProblem extraction

### High-confidence fields (explicitly stated in paper)

| Field | Value | Paper section |
|---|---|---|
| name | AbsenceBench | Title, Abstract |
| description | Identify intentionally omitted information from a document, given the original and modified versions. | §1, §2 |
| input dataset | `harveyfin/AbsenceBench` on HuggingFace, three configs: `poetry`, `numerical`, `github_prs` | §2.2, dataset card |
| output schema | List of strings (the elements predicted to have been omitted). Order is not significant. | §2.1 task definition |
| primary metric | Micro F1-score | §3.1 Evaluation Metric |
| secondary metric | Element-level Exact Match (used as the building block of F1) | §3.1 Evaluation Metric |
| subtasks | poetry, numerical, github_prs | §2.2 Dataset Construction |
| omission rate | p = 0.1 (10% of elements omitted) | §2.2 |
| total instances | 4302 across the three domains (paper claim); HF distribution we see has 1191 + 1200 + 887 = 3278 in the validation split | §2.2 + dataset card |
| context length | average 5K tokens; per-domain 4.7K (poetry) / 1.5K (numerical) / 1.7K (github_prs) | §2 figure caption |

### Inferred fields (medium confidence)

| Field | Value | Rationale |
|---|---|---|
| `predicted_omitted_context.repeated = true` | Treat the output as a string array rather than a single concatenated string | The paper compares predicted SETS to gold SETS at element level (§3.1); a list-typed field captures that semantics more naturally than a free-form string |
| Implementation hyperparameters not in paper main text (e.g., temperature value) | Default temperature=0 used in our ct2code solution; not stated for the paper's own runs | Paper Appendix B Table 9 lists models and API providers but does not specify temperature/top-p/max-tokens; defaults assumed |
| Tokenization for "exact match" | Per-line strip-whitespace match | Paper §3.1 says "exact match to check whether each element (e.g., a line of a poem) is present in a model's response"; whitespace-stripped equality is the conservative reading |

### Skipped (paper was silent or out of scope)

| Field | Reason |
|---|---|
| `croissant:implementation` (TaskProblem level) | The paper does not constrain the implementation; any model+prompt+API works as long as the output schema is followed. We elide the spec and let solutions choose. |
| Per-baseline temperatures, max-tokens | Not given in the paper; baselines record only the values explicitly listed in Table 9 (model, context length, API provider). |
| Few-shot variants | Paper §3.1 explicitly limits prompt perturbation studies; no few-shot solutions in the repo. |

## Paper-reported solutions extracted (subset of Table 3)

| Solution file | Model | Thinking | F1: poetry / numerical / github_prs / avg |
|---|---|---|---|
| `absencebench_solution_claude-3-7-sonnet.jsonld` | claude-3-7-sonnet-latest | no | 73.5 / 91.4 / 35.7 / 66.9 |
| `absencebench_solution_claude-3-7-sonnet-thinking.jsonld` | claude-3-7-sonnet-latest | yes | 72.7 / 96.0 / 40.0 / 69.6 |

We extract two of the 16 baselines reported in Table 3 — the headline closed-source result (claude-3-7-sonnet) with and without inference-time compute, mirroring the MMLU-example precedent of selecting a representative subset rather than all rows. Adding the remaining 14 (gemini-2-5-flash ±thinking, gpt-4-1, gpt-4-1-mini, gpt-4o, o3-mini, grok-3-mini-Beta, llama-4-maverick, llama-3-3-70b-instruct, qwen3-235b, qwen2-5-72b-instruct, qwq-32b, deepseek-r1, mixtral-8x7b-instruct) is a mechanical follow-up.

## Validation results

See `validation_report.json` for the structured form. Summary:

| File | JSON parse | RDF parse | SHACL conformance | Structural sanity check |
|---|---|---|---|---|
| `absencebench_problem.jsonld` | PASS | PASS | SKIPPED (upstream validator broken) | PASS |
| `absencebench_solution_claude-3-7-sonnet.jsonld` | PASS | PASS | SKIPPED | PASS |
| `absencebench_solution_claude-3-7-sonnet-thinking.jsonld` | PASS | PASS | SKIPPED | PASS |
| `absencebench_claude-4-sonnet_solution.jsonld` (ct2code) | PASS | PASS | SKIPPED | PASS |

SHACL validation against `tasks/croissant-tasks-shapes.ttl` is blocked by two distinct shape bugs that affect our four files:

- **Bug A**: `TaskProblemShape`'s "must have at least one Spec" constraint uses `sh:property` with `sh:or` of alternative `sh:path`s but no outer `sh:path`. Pyshacl 0.22-0.31 rejects with `'exists but is not a well-formed SHACL PropertyShape'`. Hits our `absencebench_problem.jsonld` (and Leo's own `tasks/testdata/valid_problem.jsonld`).
- **Bug B**: `EvaluationTaskShape`'s `croissant:evaluatedSolution` uses `sh:qualifiedMinCount 1` without a corresponding `sh:qualifiedValueShape`. Pyshacl rejects with `'QualifiedValueShapeConstraintComponent must have at least one sh:qualifiedValueShape predicate'`. Hits all three of our TaskSolution files (which carry `EvaluationTask` blocks).

Both bugs match items on the team's known-issue list as identified by the agent in the RISEBench experiment (Slack thread on 2026-04-29): Bug A = "Change 2: Fix TaskProblemShape spec constraint", Bug B = "Change 4: Fix evaluatedSolution cardinality". Validator state on simpler inputs is now healthy — `tasks/testdata/valid_solution.jsonld` and `tasks/testdata/direct_task.jsonld` PASS — so Leo's recent shape fixes did land, just not on the two shapes our files exercise.

Per the team guidance in that same Slack thread (Omar: *"we should not allow them to do that"*; Leo: *"ignore the croissant-tasks-shapes.ttl. The shapes are only important for the validator."*), **this run deliberately does NOT modify `tasks/croissant-tasks.ttl` or `tasks/croissant-tasks-shapes.ttl`.** The two bugs above are documented and worked around (via `infra/_structural_check.py`), not patched. See `validation_report.json` for the structured form, including suggested fixes for both bugs.

## Limitations / caveats

- The HF dataset's `validation` split contains 3,278 rows. The paper's text claims 4,302 total instances; the discrepancy may be explained by additional perturbation/placeholder splits not exposed via the headline configs. Worth a sanity-check with the authors if precise counts matter.
- The paper does not explicitly publish per-instance predictions for any reported baseline, so the paper-reported solutions in this directory only carry top-line F1 numbers per subtask plus the overall average — they do not have a `croissant:output` Dataset that resolves to a real outputs file. This matches the convention used by `mmlu_solution_*_fewshot.jsonld`.
- Hyperparameter coverage in paper-reported solutions is sparse (model name, context length, API provider, thinking on/off). Temperature and max-tokens are not stated in the paper main text or appendix and are therefore omitted. Add them if/when the authors publish their evaluation script.

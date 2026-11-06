# Croissant Tasks Report: CoRe — Code Reasoning Benchmark

## Overview
- **Date**: 2026-04-29 (pdf2ct stage)
- **Paper**: "CoRe: Benchmarking LLMs' Code Reasoning Capabilities through Static Analysis Tasks" — Danning Xie, Mingwei Zheng, Xuwei Liu, Jiannan Wang, Chengpeng Wang, Lin Tan, Xiangyu Zhang (Purdue University). NeurIPS 2025 Track on Datasets and Benchmarks.
- **Project page**: https://corebench.github.io/
- **Dataset URL**: https://corebench.github.io/ (also on HuggingFace at `lt-asset/CoRe`)
- **@id base**: `http://example.org/core-benchmark`
- **Parent commit**: `fa181eb6` (`mmlu_example`, post #1025 merge)

## Files emitted (relative to this run dir)

| File | Type |
|------|------|
| `pdf2ct/core_problem.jsonld` | TaskProblem |
| `pdf2ct/core_solution_gemini-2-5-pro_paper.jsonld` | TaskSolution (paper-reported numbers) |
| `pdf2ct/summary.md` | this file |
| `pdf2ct/validation_report.json` | validation report |

## TaskProblem extraction

### High-confidence fields (explicitly stated)
| Field | Value | Paper section |
|-------|-------|---------------|
| name | CoRe: Code Reasoning Benchmark | Title / Abstract |
| description | Benchmark evaluating LLMs on data dependency, control dependency, and information flow via static analysis tasks | Abstract |
| input dataset | https://corebench.github.io/ (12,553 instances, Apache-2.0) | §3, Availability note |
| output schema | dependency_exists (bool), trace (string), source[] (string) | §3.3 Task Design |
| primary metrics | F1 Score, Correct Trace Rate, Exact Match | §4 Evaluation Metrics |
| subtasks | Data Dependency, Control Dependency, Information Flow | §2, §3.3 |
| task types | Pairwise Query, Target-Centric Query | §3.3.1 |
| num instances | 12,553 (full), 1,584 (CoRe Lite) | Table 1, Table 2 |
| programming languages | C/C++, Java, Python | Abstract, §3 |

### Inferred fields (medium confidence)
| Field | Value | Rationale |
|-------|-------|-----------|
| @id base | http://example.org/core-benchmark | No arXiv URL found; project page URL used for input @id; example.org fallback for problem @id per skill convention |
| Few-shot k | 5–7 | §4 Prompt Design explicitly states "5–7 illustrative examples" in prompts |

### Skipped (paper was silent in the provided pages)
| Field | Reason |
|-------|--------|
| arXiv / DOI URL | Not yet published; NeurIPS 2025 (submission/preprint stage) |
| Temperature / top-p (Gemini) | Paper says see Appendix E; appendix not included in provided PDF pages |
| Exact prompt templates | Appendix C referenced but not in provided PDF pages |
| CoRe Lite split methodology details | Appendix D referenced |

## Solutions extracted (paper-reported only)

These are the numbers as reported in the paper. The actual computed numbers from running the implementation against `gemini-2.5-pro` live in `../ct2code/core_solution_gemini-2-5-pro.jsonld` and `../ct2code/raw_outputs/`.

| Model | Hyperparameters | Overall metrics | Subtask breakdown |
|-------|-----------------|-----------------|-------------------|
| Gemini 2.5 Pro | few_shot_examples=5-7, reasoning_model=true, prompt_includes_trace=true | F1=91.74, CT=84.02, EM=50.25 | Data Dep (F1=88.53, CT=90.38, EM=49.43), Control Dep (F1=92.49, CT=92.26, EM=75.66), InfoFlow (F1=94.79, CT=68.66, EM=26.73) |

All paper-reported results above are from Table 4 (CoRe Lite evaluation). Gemini 2.5 Pro is the only Gemini model evaluated in the paper.

## Validation results

| File | JSON valid | SHACL (patched shapes) | SHACL (unpatched upstream shapes) |
|------|---|---|---|
| `core_problem.jsonld` | PASS | PASS | FAIL — `TaskProblemShape` blank-node `sh:property` missing `sh:path` blocks load |
| `core_solution_gemini-2-5-pro_paper.jsonld` | PASS | PASS | FAIL — `EvaluationTaskShape.evaluatedSolution` uses `sh:qualifiedMinCount` without `sh:qualifiedValueShape` |

### SHACL findings — upstream `tasks/croissant-tasks-shapes.ttl` bugs

The upstream shapes file shipped in PR #1017 (commit `02b87497`) contains four patterns that pyshacl 0.25.0 / 0.26.0 / 0.31.0 cannot validate. Two of these were already documented by Luis Oala in PR #1025 (the AbsenceBench example — see Bug A and Bug B in that PR's body); two appear to be new findings. **Per the spec-discipline convention established in PR #1025, this PR does not modify `tasks/croissant-tasks*.ttl`.** Bugs are documented here as upstream issues for Leo to address.

| # | Shape | Symptom | Status vs PR #1025 |
|---|-------|---------|--------------------|
| 1 | `TaskProblemShape` | `sh:property` blank node missing `sh:path` (its body is an `sh:or`) — pyshacl rejects it as not a well-formed PropertyShape | **Known** — = Luis's Bug A |
| 2 | `TaskShape` (base) | Base `croissant:evaluation` constraint allows only `EvaluationTask`; `TaskProblemShape` allows `EvaluationSpec`; `TaskProblem ⊑ Task` so both shapes apply additively under RDFS inference, and `EvaluationSpec` (the documented pattern in MMLU canonical example) gets rejected by the base shape | **New** — not flagged in PR #1025 |
| 3 | `EvaluationTaskShape` | `sh:qualifiedMinCount 1` without `sh:qualifiedValueShape` on `croissant:evaluatedSolution` — invalid SHACL | **Known** — = Luis's Bug B |
| 4 | `TaskSolutionShape` | Deeply nested `sh:or → sh:property → sh:node → sh:property` causes pyshacl to lose the inner `sh:qualifiedValueShape` | **Possibly new** — not in PR #1025's findings table |

Suggested fixes (also recorded in `validation_report.json` `upstream_issues`):
- **#1**: lift `sh:or` to NodeShape level so each alternative is a full `sh:property` with its own `sh:path`.
- **#2**: extend base `TaskShape` evaluation constraint to `sh:or (EvaluationTask | EvaluationSpec)`.
- **#3**: replace `sh:qualifiedMinCount 1` with `sh:minCount 1` (since there is no companion `sh:qualifiedMaxCount`).
- **#4**: flatten the `sh:or` to two simple alternatives that pyshacl can process.

## Limitations / caveats
- Evaluation results above are from CoRe **Lite** (1,584 instances), not the full 12,553-instance benchmark — Table 4 reports CoRe Lite.
- Hyperparameters (temperature, top-p, max tokens) for Gemini 2.5 Pro are in Appendix E of the paper, which was not in the provided pages; only prompt-level metadata (few-shot k) is captured.
- Only Gemini 2.5 Pro is materialized as a paper-reported solution; other Table 4 baselines are mechanical follow-ups.

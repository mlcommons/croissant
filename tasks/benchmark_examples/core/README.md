# CoRe Croissant Tasks Example

End-to-end example for **CoRe** — Xie et al. 2025, *"CoRe: Benchmarking LLMs' Code Reasoning Capabilities through Static Analysis Tasks"* (NeurIPS 2025 Track on Datasets and Benchmarks). CoRe is a human-verified, multi-lingual benchmark that evaluates LLMs on three fundamental static analysis tasks — **data dependency**, **control dependency**, and **information flow** — across C/C++, Java, and Python programs (12,553 task instances; CoRe Lite is a 1,584-instance subset).

- **Project page**: https://corebench.github.io/
- **Dataset**: HuggingFace `lt-asset/CoRe`
- **Paper**: NeurIPS 2025 (no arXiv URL at time of writing)

This example exercises **both** of the runbooks at `tasks/SKILL_pdf2ct.md` and `tasks/SKILL_ct2code.md`:

- `tasks/SKILL_pdf2ct.md`: paper PDF → Croissant Tasks `TaskProblem` (+ paper-reported `TaskSolution`, summary, validation report). Outputs in [`pdf2ct/`](pdf2ct/).
- `tasks/SKILL_ct2code.md`: `TaskProblem` + a baseline spec → implementation code + populated `TaskSolution` + per-instance raw outputs. Outputs in [`ct2code/`](ct2code/).

## Layout

```
core/
├── README.md                                                ← this file
├── pdf2ct/
│   ├── core_problem.jsonld                                  ← TaskProblem (3 subtasks, OutputSpec, EvaluationSpec)
│   ├── core_solution_gemini-2-5-pro_paper.jsonld            ← TaskSolution with paper-reported metrics (no run artifacts)
│   ├── summary.md                                           ← pdf2ct extraction summary + SHACL findings
│   └── validation_report.json                               ← machine-readable validation log
└── ct2code/
    ├── core_implementation_gemini-2-5-pro.py                ← Python script that generates the run
    ├── core_solution_gemini-2-5-pro.jsonld                  ← TaskSolution populated with measured metrics
    └── raw_outputs/
        └── gemini-2-5-pro/
            ├── control_dep_trace.jsonl                      ← per-instance: prompt id, label, prediction, raw response
            └── control_dep_trace_metrics.json               ← aggregated metrics + counts (TP/FP/FN/TN, n_api_failures)
```

## Headline numbers — control-dependency / trace subtask, CoRe Lite

| Source | F1 Score | Correct Trace Rate | n |
|---|---:|---:|---:|
| **Actual run** ([`ct2code/core_solution_gemini-2-5-pro.jsonld`](ct2code/core_solution_gemini-2-5-pro.jsonld), all 489 instances) | **80.20** | **96.93** | 489 |
| Actual run, excluding 15 API failures | 82.03 | 96.93 | 474 |
| Paper Table 4 ([`pdf2ct/core_solution_gemini-2-5-pro_paper.jsonld`](pdf2ct/core_solution_gemini-2-5-pro_paper.jsonld), `gemini-2.5-pro-preview-05-06`) | 92.49 | 92.26 | 1,584 (full CoRe Lite control split) |

**Why the gap.** Two effects pull in opposite directions:

1. **Endpoint mismatch.** The paper used `gemini-2.5-pro-preview-05-06`. This run used the stable `gemini-2.5-pro` endpoint (the preview alias was no longer available). The two endpoints are not the same model.
2. **API failures dragging F1 down.** 15 of 489 instances returned no parseable response after 3 retries; per the metric definition, those were forced to `pred=False`, which depresses recall and therefore F1. Excluding the 15 failures recovers ~2 points of F1 (82.03).
3. **CT exceeds the paper.** Among the 163 positive predictions, 158 traces were valid (96.93%), beating the paper's 92.26%. CT is a per-positive-prediction metric — it doesn't suffer from the API-failure floor that F1 does.

## Scope of the run

- **Subtask covered**: control-dependency, *trace* category only (`task_id` prefix `control_*` AND `category == "trace"` in the HuggingFace `lt-asset/CoRe` dataset).
- **Population**: CoRe Lite (filtered against `lite.json` from the upstream CoRe repo).
- **Sampling**: cap at `MAX_INSTANCES = 500`; the population after filtering is 489, so all 489 ran.
- **Subtasks NOT run**: data dependency, information flow. The actual-run TaskSolution intentionally omits those subtask blocks — leaving paper numbers there would be misleading. Paper numbers for all three subtasks are preserved in [`pdf2ct/core_solution_gemini-2-5-pro_paper.jsonld`](pdf2ct/core_solution_gemini-2-5-pro_paper.jsonld).

## Reproduction

```bash
cd tasks/benchmark_examples/core/ct2code
export GEMINI_API_KEY=<your-key>
python core_implementation_gemini-2-5-pro.py
```

Required Python packages: `google-genai`, `pyyaml`. With `CONCURRENCY=8` (the default) the run takes ~30–45 minutes wall-clock against rate-limited Gemini 2.5 Pro tiers.

The script is idempotent — it checks `raw_outputs/gemini-2-5-pro/control_dep_trace.jsonl` for already-completed instances before issuing new API calls, so a partial run can be resumed.

## SHACL findings

Both `pdf2ct/core_problem.jsonld` and `pdf2ct/core_solution_gemini-2-5-pro_paper.jsonld` were tested end-to-end against `tasks/croissant-tasks-shapes.ttl` as currently shipped on the `mmlu_example` branch. Four distinct shape bugs in the upstream shapes file block validation:

| # | Shape | pyshacl symptom | Status vs PR #1025 |
|---|---|---|---|
| 1 | `TaskProblemShape` | `'exists but is not a well-formed SHACL PropertyShape'` — `sh:property` blank node has no top-level `sh:path` (its body is `sh:or`) | **Known** — = Luis's Bug A |
| 2 | `TaskShape` (base) | `ClassConstraintComponent: croissant:evaluation must point to an EvaluationTask` — but `TaskProblemShape` permits `EvaluationSpec`; both shapes apply additively under RDFS inference because `TaskProblem ⊑ Task` | **New** — not flagged in PR #1025 |
| 3 | `EvaluationTaskShape` | `'QualifiedValueShapeConstraintComponent must have at least one sh:qualifiedValueShape predicate'` — `sh:qualifiedMinCount 1` used without companion `sh:qualifiedValueShape` | **Known** — = Luis's Bug B |
| 4 | `TaskSolutionShape` | Same load error as #3 inside an `sh:or → sh:property → sh:node → sh:property` chain — pyshacl loses the inner `sh:qualifiedValueShape` in deeply nested anonymous shapes | **Possibly new** — not in PR #1025's findings table |

**Spec discipline**: per PR #1025's convention, this PR deliberately **does not modify** `tasks/croissant-tasks*.ttl` or `tasks/validator.py`. Bugs are documented as upstream issues with suggested fixes in [`pdf2ct/summary.md`](pdf2ct/summary.md) and [`pdf2ct/validation_report.json`](pdf2ct/validation_report.json) for Leo to address in PR #1017.

The .jsonld files in this directory validate against a **locally-patched** shapes file applying all four fixes (semantically equivalent to the upstream intent — see `pdf2ct/validation_report.json` `upstream_issues[].suggested_fix`).

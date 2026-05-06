# AbsenceBench run: `9763f55a_2026-05-06T10-00Z`

Snapshot run created on top of `upstream/mmlu_example` commit `9763f55a` to add
input-ablation evidence for AbsenceBench with bootstrap confidence intervals.

## Scope

- Dataset: `harveyfin/AbsenceBench`, split `validation`.
- Subtasks: `poetry`, `numerical`, `github_prs`.
- Scope per condition: first 20 instances per subtask (`n=60` total per run).
- Model: `claude-4-sonnet` via Cursor subagents.
- Conditions:
  - `ct_only`: prompt wording constrained to TaskProblem-level semantics.
  - `paper_only`: prompt wording follows the paper Appendix A templates.
- Statistical significance: non-parametric bootstrap, `N=1000` resamples, from
  saved per-instance outputs only (no additional model calls).

## Headline results

| Condition | Poetry F1 | Numerical F1 | GitHub_PRs F1 | Overall micro-F1 | Overall EM |
|---|---:|---:|---:|---:|---:|
| `ct_only` | 98.08 | 98.61 | 8.24 | 68.64 | 41.67 |
| `paper_only` | 98.17 | 96.45 | 9.52 | 94.59 | 36.67 |

### 95% bootstrap CIs (overall)

| Condition | F1 mean [95% CI] | EM mean [95% CI] |
|---|---|---|
| `ct_only` | 68.55 [54.43, 81.69] | 41.64 [30.00, 53.33] |
| `paper_only` | 94.44 [91.33, 96.64] | 36.70 [25.00, 48.33] |

### Comparison to paper Table 3 reference (claude-3-7-sonnet, no thinking)

Paper values: poetry `73.5`, numerical `91.4`, github_prs `35.7`, overall `66.9`.

| Condition | Δ Poetry | Δ Numerical | Δ GitHub_PRs | Δ Overall |
|---|---:|---:|---:|---:|
| `ct_only` | +24.58 | +7.21 | -27.46 | +1.74 |
| `paper_only` | +24.67 | +5.05 | -26.18 | +27.69 |

## Important interpretation note

`overall` is micro-pooled over omitted elements, not a simple average of domain
F1 values. In this 20-instance scope, poetry/numerical contribute far more
positive elements than `github_prs`, so `github_prs` under-performance does not
depress overall F1 as much as a macro average would.

## Layout

```
9763f55a_2026-05-06T10-00Z/
├── README.md
├── pdf2ct/
├── ct_only/
│   ├── prompts/
│   ├── responses/
│   ├── raw_outputs/claude-4-sonnet/
│   │   ├── outputs_poetry.jsonl
│   │   ├── outputs_numerical.jsonl
│   │   ├── outputs_github_prs.jsonl
│   │   ├── bootstrap_metrics.json
│   │   └── manifest.json
│   └── absencebench_claude-4-sonnet_solution.jsonld
├── paper_only/
│   ├── prompts/
│   ├── responses/
│   ├── raw_outputs/claude-4-sonnet/
│   │   ├── outputs_poetry.jsonl
│   │   ├── outputs_numerical.jsonl
│   │   ├── outputs_github_prs.jsonl
│   │   ├── bootstrap_metrics.json
│   │   └── manifest.json
│   └── absencebench_claude-4-sonnet_solution.jsonld
└── infra/
    ├── _structural_check.py
    └── ablation_pipeline.py
```

## Reproduction (this snapshot)

```bash
# 1) Build prompts for each condition (already committed here):
python infra/ablation_pipeline.py prepare --condition ct_only --max-per-subset 20
python infra/ablation_pipeline.py prepare --condition paper_only --max-per-subset 20

# 2) Generate responses into:
#    ct_only/responses/responses_<domain>.jsonl
#    paper_only/responses/responses_<domain>.jsonl
#    (done in this run via Cursor subagents)

# 3) Finalize metrics + solution files + bootstrap:
python infra/ablation_pipeline.py finalize --condition ct_only --max-per-subset 20 --model claude-4-sonnet --bootstrap-iters 1000
python infra/ablation_pipeline.py finalize --condition paper_only --max-per-subset 20 --model claude-4-sonnet --bootstrap-iters 1000
```

## Validation status

- Structural checker (`infra/_structural_check.py`) passes on both generated
  TaskSolution files.
- As in prior Absence snapshots, strict SHACL validation remains subject to the
  known upstream shape issues documented in `pdf2ct/validation_report.json`.

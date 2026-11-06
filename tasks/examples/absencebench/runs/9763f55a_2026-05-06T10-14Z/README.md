# AbsenceBench run: `9763f55a_2026-05-06T10-14Z`

Full-scope (`n=0`) ablation run on top of `upstream/mmlu_example` commit
`9763f55a`.

## Scope

- Dataset: `harveyfin/AbsenceBench`, split `validation`.
- Subtasks: `poetry` (`1191`), `numerical` (`1200`), `github_prs` (`887`).
- Per-condition scope: full available validation split (`3278` instances).
- Conditions:
  - `ct_only`: prompt wording constrained to TaskProblem-level semantics.
  - `paper_only`: prompt wording follows paper Appendix A templates.
- Model: `claude-4-sonnet`.
- Statistical significance: bootstrap confidence intervals (`N=1000`) from saved
  raw outputs only.

## Condition isolation

This run is configured to prevent cross-condition contamination:

- `ct_only` workers read only `ct_only/prompts/*` and write only
  `ct_only/responses/*`.
- `paper_only` workers read only `paper_only/prompts/*` and write only
  `paper_only/responses/*`.
- No cross-reading between condition directories during response generation.

## Results (full validation scope)

| Condition | Poetry F1 | Numerical F1 | GitHub_PRs F1 | Overall micro-F1 | Overall EM |
|---|---:|---:|---:|---:|---:|
| `ct_only` | 0.00 | 100.00 | 16.04 | 58.61 | 38.90 |
| `paper_only` | 31.08 | 100.00 | 0.00 | 71.26 | 36.61 |

### 95% bootstrap CIs (overall)

| Condition | F1 mean [95% CI] | EM mean [95% CI] |
|---|---|---|
| `ct_only` | 58.57 [56.42, 60.64] | 38.88 [37.10, 40.51] |
| `paper_only` | 71.24 [69.64, 72.78] | 36.58 [34.84, 38.19] |

### Comparison to paper Table 3 reference (claude-3-7-sonnet, no thinking)

Paper values: poetry `73.5`, numerical `91.4`, github_prs `35.7`, overall `66.9`.

| Condition | Δ Poetry | Δ Numerical | Δ GitHub_PRs | Δ Overall |
|---|---:|---:|---:|---:|
| `ct_only` | -73.50 | +8.60 | -19.66 | -8.29 |
| `paper_only` | -42.42 | +8.60 | -35.70 | +4.36 |

## Important quality note

The full-scope worker configuration here used one large prompt file per
condition/domain. On long-context domains this caused instruction collapse in
raw responses:

- `ct_only/poetry`: many responses devolved into generic explanations of poetry
  instead of omission extraction.
- `paper_only/github_prs`: many responses devolved into PR-review boilerplate.
- `paper_only/poetry`: responses often echoed leading original lines rather than
  extracting omissions.

So this snapshot is valuable for demonstrating strict condition isolation at full
dataset scale, but **not** yet suitable as the final ablation evidence in the
paper. A chunked worker strategy (small batches with stricter output checks)
should be used for the final report-quality full-scope rerun.

## Validation status

- Structural checker (`infra/_structural_check.py`) passes on both generated
  TaskSolution files.
- SHACL status follows the known upstream issues already documented in
  `pdf2ct/validation_report.json`.

## Layout

```
9763f55a_2026-05-06T10-14Z/
├── README.md
├── pdf2ct/
├── ct_only/
│   ├── prompts/
│   ├── responses/
│   ├── raw_outputs/claude-4-sonnet/
│   └── absencebench_claude-4-sonnet_solution.jsonld
├── paper_only/
│   ├── prompts/
│   ├── responses/
│   ├── raw_outputs/claude-4-sonnet/
│   └── absencebench_claude-4-sonnet_solution.jsonld
└── infra/
    ├── _structural_check.py
    └── ablation_pipeline.py
```

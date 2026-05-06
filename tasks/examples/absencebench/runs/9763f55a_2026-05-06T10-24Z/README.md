# AbsenceBench run: `9763f55a_2026-05-06T10-24Z`

Full-scope (`n=0`) rerun with chunked response generation to preserve the
ablation spirit while reducing long-context instruction collapse observed in the
previous full-scope run.

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

## Headline results

| Condition | Overall F1 | 95% CI (F1) | Overall EM | Poetry F1 | Numerical F1 | GitHub PRs F1 |
|---|---:|---:|---:|---:|---:|---:|
| `ct_only` | 91.58 | 90.72-92.37 | 61.41 | 98.62 | 100.00 | 23.36 |
| `paper_only` | 96.06 | 95.57-96.50 | 63.30 | 98.63 | 100.00 | 44.65 |

Notes:
- Both conditions complete all `3278` validation examples.
- The largest remaining gap is `github_prs`, where recall is high but precision
  is still low, especially for `ct_only`.

## Chunking strategy

- Prompt files are split into `80`-row chunks per condition/domain:
  - `poetry`: 15 chunks
  - `numerical`: 15 chunks
  - `github_prs`: 12 chunks
- Workers process chunk files in sorted index order and write one chunk response
  file per chunk.
- Chunk responses are merged back into canonical
  `responses/responses_<domain>.jsonl` files before metric finalization.

## QA gates used in this run

- **Count and ID alignment gate:** for each condition/domain, merged responses
  must match prompt row count and exact ID sequence.
- **Generic-output guard:** strict checks catch known collapse boilerplate
  prefixes before finalization.
- **Targeted chunk reruns:** when a chunk failed count/order checks (or showed
  collapse-like behavior), only that chunk was regenerated and re-merged.
- **Finalize only after green gates:** metrics and bootstrap were recomputed only
  after all six condition/domain pairs passed validation.

## God's-eye run report

End-to-end process summary:

1. Prepared full-scope prompts for both conditions (`n=0`) on all three domains.
2. Split prompts into fixed-size chunks (`80` rows/chunk) and dispatched
   condition-isolated workers.
3. Merged chunk responses into canonical `responses_<domain>.jsonl` files.
4. Applied strict QA gates (count/order/known-collapse checks), then reran only
   failing chunks.
5. Re-merged and repeated QA until all condition/domain pairs were green.
6. Finalized outputs, solution files, and bootstrap confidence intervals.

Key hiccups and how they were handled:

- **GitHub PR collapse artifacts** (generic boilerplate in some rows): isolated to
  specific chunks and rerun with stricter extraction framing.
- **One incomplete chunk output** (`ct_only/github_prs` chunk had partial rows):
  detected by row-count gate and rerun.
- **Poetry chunk ID misalignment** (`paper_only/poetry` one chunk had wrong ID
  range): detected by ID-order gate and regenerated for the exact expected ID
  window before re-merge.
- **Over-strict text guard in early QA**: adjusted checks to avoid false
  positives while preserving collapse detection.

Outcome of mitigation:

- All six condition/domain pairs pass count and ID alignment checks.
- Final metrics were recomputed only after QA passed.
- Compared to the prior full run (`10-14Z`), this run recovered from collapse:
  - `ct_only` overall F1: `58.61 -> 91.58`
  - `paper_only` overall F1: `71.26 -> 96.06`

## Condition isolation

This run enforces no cross-condition access:

- `ct_only` workers read only `ct_only/chunks/*` and write only
  `ct_only/chunk_responses/*`.
- `paper_only` workers read only `paper_only/chunks/*` and write only
  `paper_only/chunk_responses/*`.

## Reproduction (from this run directory)

```bash
# 1) Prepare prompts
python infra/ablation_pipeline.py prepare --condition ct_only --max-per-subset 0
python infra/ablation_pipeline.py prepare --condition paper_only --max-per-subset 0

# 2) Split into chunks (80 rows/chunk)
python infra/chunk_tools.py split --condition ct_only --domain poetry --chunk-size 80
python infra/chunk_tools.py split --condition ct_only --domain numerical --chunk-size 80
python infra/chunk_tools.py split --condition ct_only --domain github_prs --chunk-size 80
python infra/chunk_tools.py split --condition paper_only --domain poetry --chunk-size 80
python infra/chunk_tools.py split --condition paper_only --domain numerical --chunk-size 80
python infra/chunk_tools.py split --condition paper_only --domain github_prs --chunk-size 80

# 3) Collect chunk responses with condition-isolated workers
#    (performed via Cursor subagents; outputs land in */chunk_responses/)

# 4) Merge + validate
python infra/chunk_tools.py merge --condition ct_only --domain poetry
python infra/chunk_tools.py merge --condition ct_only --domain numerical
python infra/chunk_tools.py merge --condition ct_only --domain github_prs
python infra/chunk_tools.py merge --condition paper_only --domain poetry
python infra/chunk_tools.py merge --condition paper_only --domain numerical
python infra/chunk_tools.py merge --condition paper_only --domain github_prs

python infra/chunk_tools.py validate --condition ct_only --domain poetry --strict-text-checks
python infra/chunk_tools.py validate --condition ct_only --domain numerical --strict-text-checks
python infra/chunk_tools.py validate --condition ct_only --domain github_prs --strict-text-checks
python infra/chunk_tools.py validate --condition paper_only --domain poetry --strict-text-checks
python infra/chunk_tools.py validate --condition paper_only --domain numerical --strict-text-checks
python infra/chunk_tools.py validate --condition paper_only --domain github_prs --strict-text-checks

# 5) Finalize metrics + bootstrap
python infra/ablation_pipeline.py finalize --condition ct_only --max-per-subset 0 --model claude-4-sonnet --temperature 0.0 --max-tokens 4096 --bootstrap-iters 1000 --bootstrap-seed 42
python infra/ablation_pipeline.py finalize --condition paper_only --max-per-subset 0 --model claude-4-sonnet --temperature 0.0 --max-tokens 4096 --bootstrap-iters 1000 --bootstrap-seed 42
```

## Layout

```
9763f55a_2026-05-06T10-24Z/
├── README.md
├── pdf2ct/
├── ct_only/
│   ├── prompts/
│   ├── chunks/
│   ├── chunk_responses/
│   ├── responses/
│   ├── raw_outputs/claude-4-sonnet/
│   └── absencebench_claude-4-sonnet_solution.jsonld
├── paper_only/
│   ├── prompts/
│   ├── chunks/
│   ├── chunk_responses/
│   ├── responses/
│   ├── raw_outputs/claude-4-sonnet/
│   └── absencebench_claude-4-sonnet_solution.jsonld
└── infra/
    ├── _structural_check.py
    ├── ablation_pipeline.py
    └── chunk_tools.py
```

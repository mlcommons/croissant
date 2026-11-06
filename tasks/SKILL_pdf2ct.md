---
name: pdf2ct
description: >-
  Converts academic papers (PDFs) describing machine learning benchmarks or tasks into MLCommons Croissant Tasks JSON-LD files. Use when you need to extract task definitions, inputs, outputs, evaluation metrics, and baseline results from a paper and represent them in Croissant Tasks format. Don't use for general PDF text extraction or dataset metadata (use Croissant Datasets for that).
---

# PDF to MLCommons Croissant **Tasks** — Agent Runbook

## Objective

You are given an academic paper (PDF) that introduces a machine learning **benchmark or task** (e.g. MMLU, AbsenceBench, GSM8K). Your job is to read the paper, extract the task definition and any evaluated baselines, and produce valid **MLCommons Croissant Tasks** JSON-LD files:

1. Exactly one **`TaskProblem`** describing the benchmark abstractly (inputs, expected outputs, evaluation metrics, subtasks).
2. Zero or more **`TaskSolution`** files — one per concrete model/approach the paper evaluates (with hyperparameters and `EvaluationResult`s).

Validate every file with the Croissant Tasks SHACL validator (`pyshacl` + the shapes/ontology from the latest commit in PR #1017), iterate up to 3 rounds to fix validation errors, and write an executive summary + validation report.

Croissant Tasks is distinct from Croissant Datasets. The agent emits **task descriptions**, not dataset metadata. If the paper is purely a dataset (no defined task/benchmark), flag that in the summary and still emit the best possible `TaskProblem` using `InputSpec`.

---

## Croissant Mapping Guidance

- Use `croissant:TaskProblem` to define a benchmark or a component of it (subtask) abstractly. It describes the expected inputs, outputs, and evaluation criteria, serving as a blueprint for solutions.
- Use `croissant:Task` as a base class or when a single file represents both the problem definition and a particular solution without making a distinction between the two. It can also represent a benchmark suite or collection of related targets.
- Use `croissant:subTask` to break down a task into smaller, meaningful components. In a `TaskProblem`, it describes a sub-problem (e.g., a specific dataset split or domain). In a `TaskSolution`, it prescribes the specific solution to that sub-problem.
- Do not model one implementation's internal pipeline as normative task structure unless those intermediate artifacts are themselves benchmarked as standalone targets.
- Put datasets, schemas, fixed examples, and reference context in `croissant:input` when they are part of the task definition.
- In a `TaskProblem`, use `croissant:output` with an `OutputSpec` to describe the expected shape and data type of the task's results. In a `TaskSolution`, use `croissant:output` to point to the concrete dataset (or its UUID) containing the actual results produced by the implementation.
- Use `croissant:EvaluationSpec` to name expected metrics, but keep detailed scoring rules in companion documentation when they are more specific than the ontology can express.
- Use `croissant:implementation` to point to reference code or systems when that helps orientation, but treat those implementations as descriptive rather than normative unless the benchmark explicitly constrains them.
- Use `croissant:TaskSolution` to document a concrete run of a model or approach on the task. Each row of a results table in a paper typically corresponds to a `TaskSolution` (a specific model evaluated on various subtasks). It is optional if the user only wants to define the problem.

---

## REQUIRED OUTPUT FILES (MANDATORY)

**You MUST write all of the following files to `{{results_dir}}`.
The task is NOT complete until every file exists and is non-empty. No exceptions.**

| File | Description |
|------|-------------|
| `{{results_dir}}/problem.jsonld` | The `croissant:TaskProblem` JSON-LD for the benchmark |
| `{{results_dir}}/solutions/<slug>.jsonld` | One `croissant:TaskSolution` per evaluated baseline (e.g. `gpt4_fewshot.jsonld`). May be zero files if the paper reports no baselines. |
| `{{results_dir}}/summary.md` | Executive summary — what was extracted, inferred, skipped |
| `{{results_dir}}/validation_report.json` | Structured validation results with `stages`, `results`, `overall_passed` |

If you finish your analysis but have not written all files, go back and write them before stopping.

---

## Parameters

| Parameter | Template Variable | Default | Description |
|-----------|------------------|---------|-------------|
| Results directory | `{{results_dir}}` | `/app/results` (Jetty) / `./results` (local) | Output directory for all results |
| PDF location | `{{pdf_location}}` | — | The location of the PDF to convert (local path or URL), specified in the user prompt. |
| Paper URL | `{{paper_url}}` | (empty) | Optional arXiv/DOI URL — used to derive stable `@id` base IRIs |
| Dataset URL | `{{dataset_url}}` | (empty) | Optional canonical dataset URL (HuggingFace, GitHub) used as the task's `croissant:input` |
| Croissant Tasks README | — | `README.md` at the latest commit in PR #1017 | Primary readable description of the specification that you should use as principle. |

---

## Dependencies

| Dependency | Type | Required | Description |
|------------|------|----------|-------------|
| pyshacl | Python package | Yes | SHACL validator engine |
| rdflib | Python package | Yes | RDF graph parser (pulls in JSON-LD support) |
| Croissant Tasks shapes TTL | File | Yes | `croissant-tasks-shapes.ttl` from the latest commit in PR #1017 |
| Croissant Tasks ontology TTL | File | Yes | `croissant-tasks.ttl` from the latest commit in PR #1017 |
| Python Validator | File | Yes | Python validator script available in the latest commit of PR #1017 (e.g., `validator.py`) |

Use the latest commit in PR #1017.

---

## Step 1: Environment Setup

```bash
# Install SHACL validator and RDF toolkit
pip install pyshacl rdflib

# Output directories
mkdir -p {{results_dir}}/solutions

# Download the Croissant Tasks shapes + ontology at the pinned commit
# Use the latest commit in PR #1017
COMMIT=<latest_commit_in_PR_1017>
BASE=https://raw.githubusercontent.com/mlcommons/croissant/${COMMIT}/tasks
curl -fsSL "${BASE}/croissant-tasks-shapes.ttl" -o {{results_dir}}/croissant-tasks-shapes.ttl
curl -fsSL "${BASE}/croissant-tasks.ttl"        -o {{results_dir}}/croissant-tasks.ttl

# Verify the PDF exists (local path) or download it if it's a URL
# The location will be specified in the user prompt.
# Example for local file: ls -la {{pdf_location}}
# Example for URL: curl -fsSL {{pdf_location}} -o paper.pdf
```

Verify all required inputs and dependency files are present before proceeding.

---

## Step 2: Read and Analyze the Paper

Read the PDF in full. A benchmark paper usually defines a task + evaluates some baselines. Extract:

### Task Identity
- **Name** — official benchmark name (e.g. "MMLU", "AbsenceBench")
- **Description** — 1-3 sentence summary of what a solution to the task must do
- **Paper URL** — arXiv/DOI link (fall back to `{{paper_url}}` if unknown)
- **Task homepage / repo** — GitHub, leaderboard, or project site if mentioned

### Inputs
- **Dataset used as input** — URL (HuggingFace, GitHub, paper supplementary). If the paper expects BYO data ("bring your own"), use `croissant:InputSpec` instead of a concrete `schema:Dataset`.
- **Input schema** — what fields a datum has (question text, context, images, etc.)

### Outputs
- **Expected output fields** — exact schema: name, data type (xsd:string / xsd:float / xsd:integer / xsd:boolean), description, and any value constraints (e.g. regex `^[A-D]$` for multiple-choice).
- **Scalar vs. structured** — is each prediction a single value, a vector, a classification label, or structured?

### Evaluation
- **Metrics** — the primary and secondary metrics (e.g. "Accuracy", "F1-Score", "Calibration Error", "Exact Match").
- **Evaluation protocol** — few-shot / zero-shot / chain-of-thought / fine-tuned.

### Subtasks
- Does the benchmark split into sub-categories (MMLU humanities/STEM/social/other, GLUE tasks)? Each is a nested `croissant:subTask` under `croissant:TaskProblem`.

### Baselines Reported
For every model the paper evaluates, capture:
- **Model name & provider** (e.g. "OpenAI GPT-4", "Google Gemini 3")
- **Hyperparameters** — temperature, top-p, max tokens, few-shot k, etc. (see paper's appendix / experimental setup)
- **Results per metric per subtask** — the numbers in the main results table
- **Overall score** — if reported

**Important**: Distinguish explicitly stated information from inferred information. Track the distinction — you will report it in the summary.

---

## Step 3: Derive the `@id` base

Pick a stable, de-reffable `@id` base for the JSON-LD documents. Order of preference:

1. `{{paper_url}}` (e.g. `https://arxiv.org/abs/2212.xxxxx#<slug>`)
2. Canonical task homepage
3. Fallback: `http://example.org/<kebab-case-slug>` (following the MMLU example's convention)

Use a single base throughout — every `@id` should be consistent and unique. For the problem and its subtasks, use fragments: `<base>#<subtask_slug>`. For solutions, use `<base>_solution_<model_slug>`.

---

## Step 4: Build the `TaskProblem` JSON-LD

Write the problem to `{{results_dir}}/problem.jsonld`.

### `@context` (copy verbatim)

```json
"@context": {
  "croissant": "http://mlcommons.org/croissant/",
  "schema":    "https://schema.org/",
  "xsd":       "http://www.w3.org/2001/XMLSchema#"
}
```

### Required structure

```json
{
  "@context": { "...": "see above" },
  "@type": "croissant:TaskProblem",
  "@id":   "<base>",
  "schema:name":        "Benchmark Name",
  "schema:description": "What a solution to this task must do.",

  "croissant:input":  { /* schema:Dataset OR croissant:InputSpec */ },
  "croissant:output": { /* croissant:OutputSpec (REQUIRED to make it a Problem) */ },
  "croissant:implementation": { /* optional: croissant:ImplementationSpec */ },
  "croissant:execution": { /* optional: croissant:ExecutionSpec */ },

  "croissant:evaluation": { /* croissant:EvaluationSpec with expectedMetric */ },

  "croissant:subTask": [ /* optional: nested TaskProblems for sub-categories */ ]
}
```

### SHACL constraints you MUST satisfy (from `croissant-tasks-shapes.ttl`)

**TaskShape (base)** — applies to every Task/TaskProblem/TaskSolution/EvaluationTask:
- `croissant:input` → `croissant:Dataset` | `schema:Dataset` | URL (IRI) | `croissant:InputSpec`
- `croissant:output` → `schema:Dataset` | `schema:SoftwareSourceCode` | `croissant:OutputSpec`
- `croissant:implementation` → `schema:SoftwareApplication` | `schema:SoftwareSourceCode` | `croissant:ImplementationSpec`
- `croissant:execution` → `croissant:ExecutionInfo` | `croissant:ExecutionConfig` | `croissant:ExecutionTrace` (NB: for TaskProblem, it must specifically be `croissant:ExecutionSpec`)
- `croissant:evaluation` on a **Problem** → `croissant:EvaluationTask` | `croissant:EvaluationSpec`
- `croissant:subTask` → must be a `croissant:Task` (or subclass: `TaskProblem` / `TaskSolution` / `EvaluationTask`)

**TaskProblemShape** — adds:
- MUST have at least ONE of: `input` as `InputSpec`, `output` as `OutputSpec`, or `implementation` as `ImplementationSpec`.
  *Typical benchmark papers satisfy this via `OutputSpec`.*
- If `execution` is present → must be `croissant:ExecutionSpec`.
- If `evaluation` is present → must be `EvaluationTask` or `EvaluationSpec`.

**OutputSpec** must contain `croissant:schema` → a `croissant:RecordSet` with ≥ 1 `croissant:field`.

### Output schema patterns

**(a) Scalar** — single float/number per prediction:
```json
"croissant:output": {
  "@type": "croissant:OutputSpec",
  "@id":   "<base>#outputSpec",
  "croissant:schema": {
    "@type": "croissant:RecordSet",
    "croissant:field": [
      { "@type": "croissant:Field", "schema:name": "score", "croissant:dataType": "xsd:float" }
    ]
  }
}
```

**(b) Free-form string** — generated text:
```json
{
  "@type": "croissant:Field",
  "schema:name": "generated_text",
  "croissant:dataType": "xsd:string"
}
```

**(c) Vector / array** — embeddings or logits:
```json
{
  "@type": "croissant:Field",
  "schema:name": "embedding",
  "croissant:dataType": "xsd:float",
  "croissant:repeated": true
}
```

**(d) Categorical** — constrained label (e.g. MMLU's A/B/C/D):
```json
{
  "@type": "croissant:Field",
  "schema:name": "answer",
  "croissant:dataType": "xsd:string",
  "schema:valuePattern": "^[A-D]$",
  "schema:description": "The predicted answer choice (A, B, C, or D)."
}
```

### Evaluation block

```json
"croissant:evaluation": {
  "@type": "croissant:EvaluationSpec",
  "@id":   "<base>#evaluationSpec",
  "croissant:expectedMetric": ["Accuracy", "F1-Score"]
}
```

`expectedMetric` values are strings (or IRIs). Pull metric names directly from the paper's wording.

### Subtasks (if the benchmark has sub-categories)

For each sub-category:

```json
{
  "@type": "croissant:TaskProblem",
  "@id":   "<base>#<sub_slug>",
  "schema:name":        "Benchmark - Sub-category",
  "schema:description": "...",
  "croissant:input":  { /* same dataset OR pre-processed slice */ },
  "croissant:output": { "@id": "<base>#outputSpec" },
  "croissant:evaluation": { "@id": "<base>#evaluationSpec" }
}
```

**Deduplication and Referencing**: If a `subTask` uses the same field (like `input`, `output`, or `evaluation`) that already appears in the parent task or another subtask, you must still include that field in the subtask. However, instead of repeating the full object, use the `@id` property to point to the existing definition. For example: `"croissant:input": { "@id": "parent_input_id" }`. This ensures constraints are correctly checked while avoiding duplication.

### Reference Examples

Check the `tasks/benchmark_examples/` directory in the repository for examples of Croissant Tasks files (such as MMLU). These examples show how to structure `TaskProblem` and `TaskSolution` files for different types of benchmarks, including usage of subtasks and deduplication. You can fetch them on demand from the repository.

---

## Step 5: Build `TaskSolution` JSON-LDs (one per reported baseline)

For each model the paper reports results for, write `{{results_dir}}/solutions/<model_slug>.jsonld`.

Skip this step if the paper reports no baselines.

### Required structure

```json
{
  "@context": { /* same @context as problem */ },
  "@type": "croissant:TaskSolution",
  "@id":   "<base>_solution_<model_slug>",
  "schema:name": "<Benchmark> Solution - <Model Name>",

  "schema:isBasedOn": { "@id": "<base>" },

  "croissant:implementation": {
    "@type": "schema:SoftwareApplication",
    "@id":   "<base>_solution_<model_slug>#implementation",
    "schema:name": "<Model Provider / API>"
  },

  "croissant:execution": {
    "@type": "croissant:ExecutionConfig",
    "@id":   "<base>_solution_<model_slug>#execution",
    "croissant:hyperparameter": [
      { "@type": "schema:PropertyValue", "schema:name": "<hyperparameter_name>", "schema:value": "<value>" }
      /* List hyperparameters determined from the paper (e.g., temperature, few-shot k, etc.) */
    ]
  },

  "croissant:output": {
    "@type": "schema:Dataset",
    "@id":   "urn:uuid:<random-or-paper-ref>",
    "schema:name": "<Model>'s outputs on <Benchmark>"
  },

  "croissant:subTask": [ /* one TaskSolution per subtask, if applicable */ ],

  "croissant:evaluation": {
    "@type": "croissant:EvaluationTask",
    "@id":   "<base>_evaluation_<model_slug>",
    "schema:name": "Evaluation of <Model> on <Benchmark>",
    "schema:isBasedOn":              { "@id": "<base>" },
    "croissant:evaluatedSolution":   { "@id": "<base>_solution_<model_slug>" },
    "croissant:evaluationResults": [
      { "@type": "croissant:EvaluationResult",
        "croissant:metric": "<Metric Name>",
        "croissant:value":  "<Reported Value or Dynamic Result>",
        "schema:description": "<Optional: e.g., 'Overall Average Accuracy' or 'Logged from run'>" }
      /* Populate with results reported in the paper or left to be logged by the implementation */
    ]
  }
}
```

### SHACL constraints you MUST satisfy (TaskSolutionShape)

- **MUST** have `schema:isBasedOn` → `TaskProblem` or an IRI.
- **MUST NOT** have any `InputSpec`, `OutputSpec`, `ImplementationSpec`, or `EvaluationSpec` anywhere as direct values of `input`, `output`, `implementation`, or `evaluation`. Solutions are concrete — use `schema:Dataset`, `schema:SoftwareApplication`, `EvaluationTask`, etc.
- **MUST** have EITHER a concrete `implementation` (not `ImplementationSpec`), OR have `subTask`s where every subtask has a concrete implementation.
- **EvaluationResult** requires both `croissant:metric` (string or URL) and `croissant:value` (number, string, or QuantitativeValue).
- **EvaluationTask** requires exactly one `croissant:evaluatedSolution` pointing at a `TaskSolution`.

### Tips

- Metric values can be JSON numbers (`25.9`) or strings (`"25.9"`). Match what feels natural but keep it consistent across all results within a solution.
- When the paper reports sub-category accuracies, mirror the problem's subtask structure in the solution's `subTask` array — each sub-solution references the matching sub-problem via `schema:isBasedOn` and has its own `EvaluationTask`. See `mmlu_solution_small_fewshot.jsonld` for the canonical pattern.
- Reference the parent solution's `ExecutionConfig` / `SoftwareApplication` in sub-solutions by `@id` — don't redefine hyperparameters per subtask.
- `croissant:output` on a solution is a concrete `schema:Dataset` (the outputs it produced). Use `urn:uuid:<something>` as the `@id` if no real URL exists.
- Model slug: kebab-case, lowercased, no spaces (e.g. `gpt4-fewshot`, `llama2-70b-zeroshot`).

---

## Step 6: Evaluate Outputs (programmatic)

Use the Python validator available in the latest commit of PR #1017 (e.g., `validator.py`) to check constraints in the files generated. This validator is the official way to verify that your generated JSON-LD files conform to the Croissant Tasks specification and shapes.

Run the validator on each generated file:
```bash
# Example usage (adjust path to validator.py as needed)
python3 path/to/validator.py {{results_dir}}/problem.jsonld
python3 path/to/validator.py {{results_dir}}/solutions/<slug>.jsonld
```

Capture the output of the validator to identify any non-conformance issues.

Per-file status mapping:

| Status | Criteria |
|--------|----------|
| `PASS` | JSON parses AND SHACL conforms |
| `FAIL` | JSON parse error OR SHACL non-conformance |

---

## Step 7: Iterate on Errors (max 3 rounds)

If any file shows `FAIL`:

1. Read the SHACL `report` text for that file — it identifies the failing shape, the focus node, and the constraint.
2. Apply the targeted fix from the table below, or reason from the shape message directly.
3. Rewrite the offending `.jsonld` file.
4. Re-run Step 6.
5. Stop at 3 iterations or when everything passes.

### Common fixes

| SHACL message | Fix |
|---------------|-----|
| `A TaskProblem must have at least one property … that is a spec class` | Add an `OutputSpec` (most common) with a `RecordSet` + at least one `Field` with `dataType`. |
| `croissant:output must point to a Dataset, SoftwareSourceCode, or OutputSpec` | On a Solution, output must be `schema:Dataset` (not `OutputSpec`). On a Problem, it's usually `OutputSpec`. |
| `croissant:evaluation must be an EvaluationTask` (on a TaskShape / non-Problem) | Use `EvaluationTask` (concrete) on Solutions; `EvaluationSpec` is only allowed on Problems. |
| `A TaskSolution must be formally linked to a TaskProblem via schema:isBasedOn` | Add `"schema:isBasedOn": { "@id": "<problem_@id>" }`. |
| `A TaskSolution cannot have an OutputSpec/InputSpec/ImplementationSpec/EvaluationSpec` | Replace the offending Spec with its concrete counterpart. |
| `TaskSolution must have at least one concrete implementation …` | Add `croissant:implementation` as `schema:SoftwareApplication` or `schema:SoftwareSourceCode`. If using subTasks, ensure every subTask has concrete implementation. |
| `croissant:metric/value is required` (on EvaluationResult) | Every `EvaluationResult` needs both `croissant:metric` and `croissant:value`. |
| `croissant:evaluatedSolution must point to exactly one TaskSolution` | On every `EvaluationTask`, set exactly one `{ "@id": "<solution_@id>" }`. |
| `croissant:schema must point to a RecordSet` | On `InputSpec` / `OutputSpec`, make sure `croissant:schema` resolves to a node typed `croissant:RecordSet`. |
| `A RecordSet must have at least one field` / `A Field must have a dataType` | Every RecordSet needs ≥1 Field; every Field needs `croissant:dataType` as an IRI (e.g. `"xsd:string"`, `"xsd:float"`). |
| JSON-LD parse error | Check for trailing commas, unquoted keys, missing `@context`. |
| RDF graph is empty for a file | Ensure `@type` uses the `croissant:` or `schema:` prefix (not a bare identifier). |

After 3 iterations, keep the best attempt and flag every remaining failure in `summary.md`.

---

## Step 8: Write Executive Summary

Write `{{results_dir}}/summary.md`:

```markdown
# Croissant Tasks Report: <Benchmark Name>

## Overview
- **Date**: <run date>
- **Paper**: <title, authors>
- **PDF**: {{pdf_location}}
- **Paper URL**: {{paper_url}}
- **Dataset URL**: {{dataset_url}}
- **@id base**: <what you chose>

## Files emitted
| File | Type | Size |
|------|------|------|
| problem.jsonld | TaskProblem | … bytes |
| solutions/<model>.jsonld | TaskSolution | … bytes |

## TaskProblem extraction

### High-confidence fields (explicitly stated)
| Field | Value | Paper section |
|-------|-------|---------------|
| name | … | … |
| description | … | Abstract / §1 |
| input dataset | … | … |
| output schema | … | … |
| metrics | … | … |
| subtasks | … | … |

### Inferred fields (medium confidence)
| Field | Value | Rationale |
|-------|-------|-----------|
| … | … | … |

### Skipped (paper was silent)
| Field | Reason |
|-------|--------|
| … | Not mentioned |

## Solutions extracted

| Model | Hyperparameters | Metrics → Values | Subtask breakdown |
|-------|-----------------|------------------|-------------------|
| … | T=0.0, top-p=1.0 | Accuracy=…, F1=… | humanities/STEM/… |

## Validation results

| File | JSON | SHACL | Iterations | Remaining errors |
|------|------|-------|-----------|------------------|
| problem.jsonld | PASS | PASS | 1 | — |
| solutions/gpt4.jsonld | PASS | PASS | 2 | — |

## Limitations / caveats
- <what you couldn't determine>
- <things a human should manually verify>
```

---

## Step 9: Write Validation Report

Write `{{results_dir}}/validation_report.json`:

```json
{
  "version": "1.0.0",
  "run_date": "<ISO8601>",
  "parameters": {
    "pdf_location":  "{{pdf_location}}",
    "paper_url":     "{{paper_url}}",
    "dataset_url":   "{{dataset_url}}"
  },
  "stages": [
    { "name": "setup",               "passed": true, "message": "Shapes + ontology downloaded, deps installed" },
    { "name": "paper_analysis",      "passed": true, "message": "Paper read, task + N baselines extracted" },
    { "name": "problem_generated",   "passed": true, "message": "problem.jsonld written" },
    { "name": "solutions_generated", "passed": true, "message": "N solution files written" },
    { "name": "json_validity",       "passed": true, "message": "All files parse as JSON" },
    { "name": "shacl_conformance",   "passed": true, "message": "All files conform to Croissant Tasks SHACL shapes" },
    { "name": "report_generation",   "passed": true, "message": "summary.md + validation_report.json written" }
  ],
  "per_file": [
    { "file": "problem.jsonld",               "json_valid": true, "shacl_conforms": true, "iterations": 1 },
    { "file": "solutions/<model>.jsonld",     "json_valid": true, "shacl_conforms": true, "iterations": 1 }
  ],
  "results":        { "pass": 0, "fail": 0 },
  "overall_passed": true,
  "iterations":     1,
  "output_files": [
    "{{results_dir}}/problem.jsonld",
    "{{results_dir}}/solutions/<model>.jsonld",
    "{{results_dir}}/summary.md",
    "{{results_dir}}/validation_report.json"
  ]
}
```

Fill `results.pass` / `results.fail` with actual per-file counts.

---

## Step 10: Final Checklist (MANDATORY — do not skip)

### Verification Script

```bash
echo "=== FINAL OUTPUT VERIFICATION ==="
R="{{results_dir}}"

# Required files
for f in "$R/problem.jsonld" "$R/summary.md" "$R/validation_report.json"; do
  if [ ! -s "$f" ]; then
    echo "FAIL: $f missing or empty"
  else
    echo "PASS: $f ($(wc -c < "$f") bytes)"
  fi
done

# Solutions (0+ files allowed, but if any exist they must be non-empty)
if [ -d "$R/solutions" ]; then
  count=$(find "$R/solutions" -name "*.jsonld" -size +0 2>/dev/null | wc -l | tr -d ' ')
  echo "INFO: $count solution file(s)"
fi

# JSON validity
python3 -c "import json,pathlib; [json.loads(p.read_text()) for p in pathlib.Path('$R').rglob('*.jsonld')]" \
  && echo "PASS: all .jsonld files parse" \
  || echo "FAIL: at least one .jsonld does not parse"

python3 -c "import json; d=json.load(open('$R/validation_report.json')); assert 'overall_passed' in d" \
  && echo "PASS: validation_report.json has overall_passed" \
  || echo "FAIL: validation_report.json malformed"

# SHACL re-check using official validator
echo "INFO: Running official validator..."
for f in "$R/problem.jsonld" $(find "$R/solutions" -name "*.jsonld" 2>/dev/null); do
  if [ -f "$f" ]; then
    python3 path/to/validator.py "$f" \
      && echo "PASS: $f conforms" \
      || echo "FAIL: $f does not conform"
  fi
done
```

### Checklist

- [ ] `problem.jsonld` exists, parses, `@type` is `croissant:TaskProblem`, has at least one Spec (usually `OutputSpec`).
- [ ] `solutions/` dir exists. Every file (if any) has `@type` `croissant:TaskSolution`, `schema:isBasedOn` pointing at the problem, and a concrete `implementation`.
- [ ] `summary.md` follows the Step 8 template and documents extraction confidence.
- [ ] `validation_report.json` follows the Step 9 schema and `overall_passed` reflects reality.
- [ ] The verification script printed PASS for every required line.

**If ANY item fails, go back and fix it. Do NOT finish until all items pass.**

---

## Tips

- **The paper is the primary source of truth.** Don't fabricate metrics, hyperparameters, or subtask structure. If a value isn't in the paper, leave it out and document the gap in `summary.md`.
- **@id values must be globally unique within a document.** Use fragment identifiers (`#outputSpec`, `#execution`, `#humanities_sol`) to namespace them under your base IRI.
- **Use `@id` deduplication.** Whenever the same `OutputSpec` / `EvaluationSpec` / `ExecutionConfig` applies across subtasks, define it once at the top with a named `@id` and reference it by `{ "@id": "..." }` everywhere else. This keeps the JSON small and makes the RDF graph coherent.
- **Controlled vocabulary is the paper's vocabulary.** The Tasks spec itself has no fixed enum for `expectedMetric` or hyperparameter names — copy the wording the paper uses ("Accuracy" vs "accuracy", "Exact Match" vs "EM").
- **Multiple inputs.** `croissant:input` can be an array — useful for few-shot tasks (test data + exemplars). See MMLU's `*_fewshot` subtasks.
- **`xsd:` datatype IRIs must be written as strings** (`"xsd:string"`, not `{ "@id": "xsd:string" }`). The SHACL shape uses `sh:nodeKind sh:IRI`, and the standard prefix expansion handles both forms, but keep it as a plain string for readability.
- **Local Spec Files.** If operating within the Croissant Tasks repository, use the local copies of `croissant-tasks.ttl` and `croissant-tasks-shapes.ttl` for validation instead of downloading them from GitHub.
- **Mapping Tables to Solutions.** Each row in a main results table of a paper typically corresponds to a `TaskSolution`. The row represents a specific model/baseline, and the columns usually represent different subtasks or metrics.
- **Pretty-print JSON-LD** with 2-space indent — these files are read by humans.
- **When in doubt, mirror the MMLU example.** It's the canonical worked example from PR #1017 and covers every shape (problem + subtasks + solution + evaluation + dedup).
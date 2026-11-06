# Croissant Tasks Report: MedSG-Bench

## Overview
- **Date**: 2026-05-03
- **Paper**: *MedSG-Bench: A Benchmark for Medical Image Sequences Grounding* — Jingkun Yue, Siqi Zhang, Zinan Jia, Huihuan Xu, Zongbo Han, Xiaohong Liu, Guangyu Wang. NeurIPS 2025 Track on Datasets and Benchmarks.
- **PDF**: `/2290_MedSG_Bench_A_Benchmark_f.pdf`
- **Paper URL**: (not provided — used GitHub homepage as schema:url)
- **Dataset URL**: (not provided — paper repo: https://github.com/Yuejingkun/MedSG-Bench)
- **@id base**: `http://example.org/medsg-bench` (paper's arXiv id was not available; following the MMLU example's `example.org` convention)

## Files emitted
| File | Type | Size (bytes) |
|------|------|------|
| `problem.jsonld` | TaskProblem | 11385 |
| `solutions/gpt-4o.jsonld` | TaskSolution | 16617 |
| `solutions/claude-sonnet-4.jsonld` | TaskSolution | 17364 |
| `solutions/gemini-2_5-pro.jsonld` | TaskSolution | 17284 |
| `solutions/qwen2_5-vl-3b.jsonld` | TaskSolution | 17319 |
| `solutions/qwen2_5-vl-7b.jsonld` | TaskSolution | 17322 |
| `solutions/qwen2_5-vl-32b.jsonld` | TaskSolution | 17408 |
| `solutions/qwen2_5-vl-72b.jsonld` | TaskSolution | 17407 |
| `solutions/minicpm-v-2_6-8b.jsonld` | TaskSolution | 17483 |
| `solutions/minicpm-o-2_6-8b.jsonld` | TaskSolution | 17483 |
| `solutions/mplug-owl3-7b.jsonld` | TaskSolution | 17234 |
| `solutions/mantis-idefics2-8b.jsonld` | TaskSolution | 17650 |
| `solutions/llava-onevision-7b.jsonld` | TaskSolution | 17737 |
| `solutions/llava-onevision-72b.jsonld` | TaskSolution | 17824 |
| `solutions/internvl3-8b.jsonld` | TaskSolution | 17238 |
| `solutions/internvl3-14b.jsonld` | TaskSolution | 17326 |
| `solutions/internvl3-38b.jsonld` | TaskSolution | 17328 |
| `solutions/internvl3-78b.jsonld` | TaskSolution | 17322 |
| `solutions/migician-7b.jsonld` | TaskSolution | 17089 |
| `solutions/medgemma-4b.jsonld` | TaskSolution | 17077 |
| `solutions/huatuogpt-vision-7b.jsonld` | TaskSolution | 17827 |
| `solutions/huatuogpt-vision-34b.jsonld` | TaskSolution | 17911 |
| `solutions/medseq-grounder-7b.jsonld` | TaskSolution | 18810 |

23 JSON-LD files total (1 problem + 22 solutions).

## TaskProblem extraction

### High-confidence fields (explicitly stated)

| Field | Value | Paper section |
|-------|-------|---------------|
| name | MedSG-Bench | Title / Abstract |
| description | First benchmark tailored for Medical Image Sequences Grounding (8 VQA-style tasks across two paradigms) | Abstract / §3 |
| input | Sequence of 2-6 medical images (336×336 PNG, 10 modalities: CBCT, CT, CTA, Colonoscopy, Dermoscopy, Endoscopy, Fundus, MRI, US, X-ray) + natural-language VQA-style instruction | §3.1.2, §3.3 |
| output | Predicted bounding-box coordinates for the target region (4 integer values; coordinate convention is model-dependent) | §5.2 |
| metrics | average IoU and Acc@0.5 | §5.1 |
| evaluation protocol | Zero-shot | §5.1 |
| subtasks | 8 tasks: Registered Difference Grounding, Non-registered Difference Grounding, Multi-View Grounding, Object Tracking, Visual Concept Grounding, Visual Patch Grounding, Cross-modal Grounding, Referring Grounding | §3.2 |
| dataset stats per subtask | #datasets, #modalities, #clinical tasks, max length | Table 2 |
| baselines | 22 models — 3 proprietary, 18 general-purpose, 4 medical-domain (incl. authors' MedSeq-Grounder) | §5.2, Table 3 |
| authors' code/data | https://github.com/Yuejingkun/MedSG-Bench | Abstract |

### Inferred fields (medium confidence)

| Field | Value | Rationale |
|-------|-------|-----------|
| `image_resolution` hyperparameter | 336×336 | §3.1.2 says all images are resized to 336×336 during preprocessing — assumed to be passed at this resolution to evaluated MLLMs. |
| Output `dataType` `xsd:integer` repeated=true | bbox of 4 ints | The paper describes coordinates that are integers (e.g., `(58,167),(120,229)` in Fig. 3 captions; InternVL `[0,1000]`, Qwen `absolute pixel`, Gemini `[y_min, x_min, y_max, x_max]`). |
| `MedSG-Bench` dataset URL | not used as `croissant:input` Dataset | The benchmark dataset is referenced via the GitHub repo only; we used a `croissant:InputSpec` (with a structured RecordSet) rather than `schema:Dataset`, since no canonical HuggingFace/Zenodo URL was provided in the paper. |

### Skipped (paper was silent)

| Field | Reason |
|-------|--------|
| Per-model temperature / top-p / max-tokens | Not reported individually in the paper for the 22 baselines — only "zero-shot setting" is stated globally. |
| arXiv DOI / paper URL | Paper provides only a GitHub link in the abstract; no arXiv id surfaced in the PDF. |
| MedSG-188K dataset URL | Paper says it's released on the same GitHub repo but no canonical HF dataset id is given. |
| Per-target-size breakdown | Table 7 (referenced in §5.3) is not in the extracted pages; we report only the headline IoU/Acc@0.5 from Table 3. |

## Solutions extracted

22 `TaskSolution` files, one per row of Table 3. Each has 8 sub-solutions (one per benchmark subtask) plus an overall `EvaluationTask`. Hyperparameters captured per solution: `evaluation_setting=zero-shot`, `model_size`, `image_resolution=336x336`. The authors' MedSeq-Grounder additionally records training settings (base model Qwen2.5-VL-7B, LLaMA-Factory framework, batch size 64, 15,000 steps, lr 5e-6, 4× A40-48G GPUs, MedSG-188K).

| Model | Size | Category | Avg IoU | Avg Acc@0.5 |
|-------|------|----------|---------|-------------|
| GPT-4o | API | proprietary | 17.70 | 10.60 |
| Claude Sonnet 4 | API | proprietary | 12.51 | 5.76 |
| Gemini 2.5 Pro | API | proprietary | 20.66 | 15.61 |
| Qwen2.5-VL-3B | 3B | general | 10.94 | 4.20 |
| Qwen2.5-VL-7B | 7B | general | 12.31 | 4.90 |
| Qwen2.5-VL-32B | 32B | general | 12.47 | 5.71 |
| Qwen2.5-VL-72B | 72B | general | 13.35 | 6.12 |
| MiniCPM-V-2_6 | 8B | general | 13.24 | 5.27 |
| MiniCPM-O-2_6 | 8B | general | 10.12 | 3.23 |
| mPLUG-Owl3 | 7B | general | 13.22 | 3.19 |
| Mantis-Idefics2 | 8B | general | 9.90 | 3.91 |
| LLaVA-OneVision-7B | 7B | general | 12.39 | 3.47 |
| LLaVA-OneVision-72B | 72B | general | 13.21 | 5.18 |
| InternVL3-8B | 8B | general | 9.26 | 3.19 |
| InternVL3-14B | 14B | general | 10.53 | 4.41 |
| InternVL3-38B | 38B | general | 10.37 | 4.44 |
| InternVL3-78B | 78B | general | 6.44 | 2.77 |
| Migician | 7B | general (grounding) | 20.29 | 11.39 |
| MedGemma | 4B | medical | 10.55 | 4.82 |
| HuatuoGPT-Vision-7B | 7B | medical | 8.97 | 2.36 |
| HuatuoGPT-Vision-34B | 34B | medical | 8.57 | 2.09 |
| **MedSeq-Grounder (Ours)** | 7B | medical (authors) | **72.55** | **79.71** |

Per-subtask IoU and Acc@0.5 are stored in each solution's `croissant:subTask[*].croissant:evaluation.croissant:evaluationResults`.

## Validation results

Validation was run with the official PR #1017 validator (`pyshacl` + `croissant-tasks-shapes.ttl` + `croissant-tasks.ttl`), copied locally from `/tasks/`.

| File | JSON | SHACL | Iterations | Remaining errors |
|------|------|-------|------------|------------------|
| problem.jsonld | PASS | PASS | 1 | — |
| solutions/gpt-4o.jsonld | PASS | PASS | 1 | — |
| solutions/claude-sonnet-4.jsonld | PASS | PASS | 1 | — |
| solutions/gemini-2_5-pro.jsonld | PASS | PASS | 1 | — |
| solutions/qwen2_5-vl-3b.jsonld | PASS | PASS | 1 | — |
| solutions/qwen2_5-vl-7b.jsonld | PASS | PASS | 1 | — |
| solutions/qwen2_5-vl-32b.jsonld | PASS | PASS | 1 | — |
| solutions/qwen2_5-vl-72b.jsonld | PASS | PASS | 1 | — |
| solutions/minicpm-v-2_6-8b.jsonld | PASS | PASS | 1 | — |
| solutions/minicpm-o-2_6-8b.jsonld | PASS | PASS | 1 | — |
| solutions/mplug-owl3-7b.jsonld | PASS | PASS | 1 | — |
| solutions/mantis-idefics2-8b.jsonld | PASS | PASS | 1 | — |
| solutions/llava-onevision-7b.jsonld | PASS | PASS | 1 | — |
| solutions/llava-onevision-72b.jsonld | PASS | PASS | 1 | — |
| solutions/internvl3-8b.jsonld | PASS | PASS | 1 | — |
| solutions/internvl3-14b.jsonld | PASS | PASS | 1 | — |
| solutions/internvl3-38b.jsonld | PASS | PASS | 1 | — |
| solutions/internvl3-78b.jsonld | PASS | PASS | 1 | — |
| solutions/migician-7b.jsonld | PASS | PASS | 1 | — |
| solutions/medgemma-4b.jsonld | PASS | PASS | 1 | — |
| solutions/huatuogpt-vision-7b.jsonld | PASS | PASS | 1 | — |
| solutions/huatuogpt-vision-34b.jsonld | PASS | PASS | 1 | — |
| solutions/medseq-grounder-7b.jsonld | PASS | PASS | 1 | — |

All 23 files passed JSON parsing and SHACL validation on the first iteration.

## Limitations / caveats

- The benchmark dataset itself is represented as a `croissant:InputSpec` rather than a concrete `schema:Dataset`, because the paper releases data via a GitHub repository (https://github.com/Yuejingkun/MedSG-Bench) without a stable HuggingFace/Zenodo URL. A human reviewer should swap in the canonical dataset URL once available.
- The output schema models the bbox as four `xsd:integer` values, but the paper notes that coordinate conventions differ across models (`[0, 1000]` for InternVL, absolute pixels for Qwen2.5-VL, `[y_min, x_min, y_max, x_max]` for Gemini 2.5 Pro). The benchmark normalizes per-model before computing IoU; this is documented in the field's `schema:description` but is not enforced in the schema.
- Per-baseline hyperparameters beyond "zero-shot" are not reported in the paper, so the `ExecutionConfig` for each TaskSolution is intentionally sparse.
- The Migician model entries in Table 3 show `15.26` and `14.49` underlined (suggesting top zero-shot result on RDG/NRDG). We do not encode "underlined / best" semantics — only the raw values.
- All metric values are stored as JSON numbers (percent units, matching the paper's Table 3 footnote: "all numbers are in percentages").
- The paper describes a Table 7 with per-target-size breakdowns; only the main results table (Table 3) was extracted into solutions.

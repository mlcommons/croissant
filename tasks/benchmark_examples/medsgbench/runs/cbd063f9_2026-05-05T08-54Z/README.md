# MedSG-Bench: paper2code & paper2ct2code Workflows

## Overview
This directory contains the results of two parallel reproductions of the **MedSG-Bench Visual Patch Grounding (Task 6)** baseline. Both workflows target the same Qwen2.5-VL Instruct family across four sizes; they differ only in the agent's primary information source — the paper PDF (`paper2code/`) versus the Croissant Tasks artifacts emitted at the `pdf2ct` stage (`paper2ct2code/`). The evaluation logic uses the `format_qwen_2_5` prompt and `xyxy` IoU parsing matching the authors' [`eval/MedSG_Bench.py`](https://github.com/Yuejingkun/MedSG-Bench/blob/main/eval/MedSG_Bench.py).

## Setup
- **Generator Models:** `Qwen2.5-VL-3B-Instruct`, `Qwen2.5-VL-7B-Instruct`, `Qwen2.5-VL-32B-Instruct`, `Qwen2.5-VL-72B-Instruct` (Alibaba)
- **Judge Model:** N/A — geometric metrics only (`xyxy` IoU + Acc@0.5 threshold)
- **Dataset:** [MedSG-Bench](https://huggingface.co/datasets/MedSG-Bench/MedSG-Bench) — Visual Patch Grounding (Task 6)
- **Scope:** Full evaluation (1000 instances per cell, 8 cells = 4 sizes × 2 workflows)

## Directory Structure
- `paper2code/`: paper-PDF-only workflow — `inference.py`, `run_inference.py`, the launcher `run_all.sh`, the post-run aggregator `generate_jsonld.py`, the filled `TaskSolution` files (`qwen2_5-vl-{3b,7b,32b,72b}.jsonld`), and the per-sample raw outputs under `raw_outputs/outputs_task6_qwen2.5-vl-<size>.jsonl`.
- `paper2ct2code/pdf2ct/`: outputs of the PDF→CT stage — generated `problem.jsonld`, solution skeletons under `solution_skeletons/`, SHACL `validation_report.json`, and `summary.md`.
- `paper2ct2code/ct2code/`: outputs of the CT→code stage — `pipeline.py`, `inference.py`, `run_all.sh`, `generate_jsonld.py`, filled `TaskSolution` files, and per-sample raw outputs.
- `infra/`: structural check (`_structural_check.py`) used as a SHACL workaround per the upstream validator note.

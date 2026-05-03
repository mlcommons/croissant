# SAGE-Eval: Workflow 1 (Paper -> CT -> Code)

## Overview
This directory contains the results of the `paper2ct2code` workflow for the SAGE-Eval benchmark reproduction.
The evaluation logic uses the strict `SAFE_EVAL_UNSAFE` prompt and exact regex parsing matching the original study.

## Setup
- **Generator Models:** `gpt-4o-mini-2024-07-18`, `gemini-2.0-flash`
- **Judge Model:** `gemini-3.1-flash-lite-preview`
- **Dataset:** SAGE-Eval (HuggingFace)
- **Scope:** Full evaluation (2000 instances)

## Directory Structure
- `pdf2ct/`: Contains the generated Croissant tasks (`problem.jsonld`), solution skeletons, and validation reports.
- `ct2code/`: Contains the generated Python scripts (`evaluate_baseline.py`), final `TaskSolution` files (`gemini-2.0-flash.jsonld`, `gpt-4o-mini.jsonld`), and the raw JSONL outputs.
- `infra/`: Empty or contains structural checks.

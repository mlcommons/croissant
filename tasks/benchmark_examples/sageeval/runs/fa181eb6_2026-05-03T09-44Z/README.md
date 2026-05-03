# SAGE-Eval: Workflow 2 (Paper -> Code directly)

## Overview
This directory contains the results of the `paper2code` (direct generation) workflow for the SAGE-Eval benchmark reproduction.
It uses a standalone Python script to query the dataset and evaluate the models, skipping the intermediate Croissant Tasks (`.jsonld`) generation.
The evaluation logic uses the strict `SAFE_EVAL_UNSAFE` prompt and exact regex parsing matching the original study.

## Setup
- **Generator Model:** `gemini-2.0-flash`
- **Judge Model:** `gemini-3.1-flash-lite-preview`
- **Dataset:** SAGE-Eval (HuggingFace)
- **Scope:** Full evaluation (11,297 instances)

## Directory Structure
- `paper2code/`: Contains the generated Python script (`evaluate_sage_eval.py`) and the `raw_outputs/` directory where the `.jsonl` files are saved.

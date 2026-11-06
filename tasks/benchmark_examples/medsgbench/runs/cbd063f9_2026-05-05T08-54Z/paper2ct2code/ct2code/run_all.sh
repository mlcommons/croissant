#!/bin/bash
# Loop the Qwen2.5-VL sizes and invoke the paper2ct2code/ct2code pipeline once per size.
# Reproduces the 4-cell paper2ct2code half of this snapshot's evaluation matrix.
set -euo pipefail
cd "$(dirname "$0")/../.."

for MODEL in 3b 7b 32b 72b; do
  echo "[run_all] paper2ct2code/ct2code: ${MODEL}"
  python -m paper2ct2code.ct2code.pipeline \
    --model "${MODEL}" --task 6 --n 1000 --batch-size 1 \
    --out "paper2ct2code/ct2code/raw_outputs/outputs_task6_qwen2.5-vl-${MODEL}.jsonl"
  python paper2ct2code/ct2code/generate_jsonld.py \
    --model "${MODEL}" \
    --raw "paper2ct2code/ct2code/raw_outputs/outputs_task6_qwen2.5-vl-${MODEL}.jsonl" \
    --skeleton "paper2ct2code/pdf2ct/results/solution_skeletons/qwen2_5-vl-${MODEL}.jsonld" \
    --out "paper2ct2code/ct2code/qwen2_5-vl-${MODEL}.jsonld"
done

echo "[run_all] paper2ct2code/ct2code: 4/4 cells complete."

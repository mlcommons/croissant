#!/bin/bash

# Clear previous logs
> run_all.log

echo "Starting evaluation for gpt-4o-mini-2024-07-18..." | tee -a run_all.log
python evaluate_baseline.py --model gpt-4o-mini-2024-07-18 --concurrency 10 --eval-only >> run_all.log 2>&1

echo "Starting evaluation for gemini-2.0-flash..." | tee -a run_all.log
python evaluate_baseline.py --model gemini-2.0-flash --concurrency 10 --eval-only >> run_all.log 2>&1

echo "All evaluations completed!" | tee -a run_all.log

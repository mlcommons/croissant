# MedSG-Bench Benchmark Example

This directory contains end-to-end demonstrations of the Croissant Tasks capabilities on the [MedSG-Bench](https://github.com/Yuejingkun/MedSG-Bench) benchmark.

## Layout

- `runs/` contains immutable snapshots of individual executions.
- In `runs/<commit_id>_<timestamp>/`, you will find both the `paper2code` (direct paper-PDF-only implementation) and `paper2ct2code` (Croissant-based implementation) workflows side by side.
- `bootstrap_metrics.py` and `analysis/` are post-hoc tools that compute 95% percentile-bootstrap confidence intervals over the saved per-sample outputs.
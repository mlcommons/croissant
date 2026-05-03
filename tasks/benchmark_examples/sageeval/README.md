# SAGE-Eval Benchmark Example

This directory contains end-to-end demonstrations of the Croissant Tasks capabilities on the [SAGE-Eval](https://github.com/YuehHanChen/SAGE-Eval) benchmark.

## Layout

- `runs/` contains immutable snapshots of individual executions.
- In `runs/<commit_id>_<timestamp>/`, you will find either the `paper2code` (direct python implementation) or `paper2ct2code` (Croissant-based implementation) workflows.

Each run directory contains its own `README.md` with further details on the execution parameters and models used.

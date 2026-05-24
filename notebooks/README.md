# Notebooks

This directory is split into active notebook infrastructure and deprecated notebook reference material.

## Active

- `common/`: shared notebook helpers that remain usable for future active notebooks.
- Future active employee-pay-cycle notebooks should live directly under `notebooks/` unless a later change defines a different active layout.

## Legacy

- `legacy/shift_level/`: deprecated shift-level SNF notebooks retained for historical reference only.
- These notebooks are not the active project direction and should not define current runtime, research, or production claims.

## Execution

- Notebook helper imports continue to assume `uv run jupytext --run-path notebooks ...`.
- Fast validation still uses `NOTEBOOK_FAST=1` and writes outputs under `/tmp`.

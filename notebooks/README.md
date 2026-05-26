# Notebooks

This directory is split into active notebook infrastructure and deprecated notebook reference material.

## Active

- `common/`: shared notebook helpers that remain usable for future active notebooks.
- `employee_cycle_report.py`: active residual payroll review notebook. It focuses on employee-pay-cycle records that remain after critical hard rules remove obvious payroll problems.

## Legacy

- `legacy/shift_level/`: deprecated shift-level SNF notebooks retained for historical reference only.
- These notebooks are not the active project direction and should not define current runtime, research, or production claims.

## Execution

- Notebook helper imports continue to assume `uv run jupytext --run-path notebooks ...`.
- Fast validation still uses `NOTEBOOK_FAST=1` and writes outputs under `/tmp`.

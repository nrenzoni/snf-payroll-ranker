# Notebooks

This directory is split into active notebook infrastructure and deprecated notebook reference material.

## Active

- `common/`: shared notebook helpers that remain usable for future active notebooks.
- `employee_cycle_report.py`: the single active public reporting notebook for the repository. It covers the residual employee-pay-cycle workflow end to end, including the main narrative and technical appendix.

The active notebook contract is single-notebook, not a notebook sequence. It focuses on employee-pay-cycle records that remain after critical hard rules remove obvious payroll problems.

## Legacy

- `legacy/shift_level/`: deprecated shift-level SNF notebooks retained for historical reference only.
- These notebooks are not the active project direction and should not define current runtime, research, or production claims.
- Older split-notebook reporting narratives are also historical reference only and are not the current acceptance contract.

## Execution

- Notebook helper imports continue to assume `uv run jupytext --run-path notebooks ...`.
- Notebook validation uses `NOTEBOOK_VALIDATE=1` and writes outputs under the repo-local `tmp/` directory.
- Full paired-output refresh for the active notebook uses `uv run jupytext --set-formats ipynb,py:percent --execute notebooks/employee_cycle_report.py`.

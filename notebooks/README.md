# Notebooks

This directory contains the notebook infrastructure for the project.

## Primary Notebook

- `common/`: shared notebook helpers that remain usable for future active notebooks.
- `snf_payroll_ranker_report.py`: the single active public reporting notebook for the repository. It covers the residual employee-pay-cycle workflow end to end, including the main narrative and technical appendix.

The active notebook contract is single-notebook, not a notebook sequence. It focuses on employee-pay-cycle records that remain after critical hard rules remove obvious payroll problems.

## Execution

- Notebook helper imports continue to assume `uv run jupytext --run-path notebooks ...`.
- Notebook validation uses `NOTEBOOK_VALIDATE=1` and writes outputs under the repo-local `tmp/` directory.
- Full paired-output refresh for the active notebook uses `uv run jupytext --set-formats ipynb,py:percent --execute notebooks/snf_payroll_ranker_report.py`.

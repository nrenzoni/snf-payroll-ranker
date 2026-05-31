# Development Guide

This document keeps the operational detail out of the root README while preserving the commands needed to run, validate, and extend the project.

## Setup

Install core dependencies:

```bash
uv sync
```

Install optional notebook dependencies:

```bash
uv sync --extra notebooks
```

## Run The Pipeline

```bash
uv run python -m payroll_anomaly_ranking.pipeline
```

Expected generated artifacts include:

- `data/synthetic/*.csv`
- `outputs/evaluation/*.csv`

## Notebook Workflow

The active public notebook is `notebooks/snf_payroll_ranker_report.py`.

Validation path with reduced workload and repo-local output under `tmp/`:

```bash
NOTEBOOK_VALIDATE=1 uv run jupytext --to ipynb --execute --run-path notebooks --output tmp/snf-payroll-ranker-report.validate.ipynb notebooks/snf_payroll_ranker_report.py
```

Full paired-output refresh:

```bash
uv run jupytext --set-formats ipynb,py:percent --execute notebooks/snf_payroll_ranker_report.py
```

Notebook-only plotting helpers live under `notebooks/common/`. The runtime package under `src/` stays free of Jupyter and Lets-Plot dependencies.

## Verification

Run repository hooks after code or notebook changes:

```bash
uv run prek run --all-files
```

Run the smoke suite for quick validation:

```bash
uv run pytest tests/smoke
```

Run targeted regression checks when changing behavior in affected areas:

```bash
uv run pytest tests/integration/test_regression.py -k "generation or scenario or feature or rule or scoring or evaluation or notebook"
```

## Engineering Workflow

- Non-trivial behavior changes are tracked under `openspec/`.
- Architecture rationale lives in [`ARCHITECTURE.md`](../ARCHITECTURE.md).
- Technical decisions live in [`DECISIONS.md`](../DECISIONS.md).
- Contributor and agent workflow guidance lives in [`AGENTS.md`](../AGENTS.md).

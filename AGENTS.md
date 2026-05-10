# AGENTS.md

## Project

Python 3.13 payroll anomaly ranking pipeline using Polars, NumPy, scikit-learn, UV, Ruff, and Pyrefly. Optional notebook reporting uses Lets-Plot and Jupytext. The project follows spec-driven development.

## Workflow

- Jupytext `.py` files are the notebook source of truth; do not edit `.ipynb` artifacts directly.
- Run any Python-related project command with `uv run ...`.
- Use `uv sync --extra notebooks` before executing notebooks or rendering Lets-Plot visuals.
- After any notebook `.py` source change, validate each changed notebook with the fast path: `NOTEBOOK_FAST=1 uv run jupytext --to ipynb --execute --run-path notebooks --output /tmp/notebook-name.fast.ipynb notebook.py`. This uses reduced diagnostic workloads and minimal pipeline artifacts where notebooks support fast mode, preserves notebook-local imports, and writes the executed notebook only under `/tmp` without creating or overwriting paired `.ipynb` artifacts.
- Use full non-fast notebook execution only when the user requests a complete rerender, paired `.ipynb` refresh, analyst-visible output sync, or full-workload validation: `uv run jupytext --set-formats ipynb,py:percent --execute notebook.py`. This creates/updates the paired `.ipynb`, executes the full workload, reports failures, and lets you inspect outputs on success.

## Specs

- Specs live in `openspec/specs/` and follow the propose/apply/archive cycle.
- Before non-trivial code changes, check relevant specs for contradictions.
- If a change alters intended behavior or needs new behavior, recommend creating or updating a spec first.
- Small out-of-scope changes such as parameter renames, formatting, or code style fixes do not need to go through the spec cycle.

## Code

- Prefer strict typing and named dataclass result objects for public multi-value returns.
- Keep tabular data in Polars DataFrames; never use pandas.
- Use schema constants/enums from `columns.py` instead of raw project column strings.
- Prefer Polars expressions and vectorized NumPy over row-wise Python callbacks in hot paths.
- Keep `src/payroll_anomaly_ranking/` free of notebook-only plotting dependencies; visualization code belongs in Jupytext notebooks, with shared plotting adapters in `notebooks/common/plots.py`.
- Use Lets-Plot for notebook visualizations; never use matplotlib.
- Add comments wherever they help a new developer understand the code quickly: non-obvious business logic, leakage prevention, performance tradeoffs, long functions, classes, and anywhere there is even a slight chance of misunderstanding.

## Verify

- After code or notebook changes, run `uv run prek run --all-files`.
- After code changes, run the quick smoke suite with `uv run pytest tests/smoke` unless the change is docs-only.
- Also run targeted tests for the code area you changed when available:
  - Data generation or scenarios: `uv run pytest tests/integration/test_regression.py -k "generation or scenario or drift or anomaly"`
  - Features or rules: `uv run pytest tests/integration/test_regression.py -k "feature or rule"`
  - Scoring, uncertainty, or models: `uv run pytest tests/integration/test_regression.py -k "scoring or uncertainty"`
  - Evaluation, diagnostics, or queue simulation: `uv run pytest tests/integration/test_regression.py -k "evaluation or diagnostic or queue"`
  - Notebook contracts or dependency boundaries: `uv run pytest tests/integration/test_regression.py -k "notebook or plotting"`
- Run full `uv run pytest` for large behavior changes, pipeline-wide changes, scenario/diagnostic changes, dependency/config changes, or when the user requests full validation.

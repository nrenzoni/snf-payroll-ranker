# AGENTS.md

## Project

Python 3.13 payroll anomaly ranking pipeline using Polars, NumPy, scikit-learn, UV, Ruff, and Pyrefly. Optional notebook reporting uses Lets-Plot and Jupytext. The project follows spec-driven development.

## Workflow

- Jupytext `.py` files are the notebook source of truth; do not edit `.ipynb` artifacts directly.
- Run any Python-related project command with `uv run ...`.
- Use `uv sync --extra notebooks` before executing notebooks or rendering Lets-Plot visuals.
- To inspect cell output for a `.py` notebook, run `uv run jupytext --set-formats ipynb,py:percent --execute notebook.py`. This creates/updates the paired `.ipynb`, executes it, reports failures, and lets you inspect outputs on success.

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
- Run `uv run pytest` when behavior, pipeline logic, diagnostics, or test-covered code changes.

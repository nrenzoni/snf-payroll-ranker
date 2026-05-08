## Context

The project currently serves two audiences from one package boundary: downstream ML pipelines import `payroll_anomaly_ranking` for data generation, scoring, evaluation, diagnostics, and review-queue outputs; notebook users execute Jupytext sources that render Lets-Plot charts for narrative reporting. The current dependency list and `src/payroll_anomaly_ranking/charts.py` make notebook/reporting dependencies part of the core runtime even when downstream pipelines do not need plotting.

The Jupytext `.py` files remain the source of truth for notebooks. Core pipeline code should remain Polars-first and safe for non-notebook environments. Notebook visual coverage and `LetsPlot.setup_html()` behavior must remain intact for rendered notebooks.

## Goals / Non-Goals

**Goals:**

- Keep `src/payroll_anomaly_ranking` free of direct Jupyter and Lets-Plot imports.
- Make core runtime installation sufficient for pipeline execution without notebook/reporting packages.
- Make notebook/reporting dependencies explicit through an optional dependency extra or equivalent UV-supported install path.
- Move chart construction into notebook sources or notebook-only support modules.
- Preserve existing notebook visual coverage, narrative readability, and reproducible execution.
- Update docs and tests so future contributors understand the runtime/reporting boundary.

**Non-Goals:**

- Redesign scoring, feature engineering, diagnostics, or queue-simulation behavior.
- Change generated synthetic data schemas or analyst-safe review queue contents.
- Introduce a separate installable plotting package unless a later change identifies non-notebook chart consumers.
- Edit `.ipynb` artifacts directly outside the established Jupytext workflow.

## Decisions

- Move presentation code out of the core package rather than keeping optional imports in `src`.

  Optional imports would avoid hard dependency failures, but they would still advertise plotting as part of the downstream pipeline API. Removing chart helpers from `src` makes the package boundary clearer and prevents accidental reuse of notebook-only code in production paths.

- Inline simple one-off plots in notebooks and use `notebooks/support/` only for duplicated notebook presentation helpers.

  Inline visual encodings keep chart code adjacent to the narrative that explains it. A notebook support folder is useful only where duplication would otherwise make maintenance worse, such as shared Lets-Plot setup or repeated chart idioms.

- Keep reusable analytical data preparation in `src` when it has downstream value.

  Some current chart helpers mix visual encoding with reshaping. Plot-only reshaping can live in notebooks, but reusable diagnostic outputs and queue summaries should remain in pipeline modules as Polars DataFrames when useful to downstream pipelines.

- Use optional project dependencies for notebooks/reporting.

  Base `[project.dependencies]` should contain core runtime packages. Notebook/reporting dependencies should move to an optional extra such as `notebooks`, so `uv sync --extra notebooks` prepares the reporting environment while pipeline installs remain lean.

- Update specs/docs/tests as part of the migration.

  The behavioral contract changes from “the project environment includes notebook plotting dependencies” to “the notebook/reporting environment includes them.” Specs and README commands must match that contract or contributors will reintroduce plotting into core code.

## Risks / Trade-offs

- Notebook code may become longer → Mitigate by keeping simple plots inline and extracting only repeated presentation helpers to `notebooks/support/`.
- Tests may import notebook modules without notebook extras → Mitigate by keeping core tests independent from notebook-only imports or documenting that full notebook verification requires the notebook extra.
- Optional dependency commands may be missed by notebook users → Mitigate with README setup sections and notebook reproducibility spec updates.
- Removing `payroll_anomaly_ranking.charts` can break internal imports → Mitigate by updating all notebook imports in the same change and not preserving backward-compatible shims because the module is notebook-only and not a stated downstream API.
- Generated `.ipynb` outputs can drift from Jupytext sources → Mitigate by using the documented Jupytext execution workflow when refreshing notebook outputs.

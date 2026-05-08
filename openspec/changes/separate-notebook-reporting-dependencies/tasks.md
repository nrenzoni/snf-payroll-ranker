## 1. Dependency Boundary

- [x] 1.1 Move notebook/reporting packages (`jupyter`, `jupytext`, `lets-plot`, `nbconvert`) out of base project dependencies and into a documented optional notebook/reporting dependency extra.
- [x] 1.2 Verify the core package can import and run the payroll anomaly ranking pipeline without importing Lets-Plot or Jupyter-only modules.

## 2. Notebook Plot Migration

- [x] 2.1 Inventory all imports and calls to `payroll_anomaly_ranking.charts` from Jupytext notebook sources.
- [x] 2.2 Inline simple one-off Lets-Plot chart construction in the relevant notebook cells so visual encodings sit next to their narrative explanations.
- [x] 2.3 Move any duplicated notebook-only plotting or display helper code to a notebook-owned support module under `notebooks/` if duplication remains after inlining.
- [x] 2.4 Preserve reusable non-visual Polars data-preparation logic in core modules only when useful to downstream pipeline consumers.
- [x] 2.5 Remove `src/payroll_anomaly_ranking/charts.py` after all core and notebook imports no longer depend on it.

## 3. Documentation And Specs

- [x] 3.1 Update `README.md` to distinguish core pipeline setup from notebook/reporting setup and document the notebook execution command under the reporting environment.
- [x] 3.2 Update `AGENTS.md` to describe Lets-Plot and Jupytext as notebook/reporting tools rather than core pipeline runtime dependencies.
- [x] 3.3 Update or add tests that enforce the core package does not expose notebook-only plotting imports while preserving notebook `LetsPlot.setup_html()` checks.

## 4. Verification

- [x] 4.1 Run `uv run pytest` to verify runtime behavior and repository checks affected by the migration.
- [x] 4.2 Run `uv run prek run --all-files` and resolve all reported issues.
- [x] 4.3 If notebook outputs are refreshed, execute the affected Jupytext notebook sources using the documented notebook/reporting environment and inspect failures before committing paired outputs.

## 1. Dependency Boundary

- [ ] 1.1 Move notebook/reporting packages (`jupyter`, `jupytext`, `lets-plot`, `nbconvert`) out of base project dependencies and into a documented optional notebook/reporting dependency extra.
- [ ] 1.2 Verify the core package can import and run the payroll anomaly ranking pipeline without importing Lets-Plot or Jupyter-only modules.

## 2. Notebook Plot Migration

- [ ] 2.1 Inventory all imports and calls to `payroll_anomaly_ranking.charts` from Jupytext notebook sources.
- [ ] 2.2 Inline simple one-off Lets-Plot chart construction in the relevant notebook cells so visual encodings sit next to their narrative explanations.
- [ ] 2.3 Move any duplicated notebook-only plotting or display helper code to a notebook-owned support module under `notebooks/` if duplication remains after inlining.
- [ ] 2.4 Preserve reusable non-visual Polars data-preparation logic in core modules only when useful to downstream pipeline consumers.
- [ ] 2.5 Remove `src/payroll_anomaly_ranking/charts.py` after all core and notebook imports no longer depend on it.

## 3. Documentation And Specs

- [ ] 3.1 Update `README.md` to distinguish core pipeline setup from notebook/reporting setup and document the notebook execution command under the reporting environment.
- [ ] 3.2 Update `AGENTS.md` to describe Lets-Plot and Jupytext as notebook/reporting tools rather than core pipeline runtime dependencies.
- [ ] 3.3 Update or add tests that enforce the core package does not expose notebook-only plotting imports while preserving notebook `LetsPlot.setup_html()` checks.

## 4. Verification

- [ ] 4.1 Run `uv run pytest` to verify runtime behavior and repository checks affected by the migration.
- [ ] 4.2 Run `uv run prek run --all-files` and resolve all reported issues.
- [ ] 4.3 If notebook outputs are refreshed, execute the affected Jupytext notebook sources using the documented notebook/reporting environment and inspect failures before committing paired outputs.

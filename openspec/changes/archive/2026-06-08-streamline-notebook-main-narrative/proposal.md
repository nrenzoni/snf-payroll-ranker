## Why

The active SNF payroll ranker notebook has become too audit-table-heavy in the main narrative, especially around simulation sanity checks and benchmark details. The report should guide readers through the decision path first, while still preserving detailed synthetic-data and benchmark evidence in the appendix for review and reproducibility.

## What Changes

- Reframe the notebook main narrative around a focused decision flow: residual gate, label/feature meaning, model formulations, scenario-based benchmark results, and recommendation.
- Allow simulation sanity evidence to be summarized in the main narrative with concise prose and plot-first visuals rather than a required standalone table-heavy section.
- Move detailed cross-scenario sanity tables, scenario catalogs, benchmark metric tables, and other audit artifacts to the technical appendix when they do not directly advance the reader-facing decision story.
- Keep scenario-based benchmark conclusions in the main narrative, but prefer winner maps, winner-frequency visuals, metric interval plots, and recommendation cards over broad raw dataframe displays.
- Preserve required synthetic-data transparency and reproducibility evidence in appendix or supporting sections.
- No breaking API, data schema, or model-behavior changes are intended.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `employee-cycle-notebook-reporting`: update the active notebook reporting contract so the main narrative can be plot-first and decision-focused, with detailed sanity and audit tables moved to the appendix.
- `scenario-based-notebook-benchmark`: update benchmark presentation requirements so scenario-seed evidence can be summarized visually in the main narrative while detailed tables remain available as appendix support.

## Impact

- Affects `notebooks/snf_payroll_ranker_report.py` narrative structure and rendered outputs.
- Affects OpenSpec requirements for active notebook reporting and scenario-based benchmark presentation.
- Does not change Python package APIs, model scoring logic, generated data schemas, dependencies, or persisted artifacts.
- Verification should include `uv run prek run --all-files`, reduced notebook validation with `NOTEBOOK_VALIDATE=1 uv run jupytext --to ipynb --execute --run-path notebooks --output tmp/snf_payroll_ranker_report.validate.ipynb notebooks/snf_payroll_ranker_report.py`, smoke tests, and notebook/plotting regression tests.

## Why

The richer internal diagnostic notebooks still render sparse or low-contrast plots because the scenario presets, threshold-demand settings, and chart input preparation do not reliably produce enough visible contrast in score distributions, queue demand, subgroup concentration, or uncertainty summaries. This follow-up makes the internal notebooks useful as rendered data-science artifacts rather than only schema-level smoke tests.

## What Changes

- Calibrate internal diagnostic scenario presets so each named regime produces measurable contrast in the signal it is meant to stress: rules, statistical outliers, ML rare combinations, exposure dollars, subgroup concentration, calendar drift, and queue demand.
- Add scenario sanity-summary tables that show row counts, anomaly counts, score quantiles, candidates above operational thresholds, anomaly dollars, and subgroup-period concentration before plots are rendered.
- Replace brittle fixed queue score-threshold defaults with adaptive threshold or threshold-grid simulation views that produce interpretable demand across scenarios.
- Update internal notebooks `06` and `07` to use bounded but denser defaults, explicit fast-mode constants, and plot-ready tables that avoid point-only sparse visualizations.
- Improve chart helpers or notebook-side table preparation where needed so plots use faceting, top-N filtering, threshold grids, or scenario grouping instead of collapsing useful variation.
- Add tests that assert plot-useful contrast and non-empty diagnostic views, not only output schemas.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `synthetic-payroll-data`: Internal diagnostic scenario presets will be calibrated to produce measurable score, dollar, queue, and subgroup contrast while preserving default generation behavior and leakage boundaries.
- `payroll-anomaly-evaluation`: Internal diagnostics will produce plot-ready, non-sparse comparison, subgroup, calibration, robustness, and queue-demand tables with adaptive thresholds or threshold grids where appropriate.
- `notebook-reproducibility`: Internal diagnostic notebooks will use denser bounded defaults and documented fast-mode constants while remaining reproducible and separate from the business-facing notebook sequence.

## Impact

- Affected modules likely include `src/payroll_anomaly_ranking/scenarios.py`, `src/payroll_anomaly_ranking/data.py`, `src/payroll_anomaly_ranking/diagnostics.py`, `src/payroll_anomaly_ranking/queue_simulation.py`, `src/payroll_anomaly_ranking/charts.py`, and notebook setup cells.
- Internal notebooks `notebooks/06_internal_statistical_diagnostics.py` and `notebooks/07_simulation_and_stress_testing.py` will be revised and paired `.ipynb` outputs should be refreshed if they are committed.
- README or notebook text will document dense defaults and fast-mode reductions.
- Tests will verify that internal diagnostic inputs have enough rows, non-zero demand, score-threshold variation, and scenario contrast for meaningful plots.
- No new heavy visualization, Bayesian, or modeling dependencies are expected.

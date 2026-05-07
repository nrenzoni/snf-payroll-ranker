## Why

The project currently demonstrates a strong payroll anomaly review workflow, but its deeper data science evidence is mostly point-estimate evaluation and narrative diagnostics. Adding internal statistical diagnostics and controlled simulation will make the workflow more robust, auditable, and technically mature before any future move toward supervised ranking.

## What Changes

- Add internal statistical diagnostics for review-budget metrics, subgroup behavior, expected-pay interval calibration, score stability, exposure calibration, and perturbation sensitivity.
- Add controlled Monte Carlo and stress-test analysis for analyst queue capacity, anomaly-mix shifts, drift regimes, and change-point scenarios.
- Refactor the payroll simulator into explicit baseline generation plus dataclass-based scenario controls for anomaly, drift, and change-point experiments.
- Add internal Jupytext notebooks for statistical diagnostics and simulation/stress testing while keeping the existing business-facing notebook sequence intact.
- Add reusable library functions and chart helpers so advanced analysis is testable outside notebooks.
- Do not introduce supervised ranking models or train on synthetic evaluation labels as part of this change.
- Do not add a chainable scenario builder API initially; scenario controls will be dataclass-only for now.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `payroll-anomaly-evaluation`: Add internal statistical diagnostics, Bayesian-style uncertainty summaries, hierarchical subgroup diagnostics, calibration checks, robustness visualizations, queue simulation outputs, and internal notebook coverage.
- `synthetic-payroll-data`: Add scenario-controlled payroll generation for drift, change points, anomaly-mix shifts, and reproducible Monte Carlo experiments using dataclass scenario specifications.

## Impact

- Affected modules include `src/payroll_anomaly_ranking/data.py`, `src/payroll_anomaly_ranking/config.py`, `src/payroll_anomaly_ranking/evaluation.py`, `src/payroll_anomaly_ranking/charts.py`, and `src/payroll_anomaly_ranking/pipeline.py`.
- New modules are expected for scenario specifications, queue simulation, and internal statistical diagnostics.
- New notebooks are expected under `notebooks/`, likely `06_internal_statistical_diagnostics.py` and `07_simulation_and_stress_testing.py`.
- Tests will be expanded beyond smoke coverage to verify scenario reproducibility, drift/change-point effects, queue simulation outputs, and statistical summary table shapes.
- Existing analyst-safe queue behavior and label-leakage guardrails remain unchanged.

## Why

The internal statistical diagnostic notebooks currently render sparse or low-contrast plots because they run on one small, mostly homogeneous synthetic world. Improving the generator scenarios, diagnostics, and visual encodings will make the internal notebooks useful for data-science review rather than only smoke-level execution.

## What Changes

- Add a reusable internal scenario catalog with distinct regimes for rule-friendly anomalies, statistical outliers, ML-friendly rare combinations, exposure-heavy cases, subgroup drift, and queue-capacity stress.
- Extend scenario-controlled generation so anomaly propensity, category mix, and severity can vary by subgroup and period instead of only globally.
- Upgrade component superiority diagnostics to compare ranking signals across scenarios, seeds, and/or temporal origins with paired deltas and pairwise superiority summaries.
- Improve subgroup, calibration, queue, and robustness visualizations so they encode effect sizes, intervals, scenario context, and sample size rather than flat point-only views.
- Update internal notebooks `06` and `07` to use richer bounded defaults, explain the diagnostic question each plot answers, and retain a documented fast mode.
- Add tests that the richer scenario regimes create meaningfully different diagnostic outputs without changing analyst-safe queue fields or model feature leakage rules.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `synthetic-payroll-data`: Scenario-controlled synthetic generation will support reusable diagnostic scenario presets plus subgroup-period-targeted anomaly propensity, category mix, and severity controls.
- `payroll-anomaly-evaluation`: Internal diagnostics will compare ranking signals across richer scenario/seed/origin variation and produce more informative uncertainty, subgroup, robustness, and queue-simulation outputs.
- `notebook-reproducibility`: Internal diagnostic notebooks will remain reproducible with bounded defaults while using richer scenarios and documented fast-mode parameters.

## Impact

- Affected modules include `src/payroll_anomaly_ranking/scenarios.py`, `src/payroll_anomaly_ranking/data.py`, `src/payroll_anomaly_ranking/diagnostics.py`, `src/payroll_anomaly_ranking/queue_simulation.py`, `src/payroll_anomaly_ranking/charts.py`, and `src/payroll_anomaly_ranking/pipeline.py`.
- Internal notebooks `notebooks/06_internal_statistical_diagnostics.py` and `notebooks/07_simulation_and_stress_testing.py` will be revised.
- Tests will verify scenario contrast, diagnostic output shapes, plot-input richness, and continued analyst-safe label separation.
- No new heavy Bayesian or visualization dependencies are expected.

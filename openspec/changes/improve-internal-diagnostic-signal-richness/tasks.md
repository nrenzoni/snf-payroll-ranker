## 1. Scenario Catalog And Targeted Generation

- [ ] 1.1 Add reusable diagnostic scenario presets for baseline, rule-friendly, statistical-friendly, ML-friendly, exposure-heavy, subgroup-drift, calendar-drift, and queue-stress regimes.
- [ ] 1.2 Extend `AnomalyPlan` or related dataclasses to represent subgroup filters, period ranges, category weights, target counts or propensity multipliers, and severity distribution controls.
- [ ] 1.3 Update anomaly injection so targeted anomaly controls affect only configured subgroup-period scopes while preserving default generation behavior when no scenario is provided.
- [ ] 1.4 Ensure scenario metadata records applied presets and targeted controls without adding scenario fields to analyst-safe queue outputs or model feature columns.
- [ ] 1.5 Add scenario summary utilities that report row counts, anomaly counts, category mix, anomaly dollars, and subgroup-period concentration by scenario.

## 2. Multi-Regime Diagnostics

- [ ] 2.1 Add utilities to run configured scenario/seed/origin comparison units through the existing scoring and evaluation path with bounded defaults.
- [ ] 2.2 Upgrade component superiority diagnostics to report pairwise signal comparisons across scenario/seed/origin units.
- [ ] 2.3 Include paired metric deltas, win probabilities or frequencies, sample counts, and interval or quantile bounds in component comparison outputs.
- [ ] 2.4 Preserve regime identifiers in diagnostic outputs so notebooks can inspect which signal wins under which synthetic condition.
- [ ] 2.5 Improve subgroup diagnostics for subgroup-drift scenarios so raw estimates, pooled estimates, interval bounds, sample size, and anomaly counts are plot-ready.
- [ ] 2.6 Improve expected-pay calibration and robustness outputs so they include subgroup, residual, interval-width, queue-overlap, variability, and instability fields needed for richer plots.

## 3. Queue Simulation Enhancements

- [ ] 3.1 Extend `QueueSimulationSpec` or queue simulation functions to support threshold-based candidate demand in addition to fixed top-K queue size.
- [ ] 3.2 Add period-specific capacity shock support suitable for queue-stress scenarios.
- [ ] 3.3 Update queue simulation summaries to include scenario identifier, candidate queue size, reviewed records, overload probability, missed estimated exposure, and missed synthetic anomaly dollars.
- [ ] 3.4 Keep threshold-demand queue simulation outputs separate from existing fixed review-budget evaluation metrics.

## 4. Chart Helpers

- [ ] 4.1 Replace or supplement `posterior_comparison_chart` with a pairwise superiority heatmap using left signal, right signal, scenario or aggregate scope, win probability, mean delta, and interval fields.
- [ ] 4.2 Add effect-size interval chart helpers for component metric deltas and review-budget uncertainty summaries.
- [ ] 4.3 Improve subgroup forest, caterpillar, shrinkage, and funnel helpers to sort groups, encode sample size, and show raw versus pooled estimates with interval context.
- [ ] 4.4 Improve calibration chart helpers to show coverage, residuals, interval width, and excess over p90 by subgroup or scenario.
- [ ] 4.5 Improve queue simulation chart helpers to show scenario-dependent demand, overload, dollar capture, missed exposure, and stress-test heatmaps.
- [ ] 4.6 Keep chart helpers table-driven so notebooks avoid complex metric preparation logic.

## 5. Internal Notebooks And Documentation

- [ ] 5.1 Update `notebooks/06_internal_statistical_diagnostics.py` to use richer bounded scenario/seed/origin comparison units.
- [ ] 5.2 Update notebook `06` narrative so each plot states the diagnostic question it answers and why scenario regimes are internal stress tests.
- [ ] 5.3 Update `notebooks/07_simulation_and_stress_testing.py` to use scenario-dependent queue stress and threshold-demand simulation views.
- [ ] 5.4 Update notebook `07` narrative to distinguish fixed review-budget metrics from operational queue demand simulation.
- [ ] 5.5 Document bounded default scenario/seed/sample counts and fast-mode constants in README or notebook setup cells.
- [ ] 5.6 Keep notebooks `01` through `05` business-facing and independent from the richer internal diagnostic scenario suite.

## 6. Tests And Validation

- [ ] 6.1 Add tests that default payroll generation remains reproducible and schema-compatible after targeted scenario extensions.
- [ ] 6.2 Add tests that each scenario preset is reproducible with the same seed and produces expected metadata.
- [ ] 6.3 Add tests that targeted anomaly controls increase anomaly concentration only in configured subgroup-period scopes.
- [ ] 6.4 Add tests that scenario regimes produce meaningfully different component comparison or scenario summary outputs.
- [ ] 6.5 Add tests for queue simulation threshold-demand output shape and scenario-dependent overload behavior.
- [ ] 6.6 Add tests that chart-helper input tables include required effect-size, interval, sample-size, and scenario-context columns.
- [ ] 6.7 Add or update reproducibility checks for internal notebooks with bounded defaults or fast-mode settings.
- [ ] 6.8 Run Ruff formatting, Ruff linting, and the existing test suite; fix regressions.

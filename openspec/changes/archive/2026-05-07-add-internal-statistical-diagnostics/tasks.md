## 1. Scenario Simulation Foundation

- [x] 1.1 Add `src/payroll_anomaly_ranking/scenarios.py` with dataclasses for `ScenarioSpec`, `AnomalyPlan`, `DriftPlan`, `ChangePointEvent`, and `QueueSimulationSpec`.
- [x] 1.2 Refactor `src/payroll_anomaly_ranking/data.py` so baseline payroll generation is separate from anomaly injection and scenario application.
- [x] 1.3 Preserve default `generate_payroll(config)` behavior for existing callers when no scenario is provided.
- [x] 1.4 Add scenario-controlled anomaly category weights, target counts, and severity multipliers for supported synthetic anomaly categories.
- [x] 1.5 Add drift controls for pay-code mix, overtime behavior, deductions, gross-pay shifts, and subgroup-scoped period ranges, with payroll-total shifts implemented as subgroup-period row-level multipliers.
- [x] 1.6 Add change-point event application for configured periods and subgroup filters.
- [x] 1.7 Return scenario metadata in pipeline results and optional internal evaluation artifacts without adding scenario fields to analyst-safe queue outputs or model feature columns.

## 2. Pipeline And Queue Simulation

- [x] 2.1 Update `run_pipeline(...)` to accept an optional scenario specification while preserving existing default behavior.
- [x] 2.2 Add `src/payroll_anomaly_ranking/queue_simulation.py` with Monte Carlo queue-capacity simulation over scored records.
- [x] 2.3 Implement capacity assumptions for fixed capacity, period-varying capacity, and random capacity variation.
- [x] 2.4 Summarize queue size, reviewed records, overload probability, captured anomalies, dollars captured, missed anomalies, missed estimated exposure, and missed synthetic anomaly dollars.
- [x] 2.5 Add scenario comparison utilities that run baseline and stress scenarios through the scoring/evaluation path.

## 3. Statistical Diagnostic Tables

- [x] 3.1 Add an internal diagnostics module for Bayesian-style review-budget interval summaries for Precision@25, Recall@25, and dollar capture using closed-form, Bayesian bootstrap, Beta-Binomial, or posterior-simulation methods without requiring full MCMC.
- [x] 3.2 Add component superiority summaries comparing hybrid, rule, statistical, ML, and exposure ranking signals across seeds, origins, or bootstrap samples.
- [x] 3.3 Add subgroup diagnostic tables by department, job family, location, pay type, pay code, and job level.
- [x] 3.4 Add empirical-Bayes or partial-pooling subgroup summaries that distinguish raw estimates from pooled estimates.
- [x] 3.5 Add expected-pay calibration tables for coverage, interval width, excess over p90, residuals, and subgroup coverage.
- [x] 3.6 Add robustness tables for seed stability, temporal-origin stability, queue overlap, parameter sensitivity, and performance-instability tradeoffs.
- [x] 3.7 Add local perturbation sensitivity utilities for score movement, rank movement, and threshold-crossing behavior.
- [x] 3.8 Add exposure calibration and category severity summaries comparing estimated exposure to synthetic evaluation impact.

## 4. Chart Helpers

- [x] 4.1 Add reusable LetsPlot helpers for credible interval and posterior comparison plots.
- [x] 4.2 Add reusable subgroup forest, caterpillar, shrinkage, and funnel plot helpers.
- [x] 4.3 Add expected-pay calibration chart helpers for actual-vs-expected, coverage, residual, and percentile calibration views.
- [x] 4.4 Add robustness chart helpers for queue-overlap heatmaps, seed/origin distributions, performance-instability Pareto plots, and sensitivity heatmaps.
- [x] 4.5 Add queue simulation chart helpers for capacity distributions, overload probability, dollar-capture distributions, tornado plots, and stress-test heatmaps.
- [x] 4.6 Keep chart helpers table-driven so notebooks do not contain complex metric logic.

## 5. Internal Notebooks

- [x] 5.1 Add `notebooks/06_internal_statistical_diagnostics.py` as a Jupytext percent-format notebook.
- [x] 5.2 In notebook `06`, render Bayesian-style review-budget intervals and component superiority diagnostics.
- [x] 5.3 In notebook `06`, render hierarchical subgroup diagnostics, expected-pay calibration checks, exposure calibration, robustness plots, and perturbation sensitivity views.
- [x] 5.4 Add `notebooks/07_simulation_and_stress_testing.py` as a Jupytext percent-format notebook.
- [x] 5.5 In notebook `07`, render Monte Carlo queue-capacity outcomes, drift scenario comparisons, anomaly-mix stress tests, change-point diagnostics, and stress-test heatmaps.
- [x] 5.6 Keep notebooks `01` through `05` business-facing and avoid requiring them to display all internal diagnostic plots.

## 6. Documentation And Reproducibility

- [x] 6.1 Update README notebook documentation to list internal notebooks separately from the business-facing sequence.
- [x] 6.2 Document that advanced diagnostics use synthetic evaluation labels internally and do not alter analyst-safe queue outputs.
- [x] 6.3 Document default simulation sample counts and how to reduce them for faster local notebook execution.
- [x] 6.4 Ensure internal notebooks call `LetsPlot.setup_html()` before rendering LetsPlot charts.
- [x] 6.5 Add or update reproducibility checks so internal notebooks can execute from a clean checkout with bounded default simulation counts.

## 7. Tests And Validation

- [x] 7.1 Add tests that default payroll generation remains reproducible and schema-compatible after simulator refactoring.
- [x] 7.2 Add tests that scenario specifications are reproducible with the same seed.
- [x] 7.3 Add tests that drift and change-point events affect only configured periods and subgroups.
- [x] 7.4 Add tests that anomaly-mix controls affect injected category composition and preserve evaluation-only label separation.
- [x] 7.5 Add tests for queue simulation output shape and sanity checks for overload and dollar-capture metrics.
- [x] 7.6 Add tests for statistical diagnostic output schemas and non-empty summaries on a small synthetic run.
- [x] 7.7 Run the existing test suite and fix regressions.

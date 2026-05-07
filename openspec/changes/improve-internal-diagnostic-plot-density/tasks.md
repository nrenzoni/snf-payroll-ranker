## 1. Scenario Calibration And Summaries

- [ ] 1.1 Add or tune diagnostic scenario preset parameters so rule-friendly, statistical-friendly, ML-friendly, exposure-heavy, subgroup-drift, calendar-drift, and queue-stress regimes each produce measurable contrast under bounded notebook defaults.
- [ ] 1.2 Add score-aware scenario sanity summary utilities with row counts, anomaly counts, anomaly dollars, score quantiles, configured threshold candidate counts, category mix, and subgroup-period concentration.
- [ ] 1.3 Add checks or helper outputs that make sparse conditions visible, such as zero threshold candidates or insufficient subgroup concentration.
- [ ] 1.4 Preserve default payroll generation behavior and keep scenario metadata, labels, categories, and anomaly dollar impacts out of model feature columns and analyst-safe review queues.

## 2. Adaptive Queue-Demand Diagnostics

- [ ] 2.1 Extend queue simulation specs or utilities to support threshold grids for candidate-demand simulation.
- [ ] 2.2 Add adaptive threshold support based on score quantiles or percentiles and report the resolved threshold in simulation outputs.
- [ ] 2.3 Update queue simulation summaries to retain scenario, threshold, demand mode, candidate queue size, reviewed records, overload probability, missed estimated exposure, and missed synthetic anomaly dollars.
- [ ] 2.4 Keep adaptive and threshold-grid queue-demand outputs separate from existing fixed top-K review-budget evaluation metrics.

## 3. Diagnostic Tables And Chart Helpers

- [ ] 3.1 Update component comparison utilities or prepared tables so bounded defaults include enough scenario/seed comparison units for non-trivial aggregate and scenario-specific plots.
- [ ] 3.2 Add or improve top-N subgroup diagnostic table preparation with sorted subgroup rows, raw and pooled estimates, interval bounds, record counts, anomaly counts, and scenario context.
- [ ] 3.3 Improve calibration and robustness plot inputs so they include scenario or subgroup grouping, residuals, interval width, queue overlap, performance variability, instability metrics, and enough rows for grouped plots.
- [ ] 3.4 Improve chart helpers where needed to render threshold grids, scenario grouping, sample size, interval context, and top-N filtered tables without complex notebook-side metric preparation.

## 4. Internal Notebooks And Documentation

- [ ] 4.1 Update `notebooks/06_internal_statistical_diagnostics.py` to use calibrated scenario presets, denser bounded defaults, scenario sanity summaries, and richer component, subgroup, calibration, robustness, and perturbation plots.
- [ ] 4.2 Update `notebooks/07_simulation_and_stress_testing.py` to use scenario sanity summaries plus adaptive or threshold-grid queue-demand simulation views.
- [ ] 4.3 Document dense defaults and fast-mode reductions in README or notebook setup cells, including scenario counts, seed counts, sample counts, employee counts, pay-period counts, and queue iteration counts.
- [ ] 4.4 Keep notebooks `01` through `05` independent from the internal diagnostic plot-density scenario suite.
- [ ] 4.5 Refresh paired `.ipynb` outputs for notebooks `06` and `07` if paired outputs are committed and expected in the repository.

## 5. Tests And Validation

- [ ] 5.1 Add tests that calibrated scenario presets produce broad observable contrast such as score quantile movement, anomaly dollar separation, category mix changes, or subgroup-period concentration.
- [ ] 5.2 Add tests that scenario sanity summary outputs include required score, threshold, demand, category, dollar, and concentration fields.
- [ ] 5.3 Add tests for threshold-grid and adaptive-threshold queue simulation output shape, resolved threshold reporting, and non-empty demand under queue-stress settings.
- [ ] 5.4 Add tests that plot-ready component, subgroup, calibration, robustness, and queue tables meet minimum density and required context-column checks without image snapshot testing.
- [ ] 5.5 Add or update reproducibility checks for notebooks `06` and `07` dense defaults and fast-mode constants.
- [ ] 5.6 Run Ruff formatting, Ruff linting, and the existing test suite; fix regressions.

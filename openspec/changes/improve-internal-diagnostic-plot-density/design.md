## Context

The previous internal diagnostics change introduced scenario presets, targeted generation controls, richer diagnostics, queue simulation fields, and chart helper inputs. The rendered notebook outputs are still too sparse in practice because the defaults and visual preparation do not guarantee enough contrast for plots: some scenarios generate anomalies that score below fixed queue thresholds, component comparisons have too few scenario/seed units, subgroup views collapse to a small set of points, and several charts remain point-only despite richer tables.

This change treats rendered plot density as a first-class internal diagnostic requirement. The system should make it obvious, from notebook outputs alone, which scenario regime is being stressed and why a plot is informative. The business-facing notebooks remain separate and should not inherit the internal scenario suite.

## Goals / Non-Goals

**Goals:**

- Calibrate internal scenario presets so each one creates measurable contrast in the intended diagnostic dimension.
- Add reusable scenario sanity summaries so sparse or empty plot conditions are visible before plotting.
- Make threshold-demand queue simulation robust to scenario-specific score calibration by supporting adaptive thresholds or threshold grids.
- Update notebooks `06` and `07` to use denser bounded defaults while preserving explicit fast-mode constants.
- Improve chart inputs and helpers so plots show scenario, threshold, sample-size, effect-size, and top-N context instead of isolated sparse points.
- Add tests that verify plot-useful contrast, non-empty queue-demand views, and bounded notebook defaults.

**Non-Goals:**

- Do not make the synthetic data look like real payroll frequency evidence; scenarios remain internal stress tests.
- Do not add supervised ranking models, train on synthetic labels, or tune scoring weights against labels.
- Do not add heavyweight visualization, Bayesian, dashboard, or probabilistic dependencies.
- Do not change analyst-safe queue fields or model feature leakage boundaries.
- Do not require notebooks `01` through `05` to run the internal diagnostic scenario suite.

## Decisions

### Calibrate scenarios against observable diagnostics

Scenario presets should be checked against concrete diagnostic outputs, not just anomaly counts. Each preset should produce at least one observable contrast such as score quantile movement, non-empty threshold queue demand, category mix change, anomaly dollar concentration, subgroup-period concentration, or pairwise component metric deltas.

Rationale: More generated rows can make charts denser, but homogeneous or low-scoring anomalies still produce flat or empty plots. Calibrating presets to observable outputs makes the notebooks reliable.

Alternative considered: only increase `employee_count`, `pay_periods`, and seed counts. Rejected because it increases runtime without guaranteeing contrast.

### Use adaptive thresholds and threshold grids for queue demand

Queue simulation should support threshold demand derived from score quantiles and/or a bounded threshold grid in addition to fixed numeric thresholds. Notebook `07` should show demand and overload across threshold choices when a single threshold would be empty for some scenarios.

Rationale: Fixed thresholds like `0.55` depend on scenario-specific score calibration. A quantile or grid view keeps operational demand plots informative across regimes.

Alternative considered: lower the fixed threshold globally. Rejected because it still risks empty or saturated queues in some scenarios and hides threshold sensitivity.

### Separate sanity summaries from chart rendering

Notebooks should display compact diagnostic summaries before plots: per-scenario rows, anomaly counts, anomaly dollars, score quantiles, candidates above thresholds, and concentration measures. Chart helpers should remain table-driven, with notebooks selecting or filtering prepared tables rather than recomputing complex metrics inline.

Rationale: If a plot is sparse, the sanity table explains whether the cause is data generation, thresholding, or visualization. Keeping preparation in library code keeps notebooks readable.

Alternative considered: only improve chart styling. Rejected because styling cannot fix empty or low-contrast input data.

### Increase defaults moderately and preserve fast mode

Internal notebooks should use enough scenarios, seeds, periods, and employees to make diagnostic plots useful, but they should define constants that can be reduced locally. Tests should assert the presence of bounded defaults and fast-mode guidance rather than forcing full notebook execution.

Rationale: The notebooks are internal data-science artifacts; they can be heavier than business-facing notebooks but must remain reproducible locally.

Alternative considered: keep current small defaults. Rejected because current rendered outputs are too sparse.

### Test plot usefulness directly

Tests should verify minimum diagnostic table density and contrast: non-empty threshold queues, non-zero overload under stress settings, scenario-specific score quantile differences, subgroup concentration, pairwise comparison sample counts, and required plot context columns.

Rationale: Schema-only tests allowed sparse rendered plots to pass. Plot-usefulness tests create a tighter feedback loop without snapshot-testing images.

Alternative considered: add image snapshot tests. Rejected because Lets-Plot image snapshots would be brittle and add tooling complexity.

## Risks / Trade-offs

- Richer defaults could slow notebook execution -> Keep explicit fast-mode constants and use bounded scenario/seed counts.
- Scenario calibration could become too artificial -> Label scenarios as internal stress tests and keep default payroll generation unchanged.
- Adaptive thresholds could blur operational interpretation -> Name threshold-grid outputs clearly and keep fixed top-K evaluation metrics separate.
- Plot-density tests could be brittle across scoring tweaks -> Use broad minimums and contrast checks, not exact metric values.
- Updating paired `.ipynb` outputs may create large diffs -> Prefer regenerating only notebooks `06` and `07` if paired outputs are committed.

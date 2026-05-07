## Context

The current internal diagnostics implementation added useful table-producing functions and notebooks, but the rendered plots are sparse because the notebooks use one small baseline synthetic world. In that world anomaly rates are nearly uniform across subgroups, component comparisons are dominated by a small set of signals, and queue pressure is mostly fixed by the configured top-K budget rather than scenario-driven demand.

This change improves diagnostic signal richness without changing the business-facing notebook sequence or analyst-safe queue boundaries. The goal is to create richer internal evidence for data-science review while keeping execution bounded and reproducible.

## Goals / Non-Goals

**Goals:**

- Add reusable scenario presets that intentionally create different diagnostic regimes for rule, statistical, ML, exposure, subgroup, and queue-stress analysis.
- Extend anomaly plans so anomaly propensity, category mix, and severity can be targeted by subgroup and period.
- Compare ranking components across multiple scenarios, seeds, and temporal origins using pairwise superiority, paired deltas, and effect-size intervals.
- Improve internal chart helpers so visualizations reveal contrasts, uncertainty, subgroup sample size, and scenario context.
- Update internal notebooks `06` and `07` to use richer bounded defaults while documenting faster local settings.
- Preserve default `generate_payroll(config)` behavior and analyst-safe output leakage rules.

**Non-Goals:**

- Do not add supervised ranking models or train on synthetic labels.
- Do not add full MCMC or heavyweight probabilistic dependencies.
- Do not replace the current pipeline orchestration surface.
- Do not make business-facing notebooks depend on the full internal diagnostic scenario suite.
- Do not introduce real payroll data, production integrations, or live analyst feedback systems.

## Decisions

### Add a scenario catalog rather than embedding scenarios in notebooks

Reusable presets will live in library code, likely in `scenarios.py` or a small companion module. Presets will cover baseline, rule-friendly, statistical-friendly, ML-friendly, exposure-heavy, subgroup-drift, calendar-drift, and queue-stress regimes.

Rationale: notebooks should select and narrate scenarios, not define complex scenario logic inline. Library-level presets are testable and reusable across diagnostics, queue simulations, and future notebooks.

Alternative considered: define richer scenarios directly in notebook cells. Rejected because it would make the notebooks harder to test and would keep the logic hidden from the library surface.

### Extend anomaly controls with subgroup-period targeting

The existing `AnomalyPlan` will be extended with targeted controls, such as subgroup filters, period ranges, category weights, target counts or propensity multipliers, and severity distribution parameters.

Rationale: subgroup and drift diagnostics need intentional differences in anomaly rates and severity. Global category weights alone produce nearly uniform subgroup rates and flat shrinkage plots.

Alternative considered: only increase `employee_count` and `pay_periods`. Rejected because larger homogeneous data would reduce sampling noise but would not create the contrasts needed for informative diagnostics.

### Evaluate component superiority across scenario/seed/origin units

Component superiority summaries will treat scenario/seed/origin as comparison units and report paired metric deltas, win probability, and intervals. Bootstrap within one world can remain available, but it will not be the primary evidence in notebook `06`.

Rationale: component comparisons become meaningful when signals face situations they are expected to handle differently. One-world bootstrap often overstates or flattens comparisons because resamples preserve the same data-generating process.

Alternative considered: tune chart scales around the existing bootstrap output. Rejected because the underlying evidence would still be weak.

### Make queue demand scenario-dependent

Queue simulation will support threshold-based or candidate-count demand in addition to fixed top-K queue size. Queue stress scenarios will combine increased anomaly/outlier volume with period-specific capacity shocks.

Rationale: fixed queue size makes overload probability mostly a capacity artifact. Scenario-dependent demand lets notebook `07` show how drift and anomaly mix affect workload, missed exposure, and overload risk.

Alternative considered: leave queue size fixed and only vary capacity. Rejected because it does not explain operational demand changes under stress.

### Upgrade charts to encode effect size and uncertainty

Plot helpers will prefer heatmaps for pairwise superiority, interval/error bars for metric uncertainty, sorted subgroup forest/shrinkage views, and faceted or grouped scenario views where appropriate.

Rationale: current point-only and bar-only helpers are easy to render but often hide the actual comparison dimension. More informative encodings reduce the need for notebook-side logic.

Alternative considered: keep existing helpers and add more tables. Rejected because the user-facing issue is specifically that plotted outputs are not helpful enough for DS interpretation.

## Risks / Trade-offs

- Scenario presets could become too artificial -> Document each preset as an internal stress-test regime and avoid presenting it as real payroll frequency evidence.
- Richer notebooks could become slow -> Keep bounded defaults, expose fast-mode constants, and test with reduced scenario/seed counts.
- More scenario controls could complicate the simulator -> Keep controls concrete and dataclass-based; avoid a chainable builder API.
- Component superiority may still be dominated by the hybrid score -> Report paired deltas and per-regime results, not just overall win probability.
- Queue demand semantics may blur top-K evaluation with operational workload -> Name threshold-demand outputs separately from fixed-budget review metrics and keep analyst-safe queue behavior unchanged.

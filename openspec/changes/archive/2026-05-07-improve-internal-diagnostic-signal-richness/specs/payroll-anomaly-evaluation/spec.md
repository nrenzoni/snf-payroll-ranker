## ADDED Requirements

### Requirement: Multi-regime component superiority diagnostics
The system SHALL compare ranking components across multiple diagnostic regimes rather than relying only on bootstrap samples from a single synthetic world.

#### Scenario: Component comparison spans scenarios and seeds
- **WHEN** internal component superiority diagnostics run with configured scenarios and seeds
- **THEN** the output includes one or more comparison rows per scenario/seed/origin unit for hybrid, rule, statistical, ML, and exposure ranking signals

#### Scenario: Pairwise deltas are reported
- **WHEN** two ranking signals are compared
- **THEN** the output includes paired metric delta, win probability or win frequency, sample count, and uncertainty interval or quantile bounds for configured review-budget metrics

#### Scenario: Regime-specific results remain inspectable
- **WHEN** component superiority is summarized across regimes
- **THEN** the output retains scenario or regime identifiers so notebooks can show which signal wins under which synthetic condition

### Requirement: Informative internal diagnostic plot inputs
The system SHALL produce plot-ready diagnostic tables that include effect-size, uncertainty, sample-size, and scenario-context fields needed for data-science interpretation.

#### Scenario: Pairwise superiority heatmap input is produced
- **WHEN** component superiority diagnostics complete
- **THEN** a plot-ready table includes left signal, right signal, metric, scenario or aggregate scope, win probability, mean delta, and interval bounds

#### Scenario: Subgroup plot input includes shrinkage and sample size
- **WHEN** subgroup diagnostics run on a scenario with subgroup drift
- **THEN** the output includes raw estimate, pooled estimate, interval bounds, record count, anomaly count, and subgroup dimension

#### Scenario: Calibration plot input includes subgroup and residual context
- **WHEN** expected-pay calibration diagnostics run
- **THEN** the output includes coverage, interval width, residual, excess over p90, subgroup dimension, and record count

#### Scenario: Robustness plot input includes instability tradeoffs
- **WHEN** robustness diagnostics run across scenarios, seeds, or temporal origins
- **THEN** the output includes mean performance, performance variability, queue overlap, and an instability metric suitable for Pareto or heatmap views

### Requirement: Scenario-dependent queue simulation diagnostics
The system SHALL support queue simulation diagnostics where queue demand can vary by scenario as well as by analyst capacity.

#### Scenario: Threshold-based queue demand is summarized
- **WHEN** queue simulation is configured with score-threshold demand
- **THEN** the output reports candidate queue size, reviewed records, overload probability, missed estimated exposure, and missed synthetic anomaly dollars by period and scenario

#### Scenario: Capacity shocks are scenario-aware
- **WHEN** queue stress scenarios configure period-specific capacity reductions or random capacity variation
- **THEN** queue simulation summaries reflect the configured capacity behavior and retain scenario identifiers

#### Scenario: Fixed top-K metrics remain separate
- **WHEN** threshold-demand queue simulation is added
- **THEN** existing fixed review-budget metrics remain available and are not reinterpreted as operational queue demand

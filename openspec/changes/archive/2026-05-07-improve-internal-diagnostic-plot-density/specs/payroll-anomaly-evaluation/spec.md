## ADDED Requirements

### Requirement: Dense internal diagnostic plot inputs
The system SHALL produce internal diagnostic tables with enough rows, scenario context, effect-size context, and threshold context to render informative plots in notebooks `06` and `07`.

#### Scenario: Component comparison has sufficient comparison units
- **WHEN** internal component superiority diagnostics run with bounded notebook defaults
- **THEN** pairwise comparison outputs include multiple scenarios and seeds, retain scenario identifiers, and report sample counts sufficient for non-trivial aggregate and scenario-specific plots

#### Scenario: Pairwise outputs expose effect-size contrast
- **WHEN** two ranking signals are compared across internal diagnostic units
- **THEN** the output includes mean delta, win probability or frequency, sample count, interval bounds, scenario scope, and metric name for plotting heatmaps and effect-size interval charts

#### Scenario: Subgroup plot inputs prioritize meaningful rows
- **WHEN** subgroup diagnostics run for subgroup-drift scenarios
- **THEN** plot-ready outputs include top-N or sorted subgroup rows with raw estimate, pooled estimate, interval bounds, record count, anomaly count, and scenario context

#### Scenario: Calibration and robustness inputs avoid point-only sparse views
- **WHEN** expected-pay calibration or robustness diagnostics run across internal scenarios
- **THEN** the plot-ready outputs include subgroup or scenario grouping, residuals, interval width, queue overlap, performance variability, instability metrics, and enough rows for grouped or faceted plots

### Requirement: Adaptive threshold-demand queue diagnostics
The system SHALL support threshold-demand queue diagnostics that remain informative across scenario-specific score calibrations.

#### Scenario: Threshold grid demand is summarized
- **WHEN** queue simulation runs with a configured threshold grid
- **THEN** the output reports scenario, threshold, pay period, candidate queue size, reviewed records, overload probability, missed estimated exposure, and missed synthetic anomaly dollars

#### Scenario: Adaptive threshold demand is summarized
- **WHEN** queue simulation runs with an adaptive score quantile or percentile threshold
- **THEN** the output reports the resolved threshold, scenario, candidate queue size, reviewed records, overload probability, and missed exposure fields needed for plotting

#### Scenario: Fixed top-K evaluation remains separate
- **WHEN** adaptive or threshold-grid queue-demand diagnostics are added
- **THEN** existing fixed review-budget evaluation metrics remain available and are not reinterpreted as operational candidate demand

### Requirement: Plot-usefulness validation
The system SHALL validate internal diagnostic table usefulness with bounded, non-image tests.

#### Scenario: Plot inputs meet minimum density checks
- **WHEN** the test suite runs internal diagnostic checks
- **THEN** it verifies minimum row counts, non-empty candidate-demand views, non-zero overload under stress settings, and required scenario, interval, sample-size, and threshold columns

#### Scenario: Scenario contrast checks avoid exact metric brittleness
- **WHEN** scenario contrast tests run
- **THEN** they assert broad differences such as score quantile movement, anomaly dollar separation, category mix changes, or subgroup concentration rather than exact metric values

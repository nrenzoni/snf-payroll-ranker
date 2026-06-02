## MODIFIED Requirements

### Requirement: Evaluation stability and leakage checks
The system SHALL report stability or uncertainty summaries and explicit leakage checks for anomaly evaluation.

#### Scenario: Stability summaries are reported
- **WHEN** evaluation results are produced across seeds, origins, review budgets, or DGP scenarios
- **THEN** the output includes stability summaries such as score distribution changes, queue overlap, metric ranges, winner frequencies, or confidence intervals where applicable

#### Scenario: Leakage checks are reported
- **WHEN** evaluation runs on synthetic labels
- **THEN** the output verifies that label columns and injected anomaly dollar impacts are not used as scoring features or analyst queue inputs

## ADDED Requirements

### Requirement: Scenario-seed benchmark aggregation
The system SHALL aggregate employee-pay-cycle residual ranking results across DGP scenarios, seeds, and review-budget operating points for notebook-facing model comparison.

#### Scenario: Aggregated benchmark summaries are produced
- **WHEN** the scenario-based benchmark runs for the active employee-pay-cycle notebook
- **THEN** the outputs include aggregated summaries by scenario, seed, model, review-budget percentage, and metric
- **AND** those summaries preserve the underlying percent-budget grouped ranking metric definitions used by the employee-cycle evaluation runtime

### Requirement: Winner summaries are objective-specific
The system SHALL summarize model winners separately by operating objective rather than forcing one universal winner across all review-budget metrics.

#### Scenario: Objective-specific winners are reported
- **WHEN** notebook-facing benchmark summaries are generated
- **THEN** the outputs can identify winner frequency and winner maps for objectives such as severity ordering, dollar recovery, and incremental utility at each configured review-budget percentage

### Requirement: Median metric tables include uncertainty columns
The system SHALL provide notebook-ready median metric summary tables with interval columns for scenario-seed benchmark reporting.

#### Scenario: Median metric intervals are available
- **WHEN** the active notebook renders aggregated benchmark tables
- **THEN** it can display median metric summaries for each model and review-budget percentage with accompanying lower and upper interval columns derived from the available scenario-seed study units

## ADDED Requirements

### Requirement: Rolling-origin validation
The system SHALL evaluate payroll anomaly ranking across multiple temporal origins when enough pay periods are available.

#### Scenario: Multiple temporal origins are summarized
- **WHEN** rolling-origin evaluation runs
- **THEN** each origin trains or calibrates on earlier periods, validates on subsequent periods, tests on later periods, and reports review-budget metrics by origin

### Requirement: Validation-based operating-point selection
The system SHALL select thresholds or configurable score weights using validation periods before reporting test-period performance.

#### Scenario: Test metrics use validation-selected settings
- **WHEN** thresholds or hybrid weights are tuned
- **THEN** tuning decisions are made on validation periods and the chosen settings are then evaluated on later test periods

### Requirement: Evaluation stability and leakage checks
The system SHALL report stability or uncertainty summaries and explicit leakage checks for anomaly evaluation.

#### Scenario: Stability summaries are reported
- **WHEN** evaluation results are produced across seeds, origins, or review budgets
- **THEN** the output includes stability summaries such as score distribution changes, queue overlap, metric ranges, or confidence intervals where applicable

#### Scenario: Leakage checks are reported
- **WHEN** evaluation runs on synthetic labels
- **THEN** the output verifies that label columns and injected anomaly dollar impacts are not used as scoring features or analyst queue inputs

## MODIFIED Requirements

### Requirement: Temporal anomaly evaluation
The system SHALL evaluate anomaly detection using temporal validation rather than random row splits.

#### Scenario: Holdout periods are scored after training periods
- **WHEN** the evaluation pipeline runs
- **THEN** models, thresholds, and score weights are selected using earlier training or validation pay periods and evaluated on later pay periods

#### Scenario: Backtesting scores each period independently
- **WHEN** backtesting evaluation is enabled
- **THEN** each scored pay period uses only prior periods for feature baselines, model fitting, threshold selection, and score calibration where applicable

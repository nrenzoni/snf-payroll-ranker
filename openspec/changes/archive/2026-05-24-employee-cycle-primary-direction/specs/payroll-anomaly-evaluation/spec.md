## MODIFIED Requirements

### Requirement: Temporal anomaly evaluation
The system SHALL evaluate employee-pay-cycle ranking with temporally ordered validation as the active default and SHALL treat random row splits as debugging-only anti-pattern checks.

#### Scenario: Holdout periods are scored after training periods
- **WHEN** the active evaluation pipeline runs
- **THEN** models, thresholds, group weighting, and calibration settings are selected using earlier payroll cycles and evaluated on later payroll cycles

#### Scenario: Backtesting scores each period independently
- **WHEN** backtesting evaluation is enabled
- **THEN** each scored payroll cycle uses only prior cycles for feature baselines, model fitting, threshold selection, and score calibration where applicable

### Requirement: Review-queue metrics
The system SHALL report employee-pay-cycle grouped ranking metrics that measure review value within facility-cycle queues and aggregate those results for active research and production-candidacy decisions.

#### Scenario: Grouped top-k metrics are reported
- **WHEN** active predictions are evaluated
- **THEN** the results include top-k queue metrics computed within facility-cycle groups and aggregated across groups using explicit project-defined aggregation schemes

#### Scenario: Ranking quality is reported
- **WHEN** active predictions are evaluated against available labels
- **THEN** the results include rank-oriented metrics such as precision@K, recall@K, mean reciprocal rank, and other grouped ranking metrics selected for the active employee-pay-cycle program

## ADDED Requirements

### Requirement: Production-candidacy validation
The active evaluation program SHALL determine whether an employee-pay-cycle scoring approach is promotable into later production work.

#### Scenario: Candidate methods are judged on deployment-relevant evidence
- **WHEN** an active method is summarized after Phase 1 evaluation
- **THEN** the evaluation reports whether the method meets the project's current criteria for temporal generalization, facility generalization, top-k ranking value, uncertainty behavior, and explanation readiness

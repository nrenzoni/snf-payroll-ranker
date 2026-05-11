## MODIFIED Requirements

### Requirement: Manual threshold baseline evaluation
The system SHALL evaluate automated SNF approval ranking against administrator-style threshold baselines that include individual threshold flags and a calibrated combined manual threshold baseline.

#### Scenario: Threshold baseline metrics are reported
- **WHEN** evaluation runs on scored SNF shift-level records
- **THEN** results report approval-budget, review-burden, and exposure metrics for the calibrated manual threshold pack, gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance thresholds

#### Scenario: Threshold overflagging is summarized
- **WHEN** manual threshold baselines and automated ranking are compared
- **THEN** evaluation summarizes false positives, reviewed records required, missed high-exposure anomalies, estimated exposure captured per reviewed record, and native review burden for each threshold approach

### Requirement: SNF case-study evaluation
The system SHALL provide case-study-specific and repeated-world evaluation outputs for the implemented SNF scenarios.

#### Scenario: Overtime case-study metrics are produced
- **WHEN** overtime or double-shift staffing pressure scenarios are evaluated
- **THEN** outputs compare automated ranking against the calibrated manual threshold pack and manual overtime, total-hours, and facility-variance thresholds for review volume, precision, recall, exposure capture, and missed high-risk shifts

#### Scenario: Premium mismatch case-study metrics are produced
- **WHEN** premium pay or shift differential mismatch scenarios are evaluated
- **THEN** outputs compare automated ranking against the calibrated manual threshold pack and manual gross-pay, premium-dollar, and facility-variance thresholds for review volume, precision, recall, exposure capture, and missed unsupported premiums

#### Scenario: Repeated-world main-scenario summaries are produced
- **WHEN** the business-proof notebook prepares aggregate evidence
- **THEN** outputs include scenario-by-seed comparison summaries for `baseline`, `overtime-staffing-pressure`, and `premium-mismatch` worlds across configured facility review budgets and burden-versus-value metrics

## ADDED Requirements

### Requirement: Business-proof repeated-world comparison artifacts
The system SHALL produce plot-ready repeated-world comparison artifacts for facility-admin notebook evidence.

#### Scenario: Repeated-world superiority summaries are available
- **WHEN** scenario-by-seed business-proof diagnostics run
- **THEN** outputs include per-method win rates, mean deltas or empirical intervals, and scenario-budget comparison series suitable for notebook plots

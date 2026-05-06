## ADDED Requirements

### Requirement: Separate analyst and evaluation review queues
The system SHALL produce an analyst-safe review queue for operational triage and a separate evaluation-labeled review queue for synthetic performance analysis.

#### Scenario: Analyst queue excludes evaluation labels
- **WHEN** analyst review queue generation runs
- **THEN** the queue excludes injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts

#### Scenario: Evaluation queue includes labels for analysis
- **WHEN** evaluation-labeled queue generation runs against synthetic data
- **THEN** the queue includes injected labels and injected anomaly dollar impacts only for error analysis and metric interpretation

### Requirement: Component contribution context
The system SHALL include enough component-score and reason-code context for analysts to understand why a record was prioritized without exposing evaluation truth.

#### Scenario: Review context is explainable
- **WHEN** a record appears in the analyst-safe queue
- **THEN** the row includes reason codes, risk category, estimated exposure or dollars-at-risk estimate, expected-vs-actual context, peer context, and relevant component scores or score-driver fields

## MODIFIED Requirements

### Requirement: Analyst-ready review queue
The system SHALL produce a ranked review queue of employee-pay-period records for payroll analyst review.

#### Scenario: Review queue fields are populated
- **WHEN** review queue generation runs
- **THEN** each analyst-safe queue row includes rank, synthetic employee identifier, pay period, final score, risk category, primary reason, secondary reason, gross pay, expected gross pay or baseline, difference from expected, peer context, rule flags, and estimated dollars at risk

#### Scenario: Review queue is sorted by priority
- **WHEN** records are exported for review
- **THEN** records are sorted by pay period and descending final anomaly score or configured review priority

#### Scenario: Review queue remains review-safe
- **WHEN** records are exported for analyst review
- **THEN** the queue does not claim confirmed misconduct, confirmed fraud, or known synthetic anomaly status

## MODIFIED Requirements

### Requirement: Injected anomaly labels
The system SHALL inject known payroll anomaly categories and retain labels for evaluation-only artifacts.

#### Scenario: Supported anomaly categories are injected
- **WHEN** the data generator injects anomalies
- **THEN** generated labels include categories such as duplicate payment, overtime spike, pay after termination, gross pay spike, incorrect pay rate, missing deduction, negative net pay, retro pay outlier, department payroll spike, and new employee large payment

#### Scenario: Evaluation labels are retained separately from model features
- **WHEN** model features are built
- **THEN** injected anomaly labels are available for evaluation but are not included as training or scoring features

#### Scenario: Evaluation labels are absent from analyst outputs
- **WHEN** analyst-facing review outputs are generated
- **THEN** injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts are excluded from those outputs

#### Scenario: Evaluation labels remain available for synthetic analysis
- **WHEN** synthetic evaluation outputs are generated
- **THEN** injected anomaly labels and injected anomaly dollar impacts are available in separate evaluation artifacts for metrics, category error analysis, and notebook interpretation

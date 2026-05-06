## ADDED Requirements

### Requirement: Label-free estimated exposure scoring
The system SHALL calculate dollar or exposure score components only from production-observable payroll fields and leakage-safe baselines.

#### Scenario: Exposure score excludes injected evaluation truth
- **WHEN** scoring records for anomaly ranking
- **THEN** the exposure score MUST NOT use injected anomaly labels, injected anomaly categories, or injected anomaly dollar impacts

#### Scenario: Estimated exposure is based on observable deltas
- **WHEN** a record differs from expected history, peer baselines, deterministic rules, overtime expectations, deductions expectations, or manual adjustment norms
- **THEN** the system estimates exposure from those observable payroll differences rather than from known synthetic anomaly impact

### Requirement: Period-safe peer and robust reference features
The system SHALL compute peer-relative and robust reference features using baselines that are available at the scored period and do not include future records.

#### Scenario: Peer baseline excludes invalid references
- **WHEN** peer-relative features are computed for a scored employee-pay-period record
- **THEN** the peer baseline excludes future pay periods and excludes the scored row from its own peer aggregate where feasible

#### Scenario: Robust distribution references are period-aware
- **WHEN** robust z-scores, median absolute deviation scores, interquartile outlier flags, percentiles, or deviation ratios are computed
- **THEN** the reference distribution is derived from prior or otherwise scoring-time-available records rather than all future records

## MODIFIED Requirements

### Requirement: Payroll rule baseline
The system SHALL calculate deterministic payroll rule flags and a rule severity score.

#### Scenario: Deterministic anomalies are flagged
- **WHEN** records violate payroll rules such as payment after termination, duplicate payment signature, gross pay less than or equal to zero for an active employee, negative net pay, net pay materially greater than gross pay, extreme overtime, large manual adjustment, pay-rate change, or missing or zero deductions
- **THEN** the corresponding rule flags, reason codes, and severity contributions are populated

### Requirement: Configurable hybrid ranking score
The system SHALL combine rule, employee-history, peer-relative, ML, and estimated exposure components into a configurable final anomaly score without using injected evaluation labels or injected anomaly dollar impacts.

#### Scenario: Hybrid score ranks review candidates
- **WHEN** scoring is complete
- **THEN** each employee-pay-period record has component scores, a final anomaly score, and a rank within its pay period suitable for review queue generation

#### Scenario: Hybrid score is label-free
- **WHEN** injected labels are present for synthetic evaluation
- **THEN** the hybrid score calculation ignores `is_anomaly`, `anomaly_category`, and `anomaly_dollars`

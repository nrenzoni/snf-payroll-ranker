## MODIFIED Requirements

### Requirement: Payroll rule baseline
The system SHALL calculate deterministic SNF payroll approval rule flags and a rule severity score from shift-level schedule, timeclock, pay-code, pay policy, lifecycle, and payroll-line context.

#### Scenario: Deterministic SNF anomalies are flagged
- **WHEN** records violate SNF payroll approval rules such as paid hours materially exceeding scheduled hours, overtime or double-shift rest-gap risk, unsupported shift differential, unsupported weekend premium, duplicate premium code, premium pay without matching shift context, pay after termination, duplicate shift payment signature, nonpositive active pay, negative net pay where generated, or missing expected deductions where generated
- **THEN** the corresponding rule flags, reason codes, source-to-check values, recommended actions, and severity contributions are populated

### Requirement: Robust statistical scoring
The system SHALL calculate robust, stationary, facility-normalized anomaly scores for SNF shift-level payroll distributions.

#### Scenario: Robust SNF scores are generated
- **WHEN** employee-history, facility-role-shift peer, cross-facility peer, and pay-code baselines are available
- **THEN** the system computes robust z-scores, median absolute deviation scores, interquartile outlier flags, percentiles, deviation ratios, and normalized ratios for gross pay, worked hours, overtime hours, premium pay share, paid-vs-scheduled variance, rest-gap context, and estimated exposure

### Requirement: Machine learning anomaly scoring
The system SHALL train and apply at least one unsupervised anomaly model on leakage-safe numerical SNF shift-level features.

#### Scenario: Isolation Forest scores SNF shift records
- **WHEN** the model training pipeline runs on earlier pay periods
- **THEN** an Isolation Forest model produces normalized anomaly scores for later shift-level payroll records without using injected labels, injected anomaly categories, injected anomaly dollar impacts, or administrator-only evaluation fields as features

### Requirement: Configurable hybrid ranking score
The system SHALL combine SNF rule, employee-history, facility-normalized peer, statistical, machine-learning, schedule/timeclock, premium-eligibility, and estimated exposure components into a configurable final approval exception score without using injected evaluation labels or injected anomaly dollar impacts.

#### Scenario: Hybrid score ranks SNF approval candidates
- **WHEN** scoring is complete
- **THEN** each shift-level payroll record has component scores, a final approval exception score, and a rank within its pay period or facility-pay-period suitable for pre-approval queue generation

#### Scenario: Hybrid score is label-free
- **WHEN** injected labels are present for synthetic evaluation
- **THEN** the hybrid score calculation ignores `is_anomaly`, `anomaly_category`, and `anomaly_dollars`

### Requirement: Feature engineering notebook walkthrough
The notebooks SHALL demonstrate SNF-specific leakage-safe historical, peer, deterministic rule, stationarity, normalization, and robust statistical features using concrete synthetic shift-level payroll records.

#### Scenario: Concrete SNF feature examples are displayed
- **WHEN** the feature engineering and case-study notebooks run
- **THEN** they display selected shift-level records with actual gross pay, expected role-shift pay, scheduled hours, worked hours, overtime context, premium eligibility context, prior rolling baselines, facility-normalized peer baselines, rule reason codes, source-to-check context, and component scores

### Requirement: Label-free estimated exposure scoring
The system SHALL calculate estimated exposure score components only from production-observable SNF payroll, schedule, timeclock, policy, and leakage-safe baseline fields.

#### Scenario: Exposure score excludes injected evaluation truth
- **WHEN** scoring records for approval exception ranking
- **THEN** the exposure score MUST NOT use injected anomaly labels, injected anomaly categories, or injected anomaly dollar impacts

#### Scenario: Estimated exposure is based on observable SNF deltas
- **WHEN** a record differs from expected schedule, timeclock, role-shift pay, peer baselines, premium eligibility, overtime expectations, deductions expectations where available, or approval norms
- **THEN** the system estimates exposure from those observable payroll differences rather than from known synthetic anomaly impact

## ADDED Requirements

### Requirement: Facility-normalized transferable features
The system SHALL engineer features that support comparison across facilities and future bootstrapping of new SNF client facilities.

#### Scenario: Facility-normalized features are produced
- **WHEN** shift-level feature engineering runs
- **THEN** outputs include facility-relative, comparable-facility, role-shift peer, employee-history, and pay-code-category normalized features using prior or scoring-time-available references

#### Scenario: Stationary ratios are produced
- **WHEN** shift-level feature engineering runs
- **THEN** outputs include stationary ratios such as overtime hours per scheduled hour, worked hours per scheduled hour, premium pay share, manual edit rate where available, gross pay versus expected role-shift pay, and estimated exposure relative to expected pay

### Requirement: Premium eligibility features
The system SHALL compute premium eligibility features from synthetic pay policy, shift, schedule, and timeclock context.

#### Scenario: Premium eligibility mismatch is detected
- **WHEN** a payroll line includes shift differential, weekend premium, holiday premium if implemented, callback, or duplicate premium context
- **THEN** feature engineering identifies whether the pay code and amount are consistent with the configured synthetic policy and observed shift context

### Requirement: Fatigue and double-shift features
The system SHALL compute overtime, double-shift, rest-gap, and consecutive-work context for SNF shift-level records.

#### Scenario: Fatigue context is generated
- **WHEN** an employee works multiple shifts, long hours, or consecutive days
- **THEN** feature engineering produces trailing hours, same-day shift count, double-shift indicator, rest-gap hours, consecutive-day count, and prior-period double-shift count using leakage-safe references where history is required

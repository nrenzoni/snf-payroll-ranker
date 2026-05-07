## ADDED Requirements

### Requirement: Rolling reference window for uncertainty scoring
The system SHALL use a configurable rolling reference window of prior pay periods for uncertainty calculations that require historical comparison.

#### Scenario: Prior-period reference window is used
- **WHEN** scoring a payroll record for a pay period
- **THEN** conformal context, bootstrap references, OOD references, and expected gross-pay interval references use only records from the configured last 6 prior pay periods by default

#### Scenario: Current and future periods are excluded
- **WHEN** uncertainty calculations build training, calibration, interval, or neighbor-reference data
- **THEN** the current pay period and all future pay periods are excluded from those reference records

### Requirement: Record-level uncertainty components
The system SHALL compute uncertainty components alongside payroll anomaly risk scores without using injected evaluation labels, injected anomaly categories, injected anomaly dollar impacts, or evaluation-only OOD labels.

#### Scenario: Ensemble disagreement is computed from score signals
- **WHEN** scoring output includes rule, employee-history, peer-relative, statistical, machine-learning, and exposure score signals
- **THEN** the system computes an ensemble disagreement uncertainty component from the configurable weighted dispersion of available score signals

#### Scenario: Bootstrap score interval is computed from prior-period reference data
- **WHEN** bootstrap uncertainty is enabled and sufficient prior-period reference records exist
- **THEN** the system scores each target record across multiple bootstrapped Isolation Forest fits and reports interval statistics such as lower percentile, upper percentile, standard deviation, and normalized interval width

#### Scenario: Sample-size uncertainty is computed for peer and employee history context
- **WHEN** strict peer-group size, effective peer-reference size, or prior employee pay-period count is available for a scored record
- **THEN** the system computes peer-group uncertainty and employee-history uncertainty that increase as the available comparison sample decreases

#### Scenario: Data-quality uncertainty is computed from observed input issues
- **WHEN** required or important payroll fields are missing, invalid, unknown, stale, inconsistent, or otherwise low quality
- **THEN** the system computes a data-quality uncertainty component and records the issue drivers without using evaluation labels

#### Scenario: Out-of-distribution uncertainty is computed from numeric and pay-code context
- **WHEN** scored records contain unseen pay codes, rare pay codes, rare pay-code combinations, high missingness, out-of-range numeric values, or large nearest-neighbor distances from prior-period reference records
- **THEN** the system computes an out-of-distribution uncertainty component and records relevant OOD drivers

### Requirement: Expected gross-pay interval prediction
The system SHALL estimate an expected gross-pay interval for each scored record using only prior-period reference data.

#### Scenario: Gross-pay interval fields are produced
- **WHEN** sufficient prior-period reference records exist for expected-pay interval estimation
- **THEN** the system produces `expected_gross_pay_p10`, `expected_gross_pay_p50`, `expected_gross_pay_p90`, `expected_gross_pay_interval_width`, and `gross_pay_excess_vs_p90`

#### Scenario: Gross-pay interval uses leakage-safe references
- **WHEN** expected gross-pay intervals are estimated for a pay period
- **THEN** the interval calculation uses only records from the configured prior-period reference window and excludes the scored period and future periods

#### Scenario: Interval outputs separate risk and uncertainty context
- **WHEN** gross pay exceeds the expected p90 value or the expected interval is wide
- **THEN** excess over p90 is available as risk context and interval width is available as uncertainty context

### Requirement: Conformal anomaly context
The system SHALL compute conformal p-values and percentiles as explanation-only anomaly context.

#### Scenario: Conformal values are computed from prior calibration scores
- **WHEN** prior-period calibration anomaly scores are available and higher scores mean more anomalous records
- **THEN** the system computes a conformal p-value and conformal percentile for each scored record by comparing its anomaly score to calibration scores

#### Scenario: Conformal is excluded from composite uncertainty
- **WHEN** composite uncertainty score is computed
- **THEN** conformal p-value and conformal percentile are not included as weighted uncertainty components

### Requirement: Composite uncertainty score and bucket
The system SHALL produce a transparent composite uncertainty score and uncertainty bucket from configurable uncertainty component weights.

#### Scenario: Composite uncertainty uses configurable weights
- **WHEN** uncertainty components have been computed for a scored record
- **THEN** the system combines ensemble disagreement, bootstrap interval width, gross-pay interval width, employee-history uncertainty, peer-group uncertainty, data-quality uncertainty, and out-of-distribution uncertainty using configurable weights

#### Scenario: Uncertainty bucket is assigned from composite score
- **WHEN** a composite uncertainty score is available
- **THEN** the system assigns an uncertainty bucket of Low, Medium, or High using configured thresholds

#### Scenario: Calibration uncertainty remains unavailable without feedback labels
- **WHEN** analyst feedback labels or comparable real review outcomes are not available
- **THEN** the system does not compute calibration uncertainty and documents it as a future component rather than fabricating label-based confidence

#### Scenario: Risk score remains separate from uncertainty score
- **WHEN** risk and uncertainty outputs are generated
- **THEN** the final anomaly risk score remains available separately from uncertainty score so high-risk records are not hidden solely because uncertainty is high

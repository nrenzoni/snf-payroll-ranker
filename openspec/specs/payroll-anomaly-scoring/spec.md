## Purpose
Define leakage-safe feature engineering and hybrid scoring for payroll anomaly ranking.
## Requirements
### Requirement: Leakage-safe feature engineering
The system SHALL compute employee-history and temporal features using only information available before the scored pay period.

#### Scenario: Rolling history excludes current and future periods
- **WHEN** rolling employee features such as gross pay median, gross pay standard deviation, overtime baseline, or net-to-gross history are computed
- **THEN** the calculation excludes the current pay period and all future pay periods

#### Scenario: Temporal split avoids random row leakage
- **WHEN** model training and scoring datasets are prepared
- **THEN** records are split by pay period rather than random employee-pay-period rows

### Requirement: Payroll rule baseline
The system SHALL calculate deterministic payroll rule flags and a rule severity score.

#### Scenario: Deterministic anomalies are flagged
- **WHEN** records violate payroll rules such as payment after termination, duplicate payment signature, gross pay less than or equal to zero for an active employee, negative net pay, net pay materially greater than gross pay, extreme overtime, large manual adjustment, pay-rate change, or missing or zero deductions
- **THEN** the corresponding rule flags, reason codes, and severity contributions are populated

### Requirement: Robust statistical scoring
The system SHALL calculate robust anomaly scores for skewed payroll distributions.

#### Scenario: Robust scores are generated
- **WHEN** employee-history and peer-relative baselines are available
- **THEN** the system computes robust z-scores, median absolute deviation scores, interquartile outlier flags, percentile features, and deviation ratios for payroll amounts, overtime, deductions, and net-to-gross ratios

### Requirement: Machine learning anomaly scoring
The system SHALL train and apply at least one unsupervised anomaly model on leakage-safe numerical features.

#### Scenario: Isolation Forest scores records
- **WHEN** the model training pipeline runs on earlier pay periods
- **THEN** an Isolation Forest model produces normalized anomaly scores for later pay-period records without using injected labels as features

### Requirement: Configurable hybrid ranking score
The system SHALL combine rule, employee-history, peer-relative, ML, and estimated exposure components into a configurable final anomaly score without using injected evaluation labels or injected anomaly dollar impacts.

#### Scenario: Hybrid score ranks review candidates
- **WHEN** scoring is complete
- **THEN** each employee-pay-period record has component scores, a final anomaly score, and a rank within its pay period suitable for review queue generation

#### Scenario: Hybrid score is label-free
- **WHEN** injected labels are present for synthetic evaluation
- **THEN** the hybrid score calculation ignores `is_anomaly`, `anomaly_category`, and `anomaly_dollars`

### Requirement: Feature engineering notebook walkthrough
The notebooks SHALL demonstrate historical employee features, peer-relative features, deterministic rule-based flags, and robust statistical features using concrete synthetic payroll records.

#### Scenario: Concrete feature examples are displayed
- **WHEN** the feature engineering and baselines notebook runs
- **THEN** it displays selected records with current gross pay, prior rolling median, percentage change, peer median, peer deviation, rule reason codes, and component scores

### Requirement: Leakage-safe feature explanation
The notebooks SHALL explain which features are leakage-safe and why injected labels are retained for evaluation but not used as training or scoring features.

#### Scenario: Leakage-safe narrative is present
- **WHEN** a reviewer reads the feature engineering and baselines notebook
- **THEN** the notebook states that historical features exclude current and future periods and that labels are not used as model features

### Requirement: Baseline scoring comparison inputs
The notebooks SHALL demonstrate rule score, statistical score, ML score, and hybrid score as separate baseline ranking signals using the existing model comparison output.

#### Scenario: Baseline score columns are compared
- **WHEN** the feature engineering and modeling notebooks run
- **THEN** they display rule, statistical, ML, and hybrid score columns and explain what each contributes to payroll review prioritization

### Requirement: Payroll hybrid ranking rationale
The notebooks SHALL explain why a hybrid ranking is appropriate for payroll because deterministic compliance issues, statistical outliers, peer context, employee history, and dollar impact capture different review risks.

#### Scenario: Hybrid rationale is included
- **WHEN** a reviewer reads the feature engineering or modeling notebook
- **THEN** the notebook describes why payroll ranking combines rule-based, statistical, ML, peer/history, and dollar-impact signals rather than relying on a single model score

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

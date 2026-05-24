## Purpose
Define leakage-safe feature engineering and hybrid scoring for payroll anomaly ranking.
## Requirements
### Requirement: Leakage-safe feature engineering
The system SHALL compute employee-pay-cycle features using only information available before the scored payroll cycle and SHALL treat employee-pay-cycle records as the active feature-engineering contract.

#### Scenario: Rolling history excludes current and future periods
- **WHEN** rolling employee or facility features such as pay medians, gross-pay standard deviation, overtime baseline, or payroll-cycle history are computed
- **THEN** the calculation excludes the current payroll cycle and all future cycles

#### Scenario: Temporal split avoids random row leakage
- **WHEN** model training and scoring datasets are prepared
- **THEN** active employee-pay-cycle records are split by payroll cycle rather than random employee-cycle rows

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
The system SHALL support supervised and ranking-oriented employee-pay-cycle scoring interfaces suitable for Phase 1 production-oriented research rather than requiring a single active unsupervised anomaly model.

#### Scenario: Multiple formulation interfaces are supported
- **WHEN** active model training or scoring is implemented
- **THEN** the runtime contract supports employee-pay-cycle classification, regression, expected-value, or learning-to-rank formulations as comparable active scoring paths

#### Scenario: Active scoring interfaces stay label-safe
- **WHEN** synthetic or adjudicated labels are present for research evaluation
- **THEN** active scoring features exclude evaluation-only truth fields and use only approved feature contracts for training, calibration, or scoring

### Requirement: Phase-gated production promotion
The scoring library SHALL treat Phase 1 formulation comparison as a gate for later production promotion rather than declaring any single method as the active production answer in advance.

#### Scenario: Production candidacy is evidence-based
- **WHEN** an active scoring method is proposed for later operational use
- **THEN** the project documents that promotion depends on evaluation, generalization, uncertainty, and explainability evidence from the active research phase

### Requirement: Feature engineering notebook walkthrough
The notebooks SHALL demonstrate SNF-specific leakage-safe historical, peer, deterministic rule, stationarity, normalization, and robust statistical features using concrete synthetic shift-level payroll records.

#### Scenario: Concrete SNF feature examples are displayed
- **WHEN** the feature engineering and case-study notebooks run
- **THEN** they display selected shift-level records with actual gross pay, expected role-shift pay, scheduled hours, worked hours, overtime context, premium eligibility context, prior rolling baselines, facility-normalized peer baselines, rule reason codes, source-to-check context, and component scores

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
The system SHALL calculate estimated exposure score components only from production-observable SNF payroll, schedule, timeclock, policy, and leakage-safe baseline fields.

#### Scenario: Exposure score excludes injected evaluation truth
- **WHEN** scoring records for approval exception ranking
- **THEN** the exposure score MUST NOT use injected anomaly labels, injected anomaly categories, or injected anomaly dollar impacts

#### Scenario: Estimated exposure is based on observable SNF deltas
- **WHEN** a record differs from expected schedule, timeclock, role-shift pay, peer baselines, premium eligibility, overtime expectations, deductions expectations where available, or approval norms
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

### Requirement: Score component contribution narrative
The notebooks SHALL explain the contribution of each major scoring component to SNF payroll approval prioritization.

#### Scenario: Component contributions are displayed
- **WHEN** the SNF case-study or technical ML value notebook runs
- **THEN** it displays rule, statistical, schedule/timeclock, premium eligibility, ML, exposure, and hybrid score context where available for selected ranked records or aggregate method comparisons

#### Scenario: Hybrid rationale is tied to evidence
- **WHEN** the notebooks compare component scores with hybrid ranking
- **THEN** they explain why payroll approval benefits from combining deterministic rules, robust statistics, ML multivariate unusualness, schedule/timeclock context, premium eligibility, and estimated exposure rather than relying on one signal alone

### Requirement: ML-only value is separated from hybrid value
The technical ML value notebook SHALL distinguish the value of the ML score alone from the value of the full hybrid ranking.

#### Scenario: ML and hybrid are compared separately
- **WHEN** method-comparison outputs are displayed
- **THEN** ML-only metrics and hybrid-ranking metrics appear as separate methods so reviewers can see whether the hybrid score improves beyond unsupervised ML alone

### Requirement: Administrator threshold baseline flags
The system SHALL emit administrator-style threshold baseline flags from observable SNF payroll fields alongside the scored payroll output.

#### Scenario: Manual threshold flags are present
- **WHEN** scoring completes
- **THEN** each scored record includes gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance threshold flags for downstream evaluation and notebook comparisons

#### Scenario: Threshold flags remain label-free
- **WHEN** threshold baseline flags are computed
- **THEN** the flags use only production-observable payroll, schedule, timeclock, and facility reference fields and do not use injected anomaly labels, injected anomaly categories, or injected anomaly dollars

### Requirement: Facility payroll variance threshold flag
The system SHALL calculate a facility payroll variance threshold flag that identifies records whose gross pay materially exceeds facility-relative payroll context by a configured variance ratio.

#### Scenario: Facility variance threshold is triggered
- **WHEN** a scored record's gross pay materially exceeds scoring-time-available facility-relative baseline pay context by the configured threshold
- **THEN** `threshold_facility_variance_flag` is set for that record

#### Scenario: Facility variance threshold stays interpretable
- **WHEN** the facility variance threshold flag is surfaced in evaluation or notebook outputs
- **THEN** the comparison can be explained as a manual facility-context pay variance rule rather than as a learned model score

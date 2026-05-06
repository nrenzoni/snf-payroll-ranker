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
- **WHEN** records violate payroll rules such as payment after termination, duplicate payment signature, gross pay less than or equal to zero for an active employee, negative net pay, net pay materially greater than gross pay, extreme overtime, or large manual adjustment
- **THEN** the corresponding rule flags and severity contributions are populated

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
The system SHALL combine rule, employee-history, peer-relative, ML, and dollar-impact components into a configurable final anomaly score.

#### Scenario: Hybrid score ranks review candidates
- **WHEN** scoring is complete
- **THEN** each employee-pay-period record has component scores, a final anomaly score, and a rank within its pay period suitable for review queue generation

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

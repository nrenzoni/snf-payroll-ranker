## MODIFIED Requirements

### Requirement: Temporal anomaly evaluation
The system SHALL evaluate SNF shift-level anomaly ranking using temporal validation rather than random row splits.

#### Scenario: Holdout periods are scored after training periods
- **WHEN** the evaluation pipeline runs
- **THEN** models, thresholds, score weights, and facility-normalization references are selected using earlier training or validation pay periods and evaluated on later pay periods

#### Scenario: Backtesting scores each period independently
- **WHEN** backtesting evaluation is enabled
- **THEN** each scored pay period uses only prior periods for feature baselines, model fitting, threshold selection, and score calibration where applicable

### Requirement: Review-queue metrics
The system SHALL report metrics aligned with SNF weekly payroll approval capacity.

#### Scenario: Precision and recall at approval budgets are reported
- **WHEN** predictions are evaluated
- **THEN** the results include precision@K and recall@K for configured administrator approval budgets such as top 10, 25, and 50 shift-level records per pay period or facility-pay-period

#### Scenario: Ranking quality is reported
- **WHEN** predictions are evaluated against injected labels
- **THEN** the results include rank-oriented metrics such as average anomaly rank or mean reciprocal rank where applicable

### Requirement: Cost-sensitive evaluation
The system SHALL estimate and report approval exposure captured by ranked SNF anomaly outputs.

#### Scenario: Exposure captured at K is calculated
- **WHEN** top-ranked shift-level records are evaluated
- **THEN** the system reports estimated exposure captured@K, injected dollars-at-risk captured@K for evaluation-only analysis, and the share of total injected anomaly dollar impact captured by the approval budget

### Requirement: Model and category comparison
The system SHALL compare manual threshold, deterministic rule-based, statistical, ML, and hybrid scoring approaches across overall, facility-level, and case-study category results.

#### Scenario: Model comparison table is produced
- **WHEN** evaluation completes
- **THEN** an output table compares candidate scoring methods using approval-budget, classification, review-volume, exposure, and dollar-impact metrics where applicable

#### Scenario: Error analysis identifies misses
- **WHEN** evaluation results are summarized
- **THEN** the notebook discusses false positives, false negatives, legitimate staffing or premium exceptions, subtle missed SNF anomalies, and practical improvements

### Requirement: Business review-budget evaluation notebook
The notebooks SHALL present approval-budget metrics including precision@K, recall@K, F1@K, PR-AUC, average anomaly rank, mean reciprocal rank, exposure captured@K, and dollars-at-risk captured@K.

#### Scenario: Approval-budget metrics are displayed
- **WHEN** the modeling, evaluation, or SNF case-study notebook runs
- **THEN** it displays approval-budget metrics for configured top-K budgets, including precision, recall, F1, PR-AUC, average anomaly rank, mean reciprocal rank, estimated exposure captured, synthetic dollars captured, and dollar capture rate

### Requirement: Hierarchical subgroup diagnostics
The system SHALL evaluate anomaly-ranking performance across hierarchical SNF payroll subgroups.

#### Scenario: SNF subgroup diagnostics are reported
- **WHEN** subgroup fields such as facility, unit, role, license type, shift type, pay-code category, approval status, tenure band, or anomaly category are available
- **THEN** diagnostic outputs report performance, volume, review demand, and dollar-impact summaries at overall and subgroup levels

## ADDED Requirements

### Requirement: Manual threshold baseline evaluation
The system SHALL evaluate automated SNF approval ranking against manually configured threshold baselines.

#### Scenario: Threshold baseline metrics are reported
- **WHEN** evaluation runs on scored SNF shift-level records
- **THEN** results report approval-budget and exposure metrics for gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance thresholds

#### Scenario: Threshold overflagging is summarized
- **WHEN** manual threshold baselines and automated ranking are compared
- **THEN** evaluation summarizes false positives, reviewed records required, missed high-exposure anomalies, and estimated exposure captured per reviewed record

### Requirement: SNF case-study evaluation
The system SHALL provide case-study-specific evaluation outputs for the implemented SNF scenarios.

#### Scenario: Overtime case-study metrics are produced
- **WHEN** overtime or double-shift staffing pressure scenarios are evaluated
- **THEN** outputs compare automated ranking against manual overtime and total-hours thresholds for review volume, precision, recall, exposure capture, and missed high-risk shifts

#### Scenario: Premium mismatch case-study metrics are produced
- **WHEN** premium pay or shift differential mismatch scenarios are evaluated
- **THEN** outputs compare automated ranking against manual gross-pay and premium-dollar thresholds for review volume, precision, recall, exposure capture, and missed unsupported premiums

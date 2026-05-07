## Purpose
Define temporal validation, review-budget metrics, and model comparison for payroll anomaly evaluation.
## Requirements
### Requirement: Temporal anomaly evaluation
The system SHALL evaluate anomaly detection using temporal validation rather than random row splits.

#### Scenario: Holdout periods are scored after training periods
- **WHEN** the evaluation pipeline runs
- **THEN** models, thresholds, and score weights are selected using earlier training or validation pay periods and evaluated on later pay periods

#### Scenario: Backtesting scores each period independently
- **WHEN** backtesting evaluation is enabled
- **THEN** each scored pay period uses only prior periods for feature baselines, model fitting, threshold selection, and score calibration where applicable

### Requirement: Review-queue metrics
The system SHALL report metrics aligned with payroll analyst review capacity.

#### Scenario: Precision and recall at review budgets are reported
- **WHEN** predictions are evaluated
- **THEN** the results include precision@K and recall@K for configured review budgets such as top 10, 25, and 50 records per pay period

#### Scenario: Ranking quality is reported
- **WHEN** predictions are evaluated against injected labels
- **THEN** the results include rank-oriented metrics such as average anomaly rank or mean reciprocal rank where applicable

### Requirement: Cost-sensitive evaluation
The system SHALL estimate and report dollars-at-risk captured by ranked anomaly outputs.

#### Scenario: Dollars captured at K is calculated
- **WHEN** top-ranked anomaly records are evaluated
- **THEN** the system reports dollars-at-risk captured@K and the share of total injected anomaly dollar impact captured by the review budget

### Requirement: Model and category comparison
The system SHALL compare rule-based, statistical, ML, and hybrid scoring approaches across overall and category-level results.

#### Scenario: Model comparison table is produced
- **WHEN** evaluation completes
- **THEN** an output table compares candidate scoring methods using review-queue, classification, and dollar-impact metrics where applicable

#### Scenario: Error analysis identifies misses
- **WHEN** evaluation results are summarized
- **THEN** the notebook discusses false positives, false negatives, legitimate exceptions, subtle missed anomalies, and practical improvements

### Requirement: Business review-budget evaluation notebook
The notebooks SHALL present review-budget metrics including precision@K, recall@K, F1@K, PR-AUC, average anomaly rank, mean reciprocal rank, and dollars-at-risk captured@K.

#### Scenario: Review-budget metrics are displayed
- **WHEN** the modeling, evaluation, and error analysis notebook runs
- **THEN** it displays review-budget metrics for configured top-K budgets, including precision, recall, F1, PR-AUC, average anomaly rank, mean reciprocal rank, dollars captured, and dollar capture rate

### Requirement: Temporal validation explanation
The notebooks SHALL explain temporal validation and SHALL avoid endorsing random split framing. A notebook MAY show random row splits only as an explicitly labeled anti-pattern when it is immediately compared against temporal validation.

#### Scenario: Temporal validation is documented
- **WHEN** a reviewer reads the modeling and evaluation notebook
- **THEN** the notebook explains that payroll scoring is evaluated over time using prior periods and later periods rather than random row splits

#### Scenario: Random split anti-pattern is demonstrated
- **WHEN** the modeling and evaluation notebook demonstrates random train/test splitting
- **THEN** the random split is labeled as an anti-pattern and compared against temporal validation rather than presented as an accepted evaluation method

### Requirement: Backtesting and category error analysis notebook coverage
The notebooks SHALL show backtest-by-period results and category-level error analysis.

#### Scenario: Backtest and category tables are displayed
- **WHEN** the modeling, evaluation, and error analysis notebook runs
- **THEN** it displays period-level backtest metrics and anomaly-category error analysis, including missed anomalies and false positives where available

### Requirement: Cost-aware interpretation
The notebooks SHALL explain which review budgets capture the most dollars at risk and where precision declines as review queue size increases.

#### Scenario: Review budget trade-off is interpreted
- **WHEN** evaluation metrics are displayed
- **THEN** the notebook includes narrative interpreting dollar capture, precision changes, and the practical cost-aware trade-off of reviewing more records

### Requirement: Rolling-origin validation
The system SHALL evaluate payroll anomaly ranking across multiple temporal origins when enough pay periods are available.

#### Scenario: Multiple temporal origins are summarized
- **WHEN** rolling-origin evaluation runs
- **THEN** each origin trains or calibrates on earlier periods, validates on subsequent periods, tests on later periods, and reports review-budget metrics by origin

### Requirement: Validation-based operating-point selection
The system SHALL select thresholds or configurable score weights using validation periods before reporting test-period performance.

#### Scenario: Test metrics use validation-selected settings
- **WHEN** thresholds or hybrid weights are tuned
- **THEN** tuning decisions are made on validation periods and the chosen settings are then evaluated on later test periods

### Requirement: Evaluation stability and leakage checks
The system SHALL report stability or uncertainty summaries and explicit leakage checks for anomaly evaluation.

#### Scenario: Stability summaries are reported
- **WHEN** evaluation results are produced across seeds, origins, or review budgets
- **THEN** the output includes stability summaries such as score distribution changes, queue overlap, metric ranges, or confidence intervals where applicable

#### Scenario: Leakage checks are reported
- **WHEN** evaluation runs on synthetic labels
- **THEN** the output verifies that label columns and injected anomaly dollar impacts are not used as scoring features or analyst queue inputs

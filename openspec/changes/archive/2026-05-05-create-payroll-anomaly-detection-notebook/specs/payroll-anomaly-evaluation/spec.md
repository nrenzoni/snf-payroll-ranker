## ADDED Requirements

### Requirement: Temporal anomaly evaluation
The system SHALL evaluate anomaly detection using temporal validation rather than random row splits.

#### Scenario: Holdout periods are scored after training periods
- **WHEN** the evaluation pipeline runs
- **THEN** models and thresholds are selected using earlier pay periods and evaluated on later pay periods

#### Scenario: Backtesting scores each period independently
- **WHEN** backtesting evaluation is enabled
- **THEN** each scored pay period uses only prior periods for feature baselines and model fitting where applicable

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

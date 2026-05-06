## ADDED Requirements

### Requirement: Business review-budget evaluation notebook
The notebooks SHALL present review-budget metrics including precision@K, recall@K, F1@K, PR-AUC, average anomaly rank, mean reciprocal rank, and dollars-at-risk captured@K.

#### Scenario: Review-budget metrics are displayed
- **WHEN** the modeling, evaluation, and error analysis notebook runs
- **THEN** it displays review-budget metrics for configured top-K budgets, including precision, recall, F1, PR-AUC, average anomaly rank, mean reciprocal rank, dollars captured, and dollar capture rate

### Requirement: Temporal validation explanation
The notebooks SHALL explain temporal validation and SHALL avoid random split framing.

#### Scenario: Temporal validation is documented
- **WHEN** a reviewer reads the modeling and evaluation notebook
- **THEN** the notebook explains that payroll scoring is evaluated over time using prior periods and later periods rather than random row splits

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

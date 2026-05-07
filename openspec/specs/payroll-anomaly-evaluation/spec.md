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

### Requirement: Uncertainty quality evaluation
The system SHALL evaluate whether uncertainty scores provide useful context for synthetic payroll anomaly ranking using evaluation-labeled historical records.

#### Scenario: Precision is reported by uncertainty bucket
- **WHEN** evaluation-labeled scored records include uncertainty buckets
- **THEN** the evaluation output reports precision or anomaly rate by Low, Medium, and High uncertainty buckets

#### Scenario: Risk-coverage curve is reported
- **WHEN** evaluation-labeled scored records include uncertainty scores
- **THEN** the evaluation output reports risk-coverage results showing model performance as increasingly uncertain records are excluded or included

#### Scenario: Abstention impact is reported
- **WHEN** an uncertainty threshold or top uncertain fraction is applied for analysis
- **THEN** the evaluation output reports how precision or review quality changes when high-uncertainty records are abstained from automated prioritization analysis

#### Scenario: Existing review-budget metrics remain available
- **WHEN** uncertainty evaluation is generated
- **THEN** existing precision@K, recall@K, dollars captured@K, model comparison, and category error analysis outputs remain available across historical evaluation periods

### Requirement: Expected-pay interval evaluation
The system SHALL evaluate expected gross-pay interval behavior in evaluation-labeled synthetic outputs.

#### Scenario: Interval coverage is reported for normal records
- **WHEN** expected gross-pay interval fields and evaluation labels are available
- **THEN** the evaluation output reports how often non-anomalous records fall within the expected p10 to p90 interval

#### Scenario: Anomaly exceedance is reported
- **WHEN** expected gross-pay p90 and evaluation labels are available
- **THEN** the evaluation output reports how often synthetic anomalies exceed expected p90 and summarizes excess over p90

#### Scenario: Interval width is summarized
- **WHEN** expected gross-pay interval fields are available
- **THEN** the evaluation output summarizes interval width overall and by uncertainty bucket

### Requirement: Latest queue and historical metrics separation
The system SHALL keep operational latest-period queue behavior separate from historical evaluation metrics.

#### Scenario: Analyst queue is latest-period while metrics remain historical
- **WHEN** pipeline outputs include an analyst-safe review queue and evaluation metrics
- **THEN** the analyst-safe queue contains latest-period records only and evaluation metrics continue to summarize historical scored periods where appropriate

### Requirement: Uncertainty evaluation notebook coverage
The notebooks SHALL explain how uncertainty diagnostics fit into the payroll anomaly review workflow.

#### Scenario: Modeling and evaluation notebook shows uncertainty diagnostics
- **WHEN** the modeling, evaluation, and error analysis notebook runs
- **THEN** it displays uncertainty component summaries, expected gross-pay interval diagnostics, precision by uncertainty bucket, and a risk-coverage table or chart

#### Scenario: Production monitoring notebook documents uncertainty limits
- **WHEN** the production monitoring and deployment path notebook is reviewed
- **THEN** it documents uncertainty monitoring, calibration uncertainty as dependent on future analyst feedback labels, OOD monitoring for pay-code drift, and limitations of synthetic-label uncertainty evaluation

### Requirement: Internal Bayesian-style review-budget diagnostics
The system SHALL provide internal Bayesian-style diagnostics for review-budget performance using synthetic evaluation labels.

#### Scenario: Review-budget uncertainty is summarized
- **WHEN** internal review-budget diagnostics run
- **THEN** outputs summarize uncertainty for precision, recall, dollar capture, and queue yield at configured review budgets

### Requirement: Hierarchical subgroup diagnostics
The system SHALL evaluate anomaly-ranking performance across hierarchical payroll subgroups.

#### Scenario: Subgroup diagnostics are reported
- **WHEN** subgroup fields such as department, location, job family, pay type, tenure band, or anomaly category are available
- **THEN** diagnostic outputs report performance, volume, and dollar-impact summaries at overall and subgroup levels

### Requirement: Expected-pay calibration diagnostics
The system SHALL evaluate calibration of expected-pay estimates and intervals.

#### Scenario: Expected-pay calibration is reported
- **WHEN** expected-pay predictions, intervals, and evaluation labels are available
- **THEN** outputs report interval coverage, exceedance behavior, residual distribution, and calibration quality overall and by relevant subgroup

### Requirement: Robustness and perturbation diagnostics
The system SHALL evaluate whether anomaly-ranking behavior is stable under reproducible perturbations.

#### Scenario: Perturbation results are summarized
- **WHEN** diagnostic perturbations vary seeds, scenario parameters, thresholds, review budgets, or input noise
- **THEN** outputs summarize metric stability, rank stability, queue overlap, and sensitivity to perturbations

### Requirement: Monte Carlo queue capacity simulation
The system SHALL simulate review-queue capacity outcomes across repeated synthetic scenarios.

#### Scenario: Queue capacity distribution is reported
- **WHEN** Monte Carlo queue capacity simulation runs
- **THEN** outputs report distributions for workload, anomaly yield, dollar capture, missed dollar impact, and capacity shortfall at configured review budgets

### Requirement: Internal statistical notebook coverage
The notebooks SHALL cover internal statistical diagnostics for synthetic payroll anomaly evaluation.

#### Scenario: Internal statistical diagnostics are shown
- **WHEN** internal diagnostic notebooks run
- **THEN** they display review-budget uncertainty, subgroup diagnostics, expected-pay calibration, perturbation robustness, and Monte Carlo queue capacity results

### Requirement: Multi-regime component superiority diagnostics
The system SHALL compare anomaly score components across multiple synthetic diagnostic regimes.

#### Scenario: Component performance varies by regime
- **WHEN** diagnostic scenarios represent different anomaly mixes, drift patterns, or subgroup concentrations
- **THEN** outputs compare component-level and hybrid ranking performance by regime and identify where components are superior or weaker

### Requirement: Informative internal diagnostic plot inputs
The system SHALL produce internal diagnostic outputs suitable for informative plots.

#### Scenario: Plot inputs are produced
- **WHEN** internal diagnostics run
- **THEN** outputs include tidy data for score distributions, calibration curves, subgroup summaries, queue trade-offs, component comparisons, and temporal contrasts

### Requirement: Scenario-dependent queue simulation diagnostics
The system SHALL evaluate review-queue capacity under scenario-dependent synthetic conditions.

#### Scenario: Queue simulation is stratified by scenario
- **WHEN** queue simulation runs across diagnostic scenarios
- **THEN** outputs report capacity, yield, dollar capture, and missed-risk metrics separately by scenario

### Requirement: Dense internal diagnostic plot inputs
The system SHALL produce dense internal diagnostic plot inputs for high-signal exploratory evaluation.

#### Scenario: Dense plot data is available
- **WHEN** dense diagnostics are enabled
- **THEN** outputs include sufficiently granular records for paired plots, subgroup facets, temporal panels, threshold curves, component contrasts, and queue-capacity distributions

### Requirement: Adaptive threshold-demand queue diagnostics
The system SHALL evaluate how adaptive thresholds affect review demand and anomaly yield.

#### Scenario: Adaptive threshold demand is reported
- **WHEN** adaptive threshold diagnostics run
- **THEN** outputs report threshold levels, queue sizes, anomaly yield, dollar capture, missed-risk estimates, and capacity exceedance across periods or scenarios

### Requirement: Plot-usefulness validation
The system SHALL validate whether internal diagnostic plots provide useful signal for evaluation decisions.

#### Scenario: Plot usefulness is assessed
- **WHEN** internal diagnostic plot outputs are generated
- **THEN** validation outputs identify whether plots contain adequate variation, contrasts, sample sizes, and non-empty series for interpretation

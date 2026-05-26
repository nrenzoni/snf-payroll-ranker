## Purpose
Define temporal validation, review-budget metrics, and model comparison for payroll anomaly evaluation.
## Requirements
### Requirement: Temporal anomaly evaluation
The system SHALL evaluate employee-pay-cycle ranking with temporally ordered validation as the active default and SHALL treat random row splits as debugging-only anti-pattern checks.

#### Scenario: Holdout periods are scored after training periods
- **WHEN** the active evaluation pipeline runs
- **THEN** models, thresholds, group weighting, and calibration settings are selected using earlier payroll cycles and evaluated on later payroll cycles

#### Scenario: Backtesting scores each period independently
- **WHEN** backtesting evaluation is enabled
- **THEN** each scored payroll cycle uses only prior cycles for feature baselines, model fitting, threshold selection, and score calibration where applicable

### Requirement: Review-queue metrics
The system SHALL report employee-pay-cycle grouped ranking metrics that measure review value within facility-cycle queues and aggregate those results for active research and production-candidacy decisions.

#### Scenario: Grouped top-k metrics are reported
- **WHEN** active predictions are evaluated
- **THEN** the results include top-k queue metrics computed within facility-cycle groups and aggregated across groups using explicit project-defined aggregation schemes

#### Scenario: Grouped percent-budget metrics are reported
- **WHEN** active employee-pay-cycle predictions are evaluated using percentage review budgets
- **THEN** the results include grouped queue metrics computed from a configured share of each facility-cycle group reviewed
- **AND** the budget-to-count conversion specifies the rounding rule and any minimum reviewed-record behavior used for reproducible evaluation

#### Scenario: Ranking quality is reported
- **WHEN** active predictions are evaluated against available labels
- **THEN** the results include rank-oriented metrics such as precision@K, recall@K, mean reciprocal rank, and other grouped ranking metrics selected for the active employee-pay-cycle program

### Requirement: Production-candidacy validation
The active evaluation program SHALL determine whether an employee-pay-cycle scoring approach is promotable into later production work.

#### Scenario: Candidate methods are judged on deployment-relevant evidence
- **WHEN** an active method is summarized after Phase 1 evaluation
- **THEN** the evaluation reports whether the method meets the project's current criteria for temporal generalization, facility generalization, review-budget ranking value, uncertainty behavior, and explanation readiness

### Requirement: Cost-sensitive evaluation
The system SHALL estimate and report approval exposure captured by ranked payroll anomaly outputs.

#### Scenario: Exposure captured at K is calculated
- **WHEN** top-ranked employee-pay-cycle records are evaluated
- **THEN** the system reports estimated exposure captured@K, injected dollars-at-risk captured@K for evaluation-only analysis, and the share of total injected anomaly dollar impact captured by the approval budget

#### Scenario: Exposure captured at percent budget is calculated
- **WHEN** top-ranked employee-pay-cycle records are evaluated using percentage review budgets
- **THEN** the system reports estimated exposure captured, injected dollars-at-risk captured, and the share of total injected anomaly dollar impact captured at each configured review-budget percentage

### Requirement: Model and category comparison
The system SHALL compare manual threshold, deterministic rule-based, statistical, ML, and hybrid scoring approaches across overall, facility-level, and case-study category results.

#### Scenario: Model comparison table is produced
- **WHEN** evaluation completes
- **THEN** an output table compares candidate scoring methods using approval-budget, classification, review-volume, exposure, and dollar-impact metrics where applicable

#### Scenario: Error analysis identifies misses
- **WHEN** evaluation results are summarized
- **THEN** the notebook discusses false positives, false negatives, legitimate staffing or premium exceptions, subtle missed SNF anomalies, and practical improvements

### Requirement: Business review-budget evaluation notebook
The active employee-pay-cycle notebook SHALL present percent-based review-budget metrics including precision, recall, F1, PR-AUC, average anomaly rank, mean reciprocal rank, exposure captured, and dollars-at-risk captured where those metrics apply to the active formulation.

#### Scenario: Approval-budget metrics are displayed
- **WHEN** the active employee-pay-cycle notebook runs
- **THEN** it displays review-budget metrics for configured percentages of each facility-pay-period residual queue reviewed, including applicable precision, recall, F1, PR-AUC, average anomaly rank, mean reciprocal rank, estimated exposure captured, synthetic dollars captured, and dollar capture rate
- **AND** the notebook labels those budgets as shares of each facility-pay-period residual queue rather than as absolute top-K cutoffs

### Requirement: Temporal validation explanation
The active employee-pay-cycle notebook SHALL explain temporal validation and SHALL avoid endorsing random split framing. The notebook MAY show random row splits only as an explicitly labeled anti-pattern when it is immediately compared against temporal validation.

#### Scenario: Temporal validation is documented
- **WHEN** a reviewer reads the active employee-pay-cycle notebook
- **THEN** the notebook explains that payroll scoring is evaluated over time using prior periods and later periods rather than random row splits

#### Scenario: Random split anti-pattern is demonstrated
- **WHEN** the active employee-pay-cycle notebook demonstrates random train/test splitting
- **THEN** the random split is labeled as an anti-pattern and compared against temporal validation rather than presented as an accepted evaluation method

### Requirement: Backtesting and category error analysis notebook coverage
The active employee-pay-cycle notebook SHALL show backtest-by-period results and category-level error analysis.

#### Scenario: Backtest and category tables are displayed
- **WHEN** the active employee-pay-cycle notebook runs
- **THEN** it displays period-level backtest metrics and anomaly-category error analysis, including missed anomalies and false positives where available

### Requirement: Cost-aware interpretation
The active employee-pay-cycle notebook SHALL explain which review budgets capture the most dollars at risk and where precision declines as review queue size increases.

#### Scenario: Review budget trade-off is interpreted
- **WHEN** evaluation metrics are displayed in the active notebook
- **THEN** the notebook includes narrative interpreting dollar capture, precision changes, and the practical cost-aware trade-off of reviewing a larger share of each residual queue

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
- **THEN** existing review-budget metrics, model comparison, and category error analysis outputs remain available across historical evaluation periods for the active budget definition in use

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
The active employee-pay-cycle notebook SHALL explain how uncertainty diagnostics fit into the payroll anomaly review workflow.

#### Scenario: Active notebook shows uncertainty diagnostics
- **WHEN** the active employee-pay-cycle notebook runs
- **THEN** it displays uncertainty component summaries, expected gross-pay interval diagnostics, precision by uncertainty bucket, and a risk-coverage table or chart

#### Scenario: Active notebook documents uncertainty limits
- **WHEN** the production-readiness sections of the active employee-pay-cycle notebook are reviewed
- **THEN** they document uncertainty monitoring, calibration uncertainty as dependent on future analyst feedback labels, OOD monitoring for pay-code drift, and limitations of synthetic-label uncertainty evaluation

### Requirement: Internal Bayesian-style review-budget diagnostics
The system SHALL provide internal Bayesian-style diagnostics for review-budget performance using synthetic evaluation labels.

#### Scenario: Review-budget uncertainty is summarized
- **WHEN** internal review-budget diagnostics run
- **THEN** outputs summarize uncertainty for precision, recall, dollar capture, and queue yield at configured review budgets

### Requirement: Hierarchical subgroup diagnostics
The system SHALL evaluate anomaly-ranking performance across hierarchical SNF payroll subgroups.

#### Scenario: SNF subgroup diagnostics are reported
- **WHEN** subgroup fields such as facility, unit, role, license type, shift type, pay-code category, approval status, tenure band, or anomaly category are available
- **THEN** diagnostic outputs report performance, volume, review demand, and dollar-impact summaries at overall and subgroup levels

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
Notebook-owned internal diagnostics SHALL cover internal statistical diagnostics for synthetic payroll anomaly evaluation.

#### Scenario: Internal statistical diagnostics are shown
- **WHEN** internal diagnostic workflows run
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

#### Scenario: Flat budget curves are flagged as uninformative
- **WHEN** grouped review-budget plots are generated for the active employee-pay-cycle notebook
- **THEN** validation outputs identify when configured review budgets saturate most facility-cycle groups, leaving little or no contrast between budget levels or scoring methods
- **AND** they report enough supporting context such as grouped residual queue sizes, effective reviewed counts, or dominant saturation thresholds to explain why the plots are not decision-useful

### Requirement: Technical ML value and ablation notebook
The active employee-pay-cycle notebook SHALL include sections that demonstrate incremental residual-formulation value using evaluation-safe synthetic labels and temporal validation framing.

#### Scenario: Ablation section compares method ladder
- **WHEN** the active employee-pay-cycle notebook runs
- **THEN** its ablation studies section compares classifier, cost-sensitive classifier, regressor, expected-value, and learning-to-rank methods on the residual universe using residual review-budget metrics, PR-AUC where applicable, rank metrics, dollar capture, reviewer yield, and utility metrics where available

#### Scenario: Ablation section explains complexity value
- **WHEN** a reviewer reads the ablation studies section of the active employee-pay-cycle notebook
- **THEN** narrative text explains what each residual formulation adds, where complexity improves residual review prioritization, and where simpler methods remain useful

### Requirement: Incremental value plots
The active employee-pay-cycle notebook SHALL include plot-ready evidence that makes incremental method value observable inside the main narrative or technical appendix.

#### Scenario: Method-complexity visuals render
- **WHEN** the active employee-pay-cycle notebook runs
- **THEN** it renders visuals or tables such as residual dollars caught by review-budget percentage, rule-missed severe recall by review-budget percentage, residual NDCG by review-budget percentage, reviewer yield by review-budget percentage, net utility by review-budget percentage, and compact formulation-comparison summaries

#### Scenario: Temporal and uncertainty context remain visible
- **WHEN** the active employee-pay-cycle notebook reports ablation or model comparison results
- **THEN** it includes temporal validation context and uncertainty, stability, or risk-coverage diagnostics where active pipeline outputs support them

### Requirement: Utility-aware employee-cycle evaluation
The employee-pay-cycle evaluation workflow SHALL report business-value metrics based on an explicit `net_utility` label in addition to anomaly-capture and dollar-capture metrics.

#### Scenario: Net utility is reported at review budgets
- **WHEN** employee-pay-cycle review-budget metrics are computed
- **THEN** the outputs include utility-aware summaries such as net utility captured at K, average utility per reviewed employee-pay-cycle, or equivalent project-defined business-value metrics sourced from `net_utility`

#### Scenario: Utility remains evaluation-only
- **WHEN** `net_utility` is available in the scored evaluation frame
- **THEN** it is treated as evaluation-only business truth rather than as an analyst-facing queue field or model input

### Requirement: Residual-universe queue metrics
The employee-pay-cycle evaluation workflow SHALL compute primary notebook metrics only on residual records within facility-by-payroll-cycle groups.

#### Scenario: Residual metrics use gated scoring universe
- **WHEN** the notebook reports main queue results
- **THEN** ranking and review-budget metrics are computed only on employee-pay-cycle records not flagged by critical hard rules
- **AND** the ranking groups are facility by payroll cycle

#### Scenario: Primary residual metrics are reported
- **WHEN** residual review-budget metrics are computed
- **THEN** the outputs include residual NDCG@K, rule-missed severe recall@K, residual dollars caught@K, reviewer yield@K, and incremental utility@K or equivalent project-defined formulations of those metrics

### Requirement: Training-universe and label ablations
The active employee-pay-cycle notebook SHALL test whether residual-ranking conclusions depend on label choice or training universe definition.

#### Scenario: Training-universe ablation is shown
- **WHEN** the ablation studies section is reviewed
- **THEN** it compares training on all records, training on residual records only, and training on all records with hard-rule flag features while always scoring on the residual universe

#### Scenario: Label ablation is shown
- **WHEN** the ablation studies section is reviewed
- **THEN** it compares formulations trained or evaluated against binary issue, dollar impact, graded relevance, utility-aware, observed historical, or latent truth labels where those comparisons are supported by active outputs

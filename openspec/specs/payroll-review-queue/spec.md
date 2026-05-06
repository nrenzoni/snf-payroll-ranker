## Purpose
Define the analyst-facing review queue and notebook deliverables for payroll anomaly review.

## Requirements

### Requirement: Analyst-ready review queue
The system SHALL produce a ranked review queue of employee-pay-period records for payroll analyst review.

#### Scenario: Review queue fields are populated
- **WHEN** review queue generation runs
- **THEN** each queue row includes rank, synthetic employee identifier, pay period, final score, risk category, primary reason, secondary reason, gross pay, expected gross pay or baseline, difference from expected, peer context, rule flags, and dollars at risk

#### Scenario: Review queue is sorted by priority
- **WHEN** records are exported for review
- **THEN** records are sorted by pay period and descending final anomaly score or configured review priority

### Requirement: Human-readable anomaly explanations
The system SHALL generate concise explanations for flagged records using rule flags, score drivers, historical baselines, peer comparisons, and dollar impact.

#### Scenario: Explanation includes business context
- **WHEN** a record is flagged for a gross pay, overtime, duplicate, lifecycle, deduction, or adjustment anomaly
- **THEN** the explanation describes why the record is unusual in payroll terms rather than only reporting a model score

### Requirement: Business deliverable notebook sections
The notebook SHALL include business, technical, evaluation, and production-readiness sections needed for a presentable, polished deliverable.

#### Scenario: Notebook narrative is complete
- **WHEN** a reviewer reads the notebook
- **THEN** it includes an executive summary, privacy disclaimer, problem framing, anomaly taxonomy, synthetic data generation, EDA, feature engineering, baselines, model comparison, hybrid scoring, evaluation, review queue, error analysis, production architecture, monitoring and retraining, limitations, and future improvements

### Requirement: Production readiness discussion
The notebook SHALL describe how the workflow would operate in production without claiming integrations that were not built.

#### Scenario: Production architecture is documented
- **WHEN** the production section is reviewed
- **THEN** it describes an intended flow from payroll, HRIS, and timekeeping sources through validation, feature engineering, scoring, analyst review, feedback, monitoring, and retraining

#### Scenario: Monitoring metrics are documented
- **WHEN** monitoring guidance is reviewed
- **THEN** it includes metrics such as alert count per cycle, alert acceptance rate, false positive rate from reviews, dollars at risk flagged and confirmed, feature drift, score drift, alert concentration, latency, and data freshness

### Requirement: Multi-notebook business case study sequence
The repository SHALL include a Jupytext percent-format notebook sequence covering problem framing, data maturity, feature engineering, baselines, modeling, evaluation, error analysis, review queue explainability, thresholds, and production monitoring.

#### Scenario: Required notebooks exist
- **WHEN** the change is implemented
- **THEN** the repository includes `notebooks/01_problem_framing_and_data_maturity.py`, `notebooks/02_feature_engineering_and_baselines.py`, `notebooks/03_modeling_evaluation_and_error_analysis.py`, `notebooks/04_review_queue_explainability_and_thresholds.py`, and `notebooks/05_production_monitoring_and_deployment_path.py`

### Requirement: Executive takeaway and proof summary sections
Each notebook SHALL begin with a short executive takeaway and end with a concise what-this-proves summary.

#### Scenario: Notebook narrative has business framing
- **WHEN** a reviewer opens any notebook in the sequence
- **THEN** the first section contains an executive takeaway and the final section summarizes what the notebook proves

### Requirement: Analyst-readable review queue and case cards
The notebooks SHALL show an analyst-readable review queue and compact case cards for selected records using review-safe language.

#### Scenario: Case cards include review context
- **WHEN** the review queue, explainability, and thresholds notebook runs
- **THEN** it displays selected case cards with rank, employee identifier, pay period, risk category, primary reason, secondary reason, expected gross pay, actual gross pay, difference from expected, peer context, dollars at risk, and an explanation that avoids fraud labeling

### Requirement: Practical payroll analyst workflow
The notebooks SHALL demonstrate top-K or threshold selection, expected queue size per pay period, high/medium/low risk categories, analyst next actions, conceptual feedback capture, and an operating model for triage, approval, escalation, and feedback.

#### Scenario: Review workflow is documented
- **WHEN** a reviewer reads the review queue notebook
- **THEN** the notebook explains how analysts choose a review budget or threshold, triage records by risk category, review evidence, approve or escalate exceptions, and capture feedback for future calibration

### Requirement: Production monitoring and deployment path narrative
The notebooks SHALL document a realistic deployment path without claiming implemented live integrations.

#### Scenario: Deployment path is documented
- **WHEN** the production monitoring notebook is reviewed
- **THEN** it describes payroll, HRIS, and timekeeping extracts flowing through validation, feature generation, scoring, review queue export, analyst feedback, monitoring, and retraining without claiming those integrations are implemented

### Requirement: Monitoring, retraining, limitations, and risks
The notebooks SHALL include monitoring metrics, retraining triggers, and limitations appropriate for payroll anomaly ranking.

#### Scenario: Production risk controls are listed
- **WHEN** the production monitoring notebook is reviewed
- **THEN** it includes alert count per cycle, alert acceptance rate, false positive rate from reviews, dollars at risk flagged and confirmed, feature drift, score drift, alert concentration by department/location/job family, latency, data freshness, failed validation count, retraining triggers, and limitations of synthetic labels and unsupervised scoring

### Requirement: Required business visuals
The notebooks SHALL include clean visuals or tables for payroll trend, gross pay distribution, overtime distribution, department payroll heatmap or table, score distribution, precision@K by review budget, dollars captured@K by review budget, model comparison, backtest metrics over time, and selected employee history for a flagged record.

#### Scenario: Required visuals render from synthetic outputs
- **WHEN** the notebook sequence is run on a clean checkout
- **THEN** the required visuals or tables render using synthetic data and generated evaluation outputs
- **AND** notebooks that render LetsPlot visuals call `LetsPlot.setup_html()` before displaying those charts
- **AND** continuous distribution visuals use binned histograms or equivalent aggregation rather than one bar per raw numeric value

### Requirement: README notebook sequence documentation
The README SHALL list the notebook sequence and briefly explain the purpose of each notebook.

#### Scenario: README links notebook story
- **WHEN** a reviewer reads `README.md`
- **THEN** it describes the notebook sequence and identifies which notebook covers each major part of the payroll anomaly ranking case study

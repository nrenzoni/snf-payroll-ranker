## Purpose
Define the analyst-facing review queue and notebook deliverables for payroll anomaly review.
## Requirements
### Requirement: Analyst-ready review queue
The system SHALL produce an employee-pay-cycle ranked review queue from the active payroll ranking library instead of defining the active queue around deprecated shift-level SNF approval outputs.

#### Scenario: Active queue fields are populated
- **WHEN** active review queue generation runs
- **THEN** each queue row includes the employee-pay-cycle identifier, employee identifier, facility, payroll cycle, active priority score, risk or relevance context, explanation context, and any review-safe fields required by the active employee-pay-cycle workflow

#### Scenario: Active queue is sorted by group priority
- **WHEN** active records are exported for review
- **THEN** employee-pay-cycle rows are ordered within their active queue grouping by descending configured priority score

#### Scenario: Legacy shift-level queue fields are not treated as active requirements
- **WHEN** the active queue contract is documented
- **THEN** deprecated shift-level SNF approval queue fields are identified as legacy historical material rather than active acceptance criteria

### Requirement: Queue contract follows active runtime direction
The active review queue SHALL be derived from the active employee-pay-cycle runtime and SHALL NOT depend on deprecated shift-level hybrid queue generation.

#### Scenario: Active queue excludes deprecated runtime dependency
- **WHEN** the active queue contract is implemented or documented
- **THEN** it does not require deprecated shift-level queue modules, legacy notebook outputs, or historical hybrid score fields to operate

### Requirement: Human-readable anomaly explanations
The system SHALL generate concise administrator-readable explanations for flagged SNF shift-level records using rule flags, score drivers, schedule/timeclock context, premium eligibility, historical baselines, peer comparisons, and estimated exposure.

#### Scenario: Explanation includes SNF approval context
- **WHEN** a record is flagged for overtime, double-shift, rest-gap, paid-vs-scheduled, shift differential, weekend premium, duplicate premium, lifecycle, deduction, or payroll amount anomaly
- **THEN** the explanation describes what the administrator should verify in SNF operational terms rather than only reporting a model score

### Requirement: Business deliverable notebook sections
The notebook SHALL include business, technical, evaluation, case-study, approval workflow, and production-readiness sections needed for a presentable SNF payroll approval deliverable.

#### Scenario: Notebook narrative is complete
- **WHEN** a reviewer reads the notebook
- **THEN** it includes an executive summary, privacy disclaimer, SNF payroll approval problem framing, anomaly taxonomy, synthetic data generation, schedule/timeclock/payroll schema, EDA, feature engineering, manual threshold baselines, model comparison, hybrid scoring, evaluation, approval queue, case studies, error analysis, production architecture, monitoring and retraining, limitations, and future scenario roadmap

### Requirement: Production readiness discussion
The notebook SHALL describe how the workflow would operate in production without claiming integrations that were not built.

#### Scenario: Production architecture is documented
- **WHEN** the production section is reviewed
- **THEN** it describes an intended flow from payroll, schedule, timeclock, HR lifecycle, and facility reference extracts through validation, feature engineering, scoring, pre-approval queue export, administrator review, feedback, monitoring, and retraining

#### Scenario: Monitoring metrics are documented
- **WHEN** monitoring guidance is reviewed
- **THEN** it includes metrics such as exception count per payroll cycle, approval queue yield, false positive rate from feedback, estimated exposure flagged and confirmed, feature drift, score drift, alert concentration by facility/unit/role/shift, latency, data freshness, failed validation count, and threshold-baseline drift

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
The notebooks SHALL show an administrator-readable approval queue and compact case cards for selected records using review-safe language.

#### Scenario: Case cards include approval context
- **WHEN** the review queue, explainability, thresholds, or SNF case-study notebook runs
- **THEN** it displays selected case cards with rank, employee identifier, facility, unit, role, shift date, shift type, risk category, recommended action, source to check, primary reason, secondary reason, expected gross pay, actual gross pay, scheduled hours, worked hours, difference from expected, premium context, estimated exposure, and an explanation that avoids fraud labeling

### Requirement: Practical payroll analyst workflow
The notebooks SHALL demonstrate administrator weekly payroll approval workflow including top-K or threshold selection, expected queue size per pay period or facility, approval risk categories, next actions, conceptual feedback capture, and an operating model for confirm, approve, escalate, and feedback.

#### Scenario: Approval workflow is documented
- **WHEN** a reviewer reads the review queue or SNF case-study notebook
- **THEN** the notebook explains how administrators choose a review budget or threshold, triage records by approval risk category, check schedule/timeclock/pay-code evidence, approve known staffing exceptions, escalate questionable records, and capture feedback for future calibration

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
The notebooks SHALL include clean visuals or tables for SNF payroll trend, shift-level gross pay distribution, overtime distribution, premium pay distribution, facility payroll heatmap or table, score distribution, threshold baseline comparison, precision@K by approval budget, exposure captured@K by approval budget, model comparison, backtest metrics over time, and selected employee or shift history for a flagged record.

#### Scenario: Required visuals render from synthetic SNF outputs
- **WHEN** the notebook sequence is run on a clean checkout
- **THEN** the required visuals or tables render using synthetic SNF data and generated evaluation outputs
- **AND** notebooks that render LetsPlot visuals call `LetsPlot.setup_html()` before displaying those charts
- **AND** continuous distribution visuals use binned histograms or equivalent aggregation rather than one bar per raw numeric value

### Requirement: README notebook sequence documentation
The README SHALL list the notebook sequence and briefly explain the purpose of each notebook.

#### Scenario: README links notebook story
- **WHEN** a reviewer reads `README.md`
- **THEN** it describes the notebook sequence and identifies which notebook covers each major part of the payroll anomaly ranking case study

### Requirement: Separate analyst and evaluation review queues
The system SHALL produce an administrator-safe approval queue for operational triage and a separate evaluation-labeled approval queue for synthetic performance analysis.

#### Scenario: Administrator queue excludes evaluation labels
- **WHEN** administrator approval queue generation runs
- **THEN** the queue excludes injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts

#### Scenario: Evaluation queue includes labels for analysis
- **WHEN** evaluation-labeled queue generation runs against synthetic SNF data
- **THEN** the queue includes injected labels and injected anomaly dollar impacts only for error analysis and metric interpretation

### Requirement: Component contribution context
The system SHALL include enough component-score and reason-code context for analysts to understand why a record was prioritized without exposing evaluation truth.

#### Scenario: Review context is explainable
- **WHEN** a record appears in the analyst-safe queue
- **THEN** the row includes reason codes, risk category, estimated exposure or dollars-at-risk estimate, expected-vs-actual context, peer context, and relevant component scores or score-driver fields

### Requirement: Latest-period uncertainty-aware analyst review queue
The system SHALL surface risk and uncertainty together in an administrator-safe SNF approval queue for the latest pay period only unless a case-study explicitly requests historical evaluation output.

#### Scenario: Approval queue is limited to latest pay period
- **WHEN** administrator approval queue generation runs on scored SNF payroll records spanning multiple pay periods
- **THEN** the administrator-safe queue includes only records from the latest available pay period by default

#### Scenario: Approval queue includes risk and uncertainty fields
- **WHEN** administrator approval queue generation runs on scored SNF payroll records
- **THEN** each administrator-safe queue row includes final approval exception score, uncertainty bucket, composite uncertainty score, primary uncertainty reason, source-to-check context, and relevant uncertainty context without exposing injected evaluation labels, injected anomaly dollars, or evaluation-only OOD labels

#### Scenario: Review queue includes pay-period display context
- **WHEN** analyst queue rows are displayed
- **THEN** each row includes a human-readable pay-period date or label in addition to any internal pay-period index

#### Scenario: Review queue includes expected gross-pay interval context
- **WHEN** expected gross-pay interval fields are available
- **THEN** each analyst-safe queue row includes expected gross-pay p10, p50, p90, interval width, and excess over p90 or equivalent analyst-readable interval context

#### Scenario: High-risk medium-uncertainty records remain visible
- **WHEN** a latest-period record has a high risk score and medium uncertainty because a payroll signal such as overtime is highly anomalous but the peer-group sample is small
- **THEN** the review queue surfaces the record with both the high risk score and the medium uncertainty bucket rather than suppressing or hiding the record

#### Scenario: Conformal context is analyst-readable
- **WHEN** conformal percentile is available for a queued record
- **THEN** the review queue or case card explains the percentile in business language such as how unusual the record is relative to recent payroll history

### Requirement: Uncertainty explanations for case cards
The notebooks SHALL show compact case cards that explain both why a payroll record is risky and why its score is uncertain.

#### Scenario: Case card includes risk and uncertainty reasons
- **WHEN** the review queue, explainability, and thresholds notebook displays a selected case card
- **THEN** the case card includes risk category, risk score, uncertainty bucket, why-risky bullets, and why-uncertain bullets using review-safe language

#### Scenario: Uncertainty reasons identify dominant drivers
- **WHEN** uncertainty components are available for a queued record
- **THEN** the explanation identifies dominant uncertainty drivers such as small peer group, limited employee history, model signal disagreement, wide bootstrap interval, wide expected-pay interval, data quality issues, or out-of-distribution context

#### Scenario: Review-safe wording is preserved
- **WHEN** uncertainty-aware explanations are generated
- **THEN** they avoid claiming confirmed misconduct, confirmed fraud, confirmed payroll error, or known synthetic anomaly status

### Requirement: Facility approval summary output
The system SHALL produce administrator-safe facility/pay-period approval summary outputs.

#### Scenario: Facility summary fields are populated
- **WHEN** approval summaries are generated from scored SNF shift-level records
- **THEN** each facility/pay-period row includes facility identifier, pay period, total shifts, total gross pay, total paid hours, overtime hours, premium dollars, queue count, high-priority count, estimated exposure, top reason categories, and approval readiness context

#### Scenario: Facility summary excludes evaluation truth
- **WHEN** administrator-safe facility/pay-period summaries are exported
- **THEN** they exclude injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts

### Requirement: Threshold comparison explanation
The notebooks SHALL explain why automated SNF approval ranking improves on manually configured thresholds.

#### Scenario: Threshold limitations are shown
- **WHEN** SNF case-study outputs compare manual thresholds and automated ranking
- **THEN** the notebook explains where threshold rules overflag legitimate staffing exceptions, miss context-supported premium mismatches, or miss high-exposure records that are not extreme on a single raw field

### Requirement: Narrative case-study approval evidence
The review queue notebooks SHALL include narrative interpretation around business-facing case-study plots and tables so administrator reviewers can understand what each output proves.

#### Scenario: Narrative accompanies case-study outputs
- **WHEN** the SNF case-study notebook displays lift scorecards, threshold comparisons, case cards, facility summaries, or scenario plots
- **THEN** nearby markdown explains how to read the output, what operational decision it supports, and why the wording remains review-safe

### Requirement: Business-facing case-study visuals
The SNF case-study notebook SHALL include administrator-oriented visuals or tables that make the approval value of the ranked queue clear.

#### Scenario: Approval value visuals render
- **WHEN** the SNF case-study notebook runs
- **THEN** it renders visuals or tables for exposure captured per reviewed record, false-positive avoidance, missed high-risk records, facility approval concentration, and selected administrator-safe case cards where source data is available

#### Scenario: Case-study visuals exclude evaluation truth
- **WHEN** business-facing case-study visuals or case cards are displayed
- **THEN** they exclude injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts unless the section is explicitly labeled as evaluation-only

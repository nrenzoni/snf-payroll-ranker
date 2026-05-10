## MODIFIED Requirements

### Requirement: Analyst-ready review queue
The system SHALL produce a ranked administrator-facing pre-approval exception queue of shift-level SNF payroll records for weekly payroll approval.

#### Scenario: Approval queue fields are populated
- **WHEN** approval queue generation runs
- **THEN** each administrator-safe queue row includes rank, synthetic employee identifier, facility, unit, role, shift date, shift type, pay period, final approval exception score, approval risk category, primary reason, secondary reason, recommended action, source to check, actual gross pay, expected gross pay or role-shift baseline, difference from expected, scheduled hours, worked hours, overtime context, premium context, rule flags, and estimated exposure

#### Scenario: Approval queue is sorted by priority
- **WHEN** records are exported for approval review
- **THEN** records are sorted by pay period, facility where applicable, and descending final approval exception score or configured approval priority

#### Scenario: Approval queue remains review-safe
- **WHEN** records are exported for administrator approval review
- **THEN** the queue does not claim confirmed misconduct, confirmed fraud, confirmed payroll error, or known synthetic anomaly status

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

### Requirement: Required business visuals
The notebooks SHALL include clean visuals or tables for SNF payroll trend, shift-level gross pay distribution, overtime distribution, premium pay distribution, facility payroll heatmap or table, score distribution, threshold baseline comparison, precision@K by approval budget, exposure captured@K by approval budget, model comparison, backtest metrics over time, and selected employee or shift history for a flagged record.

#### Scenario: Required visuals render from synthetic SNF outputs
- **WHEN** the notebook sequence is run on a clean checkout
- **THEN** the required visuals or tables render using synthetic SNF data and generated evaluation outputs
- **AND** notebooks that render LetsPlot visuals call `LetsPlot.setup_html()` before displaying those charts
- **AND** continuous distribution visuals use binned histograms or equivalent aggregation rather than one bar per raw numeric value

### Requirement: Separate analyst and evaluation review queues
The system SHALL produce an administrator-safe approval queue for operational triage and a separate evaluation-labeled approval queue for synthetic performance analysis.

#### Scenario: Administrator queue excludes evaluation labels
- **WHEN** administrator approval queue generation runs
- **THEN** the queue excludes injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts

#### Scenario: Evaluation queue includes labels for analysis
- **WHEN** evaluation-labeled queue generation runs against synthetic SNF data
- **THEN** the queue includes injected labels and injected anomaly dollar impacts only for error analysis and metric interpretation

### Requirement: Latest-period uncertainty-aware analyst review queue
The system SHALL surface risk and uncertainty together in an administrator-safe SNF approval queue for the latest pay period only unless a case-study explicitly requests historical evaluation output.

#### Scenario: Approval queue is limited to latest pay period
- **WHEN** administrator approval queue generation runs on scored SNF payroll records spanning multiple pay periods
- **THEN** the administrator-safe queue includes only records from the latest available pay period by default

#### Scenario: Approval queue includes risk and uncertainty fields
- **WHEN** administrator approval queue generation runs on scored SNF payroll records
- **THEN** each administrator-safe queue row includes final approval exception score, uncertainty bucket, composite uncertainty score, primary uncertainty reason, source-to-check context, and relevant uncertainty context without exposing injected evaluation labels, injected anomaly dollars, or evaluation-only OOD labels

## ADDED Requirements

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

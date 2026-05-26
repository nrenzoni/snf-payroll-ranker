## Purpose
Define the reviewer-facing review queue and notebook deliverables for residual employee-pay-cycle payroll review.
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
The system SHALL generate concise reviewer-readable explanations for flagged employee-pay-cycle records using rule outcomes, score drivers, payroll and timekeeping context, historical baselines, peer comparisons, and estimated exposure.

#### Scenario: Explanation includes payroll review context
- **WHEN** an employee-pay-cycle record is flagged for payroll amount, overtime, premium, lifecycle, duplicate-payment, paid-vs-worked, or related payroll anomalies
- **THEN** the explanation describes what the reviewer should verify in payroll operations terms rather than only reporting a model score

### Requirement: Business deliverable notebook sections
The active notebook SHALL include business, technical, evaluation, reviewer-workflow, and production-readiness sections needed for a presentable employee-pay-cycle payroll ranking deliverable focused on residual finance or payroll review after hard rules.

#### Scenario: Notebook narrative is complete
- **WHEN** a reviewer reads the active notebook
- **THEN** it includes an executive summary, privacy disclaimer, residual payroll review problem framing, synthetic data generation, hard-rule gate definition, residual data sanity checks, label engineering, feature engineering, model formulations, residual queue evaluation, ablation studies, diagnostics and explanations, final recommendation, and technical appendix material

### Requirement: Production readiness discussion
The notebook SHALL describe how the workflow would operate in production without claiming integrations that were not built.

#### Scenario: Production architecture is documented
- **WHEN** the production section is reviewed
- **THEN** it describes an intended flow from payroll, schedule, timeclock, HR lifecycle, and facility reference extracts through validation, feature engineering, scoring, pre-approval queue export, administrator review, feedback, monitoring, and retraining

#### Scenario: Monitoring metrics are documented
- **WHEN** monitoring guidance is reviewed
- **THEN** it includes metrics such as exception count per payroll cycle, approval queue yield, false positive rate from feedback, estimated exposure flagged and confirmed, feature drift, score drift, alert concentration by facility/unit/role/shift, latency, data freshness, failed validation count, and threshold-baseline drift

### Requirement: Multi-notebook business case study sequence
The repository SHALL treat one primary employee-pay-cycle notebook as the active reporting deliverable instead of a required multi-notebook sequence.

#### Scenario: Active notebook replaces required sequence
- **WHEN** the active reporting contract is implemented
- **THEN** the repository includes one primary Jupytext percent-format employee-pay-cycle notebook under `notebooks/`
- **AND** legacy notebook sequences are not treated as required active deliverables

### Requirement: Executive takeaway and proof summary sections
The active notebook SHALL begin with a short executive takeaway and end its main narrative with a concise production recommendation before the technical appendix.

#### Scenario: Active notebook has business framing
- **WHEN** a reviewer opens the active notebook
- **THEN** the first section contains an executive takeaway
- **AND** the final main-narrative section provides the production recommendation before the appendix begins

### Requirement: Analyst-readable review queue and case cards
The active notebook SHALL show a reviewer-readable queue and compact case cards for selected records using review-safe language.

#### Scenario: Case cards include payroll review context
- **WHEN** the active notebook displays selected queued records
- **THEN** it shows compact case cards with rank, employee identifier, facility, pay period, role or employment context where relevant, risk category, recommended action, source to check, primary reason, secondary reason, expected gross pay, actual gross pay, scheduled, worked, and paid hours where available, difference from expected, estimated exposure, and an explanation that avoids fraud labeling

### Requirement: Practical payroll analyst workflow
The active notebook SHALL demonstrate payroll review workflow for ambiguous residual records including review-budget selection, expected queue size per pay period or facility, review risk categories, next actions, conceptual feedback capture, and an operating model for confirm, approve, escalate, and feedback.

#### Scenario: Approval workflow is documented
- **WHEN** a reviewer reads the workflow sections of the active notebook
- **THEN** the notebook explains how reviewers choose a review budget, triage records by risk category, check payroll, timekeeping, rate authorization, lifecycle, or facility-allocation evidence, resolve legitimate exceptions, escalate questionable records, and capture feedback for future calibration

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
The active notebook SHALL include clean visuals or tables for employee-pay-cycle payroll summaries, hard-rule funnel summaries, residual queue metrics by review budget, model comparison, backtest or rolling-origin metrics over time, and selected reviewer-facing queue examples.

#### Scenario: Required visuals render from synthetic employee-pay-cycle outputs
- **WHEN** the active notebook is run on a clean checkout
- **THEN** the required visuals or tables render using synthetic employee-pay-cycle data and generated evaluation outputs
- **AND** notebooks that render LetsPlot visuals call `LetsPlot.setup_html()` before displaying those charts
- **AND** continuous distribution visuals use binned histograms or equivalent aggregation rather than one bar per raw numeric value

#### Scenario: Review-budget visuals use percentage framing
- **WHEN** the active employee-pay-cycle notebook renders residual queue metric visuals
- **THEN** the x-axis and nearby narrative describe review budget as the percentage of each facility-pay-period residual queue reviewed
- **AND** the notebook avoids presenting those active residual queue visuals as if they were absolute top-K cutoffs unless an appendix explicitly labels a separate absolute-budget view

### Requirement: README notebook sequence documentation
The README SHALL identify the single active employee-pay-cycle notebook and briefly explain that it covers the full reporting story and appendix.

#### Scenario: README links active notebook story
- **WHEN** a reviewer reads `README.md`
- **THEN** it identifies the single active employee-pay-cycle notebook as the active reporting contract
- **AND** it explains that the notebook covers the full residual payroll ranking case study and technical appendix in one deliverable

### Requirement: Separate analyst and evaluation review queues
The system SHALL produce an administrator-safe approval queue for operational triage and a separate evaluation-labeled approval queue for synthetic performance analysis.

#### Scenario: Administrator queue excludes evaluation labels
- **WHEN** administrator approval queue generation runs
- **THEN** the queue excludes injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts

#### Scenario: Evaluation queue includes labels for analysis
- **WHEN** evaluation-labeled queue generation runs against synthetic SNF data
- **THEN** the queue includes injected labels and injected anomaly dollar impacts only for error analysis and metric interpretation

### Requirement: Component contribution context
The system SHALL include enough score-driver and reason-code context for analysts to understand why a record was prioritized without exposing evaluation truth.

#### Scenario: Review context is explainable
- **WHEN** a record appears in the analyst-safe queue
- **THEN** the row includes reason codes, risk category, estimated exposure or dollars-at-risk estimate, expected-vs-actual context, peer context, and relevant score-driver fields

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
The system SHALL produce reviewer-safe facility or pay-period approval summary outputs.

#### Scenario: Facility summary fields are populated
- **WHEN** approval summaries are generated from scored employee-pay-cycle records
- **THEN** each facility or facility-pay-period row includes facility identifier, pay period, total employee cycles, total gross pay, total paid hours, overtime hours, premium dollars, queue count, high-priority count, estimated exposure, top reason categories, and approval readiness context

#### Scenario: Facility summary excludes evaluation truth
- **WHEN** administrator-safe facility/pay-period summaries are exported
- **THEN** they exclude injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts

### Requirement: Threshold comparison explanation
The active notebook SHALL explain where residual ranking adds value beyond a hard-rule gate and simple thresholding for ambiguous payroll records.

#### Scenario: Threshold limitations are shown
- **WHEN** the active notebook compares thresholding or gating with residual ranking
- **THEN** it explains where simple rules overflag legitimate exceptions, miss context-supported payroll issues, or miss high-exposure records that are not extreme on a single raw field

### Requirement: Narrative residual-review evidence
The active notebook SHALL include narrative interpretation around reviewer-facing plots and tables so payroll reviewers can understand what each output proves.

#### Scenario: Narrative accompanies residual-review outputs
- **WHEN** the active notebook displays queue metrics, threshold comparisons, case cards, facility summaries, or diagnostic plots
- **THEN** nearby markdown explains how to read the output, what operational decision it supports, and why the wording remains review-safe

### Requirement: Business-facing residual-review visuals
The active notebook SHALL include reviewer-oriented visuals or tables that make the value of the ranked residual queue clear.

#### Scenario: Approval value visuals render
- **WHEN** the active notebook runs
- **THEN** it renders visuals or tables for exposure captured per reviewed record, false-positive avoidance, missed high-risk records, facility review concentration, and selected reviewer-safe case cards where source data is available

#### Scenario: Residual-review visuals exclude evaluation truth
- **WHEN** business-facing visuals or case cards are displayed
- **THEN** they exclude injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts unless the section is explicitly labeled as evaluation-only

### Requirement: Residual reviewer workflow framing
The active notebook SHALL describe reviewer-facing outputs as finance or payroll review of ambiguous residual records rather than as compliance or staffing review.

#### Scenario: Queue language stays in scope
- **WHEN** reviewer workflow examples or explanation text are displayed
- **THEN** they describe checking payroll, timekeeping, rate authorization, facility allocation, lifecycle, or duplicate-payment context for ambiguous residual records
- **AND** they do not frame the queue as PBJ, HPRD, staffing-compliance, or regulatory review

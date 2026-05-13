## Purpose
Define the SNF weekly payroll approval workflow, administrator action context, facility summaries, manual threshold comparisons, and case-study notebook coverage.
## Requirements
### Requirement: Weekly SNF payroll approval assistant
The system SHALL frame operational outputs as a weekly skilled nursing facility payroll approval assistant for administrator teams rather than as a dedicated payroll analyst workbench.

#### Scenario: Approval assistant narrative is present
- **WHEN** a user opens the README or business-facing notebooks
- **THEN** the project describes automated pre-payroll approval exception prioritization for SNF administrators, business office managers, DON/scheduling partners, or regional operators

#### Scenario: Analyst-only framing is avoided
- **WHEN** review outputs or notebook narratives describe the workflow
- **THEN** they avoid implying that a dedicated payroll analyst team is required to use the system

### Requirement: Administrator action context
The system SHALL provide administrator-facing action context for prioritized shift-level exceptions.

#### Scenario: Recommended action is populated
- **WHEN** a shift-level exception appears in the approval queue or case card
- **THEN** the output includes a recommended action such as confirm schedule, verify timeclock edit, confirm premium eligibility, approve known staffing exception, or escalate to payroll

#### Scenario: Source to check is populated
- **WHEN** a shift-level exception appears in the approval queue or case card
- **THEN** the output identifies the operational source to check such as schedule, timeclock, payroll code, pay policy, facility assignment, or employee lifecycle context

### Requirement: Pay-period facility approval summaries
The system SHALL summarize shift-level scoring into pay-period/facility views suitable for weekly payroll approval.

#### Scenario: Facility summary is generated
- **WHEN** scored shift-level payroll records are available
- **THEN** the system produces pay-period/facility summaries with payroll volume, overtime share, premium pay share, exception counts, estimated exposure, top reason categories, and approval readiness context

#### Scenario: Shift-level details remain traceable
- **WHEN** an administrator reviews a facility/pay-period summary
- **THEN** the summary can be traced to the underlying shift-level queued exceptions without exposing evaluation-only labels

### Requirement: Manual threshold value comparison
The system SHALL compare automated SNF anomaly ranking against administrator-style threshold baselines that include individual threshold signals and a calibrated combined manual threshold baseline.

#### Scenario: Threshold baselines are generated
- **WHEN** evaluation runs on synthetic SNF payroll data
- **THEN** results include baseline performance for the calibrated manual threshold pack, gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance thresholds

#### Scenario: Automated ranking value is summarized
- **WHEN** threshold and automated ranking results are available
- **THEN** notebooks summarize review volume, native review burden, estimated exposure captured, estimated exposure captured per reviewed record, false positives avoided, and missed high-exposure exceptions for each approach, with the calibrated manual threshold pack serving as the primary manual comparator

### Requirement: SNF case-study notebook coverage
The notebooks SHALL include two high-value SNF payroll approval case studies.

#### Scenario: Overtime case study is shown
- **WHEN** the SNF case-study notebook or notebook sequence runs
- **THEN** it demonstrates overtime, double-shift, rest-gap, and staffing-pressure exception prioritization compared with manual overtime or total-hours thresholds

#### Scenario: Premium mismatch case study is shown
- **WHEN** the SNF case-study notebook or notebook sequence runs
- **THEN** it demonstrates shift differential, weekend premium, duplicate premium, or premium-without-support exception prioritization compared with manual gross or premium-dollar thresholds

### Requirement: Business-facing SNF ML value proof
The SNF case-study notebook SHALL demonstrate the operational value of automated hybrid approval ranking for facility administrators using repeated scenario evidence and explanation-rich comparison against manual threshold review.

#### Scenario: Business proof compares repeated scenario worlds
- **WHEN** the SNF case-study notebook runs
- **THEN** it compares the calibrated manual threshold pack, deterministic rules, robust statistics, ML-only scoring, and hybrid ranking across repeated scenario and seed worlds for `baseline`, `overtime-staffing-pressure`, and `premium-mismatch` using configured facility review budgets

#### Scenario: Business narrative explains operational value
- **WHEN** a reviewer reads the SNF case-study notebook
- **THEN** narrative text explains what each method type does, where it helps facility approval review, and where thresholds, rules, statistics, ML-only scoring, and hybrid ranking each remain limited

#### Scenario: Business-safe concrete output remains visible
- **WHEN** the main proof narrative concludes
- **THEN** the notebook shows one concrete final ranked-output table with review-safe queue fields so facility administrators can see what the deployed output looks like without relying on multiple intermediate dashboard tables

### Requirement: Appendix stress diagnostics
The SNF case-study notebook SHALL separate stress evidence from the primary business proof.

#### Scenario: Stress variants are shown in appendix
- **WHEN** subgroup drift, calendar drift, or queue stress evidence is presented
- **THEN** it appears in a clearly labeled appendix section after the main proof narrative

#### Scenario: Appendix stress evidence avoids alias overclaim
- **WHEN** stress appendix comparisons are generated
- **THEN** the notebook uses true stress diagnostics or clearly labeled stress constructions rather than presenting simple scenario aliases as distinct stress worlds

#### Scenario: Appendix stress evidence remains informative
- **WHEN** queue-stress appendix evidence is generated
- **THEN** it compares review policies or metrics that produce visible operational contrast, such as missed estimated exposure, candidate queue size, reviewed-to-candidate ratio, adaptive thresholds, capacity shocks, or catch-up staffing effects

#### Scenario: Notebook probability scales render safely
- **WHEN** notebook plots use probability-like color scales
- **THEN** the plots avoid hard scale limits that can trigger renderer-domain errors while preserving readable legends or breaks

### Requirement: Case-study threshold miss evidence
The SNF case-study notebook SHALL show where manual thresholds miss or overflag records relative to automated hybrid ranking in the overtime and premium mismatch scenarios.

#### Scenario: Overtime threshold misses are shown
- **WHEN** overtime, double-shift, rest-gap, or staffing-pressure case-study outputs are displayed
- **THEN** the notebook identifies examples or summaries where manual overtime or total-hours thresholds miss review-worthy high-risk records captured by hybrid ranking

#### Scenario: Premium threshold misses are shown
- **WHEN** premium mismatch or shift differential case-study outputs are displayed
- **THEN** the notebook identifies examples or summaries where manual gross-pay or premium-dollar thresholds miss unsupported premium contexts captured by hybrid ranking

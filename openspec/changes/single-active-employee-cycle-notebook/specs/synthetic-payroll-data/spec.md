## MODIFIED Requirements

### Requirement: Business-facing privacy and governance narrative
The active employee-pay-cycle notebook SHALL explain that all demonstrated payroll records are synthetic and SHALL state that no real employee identifiers, salaries, tax IDs, bank details, HR comments, company data, or live integrations are included.

#### Scenario: Notebook privacy section is visible
- **WHEN** a reviewer opens the active employee-pay-cycle notebook
- **THEN** the notebook includes a privacy and governance section that explicitly identifies the dataset as synthetic and excludes real employee, payroll, banking, tax, HR comment, company, and integration data

### Requirement: Synthetic payroll schema dictionary
The active employee-pay-cycle notebook SHALL show a schema and data dictionary table for synthetic payroll records with field name, business meaning, type or category, privacy sensitivity, and validation expectation.

#### Scenario: Data dictionary documents payroll fields
- **WHEN** the active employee-pay-cycle notebook is executed
- **THEN** it displays a data dictionary covering the generated employee-pay-cycle payroll fields and their expected validation behavior

### Requirement: Data maturity and quality summaries
The active employee-pay-cycle notebook SHALL summarize synthetic payroll data quality, including row counts, pay periods, employee counts, missing values, lifecycle checks, pay distributions, and exception warning counts.

#### Scenario: Quality summaries are generated
- **WHEN** the active employee-pay-cycle notebook runs against generated synthetic data
- **THEN** it displays data quality summaries for record volume, payroll periods, employees, missing values, lifecycle consistency, pay distributions, and validation warning counts

### Requirement: Validation failures and exception warnings demonstration
The active employee-pay-cycle notebook SHALL demonstrate hard validation failures separately from payroll exception warnings using the existing employee-pay-cycle validation outputs.

#### Scenario: Validation outputs are separated
- **WHEN** validation results are shown in the active employee-pay-cycle notebook
- **THEN** hard failures are presented as pipeline-stopping data issues and warnings are presented as payroll exceptions that may require analyst review

### Requirement: Employee-cycle synthetic label set
The synthetic employee-pay-cycle workflow SHALL emit a documented evaluation label set that supports residual classification, severity analysis, ranking research, and business-value evaluation.

#### Scenario: Employee-cycle labels include residual targets and utility
- **WHEN** employee-pay-cycle records are generated from lower-level synthetic payroll activity
- **THEN** the output includes `is_anomaly`, `anomaly_dollars`, dominant `anomaly_category`, `observed_correction`, `observed_correction_dollars`, residual `y_issue`, residual `y_dollar`, `relevance_grade`, `rule_missed_severe_issue`, and `net_utility`
- **AND** the notebook documents that `y_issue` reflects latent residual issue truth rather than observed historical review outcomes
- **AND** the notebook documents that `observed_correction` is a biased historical signal while `relevance_grade`, `rule_missed_severe_issue`, and `net_utility` are evaluation-oriented residual labels

### Requirement: Hard-rule gate and residual issue coverage
The synthetic employee-pay-cycle workflow SHALL support a residual-ranking experiment by generating both hard-rule-caught issues and rule-missed residual issues.

#### Scenario: Critical hard-rule-detectable issues are present
- **WHEN** synthetic employee-pay-cycle payroll data is generated for the active notebook workflow
- **THEN** the generator can produce critical issues such as duplicate or overlapping shifts, negative hours, gross pay equal to zero with positive hours, missing pay rate, physically impossible hours, and terminated employees paid regular hours

#### Scenario: Residual subtle issues remain after the hard-rule gate
- **WHEN** synthetic employee-pay-cycle payroll data is generated for the active notebook workflow
- **THEN** the generator also produces ambiguous rule-missed payroll issues and warning signals so the residual universe retains nontrivial issue prevalence, severe issues, and financial impact after critical hard rules are applied

#### Scenario: Soft warning signals are available for residual modeling
- **WHEN** synthetic employee-pay-cycle payroll data is generated for the active notebook workflow
- **THEN** the observable fields include soft warning signals such as overtime above threshold, manual edits, missing punches, unusual facility patterns, pay-rate changes, and high gross pay versus employee baseline for use as residual-model features

### Requirement: Compliance and staffing metrics remain out of scope
The active residual-ranking notebook SHALL not depend on compliance or staffing metrics that are outside the payroll financial-loss objective.

#### Scenario: Excluded metrics are not required by the notebook contract
- **WHEN** the active employee-pay-cycle notebook's features, labels, or evaluation metrics are reviewed
- **THEN** compliance, PBJ, and HPRD metrics are not required inputs or targets for the notebook contract

## Purpose
Define synthetic payroll data generation requirements for anomaly detection development and evaluation.
## Requirements
### Requirement: Synthetic payroll data only
The system SHALL generate and use synthetic payroll data that contains no real employee identifiers, salaries, tax information, banking details, HR comments, or company-specific records.

#### Scenario: Privacy disclaimer is present
- **WHEN** a user opens the notebook or README
- **THEN** the documentation states that the dataset is synthetic and no real employee-level payroll records are included

#### Scenario: Synthetic identifiers are generated
- **WHEN** payroll records are generated
- **THEN** employee and manager identifiers are synthetic stable identifiers rather than real names, emails, addresses, bank details, or government identifiers

### Requirement: Employee-pay-period payroll records
The system SHALL generate payroll records at employee-pay-period grain with realistic payroll, HR, and timekeeping-like fields.

#### Scenario: Core payroll schema is generated
- **WHEN** the synthetic data generator runs
- **THEN** each output payroll row includes employee identifier, pay period, department, job family, location, employment status, pay type, regular hours, overtime hours, pay rate, gross pay, deductions, net pay, tenure, and lifecycle dates where applicable

#### Scenario: Realistic payroll variation is present
- **WHEN** generated records are analyzed
- **THEN** the data includes variation across departments, job levels, hourly and salaried workers, tenure, promotions, bonuses, commissions, retro pay, deductions, overtime, terminations, and seasonal periods

### Requirement: Injected anomaly labels
The system SHALL inject known payroll anomaly categories and retain labels for evaluation-only artifacts.

#### Scenario: Supported anomaly categories are injected
- **WHEN** the data generator injects anomalies
- **THEN** generated labels include categories such as duplicate payment, overtime spike, pay after termination, gross pay spike, incorrect pay rate, missing deduction, negative net pay, retro pay outlier, department payroll spike, and new employee large payment

#### Scenario: Evaluation labels are retained separately from model features
- **WHEN** model features are built
- **THEN** injected anomaly labels are available for evaluation but are not included as training or scoring features

#### Scenario: Evaluation labels are absent from analyst outputs
- **WHEN** analyst-facing review outputs are generated
- **THEN** injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts are excluded from those outputs

#### Scenario: Evaluation labels remain available for synthetic analysis
- **WHEN** synthetic evaluation outputs are generated
- **THEN** injected anomaly labels and injected anomaly dollar impacts are available in separate evaluation artifacts for metrics, category error analysis, and notebook interpretation

### Requirement: Reproducible data generation
The system SHALL make synthetic data generation reproducible through configuration and random seeds.

#### Scenario: Fixed seed produces stable output
- **WHEN** the generator is run twice with the same configuration and seed
- **THEN** the generated records, injected anomaly labels, and expected output files are reproducible

### Requirement: Business-facing privacy and governance narrative
The notebooks SHALL explain that all demonstrated payroll records are synthetic and SHALL state that no real employee identifiers, salaries, tax IDs, bank details, HR comments, company data, or live integrations are included.

#### Scenario: Notebook privacy section is visible
- **WHEN** a reviewer opens the problem framing and data maturity notebook
- **THEN** the notebook includes a privacy and governance section that explicitly identifies the dataset as synthetic and excludes real employee, payroll, banking, tax, HR comment, company, and integration data

### Requirement: Synthetic payroll schema dictionary
The notebooks SHALL show a schema and data dictionary table for synthetic payroll records with field name, business meaning, type or category, privacy sensitivity, and validation expectation.

#### Scenario: Data dictionary documents payroll fields
- **WHEN** the data maturity notebook is executed
- **THEN** it displays a data dictionary covering the generated employee-pay-period payroll fields and their expected validation behavior

### Requirement: Data maturity and quality summaries
The notebooks SHALL summarize synthetic payroll data quality, including row counts, pay periods, employee counts, missing values, lifecycle checks, pay distributions, and exception warning counts.

#### Scenario: Quality summaries are generated
- **WHEN** the data maturity notebook runs against generated synthetic data
- **THEN** it displays data quality summaries for record volume, payroll periods, employees, missing values, lifecycle consistency, pay distributions, and validation warning counts

### Requirement: Validation failures and exception warnings demonstration
The notebooks SHALL demonstrate hard validation failures separately from payroll exception warnings using the existing `validate_payroll` outputs.

#### Scenario: Validation outputs are separated
- **WHEN** validation results are shown in the data maturity notebook
- **THEN** hard failures are presented as pipeline-stopping data issues and warnings are presented as payroll exceptions that may require analyst review


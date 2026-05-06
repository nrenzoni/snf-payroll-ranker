## ADDED Requirements

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

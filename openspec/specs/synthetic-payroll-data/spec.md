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

### Requirement: Synthetic pay-code field
The system SHALL generate a synthetic `pay_code` field for employee-pay-period payroll records.

#### Scenario: Pay code is generated in core payroll schema
- **WHEN** synthetic payroll records are generated
- **THEN** each payroll row includes a synthetic pay code suitable for feature engineering, OOD detection, data dictionary display, and validation checks

#### Scenario: Pay code is not real payroll metadata
- **WHEN** synthetic pay codes are documented or displayed
- **THEN** the documentation identifies them as synthetic codes and not real company payroll configuration

### Requirement: Temporal pay-code OOD generation
The system SHALL generate reproducible late-period pay-code novelty and rarity for out-of-distribution demonstrations.

#### Scenario: New or rare pay codes appear in later periods
- **WHEN** the synthetic data generator runs with a fixed seed
- **THEN** later pay periods include reproducible new or rare pay-code values that were unseen or rare in the configured prior-period reference window

#### Scenario: Pay-code drift is available for OOD evaluation
- **WHEN** generated data includes late-period pay-code drift
- **THEN** evaluation-only OOD metadata may identify OOD contexts for diagnostics, and that metadata is excluded from scoring features and analyst-safe review queue fields

#### Scenario: Pay-code data dictionary is updated
- **WHEN** the data maturity notebook displays the synthetic schema dictionary
- **THEN** it includes `pay_code`, its business meaning, its synthetic nature, and its validation or OOD expectation

### Requirement: Scenario-controlled payroll simulation
The system SHALL support configurable synthetic payroll simulation scenarios for internal statistical diagnostics.

#### Scenario: Scenario controls are applied
- **WHEN** synthetic payroll data is generated with a diagnostic scenario configuration
- **THEN** the generated records reflect the configured scenario controls while retaining reproducibility for a fixed seed

### Requirement: Drift and change-point controls
The system SHALL generate synthetic payroll datasets with controlled temporal drift and change-point patterns for diagnostic evaluation.

#### Scenario: Temporal drift is generated
- **WHEN** drift or change-point controls are enabled
- **THEN** later pay periods include reproducible shifts in payroll, workforce, pay-code, department, or anomaly behavior suitable for temporal diagnostic analysis

### Requirement: Anomaly-mix scenario controls
The system SHALL support configurable anomaly mixes across synthetic payroll scenarios.

#### Scenario: Anomaly mix is controlled
- **WHEN** a scenario specifies anomaly category prevalence, severity, or concentration
- **THEN** injected anomaly labels reflect the configured mix and remain excluded from scoring features and analyst-facing outputs

### Requirement: Diagnostic scenario catalog
The system SHALL provide a catalog of named internal diagnostic scenarios for synthetic payroll generation.

#### Scenario: Named diagnostic scenarios are available
- **WHEN** diagnostic generation is requested
- **THEN** users can select documented scenarios covering baseline, drift, targeted anomaly, subgroup, and review-capacity stress conditions

### Requirement: Targeted anomaly generation controls
The system SHALL support targeted anomaly generation controls for internal diagnostic signal analysis.

#### Scenario: Targeted anomalies are injected
- **WHEN** targeted anomaly controls specify categories, employee groups, periods, or dollar impact ranges
- **THEN** the synthetic data includes matching injected anomalies with evaluation-only labels and impacts

### Requirement: Plot-calibrated internal diagnostic scenarios
The system SHALL generate internal diagnostic scenarios calibrated to produce informative plots without excessive runtime.

#### Scenario: Plot-calibrated scenario is generated
- **WHEN** plot-calibrated diagnostics are enabled
- **THEN** generated data includes sufficient contrasts, subgroup coverage, and temporal variation for dense internal diagnostic plots

### Requirement: Scenario contrast summaries
The system SHALL produce scenario contrast summaries for internal diagnostics.

#### Scenario: Scenario contrasts are summarized
- **WHEN** multiple synthetic diagnostic scenarios are generated or compared
- **THEN** outputs summarize key differences in population mix, temporal drift, anomaly mix, severity, and expected diagnostic behavior

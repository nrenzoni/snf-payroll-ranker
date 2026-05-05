## ADDED Requirements

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
The system SHALL inject known payroll anomaly categories and retain labels for evaluation.

#### Scenario: Supported anomaly categories are injected
- **WHEN** the data generator injects anomalies
- **THEN** generated labels include categories such as duplicate payment, overtime spike, pay after termination, gross pay spike, incorrect pay rate, missing deduction, negative net pay, retro pay outlier, department payroll spike, and new employee large payment

#### Scenario: Evaluation labels are retained separately from model features
- **WHEN** model features are built
- **THEN** injected anomaly labels are available for evaluation but are not included as training or scoring features

### Requirement: Reproducible data generation
The system SHALL make synthetic data generation reproducible through configuration and random seeds.

#### Scenario: Fixed seed produces stable output
- **WHEN** the generator is run twice with the same configuration and seed
- **THEN** the generated records, injected anomaly labels, and expected output files are reproducible

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
The system SHALL generate shift-level SNF payroll, schedule, and timeclock records as the primary synthetic data grain, with pay-period and facility rollups derived from the shift-level records.

#### Scenario: Core SNF shift-level schema is generated
- **WHEN** the synthetic data generator runs
- **THEN** each primary payroll row includes synthetic shift or payroll-line identifier, employee identifier, facility, unit, role, license type, pay period, shift date, shift type, scheduled hours, worked hours, pay code, pay-code category, base rate, applied rate or multiplier, gross pay, premium pay amount, timeclock context, schedule context, approval status, employment status, tenure, and lifecycle dates where applicable

#### Scenario: Pay-period facility rollups are generated
- **WHEN** shift-level payroll records are generated
- **THEN** the system derives pay-period/facility rollups with payroll amount, paid hours, overtime hours, premium dollars, exception counts, and estimated approval context without using evaluation-only labels as inputs

#### Scenario: Generic corporate workforce values are replaced
- **WHEN** synthetic data is generated for this project
- **THEN** departments and job families are SNF-specific rather than corporate values such as Sales, Engineering, commissions, or remote office roles

### Requirement: Injected anomaly labels
The system SHALL inject known SNF payroll anomaly categories and retain labels for evaluation-only artifacts.

#### Scenario: Supported SNF anomaly categories are injected
- **WHEN** the data generator injects implemented anomalies
- **THEN** generated labels include overtime/double-shift staffing pressure anomalies and premium pay or shift differential mismatch anomalies

#### Scenario: Evaluation labels are retained separately from model features
- **WHEN** model features are built
- **THEN** injected anomaly labels are available for evaluation but are not included as training, scoring, threshold-baseline, exposure-estimation, or administrator-facing queue features

#### Scenario: Evaluation labels are absent from administrator outputs
- **WHEN** administrator-facing approval outputs are generated
- **THEN** injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts are excluded from those outputs

#### Scenario: Evaluation labels remain available for synthetic analysis
- **WHEN** synthetic evaluation outputs are generated
- **THEN** injected anomaly labels and injected anomaly dollar impacts are available in separate evaluation artifacts for metrics, case-study error analysis, and notebook interpretation

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
The system SHALL generate synthetic SNF pay-code and pay-code-category fields for shift-level payroll records.

#### Scenario: SNF pay code is generated in core payroll schema
- **WHEN** synthetic shift-level payroll records are generated
- **THEN** each payroll line includes a synthetic pay code and pay-code category suitable for feature engineering, premium eligibility checks, OOD detection, data dictionary display, and validation checks

#### Scenario: Pay code is not real payroll metadata
- **WHEN** synthetic pay codes are documented or displayed
- **THEN** the documentation identifies them as synthetic SNF illustrative codes and not real company or vendor payroll configuration

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
The system SHALL support configurable synthetic SNF payroll simulation scenarios for implemented case studies and future scenario documentation.

#### Scenario: Scenario controls are applied
- **WHEN** synthetic SNF payroll data is generated with a scenario configuration
- **THEN** the generated schedule, timeclock, payroll line, anomaly label, and rollup records reflect the configured scenario controls while retaining reproducibility for a fixed seed

#### Scenario: Scenario metadata is generated
- **WHEN** a scenario-controlled run is written
- **THEN** metadata identifies the scenario name, implemented scenario family, documented future scenario families, seed, policy assumptions, and key generation settings

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
The system SHALL provide a catalog of named SNF payroll scenarios with implementation status.

#### Scenario: Implemented scenarios are available
- **WHEN** diagnostic or notebook generation is requested
- **THEN** users can select documented implemented scenarios covering overtime/double-shift staffing pressure and premium pay or shift differential mismatch

#### Scenario: Future scenarios are documented
- **WHEN** users inspect the scenario catalog
- **THEN** the catalog documents future potential scenarios for agency and float labor, census and acuity, credential and license mismatch, PBJ category mismatch, meal break premiums, new hire orientation, termination and final pay, retro and rate corrections, union or contract policy variation, new-client bootstrap, and payroll close adjustment concentration without claiming they are implemented

### Requirement: Targeted anomaly generation controls
The system SHALL support targeted SNF anomaly generation controls for implemented case-study signal analysis.

#### Scenario: Targeted SNF anomalies are injected
- **WHEN** targeted anomaly controls specify facilities, units, roles, shift types, pay-code categories, periods, or exposure ranges
- **THEN** the synthetic data includes matching observable shift-level changes with evaluation-only labels and impacts

#### Scenario: Anomaly injection preserves realistic source context
- **WHEN** implemented SNF anomalies are injected
- **THEN** the generator modifies schedule, timeclock, pay-code, premium, or hours context consistently enough for features and explanations to detect the issue without relying on labels

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

### Requirement: Typed SNF generator contracts
The system SHALL use typed configuration and result contracts for SNF synthetic generation.

#### Scenario: Generator returns named result object
- **WHEN** SNF synthetic generation completes
- **THEN** the public generator returns a named dataclass result containing Polars DataFrames for facilities, employees, schedules, timeclock records, payroll lines, labels, rollups, metadata, and validation outputs rather than a raw tuple or loose dictionary

#### Scenario: Controlled vocabularies use enums
- **WHEN** SNF domain values are defined for roles, license types, unit types, shift types, pay-code categories, approval statuses, labor sources, source-to-check values, recommendations, scenario families, or anomaly categories
- **THEN** they are represented by `StrEnum` values and schema constants rather than ad hoc plain strings

### Requirement: Early generator validation
The system SHALL fail early for invalid SNF generator configuration, policy, scenario, schema, referential, or reconciliation conditions.

#### Scenario: Invalid configuration fails before generation
- **WHEN** the SNF generator is configured with invalid facility counts, pay periods, policy windows, unknown enum values, unsupported scenario names, or impossible target counts
- **THEN** generation fails with a clear validation error before downstream feature engineering or notebooks run

#### Scenario: Rollups reconcile to shift lines
- **WHEN** pay-period/facility rollups are generated
- **THEN** validation verifies that rollup hours, gross pay, overtime hours, and premium dollars reconcile to the underlying shift-level payroll lines within configured tolerances

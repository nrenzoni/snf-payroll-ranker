## MODIFIED Requirements

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

### Requirement: Synthetic pay-code field
The system SHALL generate synthetic SNF pay-code and pay-code-category fields for shift-level payroll records.

#### Scenario: SNF pay code is generated in core payroll schema
- **WHEN** synthetic shift-level payroll records are generated
- **THEN** each payroll line includes a synthetic pay code and pay-code category suitable for feature engineering, premium eligibility checks, OOD detection, data dictionary display, and validation checks

#### Scenario: Pay code is not real payroll metadata
- **WHEN** synthetic pay codes are documented or displayed
- **THEN** the documentation identifies them as synthetic SNF illustrative codes and not real company or vendor payroll configuration

### Requirement: Scenario-controlled payroll simulation
The system SHALL support configurable synthetic SNF payroll simulation scenarios for implemented case studies and future scenario documentation.

#### Scenario: Scenario controls are applied
- **WHEN** synthetic SNF payroll data is generated with a scenario configuration
- **THEN** the generated schedule, timeclock, payroll line, anomaly label, and rollup records reflect the configured scenario controls while retaining reproducibility for a fixed seed

#### Scenario: Scenario metadata is generated
- **WHEN** a scenario-controlled run is written
- **THEN** metadata identifies the scenario name, implemented scenario family, documented future scenario families, seed, policy assumptions, and key generation settings

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

## ADDED Requirements

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

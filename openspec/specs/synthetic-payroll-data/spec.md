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
The system SHALL generate employee-pay-cycle payroll records as the primary active synthetic data grain, with any lower-level shift, schedule, or timeclock artifacts treated as optional supporting context rather than the canonical runtime contract.

#### Scenario: Core employee-pay-cycle schema is generated
- **WHEN** the synthetic data generator runs
- **THEN** each primary payroll row includes a synthetic employee-pay-cycle identifier, employee identifier, facility, pay period or payroll cycle, role or job context, aggregated hours and pay measures, relevant lifecycle and temporal context, and any active-library label fields needed for research or production-candidacy evaluation

#### Scenario: Supporting lower-level context is optional
- **WHEN** synthetic data generation includes shift, schedule, or timeclock detail
- **THEN** those lower-level artifacts are treated as optional supporting context or derived inputs rather than the canonical active modeling grain

#### Scenario: Active rollups follow the canonical grain
- **WHEN** active synthetic payroll records are generated
- **THEN** downstream active scoring, evaluation, and queue contracts use employee-pay-cycle records as their primary input grain

### Requirement: Legacy shift-level synthetic artifacts are non-normative
Deprecated shift-level synthetic payroll artifacts MAY remain in the repository for historical reference, but they SHALL NOT define the active data contract.

#### Scenario: Legacy synthetic artifacts stay out of active contracts
- **WHEN** active docs or specs describe the primary synthetic payroll interface
- **THEN** they identify employee-pay-cycle records as canonical and describe any retained shift-level artifacts as deprecated historical reference only

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

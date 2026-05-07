## ADDED Requirements

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

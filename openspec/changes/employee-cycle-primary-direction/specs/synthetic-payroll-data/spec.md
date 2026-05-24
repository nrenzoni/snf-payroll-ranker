## MODIFIED Requirements

### Requirement: Employee-pay-period payroll records
The system SHALL generate employee-pay-cycle payroll records as the primary active synthetic data grain, with any lower-level shift, schedule, or timeclock artifacts treated as optional supporting context rather than the canonical runtime contract.

#### Scenario: Core employee-pay-cycle schema is generated
- **WHEN** the active synthetic data generator runs
- **THEN** each primary payroll row includes a synthetic employee-pay-cycle identifier, employee identifier, facility, pay period or payroll cycle, role or job context, aggregated hours and pay measures, relevant lifecycle and temporal context, and any active-library label fields needed for research or production-candidacy evaluation

#### Scenario: Supporting lower-level context is optional
- **WHEN** synthetic data generation includes shift, schedule, or timeclock detail
- **THEN** those lower-level artifacts are treated as optional supporting context or derived inputs rather than the canonical active modeling grain

#### Scenario: Active rollups follow the canonical grain
- **WHEN** active synthetic payroll records are generated
- **THEN** downstream active scoring, evaluation, and queue contracts use employee-pay-cycle records as their primary input grain

## ADDED Requirements

### Requirement: Legacy shift-level synthetic artifacts are non-normative
Deprecated shift-level synthetic payroll artifacts MAY remain in the repository for historical reference, but they SHALL NOT define the active data contract.

#### Scenario: Legacy synthetic artifacts stay out of active contracts
- **WHEN** active docs or specs describe the primary synthetic payroll interface
- **THEN** they identify employee-pay-cycle records as canonical and describe any retained shift-level artifacts as deprecated historical reference only

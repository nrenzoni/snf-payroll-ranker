## MODIFIED Requirements

### Requirement: Analyst-ready review queue
The system SHALL produce an employee-pay-cycle ranked review queue from the active payroll ranking library instead of defining the active queue around deprecated shift-level SNF approval outputs.

#### Scenario: Active queue fields are populated
- **WHEN** active review queue generation runs
- **THEN** each queue row includes the employee-pay-cycle identifier, employee identifier, facility, payroll cycle, active priority score, risk or relevance context, explanation context, and any review-safe fields required by the active employee-pay-cycle workflow

#### Scenario: Active queue is sorted by group priority
- **WHEN** active records are exported for review
- **THEN** employee-pay-cycle rows are ordered within their active queue grouping by descending configured priority score

#### Scenario: Legacy shift-level queue fields are not treated as active requirements
- **WHEN** the active queue contract is documented
- **THEN** deprecated shift-level SNF approval queue fields are identified as legacy historical material rather than active acceptance criteria

## ADDED Requirements

### Requirement: Queue contract follows active runtime direction
The active review queue SHALL be derived from the active employee-pay-cycle runtime and SHALL NOT depend on deprecated shift-level hybrid queue generation.

#### Scenario: Active queue excludes deprecated runtime dependency
- **WHEN** the active queue contract is implemented or documented
- **THEN** it does not require deprecated shift-level queue modules, legacy notebook outputs, or historical hybrid score fields to operate

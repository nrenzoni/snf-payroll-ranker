## ADDED Requirements

### Requirement: Administrator threshold baseline flags
The system SHALL emit administrator-style threshold baseline flags from observable SNF payroll fields alongside the scored payroll output.

#### Scenario: Manual threshold flags are present
- **WHEN** scoring completes
- **THEN** each scored record includes gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance threshold flags for downstream evaluation and notebook comparisons

#### Scenario: Threshold flags remain label-free
- **WHEN** threshold baseline flags are computed
- **THEN** the flags use only production-observable payroll, schedule, timeclock, and facility reference fields and do not use injected anomaly labels, injected anomaly categories, or injected anomaly dollars

### Requirement: Facility payroll variance threshold flag
The system SHALL calculate a facility payroll variance threshold flag that identifies records whose gross pay materially exceeds facility-relative payroll context by a configured variance ratio.

#### Scenario: Facility variance threshold is triggered
- **WHEN** a scored record's gross pay materially exceeds scoring-time-available facility-relative baseline pay context by the configured threshold
- **THEN** `threshold_facility_variance_flag` is set for that record

#### Scenario: Facility variance threshold stays interpretable
- **WHEN** the facility variance threshold flag is surfaced in evaluation or notebook outputs
- **THEN** the comparison can be explained as a manual facility-context pay variance rule rather than as a learned model score

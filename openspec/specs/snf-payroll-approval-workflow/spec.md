## Purpose
Define how deprecated SNF shift-level payroll approval workflow materials are retained as legacy reference without defining the active employee-pay-cycle program.

## Requirements
### Requirement: Deprecated SNF workflow remains historical reference only
The older shift-level SNF payroll approval workflow MAY remain in the repository as historical reference material, but it SHALL NOT define the active project direction.

#### Scenario: Legacy SNF workflow is clearly demoted
- **WHEN** contributors inspect specs or docs that mention the older SNF approval workflow
- **THEN** those materials identify it as deprecated historical reference rather than active runtime, active research, or active production scope

### Requirement: Legacy workflow artifacts stay outside active requirements
Historical SNF workflow outputs such as shift-level approval queues, facility summaries, threshold comparisons, and case-study notebooks MAY remain for traceability, but they SHALL NOT be treated as current acceptance criteria for the active employee-pay-cycle contract.

#### Scenario: Legacy workflow artifacts are non-normative
- **WHEN** a contributor reviews active runtime, queue, evaluation, or notebook requirements
- **THEN** those requirements do not depend on the historical SNF workflow artifacts to satisfy the active contract

### Requirement: Legacy workflow documentation stays explicitly labeled
Any retained SNF workflow narrative SHALL preserve clear legacy-reference wording so readers do not confuse it with the active residual employee-pay-cycle program.

#### Scenario: Legacy notebook status is explicit
- **WHEN** a reader discovers a retained SNF workflow notebook, spec, or doc section
- **THEN** it identifies itself as deprecated historical reference and does not claim to be the active deliverable path

## ADDED Requirements

### Requirement: Deprecated payroll reference code is isolated
The repository SHALL isolate deprecated shift-level payroll scoring code, notebooks, and related helpers under an explicitly marked deprecated or legacy reference boundary rather than presenting them as active runtime modules.

#### Scenario: Legacy boundary is explicit
- **WHEN** a contributor inspects deprecated shift-level payroll code or notebooks
- **THEN** the containing namespace or directory identifies that material as deprecated historical reference rather than active runtime or active research code

### Requirement: Active runtime does not depend on legacy reference code
The active employee-pay-cycle runtime SHALL NOT import deprecated shift-level reference code for scoring, evaluation, queue generation, or production-facing workflows.

#### Scenario: Legacy code is excluded from active paths
- **WHEN** active runtime, evaluation, or production-oriented research paths are documented or implemented
- **THEN** they exclude deprecated shift-level modules and notebooks from required imports, acceptance criteria, and operational claims

### Requirement: Legacy reference status is documented
The project documentation SHALL describe deprecated shift-level hybrid work as historical reference retained for traceability and idea recovery only.

#### Scenario: Legacy status is visible in top-level docs
- **WHEN** a user reads the README, architecture notes, or decision records
- **THEN** the docs state that deprecated shift-level hybrid material is retained only for historical reference and is not part of the active runtime, research program, or production path

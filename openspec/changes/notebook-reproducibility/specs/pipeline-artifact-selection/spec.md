## ADDED Requirements

### Requirement: Selective pipeline artifact generation
The pipeline SHALL provide a typed include configuration that controls which non-core runtime artifacts `run_pipeline` generates while preserving full artifact generation as the default behavior.

#### Scenario: Default pipeline generates full artifacts
- **WHEN** `run_pipeline` is called without an include configuration
- **THEN** generated payroll, labels, scored rows, validation outputs, aggregations, evaluation outputs, backtests, rolling-origin outputs, review queues, leakage checks, and scenario metadata are available on the returned result object

#### Scenario: Scored-only pipeline skips non-core artifacts
- **WHEN** `run_pipeline` is called with the scored-only include configuration
- **THEN** generated payroll, labels, scored rows, and scenario metadata are available without generating validation outputs, aggregations, evaluation outputs, backtests, rolling-origin outputs, review queues, or leakage checks

### Requirement: Explicit excluded artifact access errors
The pipeline result object SHALL raise a custom exception when a consumer accesses an artifact that was excluded by the include configuration.

#### Scenario: Excluded artifact access fails loudly
- **WHEN** a consumer accesses an excluded artifact on a scored-only pipeline result
- **THEN** the access raises a pipeline artifact-not-generated exception that identifies the missing artifact

#### Scenario: Generated artifact access succeeds
- **WHEN** a consumer accesses an artifact that was included by the pipeline include configuration
- **THEN** the result object returns the generated artifact without raising an exception

### Requirement: Selective artifact API remains typed
The selective artifact API SHALL use named dataclasses and property access rather than raw dictionaries, tuple unpacking, or placeholder empty DataFrames for excluded artifacts.

#### Scenario: Include configuration is explicit
- **WHEN** a caller requests a non-default artifact profile
- **THEN** the caller uses a named include configuration constructor or explicit include configuration fields

#### Scenario: Excluded artifacts are not represented as placeholders
- **WHEN** an artifact is excluded by the include configuration
- **THEN** the pipeline result does not return an empty `pl.DataFrame` placeholder for that artifact

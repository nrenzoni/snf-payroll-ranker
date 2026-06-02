## MODIFIED Requirements

### Requirement: Diagnostic scenario catalog
The system SHALL provide a catalog of named SNF payroll scenarios with implementation status.

#### Scenario: Implemented scenarios are available
- **WHEN** diagnostic or notebook generation is requested
- **THEN** users can select documented implemented scenarios covering baseline operations, high timekeeping noise, high facility heterogeneity, heavy dollar tail, subtle residual issues, biased historical corrections, diversified severe issues, and temporal payroll drift

#### Scenario: Future scenarios are documented
- **WHEN** users inspect the scenario catalog
- **THEN** the catalog documents future potential scenarios for agency and float labor, census and acuity, credential and license mismatch, PBJ category mismatch, meal break premiums, new hire orientation, termination and final pay, retro and rate corrections, union or contract policy variation, new-client bootstrap, and payroll close adjustment concentration without claiming they are implemented

## ADDED Requirements

### Requirement: Scenario suite behavior is materially differentiated
The synthetic employee-pay-cycle scenario suite SHALL vary the payroll-generating process in ways that create real differences in residual queue structure rather than metadata-only relabeling.

#### Scenario: Timekeeping-noise scenario changes residual context
- **WHEN** the high timekeeping noise scenario is generated
- **THEN** the produced payroll reflects more missing punches, late edits, or paid-versus-scheduled mismatches than baseline operations while remaining reproducible for a fixed seed

#### Scenario: Temporal-drift scenario shifts later periods
- **WHEN** the temporal payroll drift scenario is generated
- **THEN** later pay periods include reproducible shifts in pay rates, overtime norms, or timekeeping patterns relative to earlier periods

### Requirement: Notebook-visible scenario contrast summaries
The system SHALL expose notebook-visible scenario summaries for the implemented DGP suite.

#### Scenario: Scenario summary rows are available
- **WHEN** notebook reporting assembles scenario-aware tables
- **THEN** the available scenario outputs can summarize residual issue rate, severe issue rate, residual dollars, dominant issue family, and label-bias strength for each implemented DGP scenario

### Requirement: Bias-strength scenario controls
The synthetic generator SHALL support scenario controls that increase or decrease observed historical correction bias without leaking those labels into scoring features.

#### Scenario: Biased historical corrections are strengthened
- **WHEN** the biased historical corrections scenario is generated
- **THEN** observed corrections are more strongly selected by prior-review-like signals such as anomaly dollars, manual edits, or low payroll maturity than in the baseline scenario
- **AND** the resulting observed-correction labels remain evaluation-only artifacts

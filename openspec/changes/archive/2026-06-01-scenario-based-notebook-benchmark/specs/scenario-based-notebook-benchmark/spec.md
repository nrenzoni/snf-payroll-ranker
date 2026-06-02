## ADDED Requirements

### Requirement: Scenario-based notebook benchmark study unit
The system SHALL support a notebook-facing main benchmark whose primary experimental unit is `DGP scenario x seed x model x review budget x metric` for employee-pay-cycle residual ranking evaluation.

#### Scenario: Benchmark units are assembled
- **WHEN** the active notebook or a supporting benchmark helper runs the main study
- **THEN** it evaluates employee-pay-cycle model performance across DGP scenarios, seeds, models, and configured review-budget percentages
- **AND** the resulting outputs can be aggregated by scenario, seed, model, review budget, and metric without redefining the underlying grouped review-budget metrics

### Requirement: Notebook-facing benchmark summaries
The system SHALL produce notebook-ready summary tables for the scenario-based employee-pay-cycle benchmark.

#### Scenario: Main study summary tables are available
- **WHEN** the main scenario-based benchmark finishes
- **THEN** the outputs include a DGP scenario catalog table, a scenario-seed design table, an aggregate winner-frequency table, and a median metric summary table with interval columns

### Requirement: Winner-map plot inputs
The system SHALL produce tidy plot inputs for winner maps by operating objective and review-budget percentage.

#### Scenario: Winner map inputs are generated
- **WHEN** notebook visualization code renders the main scenario-based benchmark
- **THEN** the benchmark outputs include tidy rows identifying the winning model for each operating objective and review-budget percentage
- **AND** those rows preserve the underlying aggregation scope so plots can distinguish scenario-seed study conclusions from single-run examples

### Requirement: Multi-seed interpretation note
The active notebook SHALL explain the distinct roles of random seeds and DGP scenarios in the main benchmark interpretation.

#### Scenario: Seed-versus-scenario interpretation is documented
- **WHEN** a reviewer reads the main benchmark section
- **THEN** the notebook states that seeds estimate random-draw stability within the same payroll-generating process
- **AND** it states that seeds do not remove structural DGP bias
- **AND** it states that structural robustness is assessed by comparing across DGP scenarios

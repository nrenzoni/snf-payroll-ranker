## MODIFIED Requirements

### Requirement: Notebook-facing benchmark summaries
The system SHALL produce notebook-ready benchmark summaries that support both reader-facing visual interpretation and appendix-level audit review for the scenario-based employee-pay-cycle benchmark.

#### Scenario: Main study summary artifacts are available
- **WHEN** the main scenario-based benchmark finishes
- **THEN** the outputs include a DGP scenario catalog table, a scenario-seed design table, an aggregate winner-frequency table, and a median metric summary table with interval columns
- **AND** those outputs are suitable for rendering as main-narrative plots, compact cards, or concise support tables without recomputing benchmark metrics
- **AND** the full tabular outputs remain available for technical appendix display or audit export

### Requirement: Winner-map plot inputs
The system SHALL produce tidy plot inputs for winner maps by operating objective and review-budget percentage.

#### Scenario: Winner map inputs are generated
- **WHEN** notebook visualization code renders the main scenario-based benchmark
- **THEN** the benchmark outputs include tidy rows identifying the winning model for each operating objective and review-budget percentage
- **AND** those rows preserve the underlying aggregation scope so plots can distinguish scenario-seed study conclusions from single-run examples
- **AND** those rows support coloring by winning model while retaining the associated selection metric value for appendix tables or compact annotations

### Requirement: Multi-seed interpretation note
The active notebook SHALL explain the distinct roles of random seeds and DGP scenarios in the main benchmark interpretation without requiring broad raw benchmark tables in the main narrative.

#### Scenario: Seed-versus-scenario interpretation is documented
- **WHEN** a reviewer reads the main benchmark section
- **THEN** the notebook states that seeds estimate random-draw stability within the same payroll-generating process
- **AND** it states that seeds do not remove structural DGP bias
- **AND** it states that structural robustness is assessed by comparing across DGP scenarios
- **AND** detailed scenario-seed design rows may be placed in the technical appendix when the main benchmark narrative uses visual summaries

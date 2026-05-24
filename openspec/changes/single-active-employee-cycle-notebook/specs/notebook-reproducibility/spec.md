## MODIFIED Requirements

### Requirement: Clean notebook execution
The active employee-pay-cycle notebook SHALL execute from a clean checkout without errors using the project environment.

#### Scenario: Active notebook executes successfully
- **WHEN** the documented notebook execution command is run for the primary employee-pay-cycle notebook
- **THEN** the notebook completes without traceback outputs or failed cells

### Requirement: Notebook output hygiene
The active employee-pay-cycle notebook SHALL maintain clean, reproducible saved outputs suitable for a polished data-science deliverable.

#### Scenario: Executed notebook has coherent execution state
- **WHEN** the active notebook is committed with saved outputs
- **THEN** code-cell execution counts are coherent for a clean run and do not show stale out-of-order exploratory execution

#### Scenario: Generated outputs are documented and refreshable
- **WHEN** the pipeline or active notebook regenerates synthetic data and evaluation outputs
- **THEN** the README or notebook index identifies the expected generated files and the outputs are reproducible from the configured seed

### Requirement: Expanded notebook sequence documentation
The documented notebook reporting contract SHALL identify the single active employee-pay-cycle notebook and explain that it includes both the main narrative and the technical appendix.

#### Scenario: Active notebook is listed in docs
- **WHEN** the README or notebook reporting documentation is reviewed
- **THEN** it identifies the single active employee-pay-cycle notebook
- **AND** it briefly explains that the notebook covers business framing, formulation comparison, queue results, diagnostics, stress testing, and the technical appendix in one deliverable

### Requirement: New validation notebook supports fast execution
The primary employee-pay-cycle notebook SHALL support fast validation when it performs repeated pipeline runs, scenario comparisons, or other material workloads.

#### Scenario: Fast validation executes active notebook
- **WHEN** `NOTEBOOK_FAST=1` fast validation is run for the primary employee-pay-cycle notebook
- **THEN** the notebook reduces expensive workloads while still producing representative section outputs needed to catch execution errors

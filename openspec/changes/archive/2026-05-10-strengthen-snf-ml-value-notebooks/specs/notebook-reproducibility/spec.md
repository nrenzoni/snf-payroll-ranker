## ADDED Requirements

### Requirement: Expanded notebook sequence documentation
The documented notebook sequence SHALL include any new technical ML value notebook added by this change.

#### Scenario: New notebook is listed
- **WHEN** the README or notebook sequence documentation is reviewed
- **THEN** it lists the technical ML value notebook and briefly explains that it covers ablation, incremental ML value, temporal validation evidence, uncertainty, and robustness diagnostics

### Requirement: New validation notebook supports fast execution
Any new technical ML value notebook SHALL support fast validation when it performs repeated pipeline runs, scenario comparisons, or other material workloads.

#### Scenario: Fast validation executes new notebook
- **WHEN** `NOTEBOOK_FAST=1` fast validation is run for the new technical ML value notebook
- **THEN** the notebook reduces expensive workloads while still producing representative ablation, comparison, and plot outputs needed to catch execution errors

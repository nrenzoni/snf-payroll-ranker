# notebook-reproducibility Specification

## Purpose
TBD - created by archiving change harden-payroll-anomaly-ds-readiness. Update Purpose after archive.
## Requirements
### Requirement: Clean notebook execution
The notebook sequence SHALL execute from a clean checkout without errors using the project environment.

#### Scenario: Notebook sequence executes successfully
- **WHEN** the documented notebook execution command is run for each business-facing notebook
- **THEN** each notebook completes without traceback outputs or failed cells

### Requirement: Notebook output hygiene
The notebook sequence SHALL maintain clean, reproducible saved outputs suitable for a polished data-science deliverable.

#### Scenario: Executed notebooks have coherent execution state
- **WHEN** notebooks are committed with saved outputs
- **THEN** code-cell execution counts are coherent for a clean run and do not show stale out-of-order exploratory execution

#### Scenario: Generated outputs are documented and refreshable
- **WHEN** the pipeline or notebooks regenerate synthetic data and evaluation outputs
- **THEN** the README or notebook index identifies the expected generated files and the outputs are reproducible from the configured seed

### Requirement: Reproducibility tests
The project SHALL include verification for key notebook and generated-output reproducibility invariants.

#### Scenario: Reproducibility checks run locally
- **WHEN** the project test or verification command is run
- **THEN** it verifies that required generated output files can be produced and that analyst-facing outputs exclude synthetic evaluation labels

### Requirement: Rich internal diagnostic notebooks with bounded defaults
The internal diagnostic notebooks SHALL provide rich diagnostic coverage while using bounded defaults suitable for local execution.

#### Scenario: Rich diagnostics run with bounded defaults
- **WHEN** internal diagnostic notebooks are executed with default settings
- **THEN** they generate rich scenario, evaluation, queue simulation, and plot-input diagnostics without requiring excessive runtime or memory

### Requirement: Dense internal notebook defaults with fast mode
The internal diagnostic notebooks SHALL support dense diagnostic defaults and an explicit fast mode for quicker refreshes.

#### Scenario: Fast mode limits diagnostic workload
- **WHEN** notebook fast mode is enabled
- **THEN** scenario counts, Monte Carlo repetitions, plot density, expensive diagnostics, and non-required pipeline artifact generation are reduced while preserving representative outputs for execution-error checks

#### Scenario: Fast mode avoids paired output refresh
- **WHEN** a fast notebook error check is run with `NOTEBOOK_FAST=1`
- **THEN** Jupytext writes the executed notebook to a temporary `/tmp` output rather than creating or overwriting the paired `.ipynb` artifact

#### Scenario: Full mode uses complete artifact generation
- **WHEN** an internal diagnostic notebook is executed without fast mode for full evaluation or paired output refresh
- **THEN** the notebook uses dense defaults and full pipeline artifact generation unless the notebook explicitly documents a narrower requirement

### Requirement: Paired notebook outputs are refreshable
The internal diagnostic notebooks SHALL produce paired outputs that can be regenerated reproducibly.

#### Scenario: Paired outputs refresh reproducibly
- **WHEN** paired internal diagnostic notebooks or notebook-output refresh commands are run with a fixed seed
- **THEN** paired tables, plot inputs, scenario summaries, and generated artifacts are refreshed consistently and documented as reproducible outputs

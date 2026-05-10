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

### Requirement: Changed notebooks use fast validation
Changed Jupytext notebook `.py` sources SHALL be validated with the fast notebook execution command before the change is considered complete, unless the user explicitly requests full notebook execution instead.

#### Scenario: Fast validation runs after notebook source change
- **WHEN** a notebook `.py` source file is changed
- **THEN** the changed notebook is executed with `NOTEBOOK_FAST=1`, `uv run jupytext --to ipynb --execute --run-path notebooks`, and an output path under `/tmp`

#### Scenario: Fast validation does not refresh paired notebook artifact
- **WHEN** fast validation is run after a notebook source change
- **THEN** the paired repository `.ipynb` artifact is not created or overwritten by the validation command

### Requirement: Full notebook execution is explicit
Full non-fast notebook execution SHALL be reserved for requested full rerenders, paired `.ipynb` refreshes, analyst-visible output synchronization, or full-workload validation.

#### Scenario: User requests paired output refresh
- **WHEN** the user requests a complete notebook rerender, paired `.ipynb` refresh, analyst-visible output sync, or full-workload validation
- **THEN** the notebook is executed without `NOTEBOOK_FAST=1` using the documented full Jupytext command that updates the paired notebook outputs

#### Scenario: Routine notebook source change does not imply full rerender
- **WHEN** a notebook `.py` source changes and the user has not requested a full rerender or paired output refresh
- **THEN** routine validation uses the fast `/tmp` execution path instead of updating paired `.ipynb` outputs

### Requirement: Material notebook workloads support fast mode
Notebook sources that perform material pipeline workloads SHALL provide a fast execution path when needed to keep routine notebook validation practical and representative.

#### Scenario: Notebook performs repeated or expensive pipeline execution
- **WHEN** a notebook performs repeated pipeline runs, dense diagnostics, simulations, or other expensive execution during normal cell evaluation
- **THEN** `NOTEBOOK_FAST=1` reduces non-required workload while preserving representative outputs for execution-error checks

#### Scenario: Fast mode preserves displayed output requirements
- **WHEN** a notebook uses fast mode
- **THEN** the reduced workload still produces the result objects and tables required by the executed notebook cells

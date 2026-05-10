## ADDED Requirements

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

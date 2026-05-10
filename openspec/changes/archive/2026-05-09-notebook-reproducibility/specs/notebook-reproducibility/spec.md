## MODIFIED Requirements

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

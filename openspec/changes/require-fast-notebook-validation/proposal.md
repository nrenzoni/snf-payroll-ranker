## Why

Recent notebook changes exposed execution errors that were not caught during the AI development cycle because changed notebooks were not consistently validated through the documented fast Jupytext path. The project needs a spec-level requirement that notebook source changes receive a quick, non-destructive execution check, while still preserving the full rerender workflow for explicitly requested paired `.ipynb` refreshes.

## What Changes

- Require changed Jupytext notebook `.py` sources to be validated with the fast `NOTEBOOK_FAST=1` Jupytext execution path that writes executed notebooks under `/tmp`.
- Clarify that full non-fast notebook execution is used when the user requests a complete rerender, paired `.ipynb` refresh, analyst-visible output synchronization, or full-workload validation.
- Ensure notebooks that perform material pipeline work support a fast execution path where needed so the standard validation command remains practical.
- Update contributor guidance so future AI development cycles run the fast notebook check after notebook changes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `notebook-reproducibility`: Add requirements for fast validation after notebook source changes and for choosing fast versus full Jupytext execution modes.

## Impact

- Affected docs: `AGENTS.md` notebook workflow and verification guidance.
- Affected notebooks: recently added or changed notebooks that perform enough pipeline work to need `NOTEBOOK_FAST` support, especially SNF case-study notebooks.
- Affected verification: notebook changes should include a fast Jupytext execution check for the changed notebook source, plus existing `prek` verification.
- No breaking API, schema, dependency, or persisted data changes are intended.

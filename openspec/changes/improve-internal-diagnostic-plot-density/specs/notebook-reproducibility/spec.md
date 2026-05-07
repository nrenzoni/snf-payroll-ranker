## ADDED Requirements

### Requirement: Dense internal notebook defaults with fast mode
The internal diagnostic notebooks SHALL use bounded defaults that are dense enough for useful rendered plots and SHALL document fast-mode constants that can be reduced locally.

#### Scenario: Internal statistical notebook renders dense diagnostics
- **WHEN** `notebooks/06_internal_statistical_diagnostics.py` runs with default settings
- **THEN** it evaluates multiple calibrated scenarios and seeds, displays scenario sanity summaries, and renders component superiority, effect-size, subgroup, calibration, robustness, and perturbation plots with visible contrast or explicit sparse-condition context

#### Scenario: Internal queue notebook renders dense threshold-demand diagnostics
- **WHEN** `notebooks/07_simulation_and_stress_testing.py` runs with default settings
- **THEN** it displays queue scenario sanity summaries and renders threshold-grid or adaptive-threshold demand, overload, dollar capture, missed exposure, and stress-test plots with non-empty scenario-dependent views

#### Scenario: Fast mode is explicit
- **WHEN** a user reviews notebook setup cells or README documentation
- **THEN** the bounded default scenario counts, seed counts, sample counts, employee counts, pay-period counts, queue iteration counts, and fast-mode reduction constants are identified

#### Scenario: Business-facing notebooks remain independent
- **WHEN** internal diagnostic notebooks use denser scenario suites
- **THEN** notebooks `01` through `05` remain available as the business-facing sequence and do not require the internal diagnostic plot-density scenario suite

### Requirement: Paired notebook outputs are refreshable
The internal diagnostic notebook source and paired outputs SHALL be refreshable after plot-density changes.

#### Scenario: Internal paired outputs reflect updated notebook logic
- **WHEN** paired `.ipynb` files for notebooks `06` and `07` are committed or regenerated
- **THEN** they reflect the updated scenario defaults, sanity summary cells, and dense plot inputs from the corresponding Jupytext `.py` files

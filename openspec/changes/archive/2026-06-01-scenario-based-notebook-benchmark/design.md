## Context

The active notebook already runs the employee-pay-cycle pipeline end to end, but its main narrative is built from a single synthetic `PayrollConfig` run. The codebase also already has scenario-aware generation hooks through `ScenarioSpec`, existing scenario catalogs, and some scenario-seed aggregation helpers in diagnostics, but those helpers are not aligned with the employee-cycle notebook's public reporting path. The requested change is cross-cutting: it updates notebook reporting contracts, expands the implemented synthetic DGP scenario suite, and adds scenario-seed aggregation outputs that become the main evidence for model selection.

Constraints:

- The notebook source of truth remains `notebooks/snf_payroll_ranker_report.py`; `.ipynb` files are derived artifacts.
- Tabular artifacts should stay as Polars DataFrames and public multi-value returns should use typed dataclass result objects.
- The active interpretation must remain leakage-safe and percent-budget based.
- Some requested scenarios fit existing `ScenarioSpec` hooks, while others require explicit generator controls so they are real behavioral shifts rather than renamed metadata.

## Goals / Non-Goals

**Goals:**

- Make the notebook's main conclusion depend on aggregated `scenario x seed x model x review budget x metric` evidence instead of one baseline run.
- Expand the implemented DGP scenario catalog to the requested eight-scenario suite with notebook-visible descriptions.
- Add employee-cycle benchmark assembly helpers that produce scenario catalog, scenario-seed design, winner frequency, median metric summaries with intervals, and winner-map inputs.
- Keep section 2 and section 4 aligned with the new scenario-family framing while preserving a small amount of baseline-only illustrative output where useful.
- Update OpenSpec contracts so the new narrative and scenario coverage are required behavior rather than notebook drift.

**Non-Goals:**

- Running the full 10-seed benchmark sweep by default during notebook validation.
- Replacing the core employee-cycle model training stack or metric definitions.
- Introducing notebook-only scenario logic that bypasses `src/payroll_anomaly_ranking/` runtime paths.
- Redesigning appendix material beyond what is needed to keep references consistent with the new main study framing.

## Decisions

### Decision: Add employee-cycle benchmark helpers in `src` rather than building the aggregation inline in the notebook

The notebook needs multiple scenario-seed outputs, and similar logic will likely be reused by tests and future diagnostics. A typed helper module under `src/payroll_anomaly_ranking/` should run scenario-seed employee-cycle pipelines and return a named dataclass containing the aggregated Polars DataFrames the notebook needs.

Why this over notebook-local loops:

- Keeps the notebook focused on presentation.
- Preserves typed runtime contracts for scenario-seed benchmark outputs.
- Makes it easier to test the aggregation logic outside notebook execution.

Alternative considered: build all scenario loops in the notebook. Rejected because it would duplicate runtime logic, make testing harder, and increase the chance that notebook outputs drift from the supported employee-cycle pipeline behavior.

### Decision: Keep the benchmark multi-seed capable but default the notebook to one seed for now

The requested study design is explicitly multi-seed, but current runtime cost would grow materially if the notebook immediately runs all ten seeds across eight scenarios and all models. The benchmark API should therefore accept an arbitrary seed tuple, while the notebook defaults to `(42,)` for now and documents that the full multi-seed sweep is the intended post-run configuration.

Why this over hard-coding ten seeds immediately:

- Preserves the target experimental unit and aggregation contract now.
- Keeps notebook validation and normal authoring loops tractable.
- Avoids designing a single-seed-only API that would need to be replaced later.

Alternative considered: defer all seed support until later. Rejected because the notebook framing would again drift from the intended benchmark design.

### Decision: Expand `ScenarioSpec` and generator hooks only where the existing controls are insufficient

Some requested scenarios can reuse existing anomaly-plan and drift-plan hooks, such as temporal payroll drift or anomaly-family concentration changes. Others require new controls around timekeeping-noise rates, facility heterogeneity, severity/dollar tails, subtle residual filtering, and observed-correction selection bias. The implementation should extend the scenario contract minimally to cover these cases instead of inventing a parallel scenario system.

Why this over encoding scenarios as notebook metadata only:

- Ensures scenario differences are reflected in generated payroll and labels.
- Keeps scenario behavior reproducible for fixed seeds.
- Preserves one scenario-control surface for generator, evaluation, and notebook reporting.

Alternative considered: reuse the current scenario names and relabel them in the notebook. Rejected because it would not create the real DGP suite requested by the change.

### Decision: Retain one baseline run for examples, but move all headline winner language to aggregated study outputs

Sections such as feature examples, top residual records, and model similarity diagnostics are easier to understand with a single scored dataset. Those examples should remain baseline illustrations. However, executive summary language, section 8 winner claims, and operating-objective recommendations must come from scenario-seed aggregation outputs only.

Why this over removing all single-run views:

- Keeps the notebook readable and concrete.
- Avoids converting every explanatory table into a cross-scenario artifact.
- Separates illustrative local views from benchmark-level conclusions.

Alternative considered: keep current section 8 and append scenario tables later. Rejected because it would continue to privilege one run as the main result.

## Risks / Trade-offs

- [Runtime growth from scenario-seed loops] -> Keep notebook defaults to one seed for now, reuse validation-mode reductions, and design helpers so tests can run reduced scenario subsets.
- [Scenario controls become too ad hoc] -> Keep new controls inside typed scenario dataclasses and generator functions, with explicit metadata describing what changed per scenario.
- [Notebook and spec drift during transition] -> Update notebook-reporting, synthetic-data, and evaluation specs in the same change as the notebook implementation.
- [Intervals based on one seed can be overinterpreted] -> Require notebook text to explain that seeds estimate random-draw stability within a DGP and that structural robustness comes from comparing scenarios.
- [Benchmark helpers accidentally duplicate evaluation behavior] -> Reuse existing employee-cycle scoring and metric functions instead of redefining metrics in the aggregation layer.

## Migration Plan

No external deployment or persisted-data migration is required.

Implementation migration sequence:

1. Update OpenSpec contracts for notebook reporting, synthetic scenario coverage, and evaluation aggregation.
2. Extend scenario definitions and generator controls to support the new DGP suite.
3. Add typed employee-cycle benchmark helpers that run scenario-seed aggregation and produce notebook-ready frames.
4. Rewrite notebook sections 0, 2, 4, and 8 to use the new benchmark outputs.
5. Validate with notebook validation execution, formatting/linting, smoke tests, and targeted notebook/reporting regression coverage.

Rollback strategy:

- Revert the change set to restore the prior single-run notebook framing and previous scenario catalog if the new benchmark helpers or runtime cost prove unworkable.

## Open Questions

- Should the notebook's default rendered seed remain exactly `(42,)`, or should validation mode use one seed while normal full runs use a small multi-seed default such as `(42, 43, 44)`?
- What interval convention should section 8 use for the median metric table when only one seed is rendered: scenario quantiles only, bootstrap-on-units, or empty/placeholder interval columns until larger runs are executed?
- Should the new scenario suite replace the old notebook-facing aliases entirely, or should legacy aliases remain only for backwards-compatible internal diagnostics?

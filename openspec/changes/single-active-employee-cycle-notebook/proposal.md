## Why

The repository's active docs and specs still describe notebook-sequence contracts that were built around older shift-level and split-notebook narratives, while the active runtime has moved to employee-pay-cycle outputs. Replacing those older contracts with one active employee-pay-cycle notebook is needed now so the reporting surface, reproducibility rules, and production-candidacy story all point to the same current workflow.

## What Changes

- **BREAKING** Replace the active multi-notebook reporting contract with one primary Jupytext percent-format notebook under `notebooks/` for the employee-pay-cycle program.
- Define the notebook's required section order as: Executive Summary, Problem Framing, Data-Generating Process, Simulation Sanity Checks, Label Engineering, Feature Engineering, Model Formulations, Main Queue-Based Results, Generalization Results, Ablation Studies, Deep Diagnostics, Model Explanation and Reviewer UX, Robustness / Stress Tests, Final Production Recommendation, and Technical Appendix.
- Require the Technical Appendix to cover metric implementation details, full ablation matrix, hyperparameter search details, extra calibration plots, full stress-test grid, feature importance by split, per-facility diagnostics, label-bias simulation variants, and mathematical ranking objective notes.
- Update active notebook, evaluation, feature-engineering, and synthetic-data specs so they describe the employee-pay-cycle notebook as the active deliverable rather than a legacy shift-level or multi-notebook sequence.
- Add an explicit employee-pay-cycle label contract for `relevance_grade` and `net_utility` so the notebook's label-engineering section, ranking formulation, and business-value evaluation are backed by real pipeline artifacts rather than aspirational prose.
- Update README and notebook documentation so they reference the single active notebook and clearly demote older notebook-sequence materials to historical reference.
- Align implementation tasks with the active runtime by fixing employee-cycle notebook blockers such as leakage-sensitive formulation wiring and missing employee-cycle diagnostic artifacts needed by the notebook contract.

## Capabilities

### New Capabilities
- `employee-cycle-notebook-reporting`: Defines the single active employee-pay-cycle notebook contract, its fixed section mapping, and appendix requirements.

### Modified Capabilities
- `notebook-reproducibility`: Replace notebook-sequence language with single-notebook execution, documentation, and fast-validation requirements.
- `payroll-anomaly-evaluation`: Replace the separate technical-validation-notebook requirement with sections inside the single active notebook and align evaluation evidence with employee-pay-cycle reporting.
- `payroll-review-queue`: Replace multi-notebook business-case-study requirements and README sequence documentation with the single active notebook contract.
- `synthetic-payroll-data`: Update notebook-facing synthetic-data documentation requirements to point to the active employee-pay-cycle notebook rather than old problem-framing sequence assumptions.
- `payroll-anomaly-scoring`: Update notebook walkthrough requirements so feature-engineering and formulation explanations live in the single active employee-pay-cycle notebook.

## Impact

- Affected specs: `openspec/specs/notebook-reproducibility/spec.md`, `payroll-anomaly-evaluation/spec.md`, `payroll-review-queue/spec.md`, `synthetic-payroll-data/spec.md`, `payroll-anomaly-scoring/spec.md`, plus a new `employee-cycle-notebook-reporting` capability.
- Affected synthetic-label contract: employee-pay-cycle outputs, evaluation artifacts, and notebook narrative now need explicit `relevance_grade` and `net_utility` fields with documented business semantics.
- Affected docs: `README.md`, `notebooks/README.md`, notebook execution examples, and active notebook discovery text.
- Affected notebook sources: add one new active Jupytext notebook under `notebooks/`; legacy notebook sources remain historical reference only.
- Affected runtime code: employee-pay-cycle scoring, evaluation, queue simulation, and diagnostic helpers needed to support the notebook sections without leakage or miswired artifacts.
- Verification impact: requires fast notebook execution for the new notebook, `uv run prek run --all-files`, smoke tests, and targeted evaluation/notebook regression checks.

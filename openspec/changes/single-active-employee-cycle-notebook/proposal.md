## Why

The repository's active docs and specs still describe notebook-sequence contracts that were built around older shift-level and split-notebook narratives, while the active runtime has moved to employee-pay-cycle outputs. Replacing those older contracts with one active employee-pay-cycle notebook is still needed, but the notebook now also needs a tighter stage-2 objective: after critical hard rules remove obvious payroll problems, compare ML formulations on the residual employee-pay-cycle universe to see which best prioritizes ambiguous payroll records under limited review capacity.

## What Changes

- **BREAKING** Replace the active multi-notebook reporting contract with one primary Jupytext percent-format notebook under `notebooks/` for the employee-pay-cycle program.
- Define the notebook's required section order as: `0. Executive Summary`, `1. Problem Framing: Residual Payroll Review After Hard Rules`, `2. Synthetic SNF Payroll Data Generation`, `3. Hard Rule Gate: Defining the Residual Universe`, `4. Simulation Sanity Checks for the Residual Dataset`, `5. Label Engineering for Residual Ranking`, `6. Feature Engineering for Ambiguous Payroll Records`, `7. Model Formulations`, `8. Main Results: Residual Queue Evaluation`, `9. Ablation Studies`, `10. Diagnostics, Explanations, and Final Recommendation`, and `11. Technical Appendix`.
- Define the notebook as a stage-2 payroll review experiment: hard rules are an upstream gate, not a competing model in section `7`, and all ML formulation comparisons are performed only on residual records not flagged by critical hard rules.
- Require the Technical Appendix to cover data dictionary, hard rule definitions, metric definitions, ranking group construction, handling zero-positive residual groups, hyperparameter search space, additional ablation tables, additional calibration plots, and stress-test configurations.
- Update active notebook, evaluation, feature-engineering, review-queue, and synthetic-data specs so they describe the employee-pay-cycle notebook as the active residual-ranking deliverable rather than a legacy shift-level or multi-notebook sequence.
- Add an explicit employee-pay-cycle residual label contract for latent residual `y_issue`, residual `y_dollar`, `relevance_grade`, `rule_missed_severe_issue`, and evaluation-only `net_utility` so the notebook's label-engineering section, ranking formulation, and business-value evaluation are backed by real pipeline artifacts rather than aspirational prose.
- Explicitly exclude compliance, PBJ, and HPRD staffing metrics from notebook targets, features, and evaluation metrics. The notebook focuses on payroll financial leakage and correction risk, not regulatory staffing issues.
- Update README and notebook documentation so they reference the single active notebook and clearly demote older notebook-sequence materials to historical reference.
- Align implementation tasks with the active runtime by fixing employee-cycle notebook blockers such as leakage-sensitive formulation wiring and missing employee-cycle diagnostic artifacts needed by the notebook contract.

## Capabilities

### New Capabilities
- `employee-cycle-notebook-reporting`: Defines the single active employee-pay-cycle notebook contract, its residual-ranking section mapping, and appendix requirements.

### Modified Capabilities
- `notebook-reproducibility`: Replace notebook-sequence language with single-notebook execution, documentation, and fast-validation requirements.
- `payroll-anomaly-evaluation`: Replace the separate technical-validation-notebook requirement with sections inside the single active notebook and align evaluation evidence with residual employee-pay-cycle ranking.
- `payroll-review-queue`: Replace multi-notebook business-case-study requirements and README sequence documentation with the single active notebook contract and residual finance/payroll review framing.
- `synthetic-payroll-data`: Update notebook-facing synthetic-data documentation requirements to point to the active employee-pay-cycle notebook and require both hard-rule-caught and rule-missed residual issues.
- `payroll-anomaly-scoring`: Update notebook walkthrough requirements so feature-engineering and ML formulation explanations live in the single active residual employee-pay-cycle notebook.

## Impact

- Affected specs: `openspec/specs/notebook-reproducibility/spec.md`, `payroll-anomaly-evaluation/spec.md`, `payroll-review-queue/spec.md`, `synthetic-payroll-data/spec.md`, `payroll-anomaly-scoring/spec.md`, plus a new `employee-cycle-notebook-reporting` capability.
- Affected synthetic-label contract: employee-pay-cycle outputs, evaluation artifacts, and notebook narrative now need explicit residual `y_issue`, `y_dollar`, `relevance_grade`, `rule_missed_severe_issue`, and `net_utility` fields with documented business semantics.
- Affected docs: `README.md`, `notebooks/README.md`, notebook execution examples, and active notebook discovery text.
- Affected notebook sources: add one new active Jupytext notebook under `notebooks/`; legacy notebook sources remain historical reference only.
- Affected runtime code: employee-pay-cycle rule gating, scoring, evaluation, queue simulation, and diagnostic helpers needed to support residual-universe notebook sections without leakage or miswired artifacts.
- Verification impact: requires fast notebook execution for the new notebook, `uv run prek run --all-files`, smoke tests, and targeted evaluation/notebook regression checks.

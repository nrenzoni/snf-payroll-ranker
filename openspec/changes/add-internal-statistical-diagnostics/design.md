## Context

The current repository uses a notebook-library pattern around a reproducible synthetic payroll pipeline. The simulator creates one baseline synthetic world, injects anomalies, and the pipeline evaluates rule, statistical, ML, and hybrid anomaly scores with temporal review-budget metrics.

The next step is to add internal data science diagnostics before any future supervised ranking path. These diagnostics need controlled scenario generation, repeatable Monte Carlo runs, subgroup-level statistical summaries, calibration checks, and advanced visualization helpers. The current simulator is functional and readable, but most scenario behavior is hard-coded in `data.py`, which makes drift and change-point experiments difficult to control.

## Goals / Non-Goals

**Goals:**

- Preserve the existing business-facing notebook sequence and add separate internal notebooks for deeper statistical diagnostics and simulation stress tests.
- Refactor payroll generation into explicit baseline, anomaly, drift, and change-point stages without changing the public meaning of the default synthetic dataset.
- Add dataclass-based scenario specifications for reproducible anomaly-mix, drift, change-point, and queue-capacity experiments.
- Add reusable statistical summary functions for Bayesian-style review-budget intervals, subgroup shrinkage diagnostics, expected-pay calibration, robustness summaries, exposure calibration, and perturbation sensitivity.
- Add reusable queue simulation functions that consume scored outputs and model review capacity, overload risk, and dollars captured under operational constraints.
- Add LetsPlot chart helpers for internal diagnostic plots and keep heavy logic out of notebooks.
- Document and execute internal notebooks separately from the required polished business-facing notebook sequence.

**Non-Goals:**

- Do not add supervised learning-to-rank models.
- Do not train models on synthetic injected labels.
- Do not replace the existing `run_pipeline(...)` orchestration surface.
- Do not introduce a chainable `ScenarioBuilder` API in this change.
- Do not add heavyweight Bayesian/MCMC dependencies unless already available numerical summaries are insufficient.
- Do not claim production integrations, analyst feedback systems, or live scheduling.

## Decisions

### Use dataclass scenario specs, not a full builder pattern

Scenario control will be represented with simple dataclasses such as `ScenarioSpec`, `AnomalyPlan`, `DriftPlan`, `ChangePointEvent`, and `QueueSimulationSpec`.

Rationale: dataclasses keep scenario inputs explicit, serializable, testable, and easy to construct in notebooks. A chainable builder API would add indirection before scenario semantics are proven.

Alternative considered: a full class-style builder with chained methods. Rejected for now because it would be more ceremony than value in a notebook-first project and could obscure the transparent simulator logic.

### Keep payroll generation and queue operations separate

Payroll generation will create records and synthetic evaluation truth. Queue simulation will consume scored records, metrics, or queues after scoring.

Rationale: analyst capacity, delays, and overload risk are operational simulations, not payroll data-generation facts. Keeping them separate preserves the current pipeline boundaries and makes tests simpler.

Alternative considered: embedding capacity simulation directly in `generate_payroll(...)`. Rejected because it would mix source-data simulation with downstream workflow simulation.

### Keep advanced diagnostics internal

The existing notebooks `01` through `05` will remain the business-facing case study. New internal notebooks will be added for statistical diagnostics and simulation stress testing.

Rationale: the advanced plots are valuable for model governance and DS review, but too dense for the current business-facing flow.

Alternative considered: adding all advanced plots to notebook `03`. Rejected because it would dilute the clear stakeholder evaluation narrative.

### Prefer closed-form and bootstrap summaries over new probabilistic dependencies

Bayesian-style intervals will use closed-form Beta/Binomial summaries, Bayesian bootstrap, empirical Bayes approximations, or simulation from simple distributions where feasible. Empirical-Bayes or partial-pooling subgroup estimates satisfy the baseline hierarchical requirement; full MCMC can be added later as a non-blocking enhancement if it materially improves the diagnostics.

Rationale: this keeps dependencies stable and implementation lightweight while still producing credible intervals, posterior-like comparisons, and uncertainty plots.

Alternative considered: adding PyMC/Stan-style MCMC. Rejected for this change because it would add runtime, dependency, and explanation cost that is not required for the planned diagnostics.

### Build table-producing functions before chart functions

Analysis functions will produce Polars DataFrames. Chart helpers will consume those tables.

Rationale: table-first outputs are easier to test, export, and inspect in notebooks. It also supports future dashboarding or CSV artifact writing without rewriting chart code.

Alternative considered: implementing diagnostics directly as notebook cells. Rejected because that would reduce testability and reuse.

### Split observable and evaluation-only queue simulation impact

Queue simulation will report production-observable missed estimated exposure separately from evaluation-only missed synthetic anomaly dollars.

Rationale: estimated exposure is available in realistic operations, while synthetic anomaly dollars are only available for internal evaluation. Splitting these fields prevents leakage confusion and keeps business and evaluation interpretations distinct.

Alternative considered: a single `missed_exposure` field. Rejected because it would be ambiguous and could conflate model-estimated exposure with injected evaluation truth.

### Store scenario metadata outside analyst-safe outputs

Scenario metadata will be exposed through pipeline result objects and optional internal evaluation artifacts, not analyst-safe queue rows or model feature columns.

Rationale: simulation controls must be auditable for internal notebooks without weakening analyst-safe output boundaries or feature leakage guarantees.

Alternative considered: adding scenario columns to every payroll row or review queue row. Rejected because row-level metadata is unnecessary for most diagnostics and could blur operational/evaluation separation.

### Define payroll-total shifts as row-level multipliers

Payroll-total shift scenario events will apply row-level multipliers, optionally with bounded noise, to matching subgroup-period records instead of solving for an exact aggregate target.

Rationale: multiplier semantics are simple, reproducible, interpretable, and easy to test. Exact aggregate target solving adds unnecessary complexity for the first simulation layer.

Alternative considered: solving row changes to hit an exact department or subgroup total. Rejected for this change because it increases implementation complexity without improving the intended stress-test value.

## Risks / Trade-offs

- Simulator refactor changes baseline data behavior unintentionally -> Preserve default scenario behavior with regression-style smoke tests on schema, row counts, label presence, validation failures, and reproducibility.
- Scenario controls become too generic or hard to understand -> Start with a small set of concrete events: anomaly mix shift, pay-code drift, overtime shock, department payroll shift, deduction policy shift, and queue capacity volatility.
- Internal notebooks become slow -> Use modest default sample counts, expose simulation counts through specs/config, and keep reusable functions efficient with Polars operations.
- Bayesian terminology overstates rigor -> Label outputs as Bayesian-style or posterior simulation diagnostics where they use approximations, and document assumptions in the internal notebook narrative.
- Subgroup diagnostics overinterpret synthetic labels -> Keep injected labels explicitly evaluation-only and frame subgroup results as synthetic stress-test evidence, not real-world fairness or fraud findings.
- New chart helpers bloat `charts.py` -> Keep complex table preparation in analysis modules and only put reusable rendering helpers in chart modules.

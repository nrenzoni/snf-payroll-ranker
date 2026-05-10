## Context

The current pipeline is a generic synthetic payroll anomaly ranking system at employee-pay-period grain. It generates corporate departments and job families, scores generic payroll anomalies, and presents analyst-oriented review queues. The target project direction is now a skilled nursing facility payroll approval assistant for administrator teams that approve weekly payroll under time pressure.

The replacement domain requires shift-level synthetic records because the highest-value SNF exceptions depend on schedule, timeclock, shift windows, role, facility, unit, and premium-pay eligibility. Pay-period/facility summaries remain necessary for leader views, but the scoring grain should be shift-level payroll lines or shift-pay-code records.

Implementation must preserve the existing engineering standards: Polars-first tabular processing, explicit pipeline stages, leakage-safe feature engineering, typed dataclass result objects, schema constants/enums instead of raw strings, reproducibility by seed, and notebook source of truth in Jupytext `.py` files.

## Goals / Non-Goals

**Goals:**

- Fully replace generic corporate payroll generation, features, scenarios, notebooks, README narrative, and review outputs with SNF shift-level payroll approval framing.
- Model a synthetic multi-facility SNF chain with facilities, units, roles, shift schedules, timeclock context, pay policies, payroll lines, anomaly labels, and pay-period/facility rollups.
- Engineer the data generator as typed domain simulation infrastructure using `StrEnum` vocabularies, dataclass configuration/results, builder stages, deterministic seeds, early validation, and scenario metadata.
- Implement two initial SNF case studies: overtime/double-shift staffing pressure and premium pay/shift differential mismatch.
- Document future scenario families in the scenario catalog without implementing them initially.
- Rebuild feature engineering for stationarity, entropy, facility normalization, peer transferability, schedule/timeclock reconciliation, premium eligibility, fatigue/rest gaps, and review-safe exposure estimates.
- Compare automated ranking against administrator-style threshold baselines for gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance.
- Produce administrator-facing pre-approval outputs with concise reasons, source-to-check context, recommended actions, approval risk categories, and facility/pay-period summaries.

**Non-Goals:**

- Do not preserve generic corporate payroll compatibility or legacy output semantics unless a test or spec requires temporary migration during implementation.
- Do not implement agency/float labor, census/acuity, credential/license compliance, PBJ category, meal break premium, union-contract, or new-client bootstrap scenarios in the initial change; document them as future scenario families.
- Do not claim legal compliance, clinical staffing adequacy, live payroll integrations, production scheduling integrations, or real client data support.
- Do not edit paired `.ipynb` files directly.

## Decisions

### Shift-Level Payroll Line Grain

Use shift-level payroll lines as the primary modeling and scoring grain, then derive pay-period/facility rollups for summaries.

Rationale: SNF overtime, double shifts, shift differentials, weekend/holiday premiums, and schedule/timeclock mismatches are shift-context problems. Employee-pay-period aggregation hides the evidence administrators need to approve or question a record.

Alternative considered: retain employee-pay-period grain and add summarized shift features. This is simpler but weakens case-card explainability and makes premium eligibility validation indirect.

### Typed Domain Builders

Replace monolithic generation with explicit builder stages:

- `FacilityBuilder`: facility profiles, regions, size tiers, payroll maturity, staffing pressure.
- `EmployeeBuilder`: synthetic employees, home facility, role, license type, tenure, base rate, shift preference, employment status.
- `ScheduleBuilder`: scheduled shifts by facility, unit, role, date, shift type, and planned hours.
- `TimeclockBuilder`: actual worked shifts, clock variance, missed punches, manual edits, approval status.
- `PayrollLineBuilder`: pay-code lines, hours, rates, multipliers, premium amounts, gross pay, net-pay proxy, and source context.
- `SNFAnomalyInjector`: scenario-specific observable changes and evaluation-only labels.
- `RollupBuilder`: pay-period/facility and pay-period/employee summaries derived from shift lines.
- `ValidationRunner`: config, referential, schema, policy, scenario, and reconciliation validation.

Rationale: The generator will be complex enough that stage boundaries and typed result objects are necessary to fail early and keep tests targeted.

Alternative considered: add SNF branches to existing `data.py`. This is faster initially but increases downstream failure risk, raw-string drift, and untestable coupling.

### Controlled Vocabularies With `StrEnum`

Add SNF-specific enums for controlled domains such as role, license type, unit type, shift type, labor source, pay-code category, approval status, source-to-check, recommendation, scenario family, and anomaly category.

Rationale: SNF feature engineering and validation depends on stable categorical semantics. Enums make invalid states explicit and reduce typo-driven downstream failures.

Alternative considered: plain string constants. This keeps code shorter but weakens typing, validation, and Pyrefly coverage.

### Early Validation Boundaries

Run validation at each major boundary: config creation, policy setup, facility generation, employee generation, schedule generation, timeclock generation, payroll line construction, anomaly injection, and rollup reconciliation.

Rationale: Complex synthetic data can otherwise fail indirectly during feature engineering or notebooks. Early errors should identify the invalid policy, scenario, or relation that caused the issue.

Alternative considered: one final validation pass. This is simpler but makes failures harder to diagnose and allows invalid intermediate data to contaminate labels/features.

### Feature Engineering For Transferability

Prioritize stationary and normalized features over raw dollars and raw hours. Use ratios, robust deviations, percentiles, trailing baselines, facility-profile normalization, role/shift peers, and leakage-safe prior-period references.

Rationale: Future client facilities will differ in scale, wage rates, staffing pressure, and pay policies. Transferable features should normalize within facility, role, shift, pay-code category, and comparable facility groups while retaining enough entropy to distinguish legitimate high-pay shifts from unsupported exceptions.

Alternative considered: rely primarily on raw gross pay, net pay, overtime hours, and Isolation Forest. This mirrors manual thresholds too closely and undercuts the value story.

### Administrator Approval Outputs

Rename and reframe analyst outputs as weekly pre-approval exceptions. Queue rows and case cards should include approval risk category, recommended action, source to check, concise reason, expected-vs-actual context, supporting context status, and estimated exposure.

Rationale: The user is not a dedicated payroll analyst team. SNF administrators need a short, action-oriented approval checklist, not a forensic analysis workbench.

Alternative considered: keep analyst-facing review queue terminology. This misrepresents the workflow and makes the notebooks less persuasive to SNF operators.

### Manual Threshold Baselines

Implement threshold baselines that mirror administrator-configured controls: gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled hours, and facility payroll variance. Do not lead with manual adjustment thresholds.

Rationale: The project should demonstrate value over the current production pattern of manually configured thresholds on fields administrators already understand.

Alternative considered: compare only against existing rule/statistical/ML scoring components. That validates models but does not clearly show business value over the current process.

## Risks / Trade-offs

- Large breaking domain replacement could destabilize existing notebooks and tests -> Implement behind a clear OpenSpec task sequence, update tests with schema-first milestones, and verify smoke/integration checks after each major stage.
- Shift-level synthetic generation may introduce row-volume and runtime growth -> Keep default demo sizes bounded, use vectorized Polars/NumPy generation where feasible, and reserve dense diagnostics for internal notebooks.
- Realistic SNF policies can imply legal/payroll advice -> Use configurable synthetic policies, document that policies are illustrative, and avoid state-specific compliance claims.
- Feature engineering can become too complex for administrator explanations -> Keep internal score components rich but translate outputs into concise approval reasons and source-to-check actions.
- Scenario injection can create label leakage if injected columns or dollar impacts enter scoring -> Keep evaluation labels separate, enforce leakage checks, and test model feature columns and queue outputs.
- Facility normalization can hide high-risk facility-wide events if over-normalized -> Preserve separate facility rollup alerts and combine normalized record-level features with absolute estimated exposure.
- Future scenario catalog may look like implemented capability -> Mark future scenario families as documented-only until implementation tasks/specs are added.

## Migration Plan

1. Add SNF schema enums, config dataclasses, result dataclasses, and validation contracts.
2. Replace synthetic generation with typed builder stages and write new shift-level/payroll-line outputs plus derived rollups.
3. Replace generic scenarios with two implemented SNF scenarios and documented future scenario families.
4. Rebuild features, rule flags, scoring, threshold baselines, explainability, evaluation, and review outputs around shift-level records.
5. Replace README and Jupytext notebook content with SNF payroll approval narrative and two case studies.
6. Update tests and verification commands for the new behavior.

Rollback is not expected to preserve generic payroll behavior because this change is intentionally breaking. If needed during implementation, use git history to recover the previous generic demo rather than adding compatibility shims.

## Open Questions

- Should net pay remain in the synthetic shift-level schema as a proxy field, or should the project focus on gross/pay-code approval context and only generate net pay in pay-period rollups?
- Should premium policy defaults include synthetic holiday calendars in the first implementation, or should holiday premiums be documented as future work while evening/night/weekend premiums are implemented first?

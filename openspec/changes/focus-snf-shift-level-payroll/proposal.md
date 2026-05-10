## Why

The project currently demonstrates a generic corporate payroll anomaly ranking workflow, but the target buyer and user workflow is skilled nursing facility weekly payroll approval. Reframing the project around shift-level SNF payroll, schedule, and timeclock data will better demonstrate value over manually configured gross, net, hours, and premium thresholds used by facility administrator teams.

## What Changes

- **BREAKING** Replace the generic employee-pay-period payroll generator with a shift-level SNF synthetic generator for a multi-facility chain.
- **BREAKING** Replace corporate departments, job families, commissions, and generic payroll narratives with SNF facilities, units, roles, shifts, pay codes, schedule context, timeclock context, and configurable pay policies.
- Add typed SNF domain architecture using dataclasses, `StrEnum` controlled vocabularies, explicit schema constants, builder-style generation stages, scenario metadata, and early validation failures.
- Add shift-level payroll records as the scoring grain, with pay-period/facility rollups generated for administrator and leader summaries.
- Add two initial high-value SNF case studies: overtime/double-shift staffing pressure and premium pay/shift differential mismatch.
- Add documentation for future SNF scenario families, including agency/float labor, census/acuity, credential/license mismatch, PBJ category mismatch, meal premiums, lifecycle, retro/rate corrections, union policy variation, new-client bootstrap, and payroll close adjustments.
- Rebuild feature engineering around stationarity, entropy, facility normalization, role/shift peers, schedule-timeclock reconciliation, premium eligibility, fatigue/rest gaps, exposure estimates, and transferability to new client facilities.
- Compare automated anomaly ranking against administrator-style manual threshold baselines such as gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance thresholds.
- Reframe review outputs from an analyst workbench to a weekly payroll approval assistant with concise review actions, approval risk categories, source-to-check context, and review-safe explanations.

## Capabilities

### New Capabilities

- `snf-payroll-approval-workflow`: Defines weekly SNF payroll approval assistant outputs, administrator-facing summaries, action-oriented case cards, and manual-threshold comparison framing.

### Modified Capabilities

- `synthetic-payroll-data`: Replace generic employee-pay-period synthetic payroll generation with shift-level SNF payroll, schedule, timeclock, pay policy, scenario, validation, and rollup generation.
- `payroll-anomaly-scoring`: Replace generic payroll features and rules with SNF shift-level, facility-normalized, schedule-aware, timeclock-aware, premium-eligibility, and approval-exposure scoring.
- `payroll-anomaly-evaluation`: Add evaluation requirements for automated ranking versus manual threshold baselines and case-study-specific SNF approval value metrics.
- `payroll-review-queue`: Replace analyst-oriented review queue framing with administrator-facing pre-approval exception queues, case cards, recommended actions, and facility/pay-period summaries.

## Impact

- Affects core schema constants and controlled vocabularies in `src/payroll_anomaly_ranking/columns.py` and likely new SNF domain modules.
- Replaces most synthetic generation behavior in `src/payroll_anomaly_ranking/data.py` with typed builder stages and validation boundaries.
- Updates scenario controls in `src/payroll_anomaly_ranking/scenarios.py` for implemented SNF scenarios and documented future scenario families.
- Rebuilds feature engineering, rule flags, scoring, explainability, presentation, validation, diagnostics, and queue generation around shift-level records and facility rollups.
- Replaces README and Jupytext notebook narrative with SNF weekly payroll approval framing; `.ipynb` artifacts remain generated outputs and should not be edited directly.
- Requires test updates for SNF schema generation, builder validation, leakage-safe feature engineering, anomaly injection, rollup reconciliation, manual threshold baselines, review-safe outputs, and notebook contracts.
- Verification should include `uv run pytest tests/smoke`, targeted integration tests for generation/scenarios/features/scoring/evaluation/notebook contracts, and `uv run prek run --all-files` after implementation.

## Why

The project's active direction needs to be corrected before more implementation builds on the wrong grain and outdated narrative. Employee-pay-cycle should be the canonical modeling object, Phase 1 should be framed as production-oriented research, and the older shift-level hybrid SNF workflow should remain only as legacy reference instead of continuing to define active requirements.

## What Changes

- **BREAKING** Recast the active project around employee-pay-cycle modeling instead of shift-level SNF approval scoring.
- **BREAKING** Reposition the project as a production-oriented payroll ranking library whose Phase 1 validates formulations for later operational promotion.
- Update active specs so scoring, evaluation, synthetic data, and review-queue requirements align with employee-pay-cycle grouped ranking research and reusable runtime-library goals.
- Add an explicit legacy-reference capability that keeps the older shift-level hybrid code and notebooks for traceability while excluding them from active runtime, research, production, and acceptance criteria.
- Update top-level documentation so README, architecture, and decision records clearly separate active direction from deprecated historical material.

## Capabilities

### New Capabilities
- `legacy-reference-code`: Defines how deprecated shift-level code and notebooks remain available for historical reference without participating in active runtime, research, or production paths.

### Modified Capabilities
- `synthetic-payroll-data`: Change the canonical generated modeling grain from shift-level rows to employee-pay-cycle records and align synthetic labels with the active research-to-production direction.
- `payroll-anomaly-scoring`: Change active scoring requirements from hybrid shift-level anomaly scoring to employee-pay-cycle ranking-library capabilities and phase-gated production promotion.
- `payroll-anomaly-evaluation`: Change active evaluation requirements to employee-pay-cycle grouped ranking research, formulation comparison, and production-candidacy validation.
- `payroll-review-queue`: Change the active queue definition from shift-level SNF approval review to employee-pay-cycle ranked review outputs built from the active library.
- `snf-payroll-approval-workflow`: Demote the old shift-level SNF workflow to deprecated historical reference rather than active implementation direction.
- `snf-admin-business-proof`: Demote the old hybrid business-value notebook narrative to deprecated historical reference rather than an active deliverable requirement.

## Impact

- Affected specs: `synthetic-payroll-data`, `payroll-anomaly-scoring`, `payroll-anomaly-evaluation`, `payroll-review-queue`, `snf-payroll-approval-workflow`, `snf-admin-business-proof`, plus new `legacy-reference-code`.
- Affected docs: `README.md`, `ARCHITECTURE.md`, `DECISIONS.md`, and follow-on notebook/runtime docs that still claim shift-level hybrid direction.
- Affected runtime planning: active modules will need to move toward employee-pay-cycle contracts, while deprecated shift-level code should be isolated under an explicitly marked legacy namespace or reference area.
- Verification for the doc/spec phase is documentation consistency review; implementation follow-up should run `uv run prek run --all-files` and targeted `uv run pytest` once runtime changes begin.

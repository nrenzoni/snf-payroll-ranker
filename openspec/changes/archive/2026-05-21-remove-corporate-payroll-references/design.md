## Context

The project is explicitly framed as a skilled nursing facility (SNF) weekly payroll approval assistant. All domain enums (`SNFRole`, `LicenseType`, `UnitType`, `ShiftType`, `PayCodeCategory`) are SNF-specific. However, test fixtures and schema constants still carry generic corporate payroll baggage:

- `tests/integration/test_regression.py` hardcodes `Finance` department, `Payroll` job family, `Remote` location, `salaried` pay type, and `SAL` pay code—none of which appear in real SNF shift-level payroll.
- `tests/integration/test_regression.py` also uses `Operations` as a department filter in drift/change-point tests.
- `columns.py` defines `COMMISSION` and `BONUS` as schema columns and includes them in `MODEL_FEATURE_COLUMNS`. Commission is a sales-specific concept; bonus is rare in hourly SNF payroll and not generated anyway.
- `data.py` emits `COMMISSION: 0.0`, `BONUS: 0.0`, and `RETRO_PAY: 0.0` for every synthetic record, signaling an inherited generic schema rather than a purpose-built SNF model.

These inconsistencies make the codebase harder to trust as a SNF-specific demonstration and violate the spec requirement that synthetic data avoid corporate values.

## Goals / Non-Goals

**Goals:**

- Replace all generic corporate values in test fixtures with SNF-specific ones.
- Remove `COMMISSION` and `BONUS` from the schema, model features, and synthetic generation.
- Decide whether `RETRO_PAY` should be removed entirely or retained as a future-scenario field (not a permanently zero placeholder).
- Ensure no downstream code references removed columns.

**Non-Goals:**

- Do not change any SNF-specific domain logic, feature engineering, scoring weights, or notebook narratives.
- Do not implement retroactive-pay scenarios now; only clean up the schema.
- Do not alter the behavior of legitimate SNF columns (e.g., `PREMIUM_PAY`, `OVERTIME_HOURS`).

## Decisions

### Remove `COMMISSION` and `BONUS` Entirely

These columns are permanently zero in synthetic data and represent corporate/sales compensation concepts irrelevant to SNF hourly payroll. Removing them tightens the schema and eliminates a spec contradiction.

Rationale: Including them implies the pipeline handles corporate pay types, which it does not.

Alternative considered: keep them as optional future fields. Rejected because they are not on the roadmap and their presence contradicts existing specs.

### Remove `RETRO_PAY` from Default Synthetic Generation

Retro pay is a plausible SNF concept (future scenario `retro_rate` exists), but emitting `RETRO_PAY: 0.0` for every record adds noise. The column can be reintroduced when that scenario is implemented.

Rationale: A permanently zero column in the training feature matrix is harmless but confusing; removing it keeps the schema honest.

Alternative considered: keep `RETRO_PAY` because it is SNF-relevant. Rejected because it is currently unimplemented and adds no signal.

### Use SNF-Specific Test Fixture Values

For `test_period_safe_feature_references_and_early_fallbacks`:
- `DEPARTMENT`: `["Nursing"] * 5`
- `JOB_FAMILY`: `["CNA"] * 5` (or another `SNFRole` value)
- `LOCATION`: `["SNF-F001"] * 5` (matches the fallback facility logic)
- `PAY_TYPE`: `["hourly"] * 5`
- `PAY_CODE`: `["SNF_REG"] * 5`

For targeted anomaly / drift tests using `Operations`:
- Change `DEPARTMENT` filter to `"Nursing"` (a valid SNF department per `data.py` logic).

Rationale: Tests should exercise the same domain values that production code uses.

## Risks / Trade-offs

- Removing columns from `MODEL_FEATURE_COLUMNS` changes the Isolation Forest feature matrix shape. This is safe because the removed columns were always zero, but any serialized model artifacts (not present in repo) would break.
- Test fixture changes may alter peer-group calculations in `test_period_safe_feature_references_and_early_fallbacks` because `_peer_key` uses `JOB_FAMILY` as a fallback for `ROLE`. Changing `"Payroll"` to `"CNA"` may shift peer medians. The test assertions should be reviewed and updated if medians change.
- `prek` (Ruff) may flag unused imports if `COMMISSION`/`BONUS` were referenced only in removed code.

## Migration Plan

1. Update `tests/integration/test_regression.py` fixtures to SNF values.
2. Remove `COMMISSION`, `BONUS`, and `RETRO_PAY` from `columns.py`.
3. Remove `COMMISSION`, `BONUS`, and `RETRO_PAY` from `data.py` default generation.
4. Remove `COMMISSION`, `BONUS`, and `RETRO_PAY` from `MODEL_FEATURE_COLUMNS` in `columns.py`.
5. Audit `src/` for any remaining references to removed columns and update or delete.
6. Run smoke and targeted integration tests; update assertions if peer medians shift.
7. Run `uv run prek run --all-files` and fix lint/format issues.

Rollback: Revert the commit. No external data migration is needed because this only affects synthetic generation and test fixtures.

## Open Questions

- Should we also remove `NET_PAY` and `DEDUCTIONS` from `MODEL_FEATURE_COLUMNS`? They are generic payroll fields but are actively used in SNF exposure estimation and rule flags, so they should stay.
- Should `TENURE_MONTHS` remain in the synthetic schema? Yes—it is used for peer grouping and tenure bucket features.

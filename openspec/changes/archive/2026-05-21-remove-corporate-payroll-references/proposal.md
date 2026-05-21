## Why

A comprehensive review of the codebase revealed that generic corporate payroll concepts have leaked into test fixtures, schema constants, and synthetic data generation—contradicting the project's stated SNF-specific domain focus. The `openspec/specs/synthetic-payroll-data/spec.md` explicitly requires that "departments and job families are SNF-specific rather than corporate values such as Sales, Engineering, commissions, or remote office roles." These leaks create domain inconsistency and risk confusing future maintainers about whether the pipeline is truly SNF-targeted or a generic corporate payroll demo.

## What Changes

- **Test fixtures**: Replace generic corporate values (`Finance` department, `Payroll` job family, `Remote` location, `salaried` pay type, `SAL` pay code, `Operations` department) in `tests/integration/test_regression.py` with SNF-specific values (`Nursing`, `CNA`, facility IDs, `hourly`, `SNF_REG`).
- **Schema cleanup**: Remove `COMMISSION` and `BONUS` columns from `src/payroll_anomaly_ranking/columns.py` and from `MODEL_FEATURE_COLUMNS`. These are sales/corporate compensation concepts that do not exist in SNF hourly payroll.
- **Synthetic data cleanup**: Remove `COMMISSION` and `BONUS` (and their always-zero values) from `src/payroll_anomaly_ranking/data.py` synthetic generation. Remove `RETRO_PAY` from the always-zero default generation or document it as a future scenario field rather than a permanently zero placeholder.
- **Downstream alignment**: Update any code in `src/payroll_anomaly_ranking/models.py`, `src/payroll_anomaly_ranking/rules.py`, or other modules that references the removed columns.

## Capabilities

### Modified Capabilities

- `synthetic-payroll-data`: Eliminate generic corporate compensation fields (`commission`, `bonus`) from synthetic generation; align test fixtures with SNF domain values.
- `payroll-anomaly-scoring`: Remove `commission` and `bonus` from `MODEL_FEATURE_COLUMNS` so the hybrid score only uses SNF-relevant production-observable fields.

## Impact

- Affects `src/payroll_anomaly_ranking/columns.py` schema constants and `MODEL_FEATURE_COLUMNS`.
- Affects `src/payroll_anomaly_ranking/data.py` synthetic generation defaults.
- Affects `tests/integration/test_regression.py` test fixtures and scenario filters.
- May affect `src/payroll_anomaly_ranking/models.py` if `_feature_matrix` or exposure calculations reference removed columns.
- Verification should include `uv run pytest tests/smoke`, targeted integration tests, and `uv run prek run --all-files`.

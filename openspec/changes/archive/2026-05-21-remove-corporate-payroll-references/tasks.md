## 1. Test Fixture Alignment

- [x] 1.1 In `tests/integration/test_regression.py`, replace generic corporate fixture values in `test_period_safe_feature_references_and_early_fallbacks`:
  - `DEPARTMENT: ["Finance"] * 5` → `DEPARTMENT: ["Nursing"] * 5`
  - `JOB_FAMILY: ["Payroll"] * 5` → `JOB_FAMILY: ["CNA"] * 5`
  - `LOCATION: ["Remote"] * 5` → `LOCATION: ["SNF-F001"] * 5`
  - `PAY_TYPE: ["salaried"] * 5` → `PAY_TYPE: ["hourly"] * 5`
  - `PAY_CODE: ["SAL"] * 5` → `PAY_CODE: ["SNF_REG"] * 5`
- [x] 1.2 In `tests/integration/test_regression.py`, replace `"Operations"` with `"Nursing"` in all `TargetedAnomalyControl`, `DriftPlan`, and `ChangePointEvent` subgroup filters and assertions.
- [x] 1.3 Review and update any hardcoded peer-median assertions in `test_period_safe_feature_references_and_early_fallbacks` if changing `JOB_FAMILY` from `"Payroll"` to `"CNA"` shifts peer group composition.

## 2. Schema Cleanup

- [x] 2.1 Remove `COMMISSION`, `BONUS`, and `RETRO_PAY` from `PayrollCol` in `src/payroll_anomaly_ranking/columns.py`.
- [x] 2.2 Remove `COMMISSION`, `BONUS`, and `RETRO_PAY` from `MODEL_FEATURE_COLUMNS` in `src/payroll_anomaly_ranking/columns.py`.
- [x] 2.3 Audit `src/payroll_anomaly_ranking/columns.py` for any other references to removed columns (e.g., in `AggregateCol`, `MetricCol`, etc.) and clean up.

## 3. Synthetic Data Cleanup

- [x] 3.1 Remove `COMMISSION`, `BONUS`, and `RETRO_PAY` from `generate_payroll_lines` default row construction in `src/payroll_anomaly_ranking/data.py`.
- [x] 3.2 Audit `src/payroll_anomaly_ranking/data.py` for any other references to removed columns and clean up.

## 4. Downstream Audit

- [x] 4.1 Search `src/payroll_anomaly_ranking/` for remaining references to `COMMISSION`, `BONUS`, `RETRO_PAY`, `Finance`, `Payroll`, `Remote`, `salaried`, `SAL`, and `Operations`.
- [x] 4.2 Update or remove any found references.
- [x] 4.3 Check `src/payroll_anomaly_ranking/models.py` for `_feature_matrix` or exposure calculations that may have referenced removed columns.
- [x] 4.4 Check `src/payroll_anomaly_ranking/rules.py` for any rule references to removed columns.
- [x] 4.5 Check `src/payroll_anomaly_ranking/validation.py` for validation checks referencing removed columns.

## 5. Verification

- [x] 5.1 Run `uv run pytest tests/smoke` and confirm all pass.
- [x] 5.2 Run targeted integration tests: `uv run pytest tests/integration/test_regression.py -k "generation or scenario or feature or rule or scoring or evaluation"` and confirm all pass.
- [x] 5.3 Run `uv run prek run --all-files` and resolve any lint/format/type issues.

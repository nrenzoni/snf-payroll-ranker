from __future__ import annotations

import polars as pl


REQUIRED_COLUMNS = {
    "employee_id",
    "pay_period_index",
    "department",
    "job_family",
    "location",
    "employment_status",
    "pay_type",
    "regular_hours",
    "overtime_hours",
    "pay_rate",
    "gross_pay",
    "deductions",
    "net_pay",
    "tenure_months",
    "hire_date",
    "termination_date",
}


def validate_payroll(payroll: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    failures: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    missing = sorted(REQUIRED_COLUMNS - set(payroll.columns))
    for column in missing:
        failures.append({"check": "required_column", "column": column, "message": f"Missing required column: {column}"})
    if missing:
        return pl.DataFrame(failures), pl.DataFrame(warnings)
    if payroll.filter(pl.col("employee_id").is_null()).height:
        failures.append({"check": "null_identifier", "column": "employee_id", "message": "Employee identifiers cannot be null"})
    if payroll.filter(pl.col("pay_period_index").is_null()).height:
        failures.append({"check": "null_period", "column": "pay_period_index", "message": "Pay periods cannot be null"})
    if payroll.filter(pl.col("hire_date") > pl.col("pay_period_end")).height:
        failures.append({"check": "invalid_lifecycle_dates", "column": "hire_date", "message": "Hire date after pay period end"})
    negative_normal = payroll.filter((pl.col("is_anomaly") == 0) & ((pl.col("gross_pay") < 0) | (pl.col("regular_hours") < 0)))
    if negative_normal.height:
        failures.append({"check": "negative_normal_payroll", "column": "gross_pay", "message": "Normal records have negative payroll values"})
    warning_checks = {
        "missing_deduction": payroll.filter(pl.col("deductions").is_null() | (pl.col("deductions") == 0)).height,
        "negative_net_pay": payroll.filter(pl.col("net_pay") < 0).height,
        "net_exceeds_gross": payroll.filter(pl.col("net_pay") > pl.col("gross_pay") * 1.05).height,
        "large_manual_adjustment": payroll.filter(pl.col("manual_adjustment").abs() > pl.col("gross_pay") * 0.25).height,
    }
    for check, count in warning_checks.items():
        if count:
            warnings.append({"check": check, "column": None, "message": f"{count} records may require payroll exception review"})
    return pl.DataFrame(failures), pl.DataFrame(warnings)


def payroll_aggregations(payroll: pl.DataFrame) -> dict[str, pl.DataFrame]:
    return {
        "payroll_volume": payroll.group_by("pay_period_index").agg(pl.len().alias("records"), pl.sum("gross_pay").alias("gross_pay")),
        "active_employee_counts": payroll.filter(pl.col("employment_status") == "active").group_by("pay_period_index").agg(pl.n_unique("employee_id").alias("active_employees")),
        "department_payroll": payroll.group_by(["pay_period_index", "department"]).agg(pl.sum("gross_pay").alias("department_gross_pay")),
        "overtime": payroll.group_by("pay_period_index").agg(pl.mean("overtime_hours").alias("mean_overtime_hours"), pl.sum("overtime_hours").alias("total_overtime_hours")),
        "manual_adjustments": payroll.group_by("pay_period_index").agg(pl.sum("manual_adjustment").alias("manual_adjustment_total"), pl.mean("manual_adjustment").alias("manual_adjustment_mean")),
        "pay_rate_changes": payroll.sort(["employee_id", "pay_period_index"]).with_columns(pl.col("pay_rate").diff().over("employee_id").abs().alias("pay_rate_change")).group_by("pay_period_index").agg((pl.col("pay_rate_change") > 0).cast(pl.Int64).sum().alias("pay_rate_changes")),
        "distribution_summary": payroll.select(pl.col("gross_pay").quantile(0.25).alias("gross_q25"), pl.median("gross_pay").alias("gross_median"), pl.col("gross_pay").quantile(0.75).alias("gross_q75"), pl.mean("net_pay").alias("mean_net_pay")),
    }

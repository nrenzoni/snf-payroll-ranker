from __future__ import annotations

import polars as pl

from payroll_anomaly_ranking.columns import (
    REQUIRED_PAYROLL_COLUMNS,
    AggregateCol,
    PayrollCol,
)

REQUIRED_COLUMNS = REQUIRED_PAYROLL_COLUMNS


def validate_payroll(payroll: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    failures: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    missing = sorted(REQUIRED_COLUMNS - set(payroll.columns))
    for column in missing:
        failures.append(
            {
                "check": "required_column",
                "column": column,
                "message": f"Missing required column: {column}",
            },
        )
    if missing:
        return pl.DataFrame(failures), pl.DataFrame(warnings)
    if payroll.filter(pl.col(PayrollCol.EMPLOYEE_ID).is_null()).height:
        failures.append(
            {
                "check": "null_identifier",
                "column": PayrollCol.EMPLOYEE_ID,
                "message": "Employee identifiers cannot be null",
            },
        )
    if payroll.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX).is_null()).height:
        failures.append(
            {
                "check": "null_period",
                "column": PayrollCol.PAY_PERIOD_INDEX,
                "message": "Pay periods cannot be null",
            },
        )
    if payroll.filter(
        pl.col(PayrollCol.HIRE_DATE) > pl.col(PayrollCol.PAY_PERIOD_END),
    ).height:
        failures.append(
            {
                "check": "invalid_lifecycle_dates",
                "column": PayrollCol.HIRE_DATE,
                "message": "Hire date after pay period end",
            },
        )
    negative_normal = payroll.filter(
        (pl.col(PayrollCol.IS_ANOMALY) == 0)
        & ((pl.col(PayrollCol.GROSS_PAY) < 0) | (pl.col(PayrollCol.REGULAR_HOURS) < 0)),
    )
    if negative_normal.height:
        failures.append(
            {
                "check": "negative_normal_payroll",
                "column": PayrollCol.GROSS_PAY,
                "message": "Normal records have negative payroll values",
            },
        )
    warning_checks = {
        "missing_deduction": payroll.filter(
            pl.col(PayrollCol.DEDUCTIONS).is_null()
            | (pl.col(PayrollCol.DEDUCTIONS) == 0),
        ).height,
        "negative_net_pay": payroll.filter(pl.col(PayrollCol.NET_PAY) < 0).height,
        "net_exceeds_gross": payroll.filter(
            pl.col(PayrollCol.NET_PAY) > pl.col(PayrollCol.GROSS_PAY) * 1.05,
        ).height,
        "large_manual_adjustment": payroll.filter(
            pl.col(PayrollCol.MANUAL_ADJUSTMENT).abs()
            > pl.col(PayrollCol.GROSS_PAY) * 0.25,
        ).height,
        "late_period_pay_code_ood_context": payroll.filter(
            pl.col(PayrollCol.OOD_PAY_CODE_CONTEXT).is_in(
                ["late_period_new_or_rare_pay_code", "rare_pay_code"],
            ),
        ).height
        if PayrollCol.OOD_PAY_CODE_CONTEXT in payroll.columns
        else 0,
    }
    for check, count in warning_checks.items():
        if count:
            warnings.append(
                {
                    "check": check,
                    "column": None,
                    "message": f"{count} records may require payroll exception review",
                },
            )
    return pl.DataFrame(failures), pl.DataFrame(warnings)


def payroll_aggregations(payroll: pl.DataFrame) -> dict[str, pl.DataFrame]:
    return {
        "payroll_volume": payroll.group_by(PayrollCol.PAY_PERIOD_INDEX).agg(
            pl.len().alias(AggregateCol.RECORDS),
            pl.sum(PayrollCol.GROSS_PAY).alias(PayrollCol.GROSS_PAY),
        ),
        "active_employee_counts": payroll.filter(
            pl.col(PayrollCol.EMPLOYMENT_STATUS) == "active",
        )
        .group_by(PayrollCol.PAY_PERIOD_INDEX)
        .agg(pl.n_unique(PayrollCol.EMPLOYEE_ID).alias(AggregateCol.ACTIVE_EMPLOYEES)),
        "department_payroll": payroll.group_by(
            [PayrollCol.PAY_PERIOD_INDEX, PayrollCol.DEPARTMENT],
        ).agg(pl.sum(PayrollCol.GROSS_PAY).alias(AggregateCol.DEPARTMENT_GROSS_PAY)),
        "overtime": payroll.group_by(PayrollCol.PAY_PERIOD_INDEX).agg(
            pl.mean(PayrollCol.OVERTIME_HOURS).alias(AggregateCol.MEAN_OVERTIME_HOURS),
            pl.sum(PayrollCol.OVERTIME_HOURS).alias(AggregateCol.TOTAL_OVERTIME_HOURS),
        ),
        "manual_adjustments": payroll.group_by(PayrollCol.PAY_PERIOD_INDEX).agg(
            pl.sum(PayrollCol.MANUAL_ADJUSTMENT).alias(
                AggregateCol.MANUAL_ADJUSTMENT_TOTAL,
            ),
            pl.mean(PayrollCol.MANUAL_ADJUSTMENT).alias(
                AggregateCol.MANUAL_ADJUSTMENT_MEAN,
            ),
        ),
        "pay_rate_changes": payroll.sort(
            [PayrollCol.EMPLOYEE_ID, PayrollCol.PAY_PERIOD_INDEX],
        )
        .with_columns(
            pl.col(PayrollCol.PAY_RATE)
            .diff()
            .over(PayrollCol.EMPLOYEE_ID)
            .abs()
            .alias(AggregateCol.PAY_RATE_CHANGE),
        )
        .group_by(PayrollCol.PAY_PERIOD_INDEX)
        .agg(
            (pl.col(AggregateCol.PAY_RATE_CHANGE) > 0)
            .cast(pl.Int64)
            .sum()
            .alias(AggregateCol.PAY_RATE_CHANGES),
        ),
        "pay_code_distribution": payroll.group_by(
            [PayrollCol.PAY_PERIOD_INDEX, PayrollCol.PAY_CODE],
        ).agg(pl.len().alias(AggregateCol.RECORDS)),
        "distribution_summary": payroll.select(
            pl.col(PayrollCol.GROSS_PAY).quantile(0.25).alias(AggregateCol.GROSS_Q25),
            pl.median(PayrollCol.GROSS_PAY).alias(AggregateCol.GROSS_MEDIAN),
            pl.col(PayrollCol.GROSS_PAY).quantile(0.75).alias(AggregateCol.GROSS_Q75),
            pl.mean(PayrollCol.NET_PAY).alias(AggregateCol.MEAN_NET_PAY),
        ),
    }

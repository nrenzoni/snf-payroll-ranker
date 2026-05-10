from __future__ import annotations

from dataclasses import dataclass, field

import polars as pl

from payroll_anomaly_ranking.columns import (
    REQUIRED_PAYROLL_COLUMNS,
    AggregateCol,
    ApprovalStatus,
    PayrollCol,
)

REQUIRED_COLUMNS = REQUIRED_PAYROLL_COLUMNS


@dataclass(frozen=True)
class ValidationResults:
    failures: pl.DataFrame
    warnings: pl.DataFrame


@dataclass(frozen=True)
class PayrollAggregations:
    payroll_volume: pl.DataFrame
    active_employee_counts: pl.DataFrame
    department_payroll: pl.DataFrame
    overtime: pl.DataFrame
    manual_adjustments: pl.DataFrame
    pay_rate_changes: pl.DataFrame
    pay_code_distribution: pl.DataFrame
    distribution_summary: pl.DataFrame
    facility_approval_summary: pl.DataFrame = field(default_factory=pl.DataFrame)


def validate_payroll(payroll: pl.DataFrame) -> ValidationResults:
    failures: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    missing = sorted(REQUIRED_COLUMNS - set(payroll.columns))
    for column in missing:
        failures.append(
            {
                "check": "required_column",
                "column": column,
                "message": f"Missing required SNF payroll column: {column}",
            },
        )
    if missing:
        return ValidationResults(pl.DataFrame(failures), pl.DataFrame(warnings))
    failure_checks = {
        "null_identifier": payroll.filter(
            pl.col(PayrollCol.EMPLOYEE_ID).is_null(),
        ).height,
        "null_shift_identifier": payroll.filter(
            pl.col(PayrollCol.SHIFT_ID).is_null(),
        ).height,
        "null_period": payroll.filter(
            pl.col(PayrollCol.PAY_PERIOD_INDEX).is_null(),
        ).height,
        "invalid_lifecycle_dates": payroll.filter(
            pl.col(PayrollCol.HIRE_DATE) > pl.col(PayrollCol.SHIFT_DATE),
        ).height,
        "negative_normal_payroll": payroll.filter(
            (pl.col(PayrollCol.IS_ANOMALY) == 0)
            & (
                (pl.col(PayrollCol.GROSS_PAY) < 0)
                | (pl.col(PayrollCol.PAID_HOURS) < 0)
                | (pl.col(PayrollCol.SCHEDULED_HOURS) < 0)
            ),
        ).height,
    }
    for check, count in failure_checks.items():
        if count:
            failures.append(
                {
                    "check": check,
                    "column": None,
                    "message": f"{count} rows failed {check}",
                },
            )
    warning_checks = {
        "paid_hours_exceed_scheduled": payroll.filter(
            pl.col(PayrollCol.PAID_HOURS) > pl.col(PayrollCol.SCHEDULED_HOURS) + 1.5,
        ).height,
        "missing_approval_context": payroll.filter(
            pl.col(PayrollCol.APPROVAL_STATUS).is_in(
                [ApprovalStatus.MISSING, ApprovalStatus.PENDING],
            ),
        ).height,
        "unsupported_premium_context": payroll.filter(
            (pl.col(PayrollCol.PREMIUM_PAY) > 0)
            & (pl.col(PayrollCol.SHIFT_TYPE) == "Day")
            & (pl.col(PayrollCol.IS_WEEKEND) == 0),
        ).height,
        "duplicate_shift_signature": payroll.filter(
            pl.struct(
                [
                    PayrollCol.EMPLOYEE_ID,
                    PayrollCol.SHIFT_DATE,
                    PayrollCol.SHIFT_TYPE,
                    PayrollCol.FACILITY_ID,
                    PayrollCol.PAY_CODE,
                ],
            ).is_duplicated(),
        ).height,
        "extreme_overtime": payroll.filter(
            pl.col(PayrollCol.OVERTIME_HOURS) > 8,
        ).height,
        "rest_gap_risk": payroll.filter(pl.col(PayrollCol.REST_GAP_HOURS) < 8).height,
        "missed_punch": payroll.filter(pl.col(PayrollCol.MISSED_PUNCH) == 1).height,
        "manual_edit": payroll.filter(pl.col(PayrollCol.MANUAL_EDIT) == 1).height,
        "negative_net_pay": payroll.filter(pl.col(PayrollCol.NET_PAY) < 0).height,
    }
    for check, count in warning_checks.items():
        if count:
            warnings.append(
                {
                    "check": check,
                    "column": None,
                    "message": f"{count} SNF shift-level records may require payroll approval review",
                },
            )
    return ValidationResults(pl.DataFrame(failures), pl.DataFrame(warnings))


def payroll_aggregations(payroll: pl.DataFrame) -> PayrollAggregations:
    facility_summary = payroll.group_by(
        [PayrollCol.PAY_PERIOD_INDEX, PayrollCol.FACILITY_ID],
    ).agg(
        pl.len().alias(AggregateCol.TOTAL_SHIFTS),
        pl.sum(PayrollCol.GROSS_PAY).alias(AggregateCol.TOTAL_GROSS_PAY),
        pl.sum(PayrollCol.PAID_HOURS).alias(AggregateCol.TOTAL_PAID_HOURS),
        pl.sum(PayrollCol.OVERTIME_HOURS).alias(AggregateCol.TOTAL_OVERTIME_HOURS),
        pl.sum(PayrollCol.PREMIUM_PAY).alias(AggregateCol.TOTAL_PREMIUM_PAY),
        pl.sum(PayrollCol.IS_ANOMALY).alias(AggregateCol.TRUE_ANOMALIES),
    )
    return PayrollAggregations(
        payroll_volume=payroll.group_by(PayrollCol.PAY_PERIOD_INDEX).agg(
            pl.len().alias(AggregateCol.RECORDS),
            pl.sum(PayrollCol.GROSS_PAY).alias(PayrollCol.GROSS_PAY),
        ),
        active_employee_counts=payroll.filter(
            pl.col(PayrollCol.EMPLOYMENT_STATUS) == "active",
        )
        .group_by(PayrollCol.PAY_PERIOD_INDEX)
        .agg(pl.n_unique(PayrollCol.EMPLOYEE_ID).alias(AggregateCol.ACTIVE_EMPLOYEES)),
        department_payroll=payroll.group_by(
            [PayrollCol.PAY_PERIOD_INDEX, PayrollCol.FACILITY_ID],
        ).agg(
            pl.sum(PayrollCol.GROSS_PAY).alias(AggregateCol.DEPARTMENT_GROSS_PAY),
        ),
        overtime=payroll.group_by(PayrollCol.PAY_PERIOD_INDEX).agg(
            pl.mean(PayrollCol.OVERTIME_HOURS).alias(AggregateCol.MEAN_OVERTIME_HOURS),
            pl.sum(PayrollCol.OVERTIME_HOURS).alias(AggregateCol.TOTAL_OVERTIME_HOURS),
            pl.max(PayrollCol.OVERTIME_HOURS).alias(AggregateCol.MAX_OVERTIME_HOURS),
        ),
        manual_adjustments=payroll.group_by(PayrollCol.PAY_PERIOD_INDEX).agg(
            pl.sum(PayrollCol.MANUAL_ADJUSTMENT).alias(
                AggregateCol.MANUAL_ADJUSTMENT_TOTAL,
            ),
            pl.mean(PayrollCol.MANUAL_ADJUSTMENT).alias(
                AggregateCol.MANUAL_ADJUSTMENT_MEAN,
            ),
        ),
        pay_rate_changes=payroll.sort([PayrollCol.EMPLOYEE_ID, PayrollCol.SHIFT_DATE])
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
        pay_code_distribution=payroll.group_by(
            [PayrollCol.PAY_PERIOD_INDEX, PayrollCol.PAY_CODE_CATEGORY],
        ).agg(
            pl.len().alias(AggregateCol.RECORDS),
        ),
        distribution_summary=payroll.select(
            pl.col(PayrollCol.GROSS_PAY).quantile(0.25).alias(AggregateCol.GROSS_Q25),
            pl.median(PayrollCol.GROSS_PAY).alias(AggregateCol.GROSS_MEDIAN),
            pl.col(PayrollCol.GROSS_PAY).quantile(0.75).alias(AggregateCol.GROSS_Q75),
            pl.mean(PayrollCol.NET_PAY).alias(AggregateCol.MEAN_NET_PAY),
        ),
        facility_approval_summary=facility_summary,
    )

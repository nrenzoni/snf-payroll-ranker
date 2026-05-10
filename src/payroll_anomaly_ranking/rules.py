from __future__ import annotations

import polars as pl

from payroll_anomaly_ranking.columns import (
    RULE_FLAG_COLUMNS,
    FeatureCol,
    PayrollCol,
    RecommendedAction,
    ReviewCol,
    RuleCol,
    SourceToCheck,
)

RULE_COLUMNS = RULE_FLAG_COLUMNS


def add_rule_flags(payroll: pl.DataFrame) -> pl.DataFrame:
    flagged = (
        payroll.sort(
            [
                PayrollCol.EMPLOYEE_ID,
                PayrollCol.SHIFT_DATE,
                PayrollCol.SHIFT_START_HOUR,
            ],
        )
        .with_columns(
            (
                (pl.col(PayrollCol.EMPLOYMENT_STATUS) == "terminated")
                & (pl.col(PayrollCol.GROSS_PAY) > 0)
            )
            .cast(pl.Int64)
            .alias(RuleCol.PAY_AFTER_TERMINATION),
            (
                pl.struct(
                    [
                        PayrollCol.EMPLOYEE_ID,
                        PayrollCol.SHIFT_DATE,
                        PayrollCol.SHIFT_TYPE,
                        PayrollCol.FACILITY_ID,
                        PayrollCol.PAY_CODE,
                        PayrollCol.GROSS_PAY,
                    ],
                ).is_duplicated()
            )
            .cast(pl.Int64)
            .alias(RuleCol.DUPLICATE_SIGNATURE),
            (
                (pl.col(PayrollCol.EMPLOYMENT_STATUS) == "active")
                & (pl.col(PayrollCol.GROSS_PAY) <= 0)
            )
            .cast(pl.Int64)
            .alias(RuleCol.NONPOSITIVE_ACTIVE_PAY),
            (pl.col(PayrollCol.NET_PAY) < 0)
            .cast(pl.Int64)
            .alias(RuleCol.NEGATIVE_NET_PAY),
            (pl.col(PayrollCol.NET_PAY) > pl.col(PayrollCol.GROSS_PAY) * 1.05)
            .cast(pl.Int64)
            .alias(RuleCol.NET_EXCEEDS_GROSS),
            (pl.col(PayrollCol.OVERTIME_HOURS) > 8)
            .cast(pl.Int64)
            .alias(RuleCol.EXTREME_OVERTIME),
            (
                pl.col(PayrollCol.MANUAL_ADJUSTMENT).abs()
                > pl.col(PayrollCol.GROSS_PAY).abs() * 0.25
            )
            .cast(pl.Int64)
            .alias(RuleCol.LARGE_MANUAL_ADJUSTMENT),
            (
                pl.col(PayrollCol.PAY_RATE)
                .pct_change()
                .over(PayrollCol.EMPLOYEE_ID)
                .abs()
                > 0.25
            )
            .fill_null(False)
            .cast(pl.Int64)
            .alias(RuleCol.PAY_RATE_CHANGE),
            (
                (pl.col(PayrollCol.GROSS_PAY) > 0)
                & (pl.col(PayrollCol.DEDUCTIONS).fill_null(0) <= 0)
            )
            .cast(pl.Int64)
            .alias(RuleCol.MISSING_DEDUCTION),
            (pl.col(FeatureCol.PAID_MINUS_SCHEDULED_HOURS).fill_null(0) > 1.5)
            .cast(pl.Int64)
            .alias(RuleCol.PAID_EXCEEDS_SCHEDULED),
            (
                (pl.col(PayrollCol.SAME_DAY_SHIFT_COUNT).fill_null(1) > 1)
                | (pl.col(PayrollCol.REST_GAP_HOURS).fill_null(24) < 8)
            )
            .cast(pl.Int64)
            .alias(RuleCol.DOUBLE_SHIFT_REST_GAP),
            (
                (pl.col(PayrollCol.PREMIUM_PAY) > 0)
                & (pl.col(PayrollCol.SHIFT_TYPE) == "Day")
                & (pl.col(PayrollCol.IS_WEEKEND) == 0)
            )
            .cast(pl.Int64)
            .alias(RuleCol.UNSUPPORTED_SHIFT_DIFFERENTIAL),
            (
                (pl.col(PayrollCol.PAY_CODE).str.contains("WKND"))
                & (pl.col(PayrollCol.IS_WEEKEND) == 0)
            )
            .cast(pl.Int64)
            .alias(RuleCol.UNSUPPORTED_WEEKEND_PREMIUM),
            pl.col(FeatureCol.DUPLICATE_PREMIUM_SIGNATURE)
            .fill_null(0)
            .cast(pl.Int64)
            .alias(RuleCol.DUPLICATE_PREMIUM),
            pl.col(FeatureCol.PREMIUM_ELIGIBILITY_MISMATCH)
            .fill_null(0)
            .cast(pl.Int64)
            .alias(RuleCol.PREMIUM_WITHOUT_SUPPORT),
        )
        .with_columns(
            (
                pl.col(RuleCol.PAY_AFTER_TERMINATION) * 35
                + pl.col(RuleCol.DUPLICATE_SIGNATURE) * 25
                + pl.col(RuleCol.NONPOSITIVE_ACTIVE_PAY) * 15
                + pl.col(RuleCol.NEGATIVE_NET_PAY) * 20
                + pl.col(RuleCol.NET_EXCEEDS_GROSS) * 12
                + pl.col(RuleCol.EXTREME_OVERTIME) * 20
                + pl.col(RuleCol.LARGE_MANUAL_ADJUSTMENT) * 8
                + pl.col(RuleCol.PAY_RATE_CHANGE) * 10
                + pl.col(RuleCol.MISSING_DEDUCTION) * 18
                + pl.col(RuleCol.PAID_EXCEEDS_SCHEDULED) * 22
                + pl.col(RuleCol.DOUBLE_SHIFT_REST_GAP) * 18
                + pl.col(RuleCol.UNSUPPORTED_SHIFT_DIFFERENTIAL) * 28
                + pl.col(RuleCol.UNSUPPORTED_WEEKEND_PREMIUM) * 25
                + pl.col(RuleCol.DUPLICATE_PREMIUM) * 20
                + pl.col(RuleCol.PREMIUM_WITHOUT_SUPPORT) * 24
            ).alias(RuleCol.SEVERITY_SCORE),
        )
    )
    return flagged.with_columns(
        pl.struct(RULE_COLUMNS)
        .map_elements(_reason_codes, return_dtype=pl.String)
        .alias(RuleCol.REASON_CODES),
    ).with_columns(
        pl.struct(RULE_COLUMNS)
        .map_elements(_source_to_check, return_dtype=pl.String)
        .alias(ReviewCol.SOURCE_TO_CHECK),
        pl.struct(RULE_COLUMNS)
        .map_elements(_recommended_action, return_dtype=pl.String)
        .alias(ReviewCol.RECOMMENDED_ACTION),
    )


def _reason_codes(values: dict[str, int]) -> str:
    return (
        ";".join(column.replace("rule_", "") for column, flag in values.items() if flag)
        or "none"
    )


def _source_to_check(values: dict[str, int]) -> str:
    if (
        values.get(RuleCol.UNSUPPORTED_SHIFT_DIFFERENTIAL)
        or values.get(RuleCol.UNSUPPORTED_WEEKEND_PREMIUM)
        or values.get(RuleCol.PREMIUM_WITHOUT_SUPPORT)
    ):
        return SourceToCheck.PAY_POLICY
    if values.get(RuleCol.PAID_EXCEEDS_SCHEDULED):
        return SourceToCheck.SCHEDULE
    if values.get(RuleCol.DOUBLE_SHIFT_REST_GAP) or values.get(
        RuleCol.EXTREME_OVERTIME,
    ):
        return SourceToCheck.TIMECLOCK
    if values.get(RuleCol.PAY_AFTER_TERMINATION):
        return SourceToCheck.EMPLOYEE_LIFECYCLE
    return SourceToCheck.PAY_CODE


def _recommended_action(values: dict[str, int]) -> str:
    if (
        values.get(RuleCol.UNSUPPORTED_SHIFT_DIFFERENTIAL)
        or values.get(RuleCol.UNSUPPORTED_WEEKEND_PREMIUM)
        or values.get(RuleCol.PREMIUM_WITHOUT_SUPPORT)
    ):
        return RecommendedAction.CONFIRM_PREMIUM_ELIGIBILITY
    if values.get(RuleCol.PAID_EXCEEDS_SCHEDULED):
        return RecommendedAction.CONFIRM_SCHEDULE
    if values.get(RuleCol.DOUBLE_SHIFT_REST_GAP) or values.get(
        RuleCol.EXTREME_OVERTIME,
    ):
        return RecommendedAction.VERIFY_TIMECLOCK_EDIT
    if values.get(RuleCol.PAY_AFTER_TERMINATION):
        return RecommendedAction.ESCALATE_TO_PAYROLL
    return RecommendedAction.APPROVE_STAFFING_EXCEPTION

from __future__ import annotations

import polars as pl

from payroll_anomaly_ranking.columns import PayrollCol, RuleCol, RULE_FLAG_COLUMNS

RULE_COLUMNS = RULE_FLAG_COLUMNS


def add_rule_flags(payroll: pl.DataFrame) -> pl.DataFrame:
    flagged = (
        payroll.sort([PayrollCol.EMPLOYEE_ID, PayrollCol.PAY_PERIOD_INDEX])
        .with_columns(
            ((pl.col(PayrollCol.EMPLOYMENT_STATUS) == "terminated") & (pl.col(PayrollCol.GROSS_PAY) > 0)).cast(pl.Int64).alias(RuleCol.PAY_AFTER_TERMINATION),
            (pl.struct([PayrollCol.EMPLOYEE_ID, PayrollCol.PAY_PERIOD_INDEX, PayrollCol.GROSS_PAY, PayrollCol.NET_PAY]).is_duplicated()).cast(pl.Int64).alias(RuleCol.DUPLICATE_SIGNATURE),
            ((pl.col(PayrollCol.EMPLOYMENT_STATUS) == "active") & (pl.col(PayrollCol.GROSS_PAY) <= 0)).cast(pl.Int64).alias(RuleCol.NONPOSITIVE_ACTIVE_PAY),
            (pl.col(PayrollCol.NET_PAY) < 0).cast(pl.Int64).alias(RuleCol.NEGATIVE_NET_PAY),
            (pl.col(PayrollCol.NET_PAY) > pl.col(PayrollCol.GROSS_PAY) * 1.05).cast(pl.Int64).alias(RuleCol.NET_EXCEEDS_GROSS),
            (pl.col(PayrollCol.OVERTIME_HOURS) > 30).cast(pl.Int64).alias(RuleCol.EXTREME_OVERTIME),
            (pl.col(PayrollCol.MANUAL_ADJUSTMENT).abs() > pl.col(PayrollCol.GROSS_PAY).abs() * 0.25).cast(pl.Int64).alias(RuleCol.LARGE_MANUAL_ADJUSTMENT),
            (pl.col(PayrollCol.PAY_RATE).pct_change().over(PayrollCol.EMPLOYEE_ID).abs() > 0.25).fill_null(False).cast(pl.Int64).alias(RuleCol.PAY_RATE_CHANGE),
        )
        .with_columns(
            (
                pl.col(RuleCol.PAY_AFTER_TERMINATION) * 35
                + pl.col(RuleCol.DUPLICATE_SIGNATURE) * 25
                + pl.col(RuleCol.NONPOSITIVE_ACTIVE_PAY) * 15
                + pl.col(RuleCol.NEGATIVE_NET_PAY) * 20
                + pl.col(RuleCol.NET_EXCEEDS_GROSS) * 12
                + pl.col(RuleCol.EXTREME_OVERTIME) * 14
                + pl.col(RuleCol.LARGE_MANUAL_ADJUSTMENT) * 10
                + pl.col(RuleCol.PAY_RATE_CHANGE) * 12
            ).alias(RuleCol.SEVERITY_SCORE)
        )
    )
    return flagged.with_columns(pl.struct(RULE_COLUMNS).map_elements(_reason_codes, return_dtype=pl.String).alias(RuleCol.REASON_CODES))


def _reason_codes(values: dict[str, int]) -> str:
    return ";".join(column.replace("rule_", "") for column, flag in values.items() if flag) or "none"

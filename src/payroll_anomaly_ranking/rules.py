from __future__ import annotations

import polars as pl


RULE_COLUMNS = [
    "rule_pay_after_termination",
    "rule_duplicate_signature",
    "rule_nonpositive_active_pay",
    "rule_negative_net_pay",
    "rule_net_exceeds_gross",
    "rule_extreme_overtime",
    "rule_large_manual_adjustment",
    "rule_pay_rate_change",
]


def add_rule_flags(payroll: pl.DataFrame) -> pl.DataFrame:
    flagged = (
        payroll.sort(["employee_id", "pay_period_index"])
        .with_columns(
            ((pl.col("employment_status") == "terminated") & (pl.col("gross_pay") > 0)).cast(pl.Int64).alias("rule_pay_after_termination"),
            (pl.struct(["employee_id", "pay_period_index", "gross_pay", "net_pay"]).is_duplicated()).cast(pl.Int64).alias("rule_duplicate_signature"),
            ((pl.col("employment_status") == "active") & (pl.col("gross_pay") <= 0)).cast(pl.Int64).alias("rule_nonpositive_active_pay"),
            (pl.col("net_pay") < 0).cast(pl.Int64).alias("rule_negative_net_pay"),
            (pl.col("net_pay") > pl.col("gross_pay") * 1.05).cast(pl.Int64).alias("rule_net_exceeds_gross"),
            (pl.col("overtime_hours") > 30).cast(pl.Int64).alias("rule_extreme_overtime"),
            (pl.col("manual_adjustment").abs() > pl.col("gross_pay").abs() * 0.25).cast(pl.Int64).alias("rule_large_manual_adjustment"),
            (pl.col("pay_rate").pct_change().over("employee_id").abs() > 0.25).fill_null(False).cast(pl.Int64).alias("rule_pay_rate_change"),
        )
        .with_columns(
            (
                pl.col("rule_pay_after_termination") * 35
                + pl.col("rule_duplicate_signature") * 25
                + pl.col("rule_nonpositive_active_pay") * 15
                + pl.col("rule_negative_net_pay") * 20
                + pl.col("rule_net_exceeds_gross") * 12
                + pl.col("rule_extreme_overtime") * 14
                + pl.col("rule_large_manual_adjustment") * 10
                + pl.col("rule_pay_rate_change") * 12
            ).alias("rule_severity_score")
        )
    )
    return flagged.with_columns(pl.struct(RULE_COLUMNS).map_elements(_reason_codes, return_dtype=pl.String).alias("rule_reason_codes"))


def _reason_codes(values: dict[str, int]) -> str:
    return ";".join(column.replace("rule_", "") for column, flag in values.items() if flag) or "none"

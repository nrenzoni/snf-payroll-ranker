from __future__ import annotations

import polars as pl


def add_history_features(payroll: pl.DataFrame) -> pl.DataFrame:
    return (
        payroll.sort(["employee_id", "pay_period_index"])
        .with_columns(
            pl.col("gross_pay").shift(1).over("employee_id").alias("lag_gross_pay"),
            pl.col("gross_pay").shift(1).rolling_median(window_size=4, min_samples=1).over("employee_id").alias("gross_pay_rolling_median"),
            pl.col("gross_pay").shift(1).rolling_std(window_size=4, min_samples=2).over("employee_id").alias("gross_pay_rolling_std"),
            pl.col("overtime_hours").shift(1).rolling_median(window_size=4, min_samples=1).over("employee_id").alias("overtime_rolling_median"),
        )
        .with_columns(
            ((pl.col("gross_pay") - pl.col("lag_gross_pay")) / pl.col("lag_gross_pay").abs().clip(1, None)).alias("gross_pay_pct_change"),
            (pl.col("deductions").fill_null(0) / pl.col("gross_pay").clip(1, None)).alias("deduction_ratio"),
            (pl.col("net_pay") / pl.col("gross_pay").clip(1, None)).alias("net_to_gross_ratio"),
        )
    )


def add_peer_features(payroll: pl.DataFrame) -> pl.DataFrame:
    base = payroll.with_columns(
        pl.when(pl.col("tenure_months") < 6)
        .then(pl.lit("new"))
        .when(pl.col("tenure_months") < 36)
        .then(pl.lit("established"))
        .otherwise(pl.lit("tenured"))
        .alias("tenure_bucket")
    )
    peers = base.group_by(["pay_period_index", "department", "job_family", "pay_type", "location", "tenure_bucket"]).agg(
        pl.median("gross_pay").alias("peer_gross_median"),
        pl.mean("gross_pay").alias("peer_gross_mean"),
        pl.std("gross_pay").alias("peer_gross_std"),
        pl.median("overtime_hours").alias("peer_overtime_median"),
    )
    return base.join(peers, on=["pay_period_index", "department", "job_family", "pay_type", "location", "tenure_bucket"], how="left").with_columns(
        ((pl.col("gross_pay") - pl.col("peer_gross_median")) / pl.col("peer_gross_median").abs().clip(1, None)).alias("peer_gross_deviation_ratio"),
        ((pl.col("overtime_hours") - pl.col("peer_overtime_median")) / (pl.col("peer_overtime_median") + 1)).alias("peer_overtime_deviation_ratio"),
    )


def add_robust_features(payroll: pl.DataFrame) -> pl.DataFrame:
    med = payroll.select(pl.median("gross_pay")).item()
    q1 = payroll.select(pl.col("gross_pay").quantile(0.25)).item()
    q3 = payroll.select(pl.col("gross_pay").quantile(0.75)).item()
    mad = payroll.select((pl.col("gross_pay") - med).abs().median()).item() or 1.0
    iqr = (q3 - q1) or 1.0
    sorted_pay = payroll.select("gross_pay").to_series().sort().to_list()
    return payroll.with_columns(
        (((pl.col("gross_pay") - med).abs()) / (1.4826 * mad)).alias("gross_pay_robust_z"),
        (((pl.col("gross_pay") - med).abs()) / mad).alias("gross_pay_mad_score"),
        ((pl.col("gross_pay") < q1 - 1.5 * iqr) | (pl.col("gross_pay") > q3 + 1.5 * iqr)).cast(pl.Int64).alias("gross_pay_iqr_outlier"),
        pl.col("gross_pay").map_elements(lambda value: _percentile(value, sorted_pay), return_dtype=pl.Float64).alias("gross_pay_percentile"),
        ((pl.col("gross_pay") - med) / max(med, 1)).alias("gross_pay_deviation_ratio"),
    )


def build_features(payroll: pl.DataFrame) -> pl.DataFrame:
    return add_robust_features(add_peer_features(add_history_features(payroll))).fill_nan(None)


def _percentile(value: float, sorted_values: list[float]) -> float:
    if not sorted_values:
        return 0.0
    less_equal = sum(1 for candidate in sorted_values if candidate <= value)
    return less_equal / len(sorted_values)

from __future__ import annotations

import polars as pl

from payroll_anomaly_ranking.columns import FeatureCol, PayrollCol, PEER_GROUP_COLUMNS


def add_history_features(payroll: pl.DataFrame) -> pl.DataFrame:
    return (
        payroll.sort([PayrollCol.EMPLOYEE_ID, PayrollCol.PAY_PERIOD_INDEX])
        .with_columns(
            pl.col(PayrollCol.GROSS_PAY).shift(1).over(PayrollCol.EMPLOYEE_ID).alias(FeatureCol.LAG_GROSS_PAY),
            pl.col(PayrollCol.GROSS_PAY).shift(1).rolling_median(window_size=4, min_samples=1).over(PayrollCol.EMPLOYEE_ID).alias(FeatureCol.GROSS_PAY_ROLLING_MEDIAN),
            pl.col(PayrollCol.GROSS_PAY).shift(1).rolling_std(window_size=4, min_samples=2).over(PayrollCol.EMPLOYEE_ID).alias(FeatureCol.GROSS_PAY_ROLLING_STD),
            pl.col(PayrollCol.OVERTIME_HOURS).shift(1).rolling_median(window_size=4, min_samples=1).over(PayrollCol.EMPLOYEE_ID).alias(FeatureCol.OVERTIME_ROLLING_MEDIAN),
        )
        .with_columns(
            ((pl.col(PayrollCol.GROSS_PAY) - pl.col(FeatureCol.LAG_GROSS_PAY)) / pl.col(FeatureCol.LAG_GROSS_PAY).abs().clip(1, None)).alias(FeatureCol.GROSS_PAY_PCT_CHANGE),
            (pl.col(PayrollCol.DEDUCTIONS).fill_null(0) / pl.col(PayrollCol.GROSS_PAY).clip(1, None)).alias(FeatureCol.DEDUCTION_RATIO),
            (pl.col(PayrollCol.NET_PAY) / pl.col(PayrollCol.GROSS_PAY).clip(1, None)).alias(FeatureCol.NET_TO_GROSS_RATIO),
        )
    )


def add_peer_features(payroll: pl.DataFrame) -> pl.DataFrame:
    base = payroll.with_columns(
        pl.when(pl.col(PayrollCol.TENURE_MONTHS) < 6)
        .then(pl.lit("new"))
        .when(pl.col(PayrollCol.TENURE_MONTHS) < 36)
        .then(pl.lit("established"))
        .otherwise(pl.lit("tenured"))
        .alias(FeatureCol.TENURE_BUCKET)
    )
    peers = base.group_by(PEER_GROUP_COLUMNS).agg(
        pl.median(PayrollCol.GROSS_PAY).alias(FeatureCol.PEER_GROSS_MEDIAN),
        pl.mean(PayrollCol.GROSS_PAY).alias(FeatureCol.PEER_GROSS_MEAN),
        pl.std(PayrollCol.GROSS_PAY).alias(FeatureCol.PEER_GROSS_STD),
        pl.median(PayrollCol.OVERTIME_HOURS).alias(FeatureCol.PEER_OVERTIME_MEDIAN),
    )
    return base.join(peers, on=PEER_GROUP_COLUMNS, how="left").with_columns(
        ((pl.col(PayrollCol.GROSS_PAY) - pl.col(FeatureCol.PEER_GROSS_MEDIAN)) / pl.col(FeatureCol.PEER_GROSS_MEDIAN).abs().clip(1, None)).alias(FeatureCol.PEER_GROSS_DEVIATION_RATIO),
        ((pl.col(PayrollCol.OVERTIME_HOURS) - pl.col(FeatureCol.PEER_OVERTIME_MEDIAN)) / (pl.col(FeatureCol.PEER_OVERTIME_MEDIAN) + 1)).alias(FeatureCol.PEER_OVERTIME_DEVIATION_RATIO),
    )


def add_robust_features(payroll: pl.DataFrame) -> pl.DataFrame:
    med = payroll.select(pl.median(PayrollCol.GROSS_PAY)).item()
    q1 = payroll.select(pl.col(PayrollCol.GROSS_PAY).quantile(0.25)).item()
    q3 = payroll.select(pl.col(PayrollCol.GROSS_PAY).quantile(0.75)).item()
    mad = payroll.select((pl.col(PayrollCol.GROSS_PAY) - med).abs().median()).item() or 1.0
    iqr = (q3 - q1) or 1.0
    sorted_pay = payroll.select(PayrollCol.GROSS_PAY).to_series().sort().to_list()
    return payroll.with_columns(
        (((pl.col(PayrollCol.GROSS_PAY) - med).abs()) / (1.4826 * mad)).alias(FeatureCol.GROSS_PAY_ROBUST_Z),
        (((pl.col(PayrollCol.GROSS_PAY) - med).abs()) / mad).alias(FeatureCol.GROSS_PAY_MAD_SCORE),
        ((pl.col(PayrollCol.GROSS_PAY) < q1 - 1.5 * iqr) | (pl.col(PayrollCol.GROSS_PAY) > q3 + 1.5 * iqr)).cast(pl.Int64).alias(FeatureCol.GROSS_PAY_IQR_OUTLIER),
        pl.col(PayrollCol.GROSS_PAY).map_elements(lambda value: _percentile(value, sorted_pay), return_dtype=pl.Float64).alias(FeatureCol.GROSS_PAY_PERCENTILE),
        ((pl.col(PayrollCol.GROSS_PAY) - med) / max(med, 1)).alias(FeatureCol.GROSS_PAY_DEVIATION_RATIO),
    )


def build_features(payroll: pl.DataFrame) -> pl.DataFrame:
    return add_robust_features(add_peer_features(add_history_features(payroll))).fill_nan(None)


def _percentile(value: float, sorted_values: list[float]) -> float:
    if not sorted_values:
        return 0.0
    less_equal = sum(1 for candidate in sorted_values if candidate <= value)
    return less_equal / len(sorted_values)

from __future__ import annotations

import math
from typing import Any, cast

import polars as pl

from payroll_anomaly_ranking.columns import PEER_GROUP_COLUMNS, FeatureCol, PayrollCol


def add_history_features(payroll: pl.DataFrame) -> pl.DataFrame:
    payroll = _ensure_snf_feature_inputs(payroll)
    return (
        payroll.sort(
            [
                PayrollCol.EMPLOYEE_ID,
                PayrollCol.PAY_PERIOD_INDEX,
                PayrollCol.SHIFT_DATE,
            ],
        )
        .with_columns(
            pl.col(PayrollCol.GROSS_PAY)
            .shift(1)
            .over(PayrollCol.EMPLOYEE_ID)
            .alias(FeatureCol.LAG_GROSS_PAY),
            pl.col(PayrollCol.GROSS_PAY)
            .shift(1)
            .rolling_median(window_size=4, min_samples=1)
            .over(PayrollCol.EMPLOYEE_ID)
            .alias(FeatureCol.GROSS_PAY_ROLLING_MEDIAN),
            pl.col(PayrollCol.GROSS_PAY)
            .shift(1)
            .rolling_std(window_size=4, min_samples=2)
            .over(PayrollCol.EMPLOYEE_ID)
            .alias(FeatureCol.GROSS_PAY_ROLLING_STD),
            pl.col(PayrollCol.OVERTIME_HOURS)
            .shift(1)
            .rolling_median(window_size=4, min_samples=1)
            .over(PayrollCol.EMPLOYEE_ID)
            .alias(FeatureCol.OVERTIME_ROLLING_MEDIAN),
            (
                pl.col(PayrollCol.PAY_PERIOD_INDEX)
                .cum_count()
                .over(PayrollCol.EMPLOYEE_ID)
                - 1
            )
            .clip(0, None)
            .alias(FeatureCol.PRIOR_EMPLOYEE_PAY_PERIOD_COUNT),
        )
        .with_columns(
            (
                (pl.col(PayrollCol.GROSS_PAY) - pl.col(FeatureCol.LAG_GROSS_PAY))
                / pl.col(FeatureCol.LAG_GROSS_PAY).abs().clip(1, None)
            ).alias(FeatureCol.GROSS_PAY_PCT_CHANGE),
            (
                pl.col(PayrollCol.DEDUCTIONS).fill_null(0)
                / pl.col(PayrollCol.GROSS_PAY).clip(1, None)
            ).alias(FeatureCol.DEDUCTION_RATIO),
            (
                pl.col(PayrollCol.NET_PAY) / pl.col(PayrollCol.GROSS_PAY).clip(1, None)
            ).alias(FeatureCol.NET_TO_GROSS_RATIO),
            (
                pl.col(PayrollCol.OVERTIME_HOURS)
                / pl.col(PayrollCol.SCHEDULED_HOURS).clip(1, None)
            ).alias(FeatureCol.OVERTIME_PER_SCHEDULED_HOUR),
            (
                pl.col(PayrollCol.WORKED_HOURS)
                / pl.col(PayrollCol.SCHEDULED_HOURS).clip(1, None)
            ).alias(FeatureCol.WORKED_TO_SCHEDULED_RATIO),
            (
                pl.col(PayrollCol.PAID_HOURS)
                / pl.col(PayrollCol.SCHEDULED_HOURS).clip(1, None)
            ).alias(FeatureCol.PAID_TO_SCHEDULED_RATIO),
            (
                pl.col(PayrollCol.PREMIUM_PAY)
                / pl.col(PayrollCol.GROSS_PAY).clip(1, None)
            ).alias(FeatureCol.PREMIUM_PAY_SHARE),
            (
                pl.col(PayrollCol.GROSS_PAY)
                / pl.col(PayrollCol.EXPECTED_SHIFT_GROSS_PAY).clip(1, None)
            ).alias(FeatureCol.GROSS_TO_EXPECTED_SHIFT_PAY),
            (pl.col(PayrollCol.PAID_HOURS) - pl.col(PayrollCol.SCHEDULED_HOURS)).alias(
                FeatureCol.PAID_MINUS_SCHEDULED_HOURS,
            ),
        )
        .with_columns(
            pl.col(FeatureCol.DEDUCTION_RATIO)
            .shift(1)
            .rolling_median(window_size=4, min_samples=1)
            .over(PayrollCol.EMPLOYEE_ID)
            .alias(FeatureCol.DEDUCTION_RATIO_ROLLING_MEDIAN),
        )
    )


def add_peer_features(payroll: pl.DataFrame) -> pl.DataFrame:
    base = payroll.with_columns(
        pl.when(pl.col(PayrollCol.TENURE_MONTHS) < 6)
        .then(pl.lit("new"))
        .when(pl.col(PayrollCol.TENURE_MONTHS) < 36)
        .then(pl.lit("established"))
        .otherwise(pl.lit("tenured"))
        .alias(FeatureCol.TENURE_BUCKET),
    )
    rows = base.sort(PayrollCol.PAY_PERIOD_INDEX).to_dicts()
    peer_rows = []
    prior_by_group: dict[tuple[object, ...], list[dict[str, object]]] = {}
    prior_rows: list[dict[str, object]] = []
    for period in sorted({row[PayrollCol.PAY_PERIOD_INDEX] for row in rows}):
        period_rows = [
            row for row in rows if row[PayrollCol.PAY_PERIOD_INDEX] == period
        ]
        for row in period_rows:
            key = _peer_key(row)
            references = prior_by_group.get(key, [])
            strict_peer_group_size = len(references)
            if len(references) < 3:
                references = prior_rows
            gross_values = [
                _row_float(candidate, PayrollCol.GROSS_PAY) for candidate in references
            ]
            overtime_values = [
                _row_float(candidate, PayrollCol.OVERTIME_HOURS)
                for candidate in references
            ]
            peer_rows.append(
                {
                    PayrollCol.RECORD_ID: row[PayrollCol.RECORD_ID],
                    FeatureCol.PEER_GROSS_MEDIAN: _median(gross_values)
                    or float(row[PayrollCol.GROSS_PAY]),
                    FeatureCol.PEER_GROSS_MEAN: _mean(gross_values)
                    or float(row[PayrollCol.GROSS_PAY]),
                    FeatureCol.PEER_GROSS_STD: _std(gross_values),
                    FeatureCol.PEER_OVERTIME_MEDIAN: _median(overtime_values)
                    or float(row[PayrollCol.OVERTIME_HOURS]),
                    FeatureCol.STRICT_PEER_GROUP_SIZE: strict_peer_group_size,
                    FeatureCol.EFFECTIVE_PEER_REFERENCE_SIZE: len(references),
                    FeatureCol.FACILITY_ROLE_SHIFT_GROSS_MEDIAN: _median(gross_values)
                    or float(row[PayrollCol.GROSS_PAY]),
                    FeatureCol.FACILITY_ROLE_SHIFT_HOURS_MEDIAN: _median(
                        [
                            _row_float(candidate, PayrollCol.PAID_HOURS)
                            for candidate in references
                        ],
                    )
                    or float(row[PayrollCol.PAID_HOURS]),
                    FeatureCol.CROSS_FACILITY_ROLE_SHIFT_GROSS_MEDIAN: _median(
                        [
                            _row_float(candidate, PayrollCol.GROSS_PAY)
                            for candidate in prior_rows
                            if candidate.get(PayrollCol.ROLE)
                            == row.get(PayrollCol.ROLE)
                            and candidate.get(PayrollCol.SHIFT_TYPE)
                            == row.get(PayrollCol.SHIFT_TYPE)
                        ],
                    )
                    or float(row[PayrollCol.GROSS_PAY]),
                },
            )
        for row in period_rows:
            prior_by_group.setdefault(_peer_key(row), []).append(row)
            prior_rows.append(row)
    peers = pl.DataFrame(peer_rows, infer_schema_length=None)
    return base.join(peers, on=PayrollCol.RECORD_ID, how="left").with_columns(
        (
            (pl.col(PayrollCol.GROSS_PAY) - pl.col(FeatureCol.PEER_GROSS_MEDIAN))
            / pl.col(FeatureCol.PEER_GROSS_MEDIAN).abs().clip(1, None)
        ).alias(FeatureCol.PEER_GROSS_DEVIATION_RATIO),
        (
            (
                pl.col(PayrollCol.OVERTIME_HOURS)
                - pl.col(FeatureCol.PEER_OVERTIME_MEDIAN)
            )
            / (pl.col(FeatureCol.PEER_OVERTIME_MEDIAN) + 1)
        ).alias(FeatureCol.PEER_OVERTIME_DEVIATION_RATIO),
        (
            pl.col(FeatureCol.PREMIUM_PAY_SHARE)
            .median()
            .over([PayrollCol.FACILITY_ID, PayrollCol.ROLE, PayrollCol.SHIFT_TYPE])
        ).alias(FeatureCol.FACILITY_PREMIUM_SHARE_MEDIAN),
    )


def add_robust_features(payroll: pl.DataFrame) -> pl.DataFrame:
    rows = payroll.sort(PayrollCol.PAY_PERIOD_INDEX).to_dicts()
    robust_rows = []
    prior_values: list[float] = []
    for period in sorted({row[PayrollCol.PAY_PERIOD_INDEX] for row in rows}):
        period_rows = [
            row for row in rows if row[PayrollCol.PAY_PERIOD_INDEX] == period
        ]
        values = prior_values or [
            float(row[PayrollCol.GROSS_PAY]) for row in period_rows
        ]
        med = _median(values) or 1.0
        q1 = _quantile(values, 0.25)
        q3 = _quantile(values, 0.75)
        mad = _median([abs(value - med) for value in values]) or 1.0
        iqr = (q3 - q1) or 1.0
        sorted_values = sorted(values)
        for row in period_rows:
            gross = float(row[PayrollCol.GROSS_PAY])
            robust_rows.append(
                {
                    PayrollCol.RECORD_ID: row[PayrollCol.RECORD_ID],
                    FeatureCol.GROSS_PAY_ROBUST_Z: abs(gross - med) / (1.4826 * mad),
                    FeatureCol.GROSS_PAY_MAD_SCORE: abs(gross - med) / mad,
                    FeatureCol.GROSS_PAY_IQR_OUTLIER: int(
                        gross < q1 - 1.5 * iqr or gross > q3 + 1.5 * iqr,
                    ),
                    FeatureCol.GROSS_PAY_PERCENTILE: _percentile(gross, sorted_values),
                    FeatureCol.GROSS_PAY_DEVIATION_RATIO: (gross - med) / max(med, 1),
                    FeatureCol.FACILITY_GROSS_ROBUST_Z: abs(gross - med)
                    / (1.4826 * mad),
                },
            )
        prior_values.extend(float(row[PayrollCol.GROSS_PAY]) for row in period_rows)
    return payroll.join(
        pl.DataFrame(robust_rows, infer_schema_length=None),
        on=PayrollCol.RECORD_ID,
        how="left",
    )


def build_features(payroll: pl.DataFrame) -> pl.DataFrame:
    payroll = _ensure_snf_feature_inputs(payroll)
    featured = add_robust_features(
        add_peer_features(add_history_features(payroll)),
    ).with_columns(
        _premium_mismatch_expr().alias(FeatureCol.PREMIUM_ELIGIBILITY_MISMATCH),
        pl.struct(
            [
                PayrollCol.EMPLOYEE_ID,
                PayrollCol.SHIFT_DATE,
                PayrollCol.FACILITY_ID,
                PayrollCol.PAY_CODE,
            ],
        )
        .is_duplicated()
        .cast(pl.Int64)
        .alias(FeatureCol.DUPLICATE_PREMIUM_SIGNATURE),
        (pl.col(PayrollCol.REST_GAP_HOURS) < 8)
        .cast(pl.Int64)
        .alias(FeatureCol.REST_GAP_RISK),
    )
    return _add_trailing_shift_features(featured).fill_nan(None)


def build_employee_cycle_features(payroll: pl.DataFrame) -> pl.DataFrame:
    base = payroll.sort(
        [PayrollCol.EMPLOYEE_ID, PayrollCol.PAY_PERIOD_INDEX],
    ).with_columns(
        pl.when(pl.col(PayrollCol.TENURE_MONTHS) < 6)
        .then(pl.lit("new"))
        .when(pl.col(PayrollCol.TENURE_MONTHS) < 36)
        .then(pl.lit("established"))
        .otherwise(pl.lit("tenured"))
        .alias(FeatureCol.TENURE_BUCKET),
        pl.col(PayrollCol.TOTAL_GROSS_PAY)
        .shift(1)
        .over(PayrollCol.EMPLOYEE_ID)
        .alias(FeatureCol.LAG_GROSS_PAY),
        pl.col(PayrollCol.TOTAL_GROSS_PAY)
        .shift(1)
        .rolling_median(window_size=4, min_samples=1)
        .over(PayrollCol.EMPLOYEE_ID)
        .alias(FeatureCol.GROSS_PAY_ROLLING_MEDIAN),
        pl.col(PayrollCol.TOTAL_GROSS_PAY)
        .shift(1)
        .rolling_std(window_size=4, min_samples=2)
        .over(PayrollCol.EMPLOYEE_ID)
        .alias(FeatureCol.GROSS_PAY_ROLLING_STD),
        pl.col(PayrollCol.TOTAL_OVERTIME_HOURS)
        .shift(1)
        .rolling_median(window_size=4, min_samples=1)
        .over(PayrollCol.EMPLOYEE_ID)
        .alias(FeatureCol.OVERTIME_ROLLING_MEDIAN),
        (
            pl.col(PayrollCol.PAY_PERIOD_INDEX).cum_count().over(PayrollCol.EMPLOYEE_ID)
            - 1
        )
        .clip(0, None)
        .alias(FeatureCol.PRIOR_EMPLOYEE_PAY_PERIOD_COUNT),
    )
    base = base.with_columns(
        (
            (pl.col(PayrollCol.TOTAL_GROSS_PAY) - pl.col(FeatureCol.LAG_GROSS_PAY))
            / pl.col(FeatureCol.LAG_GROSS_PAY).abs().clip(1, None)
        ).alias(FeatureCol.GROSS_PAY_PCT_CHANGE),
        (
            pl.col(PayrollCol.TOTAL_DEDUCTIONS).fill_null(0)
            / pl.col(PayrollCol.TOTAL_GROSS_PAY).clip(1, None)
        ).alias(FeatureCol.DEDUCTION_RATIO),
        (
            pl.col(PayrollCol.TOTAL_NET_PAY)
            / pl.col(PayrollCol.TOTAL_GROSS_PAY).clip(1, None)
        ).alias(FeatureCol.NET_TO_GROSS_RATIO),
        (
            pl.col(PayrollCol.TOTAL_OVERTIME_HOURS)
            / pl.col(PayrollCol.TOTAL_SCHEDULED_HOURS).clip(1, None)
        ).alias(FeatureCol.OVERTIME_PER_SCHEDULED_HOUR),
        (
            pl.col(PayrollCol.TOTAL_WORKED_HOURS)
            / pl.col(PayrollCol.TOTAL_SCHEDULED_HOURS).clip(1, None)
        ).alias(FeatureCol.WORKED_TO_SCHEDULED_RATIO),
        (
            pl.col(PayrollCol.TOTAL_PAID_HOURS)
            / pl.col(PayrollCol.TOTAL_SCHEDULED_HOURS).clip(1, None)
        ).alias(FeatureCol.PAID_TO_SCHEDULED_RATIO),
        (
            pl.col(PayrollCol.TOTAL_PREMIUM_PAY)
            / pl.col(PayrollCol.TOTAL_GROSS_PAY).clip(1, None)
        ).alias(FeatureCol.PREMIUM_PAY_SHARE),
        (
            pl.col(PayrollCol.TOTAL_GROSS_PAY)
            / pl.col(PayrollCol.TOTAL_EXPECTED_GROSS_PAY).clip(1, None)
        ).alias(FeatureCol.GROSS_TO_EXPECTED_SHIFT_PAY),
        (
            pl.col(PayrollCol.TOTAL_PAID_HOURS)
            - pl.col(PayrollCol.TOTAL_SCHEDULED_HOURS)
        ).alias(
            FeatureCol.PAID_MINUS_SCHEDULED_HOURS,
        ),
        pl.col(PayrollCol.SHIFT_COUNT).alias(FeatureCol.TRAILING_7_DAY_HOURS),
        (pl.col(PayrollCol.ANOMALOUS_SHIFT_COUNT).fill_null(0) > 0)
        .cast(pl.Int64)
        .shift(1)
        .rolling_sum(window_size=6, min_samples=1)
        .over(PayrollCol.EMPLOYEE_ID)
        .fill_null(0)
        .alias(FeatureCol.PRIOR_DOUBLE_SHIFT_COUNT),
    )
    peer_keys = [
        PayrollCol.FACILITY_ID,
        PayrollCol.ROLE,
        FeatureCol.TENURE_BUCKET,
    ]
    base = base.with_columns(
        pl.col(FeatureCol.DEDUCTION_RATIO)
        .shift(1)
        .rolling_median(window_size=4, min_samples=1)
        .over(PayrollCol.EMPLOYEE_ID)
        .alias(FeatureCol.DEDUCTION_RATIO_ROLLING_MEDIAN),
        pl.col(PayrollCol.TOTAL_GROSS_PAY)
        .shift(1)
        .median()
        .over(peer_keys)
        .alias(FeatureCol.PEER_GROSS_MEDIAN),
        pl.col(PayrollCol.TOTAL_GROSS_PAY)
        .shift(1)
        .mean()
        .over(peer_keys)
        .alias(FeatureCol.PEER_GROSS_MEAN),
        pl.col(PayrollCol.TOTAL_GROSS_PAY)
        .shift(1)
        .std()
        .over(peer_keys)
        .alias(FeatureCol.PEER_GROSS_STD),
        pl.col(PayrollCol.TOTAL_OVERTIME_HOURS)
        .shift(1)
        .median()
        .over(peer_keys)
        .alias(FeatureCol.PEER_OVERTIME_MEDIAN),
        pl.len().over(peer_keys).alias(FeatureCol.STRICT_PEER_GROUP_SIZE),
        pl.len().over(peer_keys).alias(FeatureCol.EFFECTIVE_PEER_REFERENCE_SIZE),
        pl.col(PayrollCol.TOTAL_GROSS_PAY)
        .shift(1)
        .median()
        .over([PayrollCol.FACILITY_ID, PayrollCol.ROLE])
        .alias(FeatureCol.FACILITY_ROLE_SHIFT_GROSS_MEDIAN),
        pl.col(PayrollCol.TOTAL_PAID_HOURS)
        .shift(1)
        .median()
        .over([PayrollCol.FACILITY_ID, PayrollCol.ROLE])
        .alias(FeatureCol.FACILITY_ROLE_SHIFT_HOURS_MEDIAN),
        pl.col(PayrollCol.TOTAL_GROSS_PAY)
        .shift(1)
        .median()
        .over([PayrollCol.ROLE, FeatureCol.TENURE_BUCKET])
        .alias(FeatureCol.CROSS_FACILITY_ROLE_SHIFT_GROSS_MEDIAN),
        pl.col(FeatureCol.PREMIUM_PAY_SHARE)
        .median()
        .over([PayrollCol.FACILITY_ID, PayrollCol.ROLE])
        .alias(FeatureCol.FACILITY_PREMIUM_SHARE_MEDIAN),
    )
    base = base.with_columns(
        (
            (pl.col(PayrollCol.TOTAL_GROSS_PAY) - pl.col(FeatureCol.PEER_GROSS_MEDIAN))
            / pl.col(FeatureCol.PEER_GROSS_MEDIAN).abs().clip(1, None)
        ).alias(FeatureCol.PEER_GROSS_DEVIATION_RATIO),
        (
            (
                pl.col(PayrollCol.TOTAL_OVERTIME_HOURS)
                - pl.col(FeatureCol.PEER_OVERTIME_MEDIAN)
            )
            / (pl.col(FeatureCol.PEER_OVERTIME_MEDIAN) + 1)
        ).alias(FeatureCol.PEER_OVERTIME_DEVIATION_RATIO),
        (
            (
                pl.col(PayrollCol.TOTAL_PREMIUM_PAY)
                / pl.col(PayrollCol.TOTAL_GROSS_PAY).clip(1, None)
            )
            > (pl.col(FeatureCol.FACILITY_PREMIUM_SHARE_MEDIAN).fill_null(0) + 0.15)
        )
        .cast(pl.Int64)
        .alias(FeatureCol.PREMIUM_ELIGIBILITY_MISMATCH),
        (
            pl.struct(
                [
                    PayrollCol.EMPLOYEE_ID,
                    PayrollCol.FACILITY_ID,
                    PayrollCol.PAY_PERIOD_INDEX,
                    PayrollCol.TOTAL_PREMIUM_PAY,
                ],
            ).is_duplicated()
            & (pl.col(PayrollCol.TOTAL_PREMIUM_PAY) > 0)
        )
        .cast(pl.Int64)
        .alias(FeatureCol.DUPLICATE_PREMIUM_SIGNATURE),
        (pl.col(PayrollCol.TOTAL_OVERTIME_HOURS) > 24)
        .cast(pl.Int64)
        .alias(FeatureCol.REST_GAP_RISK),
    )
    rows = base.sort(PayrollCol.PAY_PERIOD_INDEX).to_dicts()
    robust_rows = []
    prior_values: list[float] = []
    for period in sorted({row[PayrollCol.PAY_PERIOD_INDEX] for row in rows}):
        period_rows = [
            row for row in rows if row[PayrollCol.PAY_PERIOD_INDEX] == period
        ]
        values = prior_values or [
            float(row[PayrollCol.TOTAL_GROSS_PAY]) for row in period_rows
        ]
        med = _median(values) or 1.0
        q1 = _quantile(values, 0.25)
        q3 = _quantile(values, 0.75)
        mad = _median([abs(value - med) for value in values]) or 1.0
        iqr = (q3 - q1) or 1.0
        sorted_values = sorted(values)
        for row in period_rows:
            gross = float(row[PayrollCol.TOTAL_GROSS_PAY])
            robust_rows.append(
                {
                    PayrollCol.EMPLOYEE_PAY_CYCLE_ID: row[
                        PayrollCol.EMPLOYEE_PAY_CYCLE_ID
                    ],
                    FeatureCol.GROSS_PAY_ROBUST_Z: abs(gross - med) / (1.4826 * mad),
                    FeatureCol.GROSS_PAY_MAD_SCORE: abs(gross - med) / mad,
                    FeatureCol.GROSS_PAY_IQR_OUTLIER: int(
                        gross < q1 - 1.5 * iqr or gross > q3 + 1.5 * iqr,
                    ),
                    FeatureCol.GROSS_PAY_PERCENTILE: _percentile(gross, sorted_values),
                    FeatureCol.GROSS_PAY_DEVIATION_RATIO: (gross - med) / max(med, 1),
                    FeatureCol.FACILITY_GROSS_ROBUST_Z: abs(gross - med)
                    / (1.4826 * mad),
                },
            )
        prior_values.extend(
            float(row[PayrollCol.TOTAL_GROSS_PAY]) for row in period_rows
        )
    return base.join(
        pl.DataFrame(robust_rows, infer_schema_length=None),
        on=PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
        how="left",
    ).fill_nan(None)


def _premium_mismatch_expr() -> pl.Expr:
    return (
        (pl.col(PayrollCol.PREMIUM_PAY) > 0)
        & (pl.col(PayrollCol.SHIFT_TYPE) == "Day")
        & (pl.col(PayrollCol.IS_WEEKEND) == 0)
    ).cast(pl.Int64)


def _add_trailing_shift_features(payroll: pl.DataFrame) -> pl.DataFrame:
    sorted_payroll = payroll.sort([PayrollCol.EMPLOYEE_ID, PayrollCol.SHIFT_DATE])
    return sorted_payroll.with_columns(
        pl.col(PayrollCol.PAID_HOURS)
        .shift(1)
        .rolling_sum(window_size=7, min_samples=1)
        .over(PayrollCol.EMPLOYEE_ID)
        .fill_null(0)
        .alias(FeatureCol.TRAILING_7_DAY_HOURS),
        (pl.col(PayrollCol.SAME_DAY_SHIFT_COUNT).shift(1) > 1)
        .cast(pl.Int64)
        .rolling_sum(window_size=6, min_samples=1)
        .over(PayrollCol.EMPLOYEE_ID)
        .fill_null(0)
        .alias(FeatureCol.PRIOR_DOUBLE_SHIFT_COUNT),
    )


def _ensure_snf_feature_inputs(payroll: pl.DataFrame) -> pl.DataFrame:
    defaults: dict[str, pl.Expr] = {
        PayrollCol.SHIFT_DATE: pl.lit(None, dtype=pl.Date),
        PayrollCol.SCHEDULED_HOURS: pl.lit(8.0),
        PayrollCol.WORKED_HOURS: pl.coalesce(
            pl.col(PayrollCol.REGULAR_HOURS),
            pl.lit(8.0),
        )
        if PayrollCol.REGULAR_HOURS in payroll.columns
        else pl.lit(8.0),
        PayrollCol.PAID_HOURS: (
            pl.col(PayrollCol.REGULAR_HOURS).fill_null(0)
            + pl.col(PayrollCol.OVERTIME_HOURS).fill_null(0)
        )
        if PayrollCol.REGULAR_HOURS in payroll.columns
        else pl.lit(8.0),
        PayrollCol.PREMIUM_PAY: pl.lit(0.0),
        PayrollCol.EXPECTED_SHIFT_GROSS_PAY: pl.col(PayrollCol.GROSS_PAY),
        PayrollCol.FACILITY_ID: pl.coalesce(
            pl.col(PayrollCol.LOCATION),
            pl.lit("SNF-F001"),
        )
        if PayrollCol.LOCATION in payroll.columns
        else pl.lit("SNF-F001"),
        PayrollCol.UNIT: pl.lit("Long Term Care"),
        PayrollCol.ROLE: pl.coalesce(pl.col(PayrollCol.JOB_FAMILY), pl.lit("CNA"))
        if PayrollCol.JOB_FAMILY in payroll.columns
        else pl.lit("CNA"),
        PayrollCol.SHIFT_TYPE: pl.lit("Day"),
        PayrollCol.PAY_CODE_CATEGORY: pl.lit("Regular"),
        PayrollCol.IS_WEEKEND: pl.lit(0),
        PayrollCol.REST_GAP_HOURS: pl.lit(24.0),
        PayrollCol.SAME_DAY_SHIFT_COUNT: pl.lit(1),
        PayrollCol.MISSED_PUNCH: pl.lit(0),
        PayrollCol.MANUAL_EDIT: pl.lit(0),
        PayrollCol.CLOCK_IN_VARIANCE_MINUTES: pl.lit(0.0),
        PayrollCol.CLOCK_OUT_VARIANCE_MINUTES: pl.lit(0.0),
    }
    additions = [
        expr.alias(column)
        for column, expr in defaults.items()
        if column not in payroll.columns
    ]
    if not additions:
        return payroll
    filled = payroll.with_columns(additions)
    if filled.get_column(PayrollCol.SHIFT_DATE).null_count() == filled.height:
        filled = filled.with_columns(
            (
                pl.date(2024, 1, 1)
                + pl.duration(days=(pl.col(PayrollCol.PAY_PERIOD_INDEX) - 1) * 14)
            ).alias(PayrollCol.SHIFT_DATE),
        )
    return filled


def _percentile(value: float, sorted_values: list[float]) -> float:
    if not sorted_values:
        return 0.0
    less_equal = sum(1 for candidate in sorted_values if candidate <= value)
    return less_equal / len(sorted_values)


def _peer_key(row: dict[str, object]) -> tuple[object, ...]:
    return tuple(
        row[column]
        for column in PEER_GROUP_COLUMNS
        if column != PayrollCol.PAY_PERIOD_INDEX
    )


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    average = sum(values) / len(values)
    return math.sqrt(
        sum((value - average) ** 2 for value in values) / (len(values) - 1),
    )


def _quantile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(max(round((len(ordered) - 1) * quantile), 0), len(ordered) - 1)
    return ordered[index]


def _row_float(row: dict[str, object], key: str) -> float:
    value = row.get(key)
    return 0.0 if value is None else float(cast(Any, value))

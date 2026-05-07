from __future__ import annotations

import math

import polars as pl

from payroll_anomaly_ranking.columns import PEER_GROUP_COLUMNS, FeatureCol, PayrollCol


def add_history_features(payroll: pl.DataFrame) -> pl.DataFrame:
    return (
        payroll.sort([PayrollCol.EMPLOYEE_ID, PayrollCol.PAY_PERIOD_INDEX])
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
            if len(references) < 3:
                references = prior_rows
            gross_values = [
                float(candidate[PayrollCol.GROSS_PAY]) for candidate in references
            ]
            overtime_values = [
                float(candidate[PayrollCol.OVERTIME_HOURS]) for candidate in references
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
                },
            )
        prior_values.extend(float(row[PayrollCol.GROSS_PAY]) for row in period_rows)
    return payroll.join(
        pl.DataFrame(robust_rows, infer_schema_length=None),
        on=PayrollCol.RECORD_ID,
        how="left",
    )


def build_features(payroll: pl.DataFrame) -> pl.DataFrame:
    return add_robust_features(
        add_peer_features(add_history_features(payroll)),
    ).fill_nan(None)


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
    index = min(max(int(round((len(ordered) - 1) * quantile)), 0), len(ordered) - 1)
    return ordered[index]

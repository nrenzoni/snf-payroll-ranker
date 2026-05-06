from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.ensemble import IsolationForest

from payroll_anomaly_ranking.config import PayrollConfig


FEATURE_COLUMNS = [
    "gross_pay",
    "net_pay",
    "regular_hours",
    "overtime_hours",
    "pay_rate",
    "bonus",
    "commission",
    "retro_pay",
    "manual_adjustment",
    "gross_pay_pct_change",
    "deduction_ratio",
    "net_to_gross_ratio",
    "peer_gross_deviation_ratio",
    "peer_overtime_deviation_ratio",
    "gross_pay_robust_z",
    "gross_pay_mad_score",
    "rule_severity_score",
]


def temporal_split(payroll: pl.DataFrame, validation_periods: int = 4, test_periods: int = 4) -> dict[str, pl.DataFrame]:
    periods = sorted(payroll.get_column("pay_period_index").unique().to_list())
    test_start = periods[-test_periods]
    validation_start = periods[-(test_periods + validation_periods)]
    return {
        "train": payroll.filter(pl.col("pay_period_index") < validation_start),
        "validation": payroll.filter((pl.col("pay_period_index") >= validation_start) & (pl.col("pay_period_index") < test_start)),
        "test": payroll.filter(pl.col("pay_period_index") >= test_start),
    }


def add_statistical_scores(payroll: pl.DataFrame) -> pl.DataFrame:
    return payroll.with_columns(
        pl.max_horizontal(
            pl.col("gross_pay_robust_z").fill_null(0) / 8,
            pl.col("gross_pay_mad_score").fill_null(0) / 10,
            pl.col("peer_gross_deviation_ratio").abs().fill_null(0) / 2,
            pl.col("peer_overtime_deviation_ratio").abs().fill_null(0) / 6,
        )
        .clip(0, 1)
        .alias("statistical_score"),
        pl.max_horizontal(pl.col("gross_pay_robust_z").fill_null(0) / 8, pl.col("gross_pay_pct_change").abs().fill_null(0) / 2).clip(0, 1).alias("history_score"),
        pl.max_horizontal(pl.col("peer_gross_deviation_ratio").abs().fill_null(0) / 2, pl.col("peer_overtime_deviation_ratio").abs().fill_null(0) / 6).clip(0, 1).alias("peer_score"),
    )


def add_isolation_forest_scores(payroll: pl.DataFrame, config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    splits = temporal_split(payroll)
    train = _feature_matrix(splits["train"])
    all_features = _feature_matrix(payroll)
    model = IsolationForest(n_estimators=100, contamination=0.03, random_state=config.seed)
    model.fit(train)
    raw = -model.decision_function(all_features)
    return payroll.with_columns(pl.Series("ml_score", _minmax(raw)))


def add_hybrid_scores(payroll: pl.DataFrame, config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    scored = payroll.with_columns(
        (pl.col("rule_severity_score") / 100).clip(0, 1).alias("rule_score"),
        (pl.col("anomaly_dollars").abs() / pl.col("gross_pay").abs().clip(1, None)).clip(0, 1).alias("dollar_score"),
    )
    weights = config.hybrid_weights
    return scored.with_columns(
        sum(pl.col(name).fill_null(0) * weight for name, weight in weights.items()).alias("final_anomaly_score")
    ).with_columns(
        pl.col("final_anomaly_score").rank("ordinal", descending=True).over("pay_period_index").alias("pay_period_rank")
    )


def score_payroll(payroll: pl.DataFrame, config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    return add_hybrid_scores(add_isolation_forest_scores(add_statistical_scores(payroll), config), config)


def _feature_matrix(frame: pl.DataFrame) -> np.ndarray:
    return frame.select([pl.col(column).cast(pl.Float64).fill_null(0) for column in FEATURE_COLUMNS]).to_numpy()


def _minmax(values: np.ndarray) -> np.ndarray:
    minimum = values.min()
    maximum = values.max()
    if maximum == minimum:
        return np.zeros_like(values)
    return (values - minimum) / (maximum - minimum)

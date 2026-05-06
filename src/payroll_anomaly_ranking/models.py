from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.ensemble import IsolationForest

from payroll_anomaly_ranking.columns import FeatureCol, MODEL_FEATURE_COLUMNS, PayrollCol, RuleCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig


FEATURE_COLUMNS = MODEL_FEATURE_COLUMNS


def temporal_split(payroll: pl.DataFrame, validation_periods: int = 4, test_periods: int = 4) -> dict[str, pl.DataFrame]:
    periods = sorted(payroll.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list())
    test_start = periods[-test_periods]
    validation_start = periods[-(test_periods + validation_periods)]
    return {
        "train": payroll.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) < validation_start),
        "validation": payroll.filter((pl.col(PayrollCol.PAY_PERIOD_INDEX) >= validation_start) & (pl.col(PayrollCol.PAY_PERIOD_INDEX) < test_start)),
        "test": payroll.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) >= test_start),
    }


def add_statistical_scores(payroll: pl.DataFrame) -> pl.DataFrame:
    return payroll.with_columns(
        pl.max_horizontal(
            pl.col(FeatureCol.GROSS_PAY_ROBUST_Z).fill_null(0) / 8,
            pl.col(FeatureCol.GROSS_PAY_MAD_SCORE).fill_null(0) / 10,
            pl.col(FeatureCol.PEER_GROSS_DEVIATION_RATIO).abs().fill_null(0) / 2,
            pl.col(FeatureCol.PEER_OVERTIME_DEVIATION_RATIO).abs().fill_null(0) / 6,
        )
        .clip(0, 1)
        .alias(ScoreCol.STATISTICAL_SCORE),
        pl.max_horizontal(pl.col(FeatureCol.GROSS_PAY_ROBUST_Z).fill_null(0) / 8, pl.col(FeatureCol.GROSS_PAY_PCT_CHANGE).abs().fill_null(0) / 2).clip(0, 1).alias(ScoreCol.HISTORY_SCORE),
        pl.max_horizontal(pl.col(FeatureCol.PEER_GROSS_DEVIATION_RATIO).abs().fill_null(0) / 2, pl.col(FeatureCol.PEER_OVERTIME_DEVIATION_RATIO).abs().fill_null(0) / 6).clip(0, 1).alias(ScoreCol.PEER_SCORE),
    )


def add_isolation_forest_scores(payroll: pl.DataFrame, config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    splits = temporal_split(payroll)
    train = _feature_matrix(splits["train"])
    all_features = _feature_matrix(payroll)
    model = IsolationForest(n_estimators=100, contamination=0.03, random_state=config.seed)
    model.fit(train)
    raw = -model.decision_function(all_features)
    return payroll.with_columns(pl.Series(ScoreCol.ML_SCORE, _minmax(raw)))


def add_hybrid_scores(payroll: pl.DataFrame, config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    scored = payroll.with_columns(
        (pl.col(RuleCol.SEVERITY_SCORE) / 100).clip(0, 1).alias(ScoreCol.RULE_SCORE),
        (pl.col(PayrollCol.ANOMALY_DOLLARS).abs() / pl.col(PayrollCol.GROSS_PAY).abs().clip(1, None)).clip(0, 1).alias(ScoreCol.DOLLAR_SCORE),
    )
    weights = config.hybrid_weights
    return scored.with_columns(
        sum(pl.col(name).fill_null(0) * weight for name, weight in weights.items()).alias(ScoreCol.FINAL_ANOMALY_SCORE)
    ).with_columns(
        pl.col(ScoreCol.FINAL_ANOMALY_SCORE).rank("ordinal", descending=True).over(PayrollCol.PAY_PERIOD_INDEX).alias(ScoreCol.PAY_PERIOD_RANK)
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

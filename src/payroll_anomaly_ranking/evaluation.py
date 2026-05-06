from __future__ import annotations

import polars as pl
from sklearn.metrics import average_precision_score

from payroll_anomaly_ranking.columns import AggregateCol, PayrollCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig


def precision_recall_at_k(scored: pl.DataFrame, k: int) -> dict[str, float]:
    top = scored.sort([PayrollCol.PAY_PERIOD_INDEX, ScoreCol.FINAL_ANOMALY_SCORE], descending=[False, True]).group_by(PayrollCol.PAY_PERIOD_INDEX).head(k)
    true_positives = top.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    total_anomalies = scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    precision = true_positives / max(top.height, 1)
    recall = true_positives / max(total_anomalies, 1)
    return {"k": float(k), "precision_at_k": precision, "recall_at_k": recall, "f1_at_k": _f1(precision, recall)}


def dollars_captured_at_k(scored: pl.DataFrame, k: int) -> dict[str, float]:
    top = scored.sort([PayrollCol.PAY_PERIOD_INDEX, ScoreCol.FINAL_ANOMALY_SCORE], descending=[False, True]).group_by(PayrollCol.PAY_PERIOD_INDEX).head(k)
    captured = top.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).select(pl.sum(PayrollCol.ANOMALY_DOLLARS)).item() or 0.0
    total = scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).select(pl.sum(PayrollCol.ANOMALY_DOLLARS)).item() or 0.0
    return {"k": float(k), "dollars_captured_at_k": float(captured), "dollar_capture_rate": float(captured / total) if total else 0.0}


def ranking_metrics(scored: pl.DataFrame) -> dict[str, float]:
    anomalies = scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
    average_rank = anomalies.select(pl.mean(ScoreCol.PAY_PERIOD_RANK)).item() if anomalies.height else 0.0
    reciprocal = anomalies.select((1 / pl.col(ScoreCol.PAY_PERIOD_RANK)).mean()).item() if anomalies.height else 0.0
    try:
        pr_auc = float(average_precision_score(scored.get_column(PayrollCol.IS_ANOMALY).to_numpy(), scored.get_column(ScoreCol.FINAL_ANOMALY_SCORE).to_numpy()))
    except ValueError:
        pr_auc = 0.0
    return {"average_anomaly_rank": float(average_rank), "mean_reciprocal_rank": float(reciprocal), "pr_auc": pr_auc}


def evaluate_scores(scored: pl.DataFrame, config: PayrollConfig = PayrollConfig()) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    rows = []
    for k in config.review_budgets:
        rows.append({**precision_recall_at_k(scored, k), **dollars_captured_at_k(scored, k), **ranking_metrics(scored)})
    comparison = model_comparison(scored, config)
    category = category_error_analysis(scored)
    return pl.DataFrame(rows), comparison, category


def model_comparison(scored: pl.DataFrame, config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    rows = []
    for score_name in [ScoreCol.RULE_SCORE, ScoreCol.STATISTICAL_SCORE, ScoreCol.ML_SCORE, ScoreCol.FINAL_ANOMALY_SCORE]:
        renamed = scored.with_columns(pl.col(score_name).alias(ScoreCol.FINAL_ANOMALY_SCORE)).with_columns(pl.col(ScoreCol.FINAL_ANOMALY_SCORE).rank("ordinal", descending=True).over(PayrollCol.PAY_PERIOD_INDEX).alias(ScoreCol.PAY_PERIOD_RANK))
        metric = precision_recall_at_k(renamed, config.review_budgets[0])
        rows.append({"model": score_name.replace(ScoreCol.FINAL_ANOMALY_SCORE, "hybrid_score"), **metric, **ranking_metrics(renamed)})
    return pl.DataFrame(rows)


def category_error_analysis(scored: pl.DataFrame, review_budget: int = 25) -> pl.DataFrame:
    reviewed = scored.with_columns((pl.col(ScoreCol.PAY_PERIOD_RANK) <= review_budget).alias(AggregateCol.REVIEWED))
    return reviewed.group_by(PayrollCol.ANOMALY_CATEGORY).agg(
        pl.len().alias(AggregateCol.RECORDS),
        pl.sum(PayrollCol.IS_ANOMALY).alias(AggregateCol.TRUE_ANOMALIES),
        pl.col(AggregateCol.REVIEWED).cast(pl.Int64).sum().alias(AggregateCol.REVIEWED_RECORDS),
        (pl.col(AggregateCol.REVIEWED) & (pl.col(PayrollCol.IS_ANOMALY) == 1)).cast(pl.Int64).sum().alias(AggregateCol.TRUE_POSITIVE_REVIEWS),
        ((~pl.col(AggregateCol.REVIEWED)) & (pl.col(PayrollCol.IS_ANOMALY) == 1)).cast(pl.Int64).sum().alias(AggregateCol.FALSE_NEGATIVES),
        (pl.col(AggregateCol.REVIEWED) & (pl.col(PayrollCol.IS_ANOMALY) == 0)).cast(pl.Int64).sum().alias(AggregateCol.FALSE_POSITIVES),
    )


def backtest_by_period(scored: pl.DataFrame, config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    rows = []
    for period in sorted(scored.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list())[4:]:
        period_scores = scored.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) == period)
        rows.append({PayrollCol.PAY_PERIOD_INDEX: period, **precision_recall_at_k(period_scores, min(config.review_budgets[0], period_scores.height))})
    return pl.DataFrame(rows)


def _f1(precision: float, recall: float) -> float:
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)

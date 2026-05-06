from __future__ import annotations

import polars as pl
from sklearn.metrics import average_precision_score

from payroll_anomaly_ranking.config import PayrollConfig


def precision_recall_at_k(scored: pl.DataFrame, k: int) -> dict[str, float]:
    top = scored.sort(["pay_period_index", "final_anomaly_score"], descending=[False, True]).group_by("pay_period_index").head(k)
    true_positives = top.filter(pl.col("is_anomaly") == 1).height
    total_anomalies = scored.filter(pl.col("is_anomaly") == 1).height
    precision = true_positives / max(top.height, 1)
    recall = true_positives / max(total_anomalies, 1)
    return {"k": float(k), "precision_at_k": precision, "recall_at_k": recall, "f1_at_k": _f1(precision, recall)}


def dollars_captured_at_k(scored: pl.DataFrame, k: int) -> dict[str, float]:
    top = scored.sort(["pay_period_index", "final_anomaly_score"], descending=[False, True]).group_by("pay_period_index").head(k)
    captured = top.filter(pl.col("is_anomaly") == 1).select(pl.sum("anomaly_dollars")).item() or 0.0
    total = scored.filter(pl.col("is_anomaly") == 1).select(pl.sum("anomaly_dollars")).item() or 0.0
    return {"k": float(k), "dollars_captured_at_k": float(captured), "dollar_capture_rate": float(captured / total) if total else 0.0}


def ranking_metrics(scored: pl.DataFrame) -> dict[str, float]:
    anomalies = scored.filter(pl.col("is_anomaly") == 1)
    average_rank = anomalies.select(pl.mean("pay_period_rank")).item() if anomalies.height else 0.0
    reciprocal = anomalies.select((1 / pl.col("pay_period_rank")).mean()).item() if anomalies.height else 0.0
    try:
        pr_auc = float(average_precision_score(scored.get_column("is_anomaly").to_numpy(), scored.get_column("final_anomaly_score").to_numpy()))
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
    for score_name in ["rule_score", "statistical_score", "ml_score", "final_anomaly_score"]:
        renamed = scored.with_columns(pl.col(score_name).alias("final_anomaly_score")).with_columns(pl.col("final_anomaly_score").rank("ordinal", descending=True).over("pay_period_index").alias("pay_period_rank"))
        metric = precision_recall_at_k(renamed, config.review_budgets[0])
        rows.append({"model": score_name.replace("final_anomaly_score", "hybrid_score"), **metric, **ranking_metrics(renamed)})
    return pl.DataFrame(rows)


def category_error_analysis(scored: pl.DataFrame, review_budget: int = 25) -> pl.DataFrame:
    reviewed = scored.with_columns((pl.col("pay_period_rank") <= review_budget).alias("reviewed"))
    return reviewed.group_by("anomaly_category").agg(
        pl.len().alias("records"),
        pl.sum("is_anomaly").alias("true_anomalies"),
        pl.col("reviewed").cast(pl.Int64).sum().alias("reviewed_records"),
        (pl.col("reviewed") & (pl.col("is_anomaly") == 1)).cast(pl.Int64).sum().alias("true_positive_reviews"),
        ((~pl.col("reviewed")) & (pl.col("is_anomaly") == 1)).cast(pl.Int64).sum().alias("false_negatives"),
        (pl.col("reviewed") & (pl.col("is_anomaly") == 0)).cast(pl.Int64).sum().alias("false_positives"),
    )


def backtest_by_period(scored: pl.DataFrame, config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    rows = []
    for period in sorted(scored.get_column("pay_period_index").unique().to_list())[4:]:
        period_scores = scored.filter(pl.col("pay_period_index") == period)
        rows.append({"pay_period_index": period, **precision_recall_at_k(period_scores, min(config.review_budgets[0], period_scores.height))})
    return pl.DataFrame(rows)


def _f1(precision: float, recall: float) -> float:
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)

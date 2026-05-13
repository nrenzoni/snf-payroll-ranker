from __future__ import annotations

from dataclasses import dataclass, field

import polars as pl
from sklearn.metrics import average_precision_score

from payroll_anomaly_ranking.columns import (
    MODEL_FEATURE_COLUMNS,
    AggregateCol,
    MetricCol,
    PayrollCol,
    ReviewCol,
    ScoreCol,
)
from payroll_anomaly_ranking.config import PayrollConfig


@dataclass(frozen=True)
class EvaluationResults:
    metrics: pl.DataFrame
    model_comparison: pl.DataFrame
    category_error_analysis: pl.DataFrame
    uncertainty_bucket_metrics: pl.DataFrame
    risk_coverage_analysis: pl.DataFrame
    expected_gross_pay_interval_metrics: pl.DataFrame
    threshold_baseline_metrics: pl.DataFrame = field(default_factory=pl.DataFrame)


@dataclass(frozen=True)
class RollingOriginResults:
    metrics: pl.DataFrame
    selected_settings: pl.DataFrame
    stability_summary: pl.DataFrame


def precision_recall_at_k(scored: pl.DataFrame, k: int) -> dict[str, float]:
    top = (
        scored.sort(
            [PayrollCol.PAY_PERIOD_INDEX, ScoreCol.FINAL_ANOMALY_SCORE],
            descending=[False, True],
        )
        .group_by(PayrollCol.PAY_PERIOD_INDEX)
        .head(k)
    )
    true_positives = top.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    total_anomalies = scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    precision = true_positives / max(top.height, 1)
    recall = true_positives / max(total_anomalies, 1)
    return {
        "k": float(k),
        "precision_at_k": precision,
        "recall_at_k": recall,
        "f1_at_k": _f1(precision, recall),
    }


def dollars_captured_at_k(scored: pl.DataFrame, k: int) -> dict[str, float]:
    top = (
        scored.sort(
            [PayrollCol.PAY_PERIOD_INDEX, ScoreCol.FINAL_ANOMALY_SCORE],
            descending=[False, True],
        )
        .group_by(PayrollCol.PAY_PERIOD_INDEX)
        .head(k)
    )
    captured = (
        top.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0
    )
    total = (
        scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0
    )
    return {
        "k": float(k),
        "dollars_captured_at_k": float(captured),
        "dollar_capture_rate": float(captured / total) if total else 0.0,
    }


def ranking_metrics(scored: pl.DataFrame) -> dict[str, float]:
    anomalies = scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
    average_rank = (
        anomalies.select(pl.mean(ScoreCol.PAY_PERIOD_RANK)).item()
        if anomalies.height
        else 0.0
    )
    reciprocal = (
        anomalies.select((1 / pl.col(ScoreCol.PAY_PERIOD_RANK)).mean()).item()
        if anomalies.height
        else 0.0
    )
    try:
        pr_auc = float(
            average_precision_score(
                scored.get_column(PayrollCol.IS_ANOMALY).to_numpy(),
                scored.get_column(ScoreCol.FINAL_ANOMALY_SCORE).to_numpy(),
            ),
        )
    except ValueError:
        pr_auc = 0.0
    return {
        "average_anomaly_rank": float(average_rank),
        "mean_reciprocal_rank": float(reciprocal),
        "pr_auc": pr_auc,
    }


def evaluate_scores(
    scored: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> EvaluationResults:
    rows = []
    for k in config.review_budgets:
        rows.append(
            {
                **precision_recall_at_k(scored, k),
                **dollars_captured_at_k(scored, k),
                **ranking_metrics(scored),
            },
        )
    comparison = model_comparison(scored, config)
    category = category_error_analysis(scored)
    uncertainty = precision_by_uncertainty_bucket(scored)
    risk_coverage = risk_coverage_analysis(scored, config)
    interval = expected_gross_pay_interval_evaluation(scored)
    threshold = threshold_baseline_metrics(scored, config)
    return EvaluationResults(
        metrics=pl.DataFrame(rows),
        model_comparison=comparison,
        category_error_analysis=category,
        uncertainty_bucket_metrics=uncertainty,
        risk_coverage_analysis=risk_coverage,
        expected_gross_pay_interval_metrics=interval,
        threshold_baseline_metrics=threshold,
    )


def precision_by_uncertainty_bucket(scored: pl.DataFrame) -> pl.DataFrame:
    if ReviewCol.UNCERTAINTY_BUCKET not in scored.columns:
        return pl.DataFrame()
    return (
        scored.group_by(ReviewCol.UNCERTAINTY_BUCKET)
        .agg(
            pl.len().alias(AggregateCol.RECORDS),
            pl.sum(PayrollCol.IS_ANOMALY).alias(AggregateCol.TRUE_ANOMALIES),
            pl.mean(PayrollCol.IS_ANOMALY).alias(MetricCol.ANOMALY_RATE),
            pl.mean(ScoreCol.COMPOSITE_UNCERTAINTY_SCORE).alias(
                AggregateCol.AVG_UNCERTAINTY,
            ),
        )
        .sort(ReviewCol.UNCERTAINTY_BUCKET)
    )


def risk_coverage_analysis(
    scored: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    if ScoreCol.COMPOSITE_UNCERTAINTY_SCORE not in scored.columns:
        return pl.DataFrame()
    rows = []
    budget = min(config.review_budgets[0], scored.height)
    for coverage in [1.0, 0.9, 0.8, 0.7, 0.6]:
        covered = scored.sort(ScoreCol.COMPOSITE_UNCERTAINTY_SCORE).head(
            max(int(scored.height * coverage), budget),
        )
        top = covered.sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True).head(budget)
        rows.append(
            {
                MetricCol.COVERAGE: coverage,
                AggregateCol.RECORDS: covered.height,
                MetricCol.ABSTAINED_RECORDS: scored.height - covered.height,
                MetricCol.REVIEW_PRECISION: _precision(top),
                "review_budget": budget,
            },
        )
    return pl.DataFrame(rows)


def expected_gross_pay_interval_evaluation(scored: pl.DataFrame) -> pl.DataFrame:
    required = {
        ScoreCol.EXPECTED_GROSS_PAY_P10,
        ScoreCol.EXPECTED_GROSS_PAY_P90,
        ScoreCol.EXPECTED_GROSS_PAY_INTERVAL_WIDTH,
    }
    if not required <= set(scored.columns):
        return pl.DataFrame()
    normal = scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 0)
    anomalies = scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
    return pl.DataFrame(
        [
            {
                MetricCol.NORMAL_INTERVAL_COVERAGE: _interval_coverage(normal),
                MetricCol.ANOMALY_EXCEEDS_P90_RATE: _exceeds_p90_rate(anomalies),
                AggregateCol.AVG_INTERVAL_WIDTH: float(
                    scored.select(
                        pl.mean(ScoreCol.EXPECTED_GROSS_PAY_INTERVAL_WIDTH),
                    ).item()
                    or 0.0,
                ),
                "avg_anomaly_excess_vs_p90": float(
                    anomalies.select(pl.mean(ScoreCol.GROSS_PAY_EXCESS_VS_P90)).item()
                    or 0.0,
                ),
            },
        ],
    )


def model_comparison(
    scored: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    rows = []
    for score_name in [
        ScoreCol.RULE_SCORE,
        ScoreCol.STATISTICAL_SCORE,
        ScoreCol.SCHEDULE_TIMECLOCK_SCORE,
        ScoreCol.PREMIUM_ELIGIBILITY_SCORE,
        ScoreCol.ML_SCORE,
        ScoreCol.FINAL_ANOMALY_SCORE,
    ]:
        if score_name not in scored.columns:
            continue
        renamed = scored.with_columns(
            pl.col(score_name).alias(ScoreCol.FINAL_ANOMALY_SCORE),
        ).with_columns(
            pl.col(ScoreCol.FINAL_ANOMALY_SCORE)
            .rank("ordinal", descending=True)
            .over(PayrollCol.PAY_PERIOD_INDEX)
            .alias(ScoreCol.PAY_PERIOD_RANK),
        )
        metric = precision_recall_at_k(renamed, config.review_budgets[0])
        rows.append(
            {
                "model": score_name.replace(
                    ScoreCol.FINAL_ANOMALY_SCORE,
                    "hybrid_score",
                ),
                **metric,
                **ranking_metrics(renamed),
            },
        )
    return pl.DataFrame(rows)


def threshold_baseline_metrics(
    scored: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    calibrated = scored
    thresholds = {
        "manual_threshold_pack": ScoreCol.THRESHOLD_MANUAL_PACK_FLAG,
        "gross_pay_threshold": ScoreCol.THRESHOLD_GROSS_PAY_FLAG,
        "total_hours_threshold": ScoreCol.THRESHOLD_TOTAL_HOURS_FLAG,
        "overtime_hours_threshold": ScoreCol.THRESHOLD_OVERTIME_HOURS_FLAG,
        "premium_dollars_threshold": ScoreCol.THRESHOLD_PREMIUM_DOLLARS_FLAG,
        "paid_vs_scheduled_threshold": ScoreCol.THRESHOLD_PAID_VS_SCHEDULED_FLAG,
        "facility_payroll_variance_threshold": ScoreCol.THRESHOLD_FACILITY_VARIANCE_FLAG,
    }
    auto_top = calibrated.sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True).head(
        min(config.review_budgets[0], scored.height),
    )
    auto_false_positives = auto_top.filter(pl.col(PayrollCol.IS_ANOMALY) == 0).height
    for name, flag in thresholds.items():
        if flag not in calibrated.columns:
            continue
        reviewed = calibrated.filter(pl.col(flag) == 1)
        true_positive = reviewed.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
        false_positive = reviewed.filter(pl.col(PayrollCol.IS_ANOMALY) == 0).height
        exposure = float(
            reviewed.select(pl.sum(ScoreCol.ESTIMATED_EXPOSURE)).item() or 0.0,
        )
        synthetic = float(
            reviewed.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
            .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
            .item()
            or 0.0,
        )
        rows.append(
            {
                "baseline": name,
                MetricCol.REVIEW_VOLUME: reviewed.height,
                MetricCol.NATIVE_REVIEW_BURDEN: reviewed.height,
                MetricCol.PRECISION_AT_K: true_positive / max(reviewed.height, 1),
                MetricCol.RECALL_AT_K: true_positive
                / max(calibrated.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height, 1),
                MetricCol.EXPOSURE_CAPTURED_AT_K: exposure,
                MetricCol.EXPOSURE_PER_REVIEW: exposure / max(reviewed.height, 1),
                MetricCol.DOLLARS_CAPTURED_AT_K: synthetic,
                MetricCol.MISSED_ESTIMATED_EXPOSURE: float(
                    calibrated.filter(
                        (pl.col(flag) == 0) & (pl.col(PayrollCol.IS_ANOMALY) == 1),
                    )
                    .select(pl.sum(ScoreCol.ESTIMATED_EXPOSURE))
                    .item()
                    or 0.0,
                ),
                MetricCol.FALSE_POSITIVES_AVOIDED: max(
                    false_positive - auto_false_positives,
                    0,
                ),
            },
        )
    return pl.DataFrame(rows)


def category_error_analysis(
    scored: pl.DataFrame,
    review_budget: int = 25,
) -> pl.DataFrame:
    reviewed = scored.with_columns(
        (pl.col(ScoreCol.PAY_PERIOD_RANK) <= review_budget).alias(
            AggregateCol.REVIEWED,
        ),
    )
    return reviewed.group_by(PayrollCol.ANOMALY_CATEGORY).agg(
        pl.len().alias(AggregateCol.RECORDS),
        pl.sum(PayrollCol.IS_ANOMALY).alias(AggregateCol.TRUE_ANOMALIES),
        pl.col(AggregateCol.REVIEWED)
        .cast(pl.Int64)
        .sum()
        .alias(AggregateCol.REVIEWED_RECORDS),
        (pl.col(AggregateCol.REVIEWED) & (pl.col(PayrollCol.IS_ANOMALY) == 1))
        .cast(pl.Int64)
        .sum()
        .alias(AggregateCol.TRUE_POSITIVE_REVIEWS),
        ((~pl.col(AggregateCol.REVIEWED)) & (pl.col(PayrollCol.IS_ANOMALY) == 1))
        .cast(pl.Int64)
        .sum()
        .alias(AggregateCol.FALSE_NEGATIVES),
        (pl.col(AggregateCol.REVIEWED) & (pl.col(PayrollCol.IS_ANOMALY) == 0))
        .cast(pl.Int64)
        .sum()
        .alias(AggregateCol.FALSE_POSITIVES),
    )


def backtest_by_period(
    scored: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    rows = []
    for period in sorted(
        scored.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list(),
    )[4:]:
        period_scores = scored.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) == period)
        rows.append(
            {
                PayrollCol.PAY_PERIOD_INDEX: period,
                **precision_recall_at_k(
                    period_scores,
                    min(config.review_budgets[0], period_scores.height),
                ),
            },
        )
    return pl.DataFrame(rows)


def rolling_origin_evaluation(
    scored: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> RollingOriginResults:
    periods = sorted(scored.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list())
    if len(periods) < 6:
        return RollingOriginResults(pl.DataFrame(), pl.DataFrame(), pl.DataFrame())

    metric_rows = []
    selected_rows = []
    queue_sets = []
    thresholds = [0.35, 0.5, 0.65, 0.8]
    for origin, validation_period in enumerate(periods[3:-2], start=1):
        test_period = periods[periods.index(validation_period) + 1]
        train_periods = [period for period in periods if period < validation_period]
        validation = scored.filter(
            pl.col(PayrollCol.PAY_PERIOD_INDEX) == validation_period,
        )
        test = scored.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) == test_period)
        selected_threshold, validation_f1 = _select_threshold(validation, thresholds)
        test_at_threshold = test.filter(
            pl.col(ScoreCol.FINAL_ANOMALY_SCORE) >= selected_threshold,
        )
        budget = min(config.review_budgets[0], test.height)
        facility_period_metrics, reviewed_ids = _facility_period_review_metrics(
            test,
            budget,
        )
        queue_sets.append(reviewed_ids)
        metric_rows.append(
            {
                "origin": origin,
                "train_start_period": min(train_periods),
                "train_end_period": max(train_periods),
                "validation_period": validation_period,
                "test_period": test_period,
                "selected_threshold": selected_threshold,
                "validation_f1": validation_f1,
                "threshold_precision": _precision(test_at_threshold),
                "threshold_recall": _recall(test, test_at_threshold),
                **facility_period_metrics,
                "test_score_mean": float(
                    test.select(pl.mean(ScoreCol.FINAL_ANOMALY_SCORE)).item() or 0.0,
                ),
            },
        )
        selected_rows.append(
            {
                "origin": origin,
                "selected_on_period": validation_period,
                "applied_to_period": test_period,
                "selected_threshold": selected_threshold,
                "validation_f1": validation_f1,
            },
        )

    metrics = pl.DataFrame(metric_rows)
    settings = pl.DataFrame(selected_rows)
    stability = pl.DataFrame(
        [
            {
                "origin_count": metrics.height,
                "precision_at_k_min": float(
                    metrics.select(pl.min("precision_at_k")).item() or 0.0,
                ),
                "precision_at_k_max": float(
                    metrics.select(pl.max("precision_at_k")).item() or 0.0,
                ),
                "recall_at_k_min": float(
                    metrics.select(pl.min("recall_at_k")).item() or 0.0,
                ),
                "recall_at_k_max": float(
                    metrics.select(pl.max("recall_at_k")).item() or 0.0,
                ),
                "score_mean_min": float(
                    metrics.select(pl.min("test_score_mean")).item() or 0.0,
                ),
                "score_mean_max": float(
                    metrics.select(pl.max("test_score_mean")).item() or 0.0,
                ),
                "mean_adjacent_queue_overlap": _mean_adjacent_overlap(queue_sets),
            },
        ],
    )
    return RollingOriginResults(metrics, settings, stability)


def _facility_period_review_metrics(
    scored: pl.DataFrame,
    budget: int,
) -> tuple[dict[str, float], set[int]]:
    ranked = scored.with_columns(
        pl.col(ScoreCol.FINAL_ANOMALY_SCORE)
        .rank("ordinal", descending=True)
        .over([PayrollCol.PAY_PERIOD_INDEX, PayrollCol.FACILITY_ID])
        .alias("_facility_period_rank"),
    )
    reviewed = ranked.filter(pl.col("_facility_period_rank") <= budget)
    true_positive = reviewed.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    total_anomalies = ranked.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    exposure = float(reviewed.select(pl.sum(ScoreCol.ESTIMATED_EXPOSURE)).item() or 0.0)
    captured_dollars = float(
        reviewed.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0,
    )
    total_dollars = float(
        ranked.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0,
    )
    precision = true_positive / max(reviewed.height, 1)
    recall = true_positive / max(total_anomalies, 1)
    return (
        {
            MetricCol.K: float(budget),
            MetricCol.REVIEW_VOLUME: float(reviewed.height),
            MetricCol.NATIVE_REVIEW_BURDEN: float(reviewed.height),
            MetricCol.PRECISION_AT_K: precision,
            MetricCol.RECALL_AT_K: recall,
            MetricCol.F1_AT_K: _f1(precision, recall),
            MetricCol.EXPOSURE_CAPTURED_AT_K: exposure,
            MetricCol.EXPOSURE_PER_REVIEW: exposure / max(reviewed.height, 1),
            MetricCol.DOLLARS_CAPTURED_AT_K: captured_dollars,
            MetricCol.DOLLAR_CAPTURE_RATE: captured_dollars / total_dollars
            if total_dollars
            else 0.0,
        },
        set(reviewed.get_column(PayrollCol.RECORD_ID).to_list()),
    )


def leakage_checks(analyst_queue: pl.DataFrame) -> pl.DataFrame:
    leakage_columns = {
        PayrollCol.IS_ANOMALY,
        PayrollCol.ANOMALY_CATEGORY,
        PayrollCol.ANOMALY_DOLLARS,
    }
    return pl.DataFrame(
        [
            {
                "check": "model_features_exclude_labels",
                "passed": not bool(leakage_columns & set(MODEL_FEATURE_COLUMNS)),
            },
            {
                "check": "analyst_queue_excludes_labels",
                "passed": not bool(leakage_columns & set(analyst_queue.columns)),
            },
            {
                "check": "scoring_features_exclude_anomaly_dollars",
                "passed": PayrollCol.ANOMALY_DOLLARS not in MODEL_FEATURE_COLUMNS,
            },
        ],
    )


def _f1(precision: float, recall: float) -> float:
    return (
        0.0
        if precision + recall == 0
        else 2 * precision * recall / (precision + recall)
    )


def _select_threshold(
    validation: pl.DataFrame,
    thresholds: list[float],
) -> tuple[float, float]:
    best_threshold = thresholds[0]
    best_f1 = -1.0
    for threshold in thresholds:
        selected = validation.filter(pl.col(ScoreCol.FINAL_ANOMALY_SCORE) >= threshold)
        f1 = _f1(_precision(selected), _recall(validation, selected))
        if f1 > best_f1:
            best_threshold = threshold
            best_f1 = f1
    return best_threshold, best_f1


def _precision(selected: pl.DataFrame) -> float:
    if selected.height == 0:
        return 0.0
    return selected.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height / selected.height


def _recall(all_rows: pl.DataFrame, selected: pl.DataFrame) -> float:
    total = all_rows.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    if total == 0:
        return 0.0
    return selected.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height / total


def _interval_coverage(frame: pl.DataFrame) -> float:
    if frame.height == 0:
        return 0.0
    covered = frame.filter(
        (pl.col(PayrollCol.GROSS_PAY) >= pl.col(ScoreCol.EXPECTED_GROSS_PAY_P10))
        & (pl.col(PayrollCol.GROSS_PAY) <= pl.col(ScoreCol.EXPECTED_GROSS_PAY_P90)),
    ).height
    return covered / frame.height


def _exceeds_p90_rate(frame: pl.DataFrame) -> float:
    if frame.height == 0:
        return 0.0
    return (
        frame.filter(
            pl.col(PayrollCol.GROSS_PAY) > pl.col(ScoreCol.EXPECTED_GROSS_PAY_P90),
        ).height
        / frame.height
    )


def _mean_adjacent_overlap(queue_sets: list[set[int]]) -> float:
    if len(queue_sets) < 2:
        return 0.0
    overlaps = []
    for left, right in zip(queue_sets, queue_sets[1:], strict=False):
        denominator = len(left | right) or 1
        overlaps.append(len(left & right) / denominator)
    return sum(overlaps) / len(overlaps)

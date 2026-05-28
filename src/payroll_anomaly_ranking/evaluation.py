from __future__ import annotations

import math
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
from payroll_anomaly_ranking.models import (
    EMPLOYEE_CYCLE_FEATURE_FAMILIES,
    score_employee_pay_cycles,
    temporal_split,
)


@dataclass(frozen=True)
class EvaluationResults:
    metrics: pl.DataFrame
    model_comparison: pl.DataFrame
    category_error_analysis: pl.DataFrame
    uncertainty_bucket_metrics: pl.DataFrame
    risk_coverage_analysis: pl.DataFrame
    expected_gross_pay_interval_metrics: pl.DataFrame
    threshold_baseline_metrics: pl.DataFrame = field(default_factory=pl.DataFrame)
    production_candidacy: pl.DataFrame = field(default_factory=pl.DataFrame)


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


def evaluate_employee_cycle_scores(
    scored: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> EvaluationResults:
    review_budgets = _employee_cycle_review_budgets(config)
    rows = []
    for k in review_budgets:
        rows.append(employee_cycle_grouped_metrics(scored, k))
    comparison = employee_cycle_model_comparison(scored, config)
    category = category_error_analysis(
        _employee_cycle_residual_frame(scored),
        review_budget=max(config.review_budgets),
    )
    rolling = rolling_origin_evaluation(scored, config)
    production = employee_cycle_production_candidacy(
        scored,
        rolling.metrics,
        queue=None,
        config=config,
    )
    return EvaluationResults(
        metrics=pl.DataFrame(rows),
        model_comparison=comparison,
        category_error_analysis=category,
        uncertainty_bucket_metrics=pl.DataFrame(),
        risk_coverage_analysis=pl.DataFrame(),
        expected_gross_pay_interval_metrics=pl.DataFrame(),
        threshold_baseline_metrics=pl.DataFrame(),
        production_candidacy=production,
    )


def employee_cycle_grouped_metrics(
    scored: pl.DataFrame,
    k: float,
) -> dict[str, float | str]:
    ranked = _employee_cycle_group_ranked(_employee_cycle_residual_frame(scored), k)
    if ranked.height == 0:
        return {
            MetricCol.K: k,
            MetricCol.PRECISION_AT_K: 0.0,
            MetricCol.RECALL_AT_K: 0.0,
            MetricCol.F1_AT_K: 0.0,
            MetricCol.RESIDUAL_NDCG_AT_K: 0.0,
            MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K: 0.0,
            MetricCol.REVIEWER_YIELD_AT_K: 0.0,
            MetricCol.DOLLARS_CAPTURED_AT_K: 0.0,
            MetricCol.EXPOSURE_CAPTURED_AT_K: 0.0,
            MetricCol.EXPOSURE_PER_REVIEW: 0.0,
            MetricCol.NET_UTILITY_CAPTURED_AT_K: 0.0,
            MetricCol.INCREMENTAL_UTILITY_AT_K: 0.0,
            MetricCol.UTILITY_PER_REVIEW: 0.0,
            MetricCol.REVIEW_VOLUME: 0.0,
            MetricCol.NATIVE_REVIEW_BURDEN: 0.0,
            MetricCol.DOLLAR_CAPTURE_RATE: 0.0,
            MetricCol.AVERAGE_ANOMALY_RANK: 0.0,
            MetricCol.MEAN_RECIPROCAL_RANK: 0.0,
            MetricCol.PR_AUC: 0.0,
            "group_count": 0.0,
            "aggregation_scheme": "mean_across_facility_pay_cycle_groups",
            "review_budget_type": _employee_cycle_review_budget_type(k),
        }
    reviewed = ranked.filter(pl.col("_employee_cycle_in_budget"))
    group_metrics = (
        ranked.group_by([PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX])
        .agg(
            pl.len().alias("group_records"),
            pl.sum(PayrollCol.Y_ISSUE).alias("group_anomalies"),
            pl.col("_employee_cycle_in_budget")
            .cast(pl.Int64)
            .sum()
            .alias("group_reviewed"),
            (pl.col("_employee_cycle_in_budget") & (pl.col(PayrollCol.Y_ISSUE) == 1))
            .cast(pl.Int64)
            .sum()
            .alias("group_true_positive"),
            pl.when(pl.col(PayrollCol.Y_ISSUE) == 1)
            .then(pl.col("_employee_cycle_group_rank"))
            .otherwise(None)
            .mean()
            .alias("group_average_anomaly_rank"),
            pl.when(pl.col(PayrollCol.Y_ISSUE) == 1)
            .then(pl.col("_employee_cycle_group_rank"))
            .otherwise(None)
            .min()
            .alias("group_first_anomaly_rank"),
        )
        .with_columns(
            (
                pl.col("group_true_positive") / pl.col("group_reviewed").clip(1, None)
            ).alias("group_precision"),
            (
                pl.col("group_true_positive") / pl.col("group_anomalies").clip(1, None)
            ).alias("group_recall"),
            pl.when(pl.col("group_first_anomaly_rank").is_not_null())
            .then(1 / pl.col("group_first_anomaly_rank"))
            .otherwise(0.0)
            .alias("group_mrr"),
        )
    )
    total_dollars = float(
        ranked.filter(pl.col(PayrollCol.Y_ISSUE) == 1)
        .select(pl.sum(PayrollCol.Y_DOLLAR))
        .item()
        or 0.0,
    )
    captured_dollars = float(
        reviewed.filter(pl.col(PayrollCol.Y_ISSUE) == 1)
        .select(pl.sum(PayrollCol.Y_DOLLAR))
        .item()
        or 0.0,
    )
    exposure = float(reviewed.select(pl.sum(ScoreCol.ESTIMATED_EXPOSURE)).item() or 0.0)
    utility = float(reviewed.select(pl.sum(PayrollCol.NET_UTILITY)).item() or 0.0)
    total_severe = (
        ranked.select(pl.sum(PayrollCol.RULE_MISSED_SEVERE_ISSUE)).item() or 0
    )
    reviewed_severe = (
        reviewed.select(pl.sum(PayrollCol.RULE_MISSED_SEVERE_ISSUE)).item() or 0
    )
    try:
        pr_auc = float(
            average_precision_score(
                ranked.get_column(PayrollCol.Y_ISSUE).to_numpy(),
                ranked.get_column(ScoreCol.FINAL_ANOMALY_SCORE).to_numpy(),
            ),
        )
    except ValueError:
        pr_auc = 0.0
    reviewer_yield = reviewed.filter(pl.col(PayrollCol.Y_ISSUE) == 1).height / max(
        reviewed.height,
        1,
    )
    return {
        MetricCol.K: k,
        MetricCol.PRECISION_AT_K: float(
            group_metrics.select(pl.mean("group_precision")).item() or 0.0,
        ),
        MetricCol.RECALL_AT_K: float(
            group_metrics.select(pl.mean("group_recall")).item() or 0.0,
        ),
        MetricCol.F1_AT_K: _f1(
            float(group_metrics.select(pl.mean("group_precision")).item() or 0.0),
            float(group_metrics.select(pl.mean("group_recall")).item() or 0.0),
        ),
        MetricCol.RESIDUAL_NDCG_AT_K: _employee_cycle_residual_ndcg_at_k(ranked),
        MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K: float(reviewed_severe)
        / max(
            float(total_severe),
            1.0,
        ),
        MetricCol.REVIEWER_YIELD_AT_K: reviewer_yield,
        MetricCol.DOLLARS_CAPTURED_AT_K: captured_dollars,
        MetricCol.EXPOSURE_CAPTURED_AT_K: exposure,
        MetricCol.EXPOSURE_PER_REVIEW: exposure / max(reviewed.height, 1),
        MetricCol.NET_UTILITY_CAPTURED_AT_K: utility,
        MetricCol.INCREMENTAL_UTILITY_AT_K: utility,
        MetricCol.UTILITY_PER_REVIEW: utility / max(reviewed.height, 1),
        MetricCol.REVIEW_VOLUME: float(reviewed.height),
        MetricCol.NATIVE_REVIEW_BURDEN: float(reviewed.height),
        MetricCol.DOLLAR_CAPTURE_RATE: captured_dollars / total_dollars
        if total_dollars
        else 0.0,
        MetricCol.AVERAGE_ANOMALY_RANK: float(
            group_metrics.select(pl.mean("group_average_anomaly_rank")).item() or 0.0,
        ),
        MetricCol.MEAN_RECIPROCAL_RANK: float(
            group_metrics.select(pl.mean("group_mrr")).item() or 0.0,
        ),
        MetricCol.PR_AUC: pr_auc,
        "group_count": float(group_metrics.height),
        "aggregation_scheme": "mean_across_facility_pay_cycle_groups",
        "review_budget_type": _employee_cycle_review_budget_type(k),
    }


def employee_cycle_model_comparison(
    scored: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    review_budgets = _employee_cycle_review_budgets(config)
    rows = []
    for score_name in [
        ScoreCol.CLASSIFICATION_SCORE,
        ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
        ScoreCol.REGRESSION_SCORE,
        ScoreCol.EXPECTED_VALUE_SCORE,
        ScoreCol.RANKING_SCORE,
        ScoreCol.ML_SCORE,
        ScoreCol.FINAL_ANOMALY_SCORE,
    ]:
        if score_name not in scored.columns:
            continue
        renamed = scored.with_columns(
            pl.col(score_name).alias(ScoreCol.FINAL_ANOMALY_SCORE),
        )
        rows.append(
            {
                "model": score_name.replace(
                    ScoreCol.FINAL_ANOMALY_SCORE,
                    "active_ranking",
                ),
                **employee_cycle_grouped_metrics(renamed, review_budgets[0]),
            },
        )
    return pl.DataFrame(rows)


def employee_cycle_feature_ablation(
    payroll: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
    review_budget: float | None = None,
) -> pl.DataFrame:
    budget = review_budget or _default_employee_cycle_ablation_budget(config)
    cumulative_feature_sets = []
    selected: list[str] = []
    for feature_set, feature_columns in EMPLOYEE_CYCLE_FEATURE_FAMILIES.items():
        selected.extend(feature_columns)
        cumulative_feature_sets.append((feature_set, tuple(dict.fromkeys(selected))))

    rows: list[dict[str, float | str]] = []
    for feature_set, feature_columns in cumulative_feature_sets:
        scored = score_employee_pay_cycles(
            payroll,
            config,
            feature_columns=feature_columns,
        ).scored
        metrics = employee_cycle_grouped_metrics(scored, budget)
        rows.append(
            {
                "feature_set": feature_set,
                MetricCol.K: budget,
                MetricCol.RESIDUAL_NDCG_AT_K: float(
                    metrics[MetricCol.RESIDUAL_NDCG_AT_K],
                ),
                MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K: float(
                    metrics[MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K],
                ),
                MetricCol.DOLLARS_CAPTURED_AT_K: float(
                    metrics[MetricCol.DOLLARS_CAPTURED_AT_K],
                ),
                MetricCol.REVIEWER_YIELD_AT_K: float(
                    metrics[MetricCol.REVIEWER_YIELD_AT_K],
                ),
                MetricCol.INCREMENTAL_UTILITY_AT_K: float(
                    metrics[MetricCol.INCREMENTAL_UTILITY_AT_K],
                ),
            },
        )
    return pl.DataFrame(rows)


def employee_cycle_training_universe_ablation(
    payroll: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
    review_budget: float | None = None,
) -> pl.DataFrame:
    budget = review_budget or _default_employee_cycle_ablation_budget(config)
    split = temporal_split(payroll)
    holdout_periods = (
        split.test.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list()
    )
    scenarios = [
        ("all_records", "all_records", False),
        ("residual_records_only", "residual_only", False),
        ("all_records_with_gate_feature", "all_records_with_gate_feature", True),
    ]
    rows: list[dict[str, float | str]] = []
    for label, training_universe, include_gate_feature in scenarios:
        scored = score_employee_pay_cycles(
            payroll,
            config,
            training_universe=training_universe,
            include_hard_rule_flag_feature=include_gate_feature,
        ).scored
        train_frame = _employee_cycle_ablation_training_frame(scored, training_universe)
        holdout_scored = scored.filter(
            pl.col(PayrollCol.PAY_PERIOD_INDEX).is_in(holdout_periods),
        )
        metrics = employee_cycle_grouped_metrics(holdout_scored, budget)
        rows.append(
            {
                "training_universe": label,
                "scoring_universe": "residual_only",
                "holdout_period_start": float(
                    min(holdout_periods) if holdout_periods else 0,
                ),
                "holdout_period_end": float(
                    max(holdout_periods) if holdout_periods else 0,
                ),
                "train_records": float(train_frame.height),
                "train_residual_records": float(
                    train_frame.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1).height,
                ),
                "train_hard_rule_share": float(
                    train_frame.select(
                        pl.mean(PayrollCol.CRITICAL_HARD_RULE_FLAG),
                    ).item()
                    or 0.0,
                ),
                MetricCol.K: budget,
                MetricCol.RESIDUAL_NDCG_AT_K: float(
                    metrics[MetricCol.RESIDUAL_NDCG_AT_K],
                ),
                MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K: float(
                    metrics[MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K],
                ),
                MetricCol.DOLLARS_CAPTURED_AT_K: float(
                    metrics[MetricCol.DOLLARS_CAPTURED_AT_K],
                ),
                MetricCol.REVIEWER_YIELD_AT_K: float(
                    metrics[MetricCol.REVIEWER_YIELD_AT_K],
                ),
                MetricCol.INCREMENTAL_UTILITY_AT_K: float(
                    metrics[MetricCol.INCREMENTAL_UTILITY_AT_K],
                ),
            },
        )
    return pl.DataFrame(rows)


def employee_cycle_label_ablation(
    scored: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
    review_budget: float | None = None,
) -> pl.DataFrame:
    budget = review_budget or _default_employee_cycle_ablation_budget(config)
    comparison_rows = []
    for model_name, score_name in _employee_cycle_model_scores(scored):
        renamed = scored.with_columns(
            pl.col(score_name).alias(ScoreCol.FINAL_ANOMALY_SCORE),
        )
        metrics = employee_cycle_grouped_metrics(renamed, budget)
        comparison_rows.append({"model": model_name, **metrics})
    comparison = pl.DataFrame(comparison_rows)

    return pl.DataFrame(
        [
            _label_ablation_row(
                comparison,
                "binary_issue",
                ["classifier", "cost_sensitive_classifier"],
                MetricCol.PR_AUC,
                "Best residual issue-probability ranking among binary classifiers.",
            ),
            _label_ablation_row(
                comparison,
                "dollar_impact",
                ["regressor", "expected_value"],
                MetricCol.DOLLARS_CAPTURED_AT_K,
                "Financial exposure targets still matter after the hard-rule gate.",
            ),
            _label_ablation_row(
                comparison,
                "graded_relevance",
                ["learning_to_rank", "final_active_ranking"],
                MetricCol.RESIDUAL_NDCG_AT_K,
                "Direct graded ranking tends to help top-of-queue ordering.",
            ),
            _label_ablation_row(
                comparison,
                "utility_label",
                ["expected_value", "final_active_ranking"],
                MetricCol.INCREMENTAL_UTILITY_AT_K,
                "Utility-aware winners balance recovery against wasted review effort.",
            ),
            _label_ablation_row(
                comparison,
                "observed_historical_label",
                ["classifier", "cost_sensitive_classifier"],
                MetricCol.REVIEWER_YIELD_AT_K,
                "Observed-correction-style signals favor issue triage but can inherit review bias.",
            ),
            _label_ablation_row(
                comparison,
                "latent_true_label",
                ["learning_to_rank", "expected_value", "final_active_ranking"],
                MetricCol.RESIDUAL_NDCG_AT_K,
                "Latent residual truth highlights methods that preserve queue quality after gating.",
            ),
        ],
    )


def employee_cycle_issue_type_model_performance(
    scored: pl.DataFrame,
    review_budget: float,
) -> pl.DataFrame:
    rows: list[dict[str, float | str]] = []
    for model_name, score_name in _employee_cycle_model_scores(scored):
        ranked = _employee_cycle_group_ranked(
            _employee_cycle_residual_frame(
                scored.with_columns(
                    pl.col(score_name).alias(ScoreCol.FINAL_ANOMALY_SCORE),
                ),
            ),
            review_budget,
        )
        category_metrics = (
            ranked.filter(pl.col(PayrollCol.Y_ISSUE) == 1)
            .group_by(PayrollCol.ANOMALY_CATEGORY)
            .agg(
                pl.len().alias("issue_records"),
                pl.sum(PayrollCol.RULE_MISSED_SEVERE_ISSUE).alias(
                    "severe_issue_records",
                ),
                pl.sum(PayrollCol.Y_DOLLAR).alias("issue_dollars"),
                pl.col("_employee_cycle_in_budget")
                .cast(pl.Int64)
                .sum()
                .alias("reviewed_issues"),
                (
                    pl.col("_employee_cycle_in_budget")
                    & (pl.col(PayrollCol.RULE_MISSED_SEVERE_ISSUE) == 1)
                )
                .cast(pl.Int64)
                .sum()
                .alias("reviewed_severe_issues"),
                pl.when(pl.col("_employee_cycle_in_budget"))
                .then(pl.col(PayrollCol.Y_DOLLAR))
                .otherwise(0.0)
                .sum()
                .alias("reviewed_dollars"),
            )
            .with_columns(
                pl.lit(model_name).alias("model"),
                pl.lit(review_budget).alias(MetricCol.K),
                (
                    pl.col("reviewed_issues") / pl.col("issue_records").clip(1, None)
                ).alias(
                    MetricCol.RECALL_AT_K,
                ),
                (
                    pl.col("reviewed_severe_issues")
                    / pl.col("severe_issue_records").clip(1, None)
                ).alias(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K),
                (
                    pl.col("reviewed_dollars")
                    / pl.col("issue_dollars").clip(1e-9, None)
                ).alias(
                    MetricCol.DOLLAR_CAPTURE_RATE,
                ),
            )
        )
        rows.extend(category_metrics.to_dicts())
    return pl.DataFrame(rows).sort(
        ["model", MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K, "issue_records"],
        descending=[False, True, True],
    )


def employee_cycle_severe_miss_examples(
    scored: pl.DataFrame,
    review_budget: float,
    *,
    limit_per_model: int = 5,
) -> pl.DataFrame:
    rows: list[pl.DataFrame] = []
    for model_name, score_name in _employee_cycle_model_scores(scored):
        ranked = _employee_cycle_group_ranked(
            _employee_cycle_residual_frame(
                scored.with_columns(
                    pl.col(score_name).alias(ScoreCol.FINAL_ANOMALY_SCORE),
                ),
            ),
            review_budget,
        )
        rows.append(
            ranked.filter(
                (pl.col(PayrollCol.RULE_MISSED_SEVERE_ISSUE) == 1)
                & (~pl.col("_employee_cycle_in_budget")),
            )
            .with_columns(
                pl.lit(model_name).alias("model"),
                pl.lit(review_budget).alias(MetricCol.K),
            )
            .sort(
                [PayrollCol.Y_DOLLAR, ScoreCol.FINAL_ANOMALY_SCORE],
                descending=[True, True],
            )
            .select(
                "model",
                MetricCol.K,
                PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
                PayrollCol.EMPLOYEE_ID,
                PayrollCol.FACILITY_ID,
                PayrollCol.PAY_PERIOD_INDEX,
                PayrollCol.ANOMALY_CATEGORY,
                PayrollCol.Y_DOLLAR,
                PayrollCol.RELEVANCE_GRADE,
                ScoreCol.FINAL_ANOMALY_SCORE,
                "_employee_cycle_group_rank",
                "_employee_cycle_group_budget_count",
            )
            .head(limit_per_model),
        )
    return pl.concat(rows, how="vertical") if rows else pl.DataFrame()


def employee_cycle_backtest_by_period(
    scored: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    review_budgets = _employee_cycle_review_budgets(config)
    rows = []
    for period in sorted(
        scored.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list(),
    )[4:]:
        period_scores = scored.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) == period)
        rows.append(
            {
                PayrollCol.PAY_PERIOD_INDEX: period,
                **employee_cycle_grouped_metrics(
                    period_scores,
                    review_budgets[0],
                ),
            },
        )
    return pl.DataFrame(rows)


def employee_cycle_production_candidacy(
    scored: pl.DataFrame,
    rolling_metrics: pl.DataFrame,
    queue: pl.DataFrame | None,
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    review_budgets = _employee_cycle_review_budgets(config)
    top_k_metrics = employee_cycle_grouped_metrics(scored, review_budgets[0])
    precision_ready = float(top_k_metrics[MetricCol.PRECISION_AT_K]) > 0.05
    recall_ready = float(top_k_metrics[MetricCol.RECALL_AT_K]) > 0.05
    temporal_ready = bool(rolling_metrics.height)
    facility_ready = (
        scored.select(pl.n_unique(PayrollCol.FACILITY_ID)).item() or 0
    ) >= 2
    uncertainty_ready = (
        ScoreCol.ML_SCORE in scored.columns and ScoreCol.RANKING_SCORE in scored.columns
    )
    explanation_ready = queue is not None and {
        PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.EXPLANATION,
    } <= set(queue.columns)
    rows = [
        {
            "criterion": "temporal_generalization",
            "passed": temporal_ready,
            "evidence": "rolling_origin_available"
            if temporal_ready
            else "rolling_origin_missing",
        },
        {
            "criterion": "facility_generalization",
            "passed": facility_ready,
            "evidence": "multiple_facilities_present"
            if facility_ready
            else "single_facility_scope",
        },
        {
            "criterion": "top_k_ranking_value",
            "passed": precision_ready and recall_ready,
            "evidence": f"review_budget={_employee_cycle_review_budget_label(review_budgets[0])}; precision={float(top_k_metrics[MetricCol.PRECISION_AT_K]):.3f}; recall={float(top_k_metrics[MetricCol.RECALL_AT_K]):.3f}",
        },
        {
            "criterion": "uncertainty_behavior",
            "passed": uncertainty_ready,
            "evidence": "multiple_formulation_scores_available"
            if uncertainty_ready
            else "uncertainty_signals_missing",
        },
        {
            "criterion": "explanation_readiness",
            "passed": explanation_ready,
            "evidence": "queue_contains_review_safe_explanations"
            if explanation_ready
            else "queue_explanation_fields_missing",
        },
    ]
    overall = all(bool(row["passed"]) for row in rows)
    rows.append(
        {
            "criterion": "overall_promotable",
            "passed": overall,
            "evidence": "all_phase_1_gates_met"
            if overall
            else "follow_up_needed_before_promotion",
        },
    )
    return pl.DataFrame(rows)


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
    review_budgets = _employee_cycle_review_budgets(config)
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
        facility_period_metrics, reviewed_ids = _facility_period_review_metrics(
            test,
            review_budgets[0],
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
    budget: float,
) -> tuple[dict[str, float], set[int]]:
    ranked = _employee_cycle_group_ranked(scored, budget).rename(
        {
            "_employee_cycle_group_rank": "_facility_period_rank",
            "_employee_cycle_group_budget_count": "_facility_period_budget_count",
            "_employee_cycle_in_budget": "_facility_period_in_budget",
        },
    )
    reviewed = ranked.filter(pl.col("_facility_period_in_budget"))
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
            MetricCol.K: budget,
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
    return leakage_checks_for_features(
        analyst_queue,
        [str(column) for column in MODEL_FEATURE_COLUMNS],
    )


def leakage_checks_for_features(
    analyst_queue: pl.DataFrame,
    feature_columns: list[str] | tuple[str, ...],
) -> pl.DataFrame:
    leakage_columns = {
        PayrollCol.IS_ANOMALY,
        PayrollCol.ANOMALY_CATEGORY,
        PayrollCol.ANOMALY_DOLLARS,
        PayrollCol.Y_ISSUE,
        PayrollCol.Y_DOLLAR,
        PayrollCol.RULE_MISSED_SEVERE_ISSUE,
        PayrollCol.RELEVANCE_GRADE,
        PayrollCol.NET_UTILITY,
    }
    return pl.DataFrame(
        [
            {
                "check": "model_features_exclude_labels",
                "passed": not bool(leakage_columns & set(feature_columns)),
            },
            {
                "check": "analyst_queue_excludes_labels",
                "passed": not bool(leakage_columns & set(analyst_queue.columns)),
            },
            {
                "check": "scoring_features_exclude_anomaly_dollars",
                "passed": PayrollCol.ANOMALY_DOLLARS not in feature_columns,
            },
        ],
    )


def _employee_cycle_group_ranked(
    scored: pl.DataFrame,
    budget: float | None = None,
) -> pl.DataFrame:
    ranked = scored.with_columns(
        pl.col(ScoreCol.FINAL_ANOMALY_SCORE)
        .rank("ordinal", descending=True)
        .over([PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX])
        .alias("_employee_cycle_group_rank"),
        pl.len()
        .over([PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX])
        .alias("_employee_cycle_group_size"),
    )
    if budget is None:
        return ranked
    return ranked.with_columns(
        _employee_cycle_group_budget_count_expr(budget).alias(
            "_employee_cycle_group_budget_count",
        ),
    ).with_columns(
        (
            pl.col("_employee_cycle_group_rank")
            <= pl.col("_employee_cycle_group_budget_count")
        ).alias("_employee_cycle_in_budget"),
    )


def _employee_cycle_residual_frame(scored: pl.DataFrame) -> pl.DataFrame:
    if PayrollCol.RESIDUAL_RECORD not in scored.columns:
        return scored
    return scored.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)


def _employee_cycle_model_scores(scored: pl.DataFrame) -> list[tuple[str, str]]:
    model_scores = [
        ("classifier", ScoreCol.CLASSIFICATION_SCORE),
        (
            "cost_sensitive_classifier",
            ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
        ),
        ("regressor", ScoreCol.REGRESSION_SCORE),
        ("expected_value", ScoreCol.EXPECTED_VALUE_SCORE),
        ("learning_to_rank", ScoreCol.RANKING_SCORE),
        ("final_active_ranking", ScoreCol.FINAL_ANOMALY_SCORE),
    ]
    return [
        (model_name, score_name)
        for model_name, score_name in model_scores
        if score_name in scored.columns
    ]


def _label_ablation_row(
    comparison: pl.DataFrame,
    label_name: str,
    candidate_models: list[str],
    selection_metric: str,
    interpretation: str,
) -> dict[str, float | str]:
    candidates = comparison.filter(pl.col("model").is_in(candidate_models))
    if candidates.is_empty():
        return {
            "label": label_name,
            "best_model": "unavailable",
            "selection_metric": selection_metric,
            "selection_value": 0.0,
            "interpretation": interpretation,
        }
    winner = candidates.sort(selection_metric, descending=True).row(0, named=True)
    return {
        "label": label_name,
        "best_model": str(winner["model"]),
        "selection_metric": selection_metric,
        "selection_value": float(winner[selection_metric] or 0.0),
        "interpretation": interpretation,
    }


def _default_employee_cycle_ablation_budget(config: PayrollConfig) -> float:
    review_budgets = _employee_cycle_review_budgets(config)
    if 0.05 in review_budgets:
        return 0.05
    return review_budgets[0]


def _employee_cycle_ablation_training_frame(
    scored: pl.DataFrame,
    training_universe: str,
) -> pl.DataFrame:
    train_periods = (
        temporal_split(scored)
        .train.get_column(PayrollCol.PAY_PERIOD_INDEX)
        .unique()
        .to_list()
    )
    train_frame = scored.filter(
        pl.col(PayrollCol.PAY_PERIOD_INDEX).is_in(train_periods),
    )
    if training_universe in {"residual_only", "residual_records_only"}:
        residual_only = train_frame.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)
        return residual_only if residual_only.height else train_frame
    return train_frame


def _employee_cycle_residual_ndcg_at_k(scored: pl.DataFrame) -> float:
    if scored.height == 0:
        return 0.0
    values: list[float] = []
    for _, group in scored.group_by(
        [PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX],
    ):
        relevances: list[float] = (
            group.sort("_employee_cycle_group_rank")
            .get_column(
                PayrollCol.RELEVANCE_GRADE,
            )
            .cast(pl.Float64)
            .to_list()
        )
        budget_count = int(
            group.select(pl.max("_employee_cycle_group_budget_count")).item() or 0,
        )
        actual = _dcg(relevances[:budget_count])
        ideal = _dcg(sorted(relevances, reverse=True)[:budget_count])
        values.append(0.0 if ideal == 0 else actual / ideal)
    return (sum(values) / len(values)) if values else 0.0


def _employee_cycle_group_budget_count_expr(budget: float) -> pl.Expr:
    if budget <= 1:
        return (
            (pl.col("_employee_cycle_group_size") * budget)
            .ceil()
            .cast(pl.Int64)
            .clip(1, None)
        )
    return pl.lit(max(math.ceil(budget), 1), dtype=pl.Int64)


def _employee_cycle_review_budgets(config: PayrollConfig) -> tuple[float, ...]:
    if config.employee_cycle_review_budget_percents is not None:
        return config.employee_cycle_review_budget_percents
    return tuple(float(budget) for budget in config.review_budgets)


def _employee_cycle_review_budget_type(budget: float) -> str:
    return "percent_of_group" if budget <= 1 else "top_k_per_group"


def _employee_cycle_review_budget_label(budget: float) -> str:
    if budget <= 1:
        return f"{budget:.0%}"
    return str(int(budget))


def _dcg(relevances: list[float]) -> float:
    total = 0.0
    for index, relevance in enumerate(relevances, start=1):
        gain = (2**relevance) - 1.0
        total += gain / math.log2(index + 1.0)
    return total


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

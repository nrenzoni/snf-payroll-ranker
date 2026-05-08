from __future__ import annotations

from typing import Any

import lets_plot as lp
import polars as pl

from payroll_anomaly_ranking.columns import (
    AggregateCol,
    FeatureCol,
    PayrollCol,
    ScoreCol,
)

aes: Any = getattr(lp, "aes")
geom_errorbar: Any = getattr(lp, "geom_errorbar")
geom_density: Any = getattr(lp, "geom_density")
geom_histogram: Any = getattr(lp, "geom_histogram")
geom_line: Any = getattr(lp, "geom_line")
geom_point: Any = getattr(lp, "geom_point")
geom_segment: Any = getattr(lp, "geom_segment")
geom_tile: Any = getattr(lp, "geom_tile")
ggplot: Any = getattr(lp, "ggplot")
ggtitle: Any = getattr(lp, "ggtitle")
theme_minimal: Any = getattr(lp, "theme_minimal")


def payroll_trend_chart(payroll: pl.DataFrame):
    data = _plot_data(
        payroll.group_by(PayrollCol.PAY_PERIOD_INDEX)
        .agg(pl.sum(PayrollCol.GROSS_PAY).alias(PayrollCol.GROSS_PAY))
        .sort(PayrollCol.PAY_PERIOD_INDEX),
    )
    return (
        ggplot(data, aes(PayrollCol.PAY_PERIOD_INDEX, PayrollCol.GROSS_PAY))
        + geom_line()
        + ggtitle("Synthetic Payroll Trend")
        + theme_minimal()
    )


def pay_distribution_chart(payroll: pl.DataFrame):
    return (
        ggplot(
            _plot_data(payroll.select(PayrollCol.GROSS_PAY)),
            aes(PayrollCol.GROSS_PAY),
        )
        + geom_histogram(bins=30)
        + ggtitle("Gross Pay Distribution")
        + theme_minimal()
    )


def overtime_distribution_chart(payroll: pl.DataFrame):
    return (
        ggplot(
            _plot_data(payroll.select(PayrollCol.OVERTIME_HOURS)),
            aes(PayrollCol.OVERTIME_HOURS),
        )
        + geom_histogram(bins=30)
        + ggtitle("Overtime Distribution")
        + theme_minimal()
    )


def department_heatmap_data(payroll: pl.DataFrame) -> pl.DataFrame:
    return payroll.group_by([PayrollCol.PAY_PERIOD_INDEX, PayrollCol.DEPARTMENT]).agg(
        pl.sum(PayrollCol.GROSS_PAY).alias(AggregateCol.DEPARTMENT_GROSS_PAY),
    )


def score_distribution_chart(scored: pl.DataFrame):
    return (
        ggplot(
            _plot_data(scored.select(ScoreCol.FINAL_ANOMALY_SCORE)),
            aes(ScoreCol.FINAL_ANOMALY_SCORE),
        )
        + geom_histogram(bins=30)
        + ggtitle("Hybrid Score Distribution")
        + theme_minimal()
    )


def precision_at_k_chart(metrics: pl.DataFrame):
    return (
        ggplot(_plot_data(metrics), aes("k", "precision_at_k"))
        + geom_point()
        + geom_line()
        + ggtitle("Precision@K")
        + theme_minimal()
    )


def dollars_captured_chart(metrics: pl.DataFrame):
    return (
        ggplot(_plot_data(metrics), aes("k", "dollar_capture_rate"))
        + geom_point()
        + geom_line()
        + ggtitle("Dollars Captured@K")
        + theme_minimal()
    )


def employee_history_chart(scored: pl.DataFrame, employee_id: str):
    data = _plot_data(
        scored.filter(pl.col(PayrollCol.EMPLOYEE_ID) == employee_id)
        .select(
            [
                PayrollCol.PAY_PERIOD_INDEX,
                PayrollCol.GROSS_PAY,
                FeatureCol.GROSS_PAY_ROLLING_MEDIAN,
            ],
        )
        .sort(PayrollCol.PAY_PERIOD_INDEX),
    )
    return (
        ggplot(data, aes(PayrollCol.PAY_PERIOD_INDEX, PayrollCol.GROSS_PAY))
        + geom_line()
        + geom_point()
        + ggtitle(f"Highlighted History: {employee_id}")
        + theme_minimal()
    )


def credible_interval_chart(intervals: pl.DataFrame, metric_col: str = "metric"):
    return (
        ggplot(_plot_data(intervals), aes(metric_col, "mean"))
        + geom_point()
        + ggtitle("Bayesian-Style Review Budget Intervals")
        + theme_minimal()
    )


def posterior_comparison_chart(comparison: pl.DataFrame):
    return pairwise_superiority_heatmap(comparison)


def pairwise_superiority_heatmap(comparison: pl.DataFrame):
    fill_col = (
        "win_probability"
        if "win_probability" in comparison.columns
        else "superiority_probability"
    )
    return (
        ggplot(
            _plot_data(comparison),
            aes("left_signal", "right_signal", fill=fill_col),
        )
        + geom_tile()
        + ggtitle("Pairwise Component Superiority")
        + theme_minimal()
    )


def effect_size_interval_chart(
    intervals: pl.DataFrame,
    x: str = "left_signal",
    y: str = "mean_delta",
):
    return (
        ggplot(_plot_data(intervals), aes(x, y))
        + geom_point(aes(size="samples", color="scenario"))
        + geom_errorbar(aes(ymin="lower_95", ymax="upper_95"), width=0.2)
        + ggtitle("Effect-Size Intervals")
        + theme_minimal()
    )


def review_budget_interval_chart(intervals: pl.DataFrame):
    return (
        ggplot(_plot_data(intervals), aes("metric", "mean"))
        + geom_point()
        + geom_errorbar(aes(ymin="lower_95", ymax="upper_95"), width=0.2)
        + ggtitle("Review-Budget Uncertainty Intervals")
        + theme_minimal()
    )


def subgroup_forest_chart(subgroups: pl.DataFrame):
    data = _sort_if_present(subgroups, "pooled_anomaly_rate")
    return (
        ggplot(_plot_data(data), aes("subgroup", "pooled_anomaly_rate"))
        + geom_point(aes(size="records", color="scenario"))
        + geom_errorbar(aes(ymin="lower_95", ymax="upper_95"), width=0.2)
        + ggtitle("Subgroup Pooled Anomaly Rates")
        + theme_minimal()
    )


def subgroup_caterpillar_chart(subgroups: pl.DataFrame):
    return (
        ggplot(
            _plot_data(subgroups.sort("pooled_anomaly_rate")),
            aes("subgroup", "pooled_anomaly_rate"),
        )
        + geom_point(aes(size="records"))
        + geom_errorbar(aes(ymin="lower_95", ymax="upper_95"), width=0.2)
        + ggtitle("Subgroup Caterpillar View")
        + theme_minimal()
    )


def subgroup_shrinkage_chart(subgroups: pl.DataFrame):
    return (
        ggplot(_plot_data(subgroups), aes("raw_anomaly_rate", "pooled_anomaly_rate"))
        + geom_point(aes(size="records"))
        + ggtitle("Raw vs Pooled Subgroup Rates")
        + theme_minimal()
    )


def subgroup_funnel_chart(subgroups: pl.DataFrame):
    return (
        ggplot(_plot_data(subgroups), aes("records", "raw_anomaly_rate"))
        + geom_point()
        + ggtitle("Subgroup Funnel Diagnostic")
        + theme_minimal()
    )


def expected_pay_actual_vs_expected_chart(calibration: pl.DataFrame):
    return _simple_point_chart(
        calibration,
        "avg_residual",
        "coverage",
        "Expected Pay Calibration",
    )


def expected_pay_coverage_chart(calibration: pl.DataFrame):
    return _simple_point_chart(
        calibration,
        "subgroup" if "subgroup" in calibration.columns else "records",
        "coverage",
        "Expected Pay Coverage",
    )


def expected_pay_residual_chart(calibration: pl.DataFrame):
    return _simple_point_chart(
        calibration,
        "subgroup" if "subgroup" in calibration.columns else "records",
        "avg_residual",
        "Expected Pay Residuals",
    )


def expected_pay_percentile_chart(calibration: pl.DataFrame):
    return _simple_point_chart(
        calibration,
        "avg_interval_width",
        "coverage",
        "Interval Width vs Coverage",
    )


def calibration_interval_width_chart(calibration: pl.DataFrame):
    return _simple_point_chart(
        calibration,
        "avg_interval_width",
        "avg_excess_over_p90",
        "Calibration Interval Width vs Tail Excess",
    )


def queue_overlap_heatmap(overlap: pl.DataFrame):
    return (
        ggplot(_plot_data(overlap), aes("left", "right", fill="overlap"))
        + geom_tile()
        + ggtitle("Queue Overlap Heatmap")
        + theme_minimal()
    )


def seed_origin_distribution_chart(robustness: pl.DataFrame):
    return _simple_point_chart(
        robustness,
        "setting",
        "precision_at_k",
        "Seed/Origin Precision Distribution",
    )


def performance_instability_pareto_chart(robustness: pl.DataFrame):
    return _simple_point_chart(
        robustness,
        "performance_instability",
        "precision_at_k",
        "Performance vs Instability",
    )


def sensitivity_heatmap(sensitivity: pl.DataFrame):
    return _simple_point_chart(
        sensitivity,
        "rank_movement",
        "score_movement",
        "Perturbation Sensitivity",
    )


def capacity_distribution_chart(simulation: pl.DataFrame):
    return (
        ggplot(_plot_data(simulation), aes("capacity"))
        + geom_histogram(aes(y="..density.."), bins=40, alpha=0.25)
        + geom_density(color="#0f766e", size=1.2)
        + ggtitle("Queue Capacity Distribution")
        + theme_minimal()
    )


def scenario_candidate_threshold_chart(queue_sanity: pl.DataFrame):
    candidate_columns = [
        column for column in queue_sanity.columns if column.startswith("candidates_at_")
    ]
    rows: list[dict[str, object]] = []
    for row in queue_sanity.select(["scenario", *candidate_columns]).to_dicts():
        for column in candidate_columns:
            rows.append(
                {
                    "scenario": row["scenario"],
                    "threshold": column.removeprefix("candidates_at_"),
                    "candidates": row[column],
                },
            )
    return (
        ggplot(_plot_data(pl.DataFrame(rows)), aes("threshold", "candidates"))
        + geom_point(aes(color="scenario"), size=3)
        + geom_line(aes(color="scenario"))
        + ggtitle("Scenario Candidate Demand by Threshold")
        + theme_minimal()
    )


def scenario_anomaly_exposure_chart(queue_sanity: pl.DataFrame):
    return (
        ggplot(
            _plot_data(queue_sanity),
            aes("scenario", "anomaly_rate"),
        )
        + geom_point(aes(size="anomaly_dollars", color="anomaly_count"), alpha=0.8)
        + ggtitle("Scenario Anomaly Load and Synthetic Exposure")
        + theme_minimal()
    )


def overload_probability_chart(summary: pl.DataFrame):
    color = (
        "resolved_threshold" if "resolved_threshold" in summary.columns else "scenario"
    )
    return (
        ggplot(
            _plot_data(summary),
            aes(PayrollCol.PAY_PERIOD_INDEX, "overload_probability"),
        )
        + geom_point(aes(color=color, size="avg_candidate_queue_size"))
        + ggtitle("Overload Probability")
        + theme_minimal()
    )


def queue_overload_heatmap(summary: pl.DataFrame):
    fill = "overload_probability"
    return (
        ggplot(
            _plot_data(summary),
            aes("resolved_threshold", PayrollCol.PAY_PERIOD_INDEX, fill=fill),
        )
        + geom_tile()
        + ggtitle("Overload Probability Heatmap")
        + theme_minimal()
    )


def dollar_capture_distribution_chart(simulation: pl.DataFrame):
    return (
        ggplot(_plot_data(simulation), aes("dollars_captured"))
        + geom_histogram(bins=20)
        + ggtitle("Dollar Capture Distribution")
        + theme_minimal()
    )


def queue_tornado_chart(summary: pl.DataFrame):
    data = _queue_tornado_data(summary)
    return (
        ggplot(_plot_data(data), aes("low", "condition"))
        + geom_segment(
            aes(x="low", xend="high", y="condition", yend="condition", color="impact"),
            size=5,
        )
        + geom_point(aes(x="mean_value"), color="#111827", size=3)
        + ggtitle("Queue Sensitivity Tornado")
        + theme_minimal()
    )


def adaptive_threshold_comparison_chart(
    fixed_summary: pl.DataFrame,
    adaptive_summary: pl.DataFrame,
):
    data = pl.concat(
        [
            _policy_summary(fixed_summary, "fixed threshold"),
            _policy_summary(adaptive_summary, "adaptive p90"),
        ],
    )
    return (
        ggplot(
            _plot_data(data),
            aes("mean_overload_probability", "mean_missed_exposure"),
        )
        + geom_point(aes(color="policy", size="mean_candidate_queue_size"), alpha=0.8)
        + ggtitle("Adaptive vs Fixed Threshold Queue Risk")
        + theme_minimal()
    )


def scenario_risk_bar_chart(comparison: pl.DataFrame):
    data = (
        comparison.group_by("scenario")
        .agg(
            pl.max("overload_probability").alias("max_overload_probability"),
            pl.max("avg_missed_estimated_exposure").alias("max_missed_exposure"),
            pl.mean("avg_candidate_queue_size").alias("mean_candidate_queue_size"),
        )
        .sort("max_missed_exposure")
    )
    return (
        ggplot(
            _plot_data(data),
            aes("scenario", "max_missed_exposure"),
        )
        + geom_point(
            aes(color="max_overload_probability", size="mean_candidate_queue_size"),
        )
        + ggtitle("Scenario Queue Risk Ranking")
        + theme_minimal()
    )


def stress_test_heatmap(comparison: pl.DataFrame):
    return (
        ggplot(
            _plot_data(comparison),
            aes("scenario", PayrollCol.PAY_PERIOD_INDEX, fill="overload_probability"),
        )
        + geom_tile()
        + ggtitle("Stress-Test Queue Outcomes")
        + theme_minimal()
    )


def queue_demand_chart(summary: pl.DataFrame):
    y = (
        "avg_candidate_queue_size"
        if "avg_candidate_queue_size" in summary.columns
        else "avg_queue_size"
    )
    color = (
        "resolved_threshold" if "resolved_threshold" in summary.columns else "scenario"
    )
    return (
        ggplot(_plot_data(summary), aes(PayrollCol.PAY_PERIOD_INDEX, y))
        + geom_point(aes(color=color, size="avg_reviewed_records"))
        + ggtitle("Scenario Queue Demand")
        + theme_minimal()
    )


def missed_exposure_chart(summary: pl.DataFrame):
    color = (
        "resolved_threshold" if "resolved_threshold" in summary.columns else "scenario"
    )
    return (
        ggplot(
            _plot_data(summary),
            aes(PayrollCol.PAY_PERIOD_INDEX, "avg_missed_estimated_exposure"),
        )
        + geom_point(
            aes(color=color, size="avg_missed_synthetic_anomaly_dollars"),
            alpha=0.75,
        )
        + ggtitle("Missed Exposure by Period and Policy")
        + theme_minimal()
    )


def _plot_data(frame: pl.DataFrame) -> dict[str, list[object]]:
    return frame.to_dict(as_series=False)


def _sort_if_present(frame: pl.DataFrame, column: str) -> pl.DataFrame:
    return frame.sort(column) if column in frame.columns else frame


def _queue_tornado_data(summary: pl.DataFrame) -> pl.DataFrame:
    if summary.is_empty():
        return pl.DataFrame(
            schema={
                "condition": pl.String,
                "low": pl.Float64,
                "high": pl.Float64,
                "mean_value": pl.Float64,
                "impact": pl.Float64,
            },
        )
    driver = (
        "resolved_threshold" if "resolved_threshold" in summary.columns else "scenario"
    )
    data = summary.with_columns(
        pl.col(driver).cast(pl.String).alias("condition"),
    )
    return (
        data.group_by("condition")
        .agg(
            pl.min("avg_missed_estimated_exposure").alias("low"),
            pl.max("avg_missed_estimated_exposure").alias("high"),
            pl.mean("avg_missed_estimated_exposure").alias("mean_value"),
        )
        .with_columns((pl.col("high") - pl.col("low")).alias("impact"))
        .sort("impact")
    )


def _policy_summary(summary: pl.DataFrame, policy: str) -> pl.DataFrame:
    if summary.is_empty():
        return pl.DataFrame(
            schema={
                "policy": pl.String,
                "mean_overload_probability": pl.Float64,
                "mean_missed_exposure": pl.Float64,
                "mean_candidate_queue_size": pl.Float64,
            },
        )
    if "resolved_threshold" not in summary.columns:
        return summary.select(
            pl.mean("overload_probability").alias("mean_overload_probability"),
            pl.mean("avg_missed_estimated_exposure").alias("mean_missed_exposure"),
            pl.mean("avg_candidate_queue_size").alias("mean_candidate_queue_size"),
        ).with_columns(pl.lit(policy).alias("policy"))
    return (
        summary.group_by("resolved_threshold")
        .agg(
            pl.mean("overload_probability").alias("mean_overload_probability"),
            pl.mean("avg_missed_estimated_exposure").alias("mean_missed_exposure"),
            pl.mean("avg_candidate_queue_size").alias("mean_candidate_queue_size"),
        )
        .with_columns(
            pl.when(pl.col("resolved_threshold").is_not_null())
            .then(
                pl.lit(policy + " ")
                + pl.col("resolved_threshold").round(2).cast(pl.String),
            )
            .otherwise(pl.lit(policy))
            .alias("policy"),
        )
        .select(
            [
                "policy",
                "mean_overload_probability",
                "mean_missed_exposure",
                "mean_candidate_queue_size",
            ],
        )
    )


def _simple_point_chart(frame: pl.DataFrame, x: str, y: str, title: str):
    return (
        ggplot(_plot_data(frame), aes(x, y))
        + geom_point()
        + ggtitle(title)
        + theme_minimal()
    )

from __future__ import annotations

import polars as pl
from lets_plot import (
    aes,
    geom_bar,
    geom_histogram,
    geom_line,
    geom_point,
    geom_tile,
    ggplot,
    ggtitle,
    theme_minimal,
)

from payroll_anomaly_ranking.columns import (
    AggregateCol,
    FeatureCol,
    PayrollCol,
    ScoreCol,
)


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
    return (
        ggplot(_plot_data(comparison), aes("left_signal", "superiority_probability"))
        + geom_bar(stat="identity")
        + ggtitle("Component Superiority Probability")
        + theme_minimal()
    )


def subgroup_forest_chart(subgroups: pl.DataFrame):
    return (
        ggplot(_plot_data(subgroups), aes("subgroup", "pooled_anomaly_rate"))
        + geom_point()
        + ggtitle("Subgroup Pooled Anomaly Rates")
        + theme_minimal()
    )


def subgroup_caterpillar_chart(subgroups: pl.DataFrame):
    return (
        ggplot(
            _plot_data(subgroups.sort("pooled_anomaly_rate")),
            aes("subgroup", "pooled_anomaly_rate"),
        )
        + geom_point()
        + ggtitle("Subgroup Caterpillar View")
        + theme_minimal()
    )


def subgroup_shrinkage_chart(subgroups: pl.DataFrame):
    return (
        ggplot(_plot_data(subgroups), aes("raw_anomaly_rate", "pooled_anomaly_rate"))
        + geom_point()
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
        "records",
        "coverage",
        "Expected Pay Coverage",
    )


def expected_pay_residual_chart(calibration: pl.DataFrame):
    return _simple_point_chart(
        calibration,
        "records",
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
        + geom_histogram(bins=20)
        + ggtitle("Queue Capacity Distribution")
        + theme_minimal()
    )


def overload_probability_chart(summary: pl.DataFrame):
    return _simple_point_chart(
        summary,
        PayrollCol.PAY_PERIOD_INDEX,
        "overload_probability",
        "Overload Probability",
    )


def dollar_capture_distribution_chart(simulation: pl.DataFrame):
    return (
        ggplot(_plot_data(simulation), aes("dollars_captured"))
        + geom_histogram(bins=20)
        + ggtitle("Dollar Capture Distribution")
        + theme_minimal()
    )


def queue_tornado_chart(summary: pl.DataFrame):
    return _simple_point_chart(
        summary,
        "avg_missed_estimated_exposure",
        "avg_dollars_captured",
        "Queue Outcome Tornado View",
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


def _plot_data(frame: pl.DataFrame) -> dict[str, list[object]]:
    return frame.to_dict(as_series=False)


def _simple_point_chart(frame: pl.DataFrame, x: str, y: str, title: str):
    return (
        ggplot(_plot_data(frame), aes(x, y))
        + geom_point()
        + ggtitle(title)
        + theme_minimal()
    )

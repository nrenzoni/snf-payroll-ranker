from __future__ import annotations

import polars as pl
from lets_plot import aes, geom_histogram, geom_line, geom_point, ggplot, ggtitle, theme_minimal

from payroll_anomaly_ranking.columns import AggregateCol, FeatureCol, PayrollCol, ScoreCol


def payroll_trend_chart(payroll: pl.DataFrame):
    data = _plot_data(payroll.group_by(PayrollCol.PAY_PERIOD_INDEX).agg(pl.sum(PayrollCol.GROSS_PAY).alias(PayrollCol.GROSS_PAY)).sort(PayrollCol.PAY_PERIOD_INDEX))
    return ggplot(data, aes(PayrollCol.PAY_PERIOD_INDEX, PayrollCol.GROSS_PAY)) + geom_line() + ggtitle("Synthetic Payroll Trend") + theme_minimal()


def pay_distribution_chart(payroll: pl.DataFrame):
    return ggplot(_plot_data(payroll.select(PayrollCol.GROSS_PAY)), aes(PayrollCol.GROSS_PAY)) + geom_histogram(bins=30) + ggtitle("Gross Pay Distribution") + theme_minimal()


def overtime_distribution_chart(payroll: pl.DataFrame):
    return ggplot(_plot_data(payroll.select(PayrollCol.OVERTIME_HOURS)), aes(PayrollCol.OVERTIME_HOURS)) + geom_histogram(bins=30) + ggtitle("Overtime Distribution") + theme_minimal()


def department_heatmap_data(payroll: pl.DataFrame) -> pl.DataFrame:
    return payroll.group_by([PayrollCol.PAY_PERIOD_INDEX, PayrollCol.DEPARTMENT]).agg(pl.sum(PayrollCol.GROSS_PAY).alias(AggregateCol.DEPARTMENT_GROSS_PAY))


def score_distribution_chart(scored: pl.DataFrame):
    return ggplot(_plot_data(scored.select(ScoreCol.FINAL_ANOMALY_SCORE)), aes(ScoreCol.FINAL_ANOMALY_SCORE)) + geom_histogram(bins=30) + ggtitle("Hybrid Score Distribution") + theme_minimal()


def precision_at_k_chart(metrics: pl.DataFrame):
    return ggplot(_plot_data(metrics), aes("k", "precision_at_k")) + geom_point() + geom_line() + ggtitle("Precision@K") + theme_minimal()


def dollars_captured_chart(metrics: pl.DataFrame):
    return ggplot(_plot_data(metrics), aes("k", "dollar_capture_rate")) + geom_point() + geom_line() + ggtitle("Dollars Captured@K") + theme_minimal()


def employee_history_chart(scored: pl.DataFrame, employee_id: str):
    data = _plot_data(scored.filter(pl.col(PayrollCol.EMPLOYEE_ID) == employee_id).select([PayrollCol.PAY_PERIOD_INDEX, PayrollCol.GROSS_PAY, FeatureCol.GROSS_PAY_ROLLING_MEDIAN]).sort(PayrollCol.PAY_PERIOD_INDEX))
    return ggplot(data, aes(PayrollCol.PAY_PERIOD_INDEX, PayrollCol.GROSS_PAY)) + geom_line() + geom_point() + ggtitle(f"Highlighted History: {employee_id}") + theme_minimal()


def _plot_data(frame: pl.DataFrame) -> dict[str, list[object]]:
    return frame.to_dict(as_series=False)

from __future__ import annotations

import polars as pl
from lets_plot import aes, geom_bar, geom_line, geom_point, ggplot, ggtitle, theme_minimal


def payroll_trend_chart(payroll: pl.DataFrame):
    data = payroll.group_by("pay_period_index").agg(pl.sum("gross_pay").alias("gross_pay")).to_pandas()
    return ggplot(data, aes("pay_period_index", "gross_pay")) + geom_line() + ggtitle("Synthetic Payroll Trend") + theme_minimal()


def pay_distribution_chart(payroll: pl.DataFrame):
    return ggplot(payroll.select("gross_pay").to_pandas(), aes("gross_pay")) + geom_bar() + ggtitle("Gross Pay Distribution") + theme_minimal()


def overtime_distribution_chart(payroll: pl.DataFrame):
    return ggplot(payroll.select("overtime_hours").to_pandas(), aes("overtime_hours")) + geom_bar() + ggtitle("Overtime Distribution") + theme_minimal()


def department_heatmap_data(payroll: pl.DataFrame) -> pl.DataFrame:
    return payroll.group_by(["pay_period_index", "department"]).agg(pl.sum("gross_pay").alias("department_gross_pay"))


def score_distribution_chart(scored: pl.DataFrame):
    return ggplot(scored.select("final_anomaly_score").to_pandas(), aes("final_anomaly_score")) + geom_bar() + ggtitle("Hybrid Score Distribution") + theme_minimal()


def precision_at_k_chart(metrics: pl.DataFrame):
    return ggplot(metrics.to_pandas(), aes("k", "precision_at_k")) + geom_point() + geom_line() + ggtitle("Precision@K") + theme_minimal()


def dollars_captured_chart(metrics: pl.DataFrame):
    return ggplot(metrics.to_pandas(), aes("k", "dollar_capture_rate")) + geom_point() + geom_line() + ggtitle("Dollars Captured@K") + theme_minimal()


def employee_history_chart(scored: pl.DataFrame, employee_id: str):
    data = scored.filter(pl.col("employee_id") == employee_id).select(["pay_period_index", "gross_pay", "gross_pay_rolling_median"]).to_pandas()
    return ggplot(data, aes("pay_period_index", "gross_pay")) + geom_line() + geom_point() + ggtitle(f"Highlighted History: {employee_id}") + theme_minimal()

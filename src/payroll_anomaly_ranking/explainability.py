from __future__ import annotations

import polars as pl

from payroll_anomaly_ranking.rules import RULE_COLUMNS


def add_explanations(scored: pl.DataFrame) -> pl.DataFrame:
    return scored.with_columns(
        pl.struct(scored.columns).map_elements(_primary_reason, return_dtype=pl.String).alias("primary_reason"),
        pl.struct(scored.columns).map_elements(_secondary_reason, return_dtype=pl.String).alias("secondary_reason"),
        pl.struct(scored.columns).map_elements(_risk_category, return_dtype=pl.String).alias("risk_category"),
        (pl.col("gross_pay") - pl.col("gross_pay_rolling_median").fill_null(pl.col("peer_gross_median")).fill_null(pl.col("gross_pay"))).alias("difference_from_expected"),
    ).with_columns(
        pl.struct(scored.columns + ["primary_reason", "secondary_reason"]).map_elements(_explanation, return_dtype=pl.String).alias("explanation")
    )


def build_review_queue(scored: pl.DataFrame, top_k: int = 25) -> pl.DataFrame:
    explained = add_explanations(scored)
    fields = [
        "pay_period_rank",
        "employee_id",
        "pay_period_index",
        "final_anomaly_score",
        "risk_category",
        "primary_reason",
        "secondary_reason",
        "gross_pay",
        "gross_pay_rolling_median",
        "difference_from_expected",
        "peer_gross_median",
        "rule_reason_codes",
        "anomaly_dollars",
        "anomaly_category",
        "explanation",
        *RULE_COLUMNS,
    ]
    return explained.filter(pl.col("pay_period_rank") <= top_k).select(fields).rename(
        {"pay_period_rank": "rank", "gross_pay_rolling_median": "expected_gross_pay", "peer_gross_median": "peer_context", "anomaly_dollars": "dollars_at_risk"}
    ).sort(["pay_period_index", "rank"])


def sample_review_language() -> str:
    return "This synthetic record is prioritized for payroll review because it differs from expected history, peer context, or deterministic payroll rules; it is not a confirmed fraud finding."


def _primary_reason(row: dict[str, object]) -> str:
    if row.get("rule_reason_codes") and row["rule_reason_codes"] != "none":
        return f"Rule flag: {row['rule_reason_codes']}"
    if abs(float(row.get("peer_gross_deviation_ratio") or 0)) > 0.5:
        return "Gross pay materially differs from similar peer group"
    if abs(float(row.get("gross_pay_pct_change") or 0)) > 0.5:
        return "Gross pay changed sharply versus prior payroll history"
    return "High combined anomaly score"


def _secondary_reason(row: dict[str, object]) -> str:
    if float(row.get("overtime_hours") or 0) > 20:
        return "Elevated overtime hours contribute to payroll risk"
    if float(row.get("difference_from_expected") or 0) > 1000:
        return "Dollar difference from expected payroll baseline is meaningful"
    return "Review recommended before treating the record as an approved exception"


def _risk_category(row: dict[str, object]) -> str:
    score = float(row.get("final_anomaly_score") or 0)
    if score >= 0.65:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def _explanation(row: dict[str, object]) -> str:
    return f"Synthetic payroll record requires review: {row.get('primary_reason')}. {row.get('secondary_reason')}. This is an exception triage signal, not a fraud conclusion."

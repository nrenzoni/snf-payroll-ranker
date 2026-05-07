from __future__ import annotations

import polars as pl

from payroll_anomaly_ranking.columns import (
    FeatureCol,
    PayrollCol,
    ReviewCol,
    RuleCol,
    ScoreCol,
)
from payroll_anomaly_ranking.rules import RULE_COLUMNS


def add_explanations(scored: pl.DataFrame) -> pl.DataFrame:
    return scored.with_columns(
        pl.struct(scored.columns)
        .map_elements(_primary_reason, return_dtype=pl.String)
        .alias(ReviewCol.PRIMARY_REASON),
        pl.struct(scored.columns)
        .map_elements(_secondary_reason, return_dtype=pl.String)
        .alias(ReviewCol.SECONDARY_REASON),
        pl.struct(scored.columns)
        .map_elements(_risk_category, return_dtype=pl.String)
        .alias(ReviewCol.RISK_CATEGORY),
        (
            pl.col(PayrollCol.GROSS_PAY)
            - pl.col(FeatureCol.GROSS_PAY_ROLLING_MEDIAN)
            .fill_null(pl.col(FeatureCol.PEER_GROSS_MEDIAN))
            .fill_null(pl.col(PayrollCol.GROSS_PAY))
        ).alias(ReviewCol.DIFFERENCE_FROM_EXPECTED),
    ).with_columns(
        pl.struct(
            scored.columns + [ReviewCol.PRIMARY_REASON, ReviewCol.SECONDARY_REASON],
        )
        .map_elements(_explanation, return_dtype=pl.String)
        .alias(ReviewCol.EXPLANATION),
    )


def build_review_queue(scored: pl.DataFrame, top_k: int = 25) -> pl.DataFrame:
    explained = add_explanations(scored)
    fields = [
        ScoreCol.PAY_PERIOD_RANK,
        PayrollCol.EMPLOYEE_ID,
        PayrollCol.PAY_PERIOD_INDEX,
        ScoreCol.FINAL_ANOMALY_SCORE,
        ReviewCol.RISK_CATEGORY,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.SECONDARY_REASON,
        PayrollCol.GROSS_PAY,
        FeatureCol.GROSS_PAY_ROLLING_MEDIAN,
        ReviewCol.DIFFERENCE_FROM_EXPECTED,
        FeatureCol.PEER_GROSS_MEDIAN,
        RuleCol.REASON_CODES,
        ScoreCol.ESTIMATED_EXPOSURE,
        ReviewCol.EXPLANATION,
        *RULE_COLUMNS,
    ]
    return (
        explained.filter(pl.col(ScoreCol.PAY_PERIOD_RANK) <= top_k)
        .select(fields)
        .rename(
            {
                ScoreCol.PAY_PERIOD_RANK: ReviewCol.RANK,
                FeatureCol.GROSS_PAY_ROLLING_MEDIAN: ReviewCol.EXPECTED_GROSS_PAY,
                FeatureCol.PEER_GROSS_MEDIAN: ReviewCol.PEER_CONTEXT,
                ScoreCol.ESTIMATED_EXPOSURE: ReviewCol.DOLLARS_AT_RISK,
            },
        )
        .sort([PayrollCol.PAY_PERIOD_INDEX, ReviewCol.RANK])
    )


def build_evaluation_review_queue(
    scored: pl.DataFrame,
    top_k: int = 25,
) -> pl.DataFrame:
    return build_review_queue(scored, top_k).join(
        scored.select(
            PayrollCol.EMPLOYEE_ID,
            PayrollCol.PAY_PERIOD_INDEX,
            PayrollCol.IS_ANOMALY,
            PayrollCol.ANOMALY_CATEGORY,
            PayrollCol.ANOMALY_DOLLARS,
        ),
        on=[PayrollCol.EMPLOYEE_ID, PayrollCol.PAY_PERIOD_INDEX],
        how="left",
    )


def sample_review_language() -> str:
    return "This synthetic record is prioritized for payroll review because it differs from expected history, peer context, or deterministic payroll rules; it is not a confirmed misconduct finding."


def _primary_reason(row: dict[str, object]) -> str:
    if int(row.get(RuleCol.MISSING_DEDUCTION) or 0):
        return "Rule flag: missing or zero deductions"
    if row.get(RuleCol.REASON_CODES) and row[RuleCol.REASON_CODES] != "none":
        return f"Rule flag: {row[RuleCol.REASON_CODES]}"
    if abs(float(row.get(FeatureCol.PEER_GROSS_DEVIATION_RATIO) or 0)) > 0.5:
        return "Gross pay materially differs from similar peer group"
    if abs(float(row.get(FeatureCol.GROSS_PAY_PCT_CHANGE) or 0)) > 0.5:
        return "Gross pay changed sharply versus prior payroll history"
    return "High combined anomaly score"


def _secondary_reason(row: dict[str, object]) -> str:
    if int(row.get(RuleCol.MISSING_DEDUCTION) or 0):
        return "Expected payroll deductions appear absent or materially understated"
    if float(row.get(PayrollCol.OVERTIME_HOURS) or 0) > 20:
        return "Elevated overtime hours contribute to payroll risk"
    if float(row.get(ReviewCol.DIFFERENCE_FROM_EXPECTED) or 0) > 1000:
        return "Dollar difference from expected payroll baseline is meaningful"
    return "Review recommended before treating the record as an approved exception"


def _risk_category(row: dict[str, object]) -> str:
    score = float(row.get(ScoreCol.FINAL_ANOMALY_SCORE) or 0)
    if score >= 0.65:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def _explanation(row: dict[str, object]) -> str:
    return f"Synthetic payroll record requires review: {row.get(ReviewCol.PRIMARY_REASON)}. {row.get(ReviewCol.SECONDARY_REASON)}. This is an exception triage signal, not a misconduct conclusion."

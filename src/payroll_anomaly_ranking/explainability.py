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
    explained = scored.with_columns(
        pl.concat_str(
            [
                pl.lit("Pay period "),
                pl.col(PayrollCol.PAY_PERIOD_INDEX).cast(pl.String),
                pl.lit(" ending "),
                pl.col(PayrollCol.PAY_PERIOD_END).cast(pl.String),
            ],
        ).alias(ReviewCol.PAY_PERIOD_LABEL),
        (
            pl.col(PayrollCol.GROSS_PAY)
            - pl.col(FeatureCol.GROSS_PAY_ROLLING_MEDIAN)
            .fill_null(pl.col(FeatureCol.PEER_GROSS_MEDIAN))
            .fill_null(pl.col(PayrollCol.GROSS_PAY))
        ).alias(ReviewCol.DIFFERENCE_FROM_EXPECTED),
    ).with_columns(
        pl.when(pl.col(RuleCol.MISSING_DEDUCTION).fill_null(0) == 1)
        .then(pl.lit("Rule flag: missing or zero deductions"))
        .when(
            pl.col(RuleCol.REASON_CODES).is_not_null()
            & (pl.col(RuleCol.REASON_CODES) != "none"),
        )
        .then(pl.concat_str([pl.lit("Rule flag: "), pl.col(RuleCol.REASON_CODES)]))
        .when(pl.col(FeatureCol.PEER_GROSS_DEVIATION_RATIO).fill_null(0).abs() > 0.5)
        .then(pl.lit("Gross pay materially differs from similar peer group"))
        .when(pl.col(FeatureCol.GROSS_PAY_PCT_CHANGE).fill_null(0).abs() > 0.5)
        .then(pl.lit("Gross pay changed sharply versus prior payroll history"))
        .otherwise(pl.lit("High combined anomaly score"))
        .alias(ReviewCol.PRIMARY_REASON),
        pl.when(pl.col(RuleCol.MISSING_DEDUCTION).fill_null(0) == 1)
        .then(
            pl.lit(
                "Expected payroll deductions appear absent or materially understated",
            ),
        )
        .when(pl.col(PayrollCol.OVERTIME_HOURS).fill_null(0) > 20)
        .then(pl.lit("Elevated overtime hours contribute to payroll risk"))
        .when(pl.col(ReviewCol.DIFFERENCE_FROM_EXPECTED).fill_null(0) > 1000)
        .then(pl.lit("Dollar difference from expected payroll baseline is meaningful"))
        .otherwise(
            pl.lit(
                "Review recommended before treating the record as an approved exception",
            ),
        )
        .alias(ReviewCol.SECONDARY_REASON),
        pl.when(pl.col(ScoreCol.FINAL_ANOMALY_SCORE).fill_null(0) >= 0.65)
        .then(pl.lit("high"))
        .when(pl.col(ScoreCol.FINAL_ANOMALY_SCORE).fill_null(0) >= 0.35)
        .then(pl.lit("medium"))
        .otherwise(pl.lit("low"))
        .alias(ReviewCol.RISK_CATEGORY),
        pl.when(
            pl.col(ReviewCol.UNCERTAINTY_DRIVERS).is_not_null()
            & (pl.col(ReviewCol.UNCERTAINTY_DRIVERS) != "none"),
        )
        .then(pl.col(ReviewCol.UNCERTAINTY_DRIVERS))
        .otherwise(
            pl.lit("Recent payroll context is comparatively stable for this score"),
        )
        .alias(ReviewCol.WHY_UNCERTAIN),
    )
    return explained.with_columns(
        pl.concat_str(
            [
                pl.col(ReviewCol.PRIMARY_REASON),
                pl.when(pl.col(ScoreCol.GROSS_PAY_EXCESS_VS_P90).fill_null(0) > 0)
                .then(pl.lit("; gross pay is above the recent expected p90"))
                .otherwise(pl.lit("")),
                pl.when(pl.col(ScoreCol.CONFORMAL_PERCENTILE).fill_null(0) >= 0.9)
                .then(pl.lit("; score is unusually high versus recent payroll history"))
                .otherwise(pl.lit("")),
            ],
        ).alias(ReviewCol.WHY_RISKY),
        pl.concat_str(
            [
                pl.lit("Synthetic payroll record requires review: "),
                pl.col(ReviewCol.PRIMARY_REASON),
                pl.lit(". "),
                pl.col(ReviewCol.SECONDARY_REASON),
                pl.lit(
                    ". This is an exception triage signal, not a misconduct conclusion.",
                ),
            ],
        ).alias(ReviewCol.EXPLANATION),
    )


def build_review_queue(scored: pl.DataFrame, top_k: int = 25) -> pl.DataFrame:
    explained = add_explanations(scored)
    fields = [
        ScoreCol.PAY_PERIOD_RANK,
        PayrollCol.EMPLOYEE_ID,
        PayrollCol.PAY_PERIOD_INDEX,
        ReviewCol.PAY_PERIOD_LABEL,
        ScoreCol.FINAL_ANOMALY_SCORE,
        ReviewCol.UNCERTAINTY_BUCKET,
        ScoreCol.COMPOSITE_UNCERTAINTY_SCORE,
        ReviewCol.PRIMARY_UNCERTAINTY_REASON,
        ReviewCol.UNCERTAINTY_DRIVERS,
        ScoreCol.CONFORMAL_P_VALUE,
        ScoreCol.CONFORMAL_PERCENTILE,
        ScoreCol.EXPECTED_GROSS_PAY_P10,
        ScoreCol.EXPECTED_GROSS_PAY_P50,
        ScoreCol.EXPECTED_GROSS_PAY_P90,
        ScoreCol.EXPECTED_GROSS_PAY_INTERVAL_WIDTH,
        ScoreCol.GROSS_PAY_EXCESS_VS_P90,
        ReviewCol.RISK_CATEGORY,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.SECONDARY_REASON,
        PayrollCol.GROSS_PAY,
        FeatureCol.GROSS_PAY_ROLLING_MEDIAN,
        ReviewCol.DIFFERENCE_FROM_EXPECTED,
        FeatureCol.PEER_GROSS_MEDIAN,
        RuleCol.REASON_CODES,
        ScoreCol.ESTIMATED_EXPOSURE,
        ReviewCol.WHY_RISKY,
        ReviewCol.WHY_UNCERTAIN,
        ReviewCol.EXPLANATION,
        *RULE_COLUMNS,
    ]
    latest_period = explained.select(pl.max(PayrollCol.PAY_PERIOD_INDEX)).item()
    return (
        explained.filter(
            (pl.col(PayrollCol.PAY_PERIOD_INDEX) == latest_period)
            & (pl.col(ScoreCol.PAY_PERIOD_RANK) <= top_k),
        )
        .select(fields)
        .rename(
            {
                ScoreCol.PAY_PERIOD_RANK: ReviewCol.RANK,
                FeatureCol.GROSS_PAY_ROLLING_MEDIAN: ReviewCol.EXPECTED_GROSS_PAY,
                FeatureCol.PEER_GROSS_MEDIAN: ReviewCol.PEER_CONTEXT,
                ScoreCol.ESTIMATED_EXPOSURE: ReviewCol.DOLLARS_AT_RISK,
            },
        )
        .sort(ReviewCol.RANK)
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

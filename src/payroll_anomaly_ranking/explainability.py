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
            - pl.col(PayrollCol.EXPECTED_SHIFT_GROSS_PAY).fill_null(
                pl.col(PayrollCol.GROSS_PAY),
            )
        ).alias(ReviewCol.DIFFERENCE_FROM_EXPECTED),
        pl.concat_str(
            [
                pl.col(PayrollCol.OVERTIME_HOURS).round(2).cast(pl.String),
                pl.lit(" OT hours; "),
                pl.col(PayrollCol.PAID_HOURS).round(2).cast(pl.String),
                pl.lit(" paid vs "),
                pl.col(PayrollCol.SCHEDULED_HOURS).round(2).cast(pl.String),
                pl.lit(" scheduled"),
            ],
        ).alias(ReviewCol.OVERTIME_CONTEXT),
        pl.concat_str(
            [
                pl.lit("premium $"),
                pl.col(PayrollCol.PREMIUM_PAY).round(2).cast(pl.String),
                pl.lit("; code "),
                pl.col(PayrollCol.PAY_CODE),
                pl.lit("; shift "),
                pl.col(PayrollCol.SHIFT_TYPE),
            ],
        ).alias(ReviewCol.PREMIUM_CONTEXT),
    ).with_columns(
        pl.when(pl.col(RuleCol.MISSING_DEDUCTION).fill_null(0) == 1)
        .then(pl.lit("Expected payroll deductions appear missing or zero"))
        .when(pl.col(RuleCol.UNSUPPORTED_SHIFT_DIFFERENTIAL).fill_null(0) == 1)
        .then(pl.lit("Premium pay does not match the shift context"))
        .when(pl.col(RuleCol.PAID_EXCEEDS_SCHEDULED).fill_null(0) == 1)
        .then(pl.lit("Paid hours materially exceed scheduled hours"))
        .when(pl.col(RuleCol.DOUBLE_SHIFT_REST_GAP).fill_null(0) == 1)
        .then(pl.lit("Double-shift or short rest-gap context needs review"))
        .when(pl.col(RuleCol.EXTREME_OVERTIME).fill_null(0) == 1)
        .then(pl.lit("Overtime is unusually high for approval"))
        .when(
            pl.col(RuleCol.REASON_CODES).is_not_null()
            & (pl.col(RuleCol.REASON_CODES) != "none"),
        )
        .then(pl.concat_str([pl.lit("Rule flag: "), pl.col(RuleCol.REASON_CODES)]))
        .when(pl.col(FeatureCol.PEER_GROSS_DEVIATION_RATIO).fill_null(0).abs() > 0.5)
        .then(pl.lit("Gross pay materially differs from similar SNF role/shift peers"))
        .otherwise(pl.lit("High combined approval exception score"))
        .alias(ReviewCol.PRIMARY_REASON),
        pl.when(pl.col(PayrollCol.MISSED_PUNCH).fill_null(0) == 1)
        .then(pl.lit("Timeclock has a missed punch or manual context"))
        .when(pl.col(PayrollCol.PREMIUM_PAY).fill_null(0) > 0)
        .then(pl.lit("Confirm premium eligibility against schedule and pay policy"))
        .when(pl.col(ReviewCol.DIFFERENCE_FROM_EXPECTED).fill_null(0) > 250)
        .then(pl.lit("Dollar difference from expected shift pay is meaningful"))
        .otherwise(
            pl.lit(
                "Confirm supporting schedule/timeclock evidence before payroll approval",
            ),
        )
        .alias(ReviewCol.SECONDARY_REASON),
        pl.when(pl.col(ScoreCol.FINAL_ANOMALY_SCORE).fill_null(0) >= 0.65)
        .then(pl.lit("review before approval"))
        .when(pl.col(ScoreCol.FINAL_ANOMALY_SCORE).fill_null(0) >= 0.35)
        .then(pl.lit("confirm if time permits"))
        .otherwise(pl.lit("monitor"))
        .alias(ReviewCol.APPROVAL_RISK_CATEGORY),
    )
    return explained.with_columns(
        pl.concat_str(
            [
                pl.col(ReviewCol.PRIMARY_REASON),
                pl.lit(". Check: "),
                pl.col(ReviewCol.SOURCE_TO_CHECK).fill_null("schedule/timeclock"),
            ],
        ).alias(ReviewCol.WHY_RISKY),
        pl.when(
            pl.col(ReviewCol.UNCERTAINTY_DRIVERS).is_not_null()
            & (pl.col(ReviewCol.UNCERTAINTY_DRIVERS) != "none"),
        )
        .then(pl.col(ReviewCol.UNCERTAINTY_DRIVERS))
        .otherwise(pl.lit("Recent SNF role/shift comparison context is stable"))
        .alias(ReviewCol.WHY_UNCERTAIN),
        pl.concat_str(
            [
                pl.lit("Review before weekly SNF payroll approval: "),
                pl.col(ReviewCol.PRIMARY_REASON),
                pl.lit(". "),
                pl.col(ReviewCol.SECONDARY_REASON),
                pl.lit(
                    ". This is a pre-approval exception signal, not a confirmed error or misconduct finding.",
                ),
            ],
        ).alias(ReviewCol.EXPLANATION),
        pl.when(pl.col(ReviewCol.APPROVAL_RISK_CATEGORY) == "review before approval")
        .then(pl.lit("Needs administrator review"))
        .otherwise(pl.lit("Likely supportable if source context is confirmed"))
        .alias(ReviewCol.APPROVAL_READINESS),
    )


def build_review_queue(scored: pl.DataFrame, top_k: int = 25) -> pl.DataFrame:
    explained = add_explanations(scored)
    fields = [
        ScoreCol.PAY_PERIOD_RANK,
        PayrollCol.EMPLOYEE_ID,
        PayrollCol.FACILITY_ID,
        PayrollCol.UNIT,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_DATE,
        PayrollCol.SHIFT_TYPE,
        PayrollCol.PAY_PERIOD_INDEX,
        ReviewCol.PAY_PERIOD_LABEL,
        ScoreCol.FINAL_ANOMALY_SCORE,
        ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE,
        ReviewCol.UNCERTAINTY_BUCKET,
        ScoreCol.COMPOSITE_UNCERTAINTY_SCORE,
        ReviewCol.PRIMARY_UNCERTAINTY_REASON,
        ReviewCol.APPROVAL_RISK_CATEGORY,
        ReviewCol.RECOMMENDED_ACTION,
        ReviewCol.SOURCE_TO_CHECK,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.SECONDARY_REASON,
        PayrollCol.GROSS_PAY,
        PayrollCol.EXPECTED_SHIFT_GROSS_PAY,
        ReviewCol.DIFFERENCE_FROM_EXPECTED,
        PayrollCol.SCHEDULED_HOURS,
        PayrollCol.WORKED_HOURS,
        PayrollCol.PAID_HOURS,
        PayrollCol.OVERTIME_HOURS,
        PayrollCol.PREMIUM_PAY,
        ReviewCol.OVERTIME_CONTEXT,
        ReviewCol.PREMIUM_CONTEXT,
        RuleCol.REASON_CODES,
        ScoreCol.ESTIMATED_EXPOSURE,
        ReviewCol.APPROVAL_READINESS,
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
                ScoreCol.ESTIMATED_EXPOSURE: ReviewCol.DOLLARS_AT_RISK,
            },
        )
        .sort(
            [PayrollCol.FACILITY_ID, ReviewCol.RANK, RuleCol.MISSING_DEDUCTION],
            descending=[False, False, True],
        )
    )


def build_evaluation_review_queue(
    scored: pl.DataFrame,
    top_k: int = 25,
) -> pl.DataFrame:
    return build_review_queue(scored, top_k).join(
        scored.select(
            PayrollCol.EMPLOYEE_ID,
            PayrollCol.PAY_PERIOD_INDEX,
            PayrollCol.SHIFT_DATE,
            PayrollCol.SHIFT_TYPE,
            PayrollCol.IS_ANOMALY,
            PayrollCol.ANOMALY_CATEGORY,
            PayrollCol.ANOMALY_DOLLARS,
        ),
        on=[
            PayrollCol.EMPLOYEE_ID,
            PayrollCol.PAY_PERIOD_INDEX,
            PayrollCol.SHIFT_DATE,
            PayrollCol.SHIFT_TYPE,
        ],
        how="left",
    )


def build_facility_approval_summary(
    scored: pl.DataFrame,
    top_k: int = 25,
) -> pl.DataFrame:
    explained = add_explanations(scored)
    latest_period = explained.select(pl.max(PayrollCol.PAY_PERIOD_INDEX)).item()
    latest = explained.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) == latest_period)
    queued = latest.with_columns(
        (pl.col(ScoreCol.PAY_PERIOD_RANK) <= top_k).alias("in_queue"),
    )
    return queued.group_by([PayrollCol.PAY_PERIOD_INDEX, PayrollCol.FACILITY_ID]).agg(
        pl.len().alias("total_shifts"),
        pl.sum(PayrollCol.GROSS_PAY).alias("total_gross_pay"),
        pl.sum(PayrollCol.PAID_HOURS).alias("total_paid_hours"),
        pl.sum(PayrollCol.OVERTIME_HOURS).alias("overtime_hours"),
        pl.sum(PayrollCol.PREMIUM_PAY).alias("premium_dollars"),
        pl.col("in_queue").cast(pl.Int64).sum().alias("queue_count"),
        (pl.col(ReviewCol.APPROVAL_RISK_CATEGORY) == "review before approval")
        .cast(pl.Int64)
        .sum()
        .alias("high_priority_count"),
        pl.sum(ScoreCol.ESTIMATED_EXPOSURE).alias("estimated_exposure"),
        pl.first(ReviewCol.PRIMARY_REASON).alias("top_reason_categories"),
        pl.first(ReviewCol.APPROVAL_READINESS).alias("approval_readiness"),
    )


def sample_review_language() -> str:
    return "This synthetic SNF shift is prioritized for weekly payroll approval review because schedule, timeclock, premium, or peer context may not support the payroll amount; it is not a confirmed error or misconduct finding."

# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # SNF Payroll Approval Case Studies
#
# **Executive takeaway:** Automated hybrid approval ranking makes SNF payroll review more focused than one-field manual thresholds. It combines schedule, timeclock, premium eligibility, peer/history, ML, rules, and estimated exposure so administrators can spend limited weekly review capacity on the shifts most worth checking before payroll approval.
#
# This notebook is business-facing. It uses administrator-safe queue fields and review-safe wording: the queue surfaces records to verify, not confirmed fraud, misconduct, or known payroll error.

# %%
import polars as pl
from common.execution import notebook_fast_mode
from common.plots import (
    LetsPlot,
    aes,
    geom_bar,
    geom_point,
    geom_tile,
    ggplot,
    labs,
    theme_minimal,
)

from payroll_anomaly_ranking.columns import (
    MetricCol,
    PayrollCol,
    ReviewCol,
    RuleCol,
    ScoreCol,
)
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.evaluation import evaluate_scores
from payroll_anomaly_ranking.pipeline import PipelineIncludeConfig, run_pipeline
from payroll_anomaly_ranking.presentation import compact_case_cards
from payroll_anomaly_ranking.scenarios import diagnostic_scenario_presets

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=140, pay_periods=12, review_budgets=(10, 25))
FAST_CONFIG = PayrollConfig(employee_count=90, pay_periods=10, review_budgets=(10, 25))
NOTEBOOK_FAST = notebook_fast_mode()
active_config = FAST_CONFIG if NOTEBOOK_FAST else config
active_pipeline_include = (
    PipelineIncludeConfig(
        validation=False,
        aggregations=False,
        evaluation=True,
        backtest=False,
        rolling_origin=False,
        review_queues=True,
        leakage_checks=False,
    )
    if NOTEBOOK_FAST
    else PipelineIncludeConfig.all()
)

THRESHOLD_FLAGS = [
    ScoreCol.THRESHOLD_GROSS_PAY_FLAG,
    ScoreCol.THRESHOLD_TOTAL_HOURS_FLAG,
    ScoreCol.THRESHOLD_OVERTIME_HOURS_FLAG,
    ScoreCol.THRESHOLD_PREMIUM_DOLLARS_FLAG,
    ScoreCol.THRESHOLD_PAID_VS_SCHEDULED_FLAG,
]


def _case_study_run(name: str):
    scenario = diagnostic_scenario_presets((name,))[name]
    return run_pipeline(
        active_config,
        scenario=scenario,
        include=active_pipeline_include,
    )


def _latest_period(frame: pl.DataFrame) -> pl.DataFrame:
    latest_period = frame.select(pl.max(PayrollCol.PAY_PERIOD_INDEX)).item()
    return frame.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) == latest_period)


def _hybrid_budget_scorecard(scored: pl.DataFrame) -> pl.DataFrame:
    rows = []
    total_anomalies = scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    total_anomaly_dollars = float(
        scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0,
    )
    for budget in active_config.review_budgets:
        top = (
            scored.sort(
                [PayrollCol.PAY_PERIOD_INDEX, ScoreCol.FINAL_ANOMALY_SCORE],
                descending=[False, True],
            )
            .group_by(PayrollCol.PAY_PERIOD_INDEX)
            .head(budget)
        )
        true_positives = top.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
        captured_dollars = float(
            top.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
            .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
            .item()
            or 0.0,
        )
        rows.append(
            {
                "method": f"hybrid top {budget}",
                "method_type": "automated hybrid ranking",
                MetricCol.REVIEW_VOLUME: top.height,
                MetricCol.PRECISION_AT_K: true_positives / max(top.height, 1),
                MetricCol.RECALL_AT_K: true_positives / max(total_anomalies, 1),
                MetricCol.EXPOSURE_CAPTURED_AT_K: float(
                    top.select(pl.sum(ScoreCol.ESTIMATED_EXPOSURE)).item() or 0.0,
                ),
                MetricCol.DOLLARS_CAPTURED_AT_K: captured_dollars,
                MetricCol.DOLLAR_CAPTURE_RATE: captured_dollars / total_anomaly_dollars
                if total_anomaly_dollars
                else 0.0,
                MetricCol.FALSE_POSITIVES_AVOIDED: 0,
            },
        )
    return pl.DataFrame(rows)


def _business_lift_scorecard(scored: pl.DataFrame) -> pl.DataFrame:
    threshold_rows = evaluate_scores(scored, active_config).threshold_baseline_metrics
    total_anomaly_dollars = float(
        scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0,
    )
    threshold_rows = threshold_rows.with_columns(
        pl.col("baseline").alias("method"),
        pl.lit("manual threshold").alias("method_type"),
        (
            pl.col(MetricCol.DOLLARS_CAPTURED_AT_K) / max(total_anomaly_dollars, 1.0)
        ).alias(
            MetricCol.DOLLAR_CAPTURE_RATE,
        ),
    ).select(
        [
            "method",
            "method_type",
            MetricCol.REVIEW_VOLUME,
            MetricCol.PRECISION_AT_K,
            MetricCol.RECALL_AT_K,
            MetricCol.EXPOSURE_CAPTURED_AT_K,
            MetricCol.DOLLARS_CAPTURED_AT_K,
            MetricCol.DOLLAR_CAPTURE_RATE,
            MetricCol.FALSE_POSITIVES_AVOIDED,
        ],
    )
    return pl.concat([threshold_rows, _hybrid_budget_scorecard(scored)], how="diagonal")


def _threshold_missed_hybrid_records(
    scored: pl.DataFrame,
    *,
    limit: int = 12,
) -> pl.DataFrame:
    latest = _latest_period(scored)
    threshold_sum = pl.sum_horizontal(
        [pl.col(flag).fill_null(0) for flag in THRESHOLD_FLAGS],
    )
    return (
        latest.with_columns(threshold_sum.alias("manual_threshold_flags"))
        .filter(pl.col("manual_threshold_flags") == 0)
        .sort(ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE, descending=True)
        .select(
            [
                PayrollCol.FACILITY_ID,
                PayrollCol.UNIT,
                PayrollCol.ROLE,
                PayrollCol.SHIFT_DATE,
                PayrollCol.SHIFT_TYPE,
                PayrollCol.SCHEDULED_HOURS,
                PayrollCol.PAID_HOURS,
                PayrollCol.OVERTIME_HOURS,
                PayrollCol.PREMIUM_PAY,
                ScoreCol.ESTIMATED_EXPOSURE,
                ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE,
                "manual_threshold_flags",
                ReviewCol.RECOMMENDED_ACTION,
                ReviewCol.SOURCE_TO_CHECK,
                RuleCol.REASON_CODES,
            ],
        )
        .head(limit)
    )


def _component_context(scored: pl.DataFrame) -> pl.DataFrame:
    return _latest_period(scored).select(
        [
            ScoreCol.RULE_SCORE,
            ScoreCol.STATISTICAL_SCORE,
            ScoreCol.ML_SCORE,
            ScoreCol.SCHEDULE_TIMECLOCK_SCORE,
            ScoreCol.PREMIUM_ELIGIBILITY_SCORE,
            ScoreCol.EXPOSURE_SCORE,
            ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE,
        ],
    )


# %% [markdown]
# ## How To Read The Proof
#
# The comparison below uses synthetic labels only to evaluate historical performance. The business queue itself remains review-safe. The practical question is not whether a generic classifier scores well; it is whether a fixed weekly review budget captures more payroll risk and wastes fewer reviews than broad manual thresholds.
#
# The method ladder is intentionally simple:
#
# 1. Manual thresholds ask whether one raw field is large.
# 2. Rules ask whether known SNF approval logic is violated.
# 3. Robust statistics ask whether a shift is unusual for its history and peer context.
# 4. ML asks whether the multivariate combination is unusual.
# 5. Hybrid ranking combines those signals with estimated exposure so the queue is useful before payroll approval.

# %% [markdown]
# ## Case Study 1: Overtime, Double Shifts, And Staffing Pressure
#
# SNF overtime is often legitimate because census, call-outs, acuity, and coverage gaps create real staffing pressure. A manual overtime threshold can overflag those legitimate shifts and still miss the higher-risk combinations: short rest gaps, double shifts, missed punches, paid-vs-scheduled variance, and unusual exposure for the facility-role-shift context.

# %%
overtime_results = _case_study_run("overtime-staffing-pressure")
overtime_scorecard = _business_lift_scorecard(overtime_results.scored)
overtime_scorecard.sort(
    [MetricCol.EXPOSURE_CAPTURED_AT_K, MetricCol.PRECISION_AT_K],
    descending=True,
)

# %% [markdown]
# **What this shows:** the automated rows represent fixed top-K weekly review capacity. Threshold rows represent broad manual policies that may expand or shrink review volume depending on how many records cross one raw cutoff. The useful business measure is not just precision; it is exposure captured for each review the administrator has time to complete.

# %%
overtime_value = overtime_scorecard.with_columns(
    (
        pl.col(MetricCol.EXPOSURE_CAPTURED_AT_K)
        / pl.max_horizontal(pl.col(MetricCol.REVIEW_VOLUME), pl.lit(1))
    ).alias("exposure_per_review"),
)
(
    ggplot(overtime_value, aes("method", "exposure_per_review"))
    + geom_bar(aes(fill="method_type"), stat="identity")
    + labs(
        title="Overtime case: estimated exposure captured per reviewed record",
        x="Review method",
        y="Estimated exposure per review",
        fill="Method type",
    )
    + theme_minimal()
)

# %% [markdown]
# **Threshold-missed queue candidates:** these are latest-period records that did not fire any of the broad manual threshold flags but still rank highly under the hybrid score because the combined schedule, timeclock, rule, peer/history, ML, and exposure context makes them worth checking.

# %%
overtime_missed_by_thresholds = _threshold_missed_hybrid_records(
    overtime_results.scored,
)
overtime_missed_by_thresholds

# %%
(
    ggplot(
        overtime_missed_by_thresholds,
        aes(PayrollCol.OVERTIME_HOURS, ScoreCol.ESTIMATED_EXPOSURE),
    )
    + geom_point(
        aes(color=ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE, size=PayrollCol.PAID_HOURS),
        alpha=0.8,
    )
    + labs(
        title="Overtime records missed by broad thresholds but prioritized by hybrid ranking",
        x="Overtime hours",
        y="Estimated exposure",
        color="Hybrid score",
        size="Paid hours",
    )
    + theme_minimal()
)

# %% [markdown]
# **Administrator-safe queue:** the queue tells the administrator what to check before approval. It does not assert that the record is wrong; it names the schedule, timeclock, pay-code, or policy evidence to verify.

# %%
overtime_queue = overtime_results.analyst_review_queue
overtime_queue.select(
    [
        ReviewCol.RANK,
        PayrollCol.FACILITY_ID,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_DATE,
        PayrollCol.SHIFT_TYPE,
        ReviewCol.APPROVAL_RISK_CATEGORY,
        ReviewCol.RECOMMENDED_ACTION,
        ReviewCol.SOURCE_TO_CHECK,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.OVERTIME_CONTEXT,
        ReviewCol.DOLLARS_AT_RISK,
    ],
).head(12)

# %%
compact_case_cards(overtime_queue, limit=4)

# %% [markdown]
# ## Case Study 2: Premium Pay And Shift Differential Mismatch
#
# Premium pay is normal in SNF operations: evening, night, weekend, and hard-to-fill shifts often carry legitimate differentials. The review problem is not "premium equals bad." The useful question is whether the premium is supported by the shift, weekend, pay-code, schedule, and policy context.

# %%
premium_results = _case_study_run("premium-mismatch")
premium_scorecard = _business_lift_scorecard(premium_results.scored)
premium_scorecard.sort(
    [MetricCol.EXPOSURE_CAPTURED_AT_K, MetricCol.PRECISION_AT_K],
    descending=True,
)

# %% [markdown]
# **Premium value view:** a high premium-dollar threshold can miss unsupported smaller premiums, while a gross-pay threshold can overflag legitimate high-paying shifts. The hybrid queue prioritizes premium context and estimated exposure together.

# %%
premium_value = premium_scorecard.with_columns(
    (
        pl.col(MetricCol.EXPOSURE_CAPTURED_AT_K)
        / pl.max_horizontal(pl.col(MetricCol.REVIEW_VOLUME), pl.lit(1))
    ).alias("exposure_per_review"),
)
(
    ggplot(premium_value, aes("method", MetricCol.PRECISION_AT_K))
    + geom_bar(aes(fill="method_type"), stat="identity")
    + labs(
        title="Premium case: review precision by method",
        x="Review method",
        y="Precision or review yield",
        fill="Method type",
    )
    + theme_minimal()
)

# %%
premium_missed_by_thresholds = _threshold_missed_hybrid_records(premium_results.scored)
premium_missed_by_thresholds

# %%
(
    ggplot(
        premium_missed_by_thresholds,
        aes(PayrollCol.PREMIUM_PAY, ScoreCol.ESTIMATED_EXPOSURE),
    )
    + geom_point(
        aes(color=ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE, size=PayrollCol.PAID_HOURS),
        alpha=0.8,
    )
    + labs(
        title="Premium records missed by broad thresholds but prioritized by hybrid ranking",
        x="Premium pay",
        y="Estimated exposure",
        color="Hybrid score",
        size="Paid hours",
    )
    + theme_minimal()
)

# %%
premium_queue = premium_results.analyst_review_queue
premium_queue.select(
    [
        ReviewCol.RANK,
        PayrollCol.FACILITY_ID,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_DATE,
        PayrollCol.SHIFT_TYPE,
        PayrollCol.PREMIUM_PAY,
        ReviewCol.APPROVAL_RISK_CATEGORY,
        ReviewCol.RECOMMENDED_ACTION,
        ReviewCol.SOURCE_TO_CHECK,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.PREMIUM_CONTEXT,
        ReviewCol.DOLLARS_AT_RISK,
    ],
).head(12)

# %%
compact_case_cards(premium_queue, limit=4)

# %% [markdown]
# ## Facility Approval Concentration
#
# Administrators and regional operators also need to know whether the review queue is concentrated in a facility or pay period. This view stays business-safe: it summarizes queue count, high-priority count, and estimated exposure without exposing synthetic evaluation labels.

# %%
facility_summary = pl.concat(
    [
        overtime_results.facility_approval_summary.with_columns(
            pl.lit("overtime staffing pressure").alias("case_study"),
        ),
        premium_results.facility_approval_summary.with_columns(
            pl.lit("premium mismatch").alias("case_study"),
        ),
    ],
    how="diagonal",
)
facility_summary.sort("estimated_exposure", descending=True).head(12)

# %%
(
    ggplot(
        facility_summary,
        aes(PayrollCol.FACILITY_ID, "case_study", fill="estimated_exposure"),
    )
    + geom_tile()
    + labs(
        title="Facility approval concentration by case study",
        x="Facility",
        y="Case study",
        fill="Estimated exposure",
    )
    + theme_minimal()
)

# %% [markdown]
# ## Why Hybrid Ranking Is Different From A Threshold
#
# The table below summarizes the score components available to the ranking logic. In payroll approval, a single score source is rarely enough: rules catch hard policy concerns, robust statistics catch unusual distributions, ML catches unusual combinations, premium and schedule/timeclock signals keep the review grounded in SNF operations, and exposure estimates help prioritize scarce review time.

# %%
_component_context(premium_results.scored).describe()

# %% [markdown]
# ## What This Proves
#
# The two highest-value initial SNF scenarios are operationally understandable to administrator teams: overtime/double-shift pressure and premium mismatch. The incremental value of automated ranking is that it preserves the useful parts of rules and thresholds while adding SNF context, multivariate ML signal, and exposure-aware prioritization.
#
# The next notebook, `09_model_ablation_and_ml_value.py`, validates the technical side: whether the rule, statistical, ML, and hybrid methods earn their complexity under approval-budget, temporal, uncertainty, and robustness diagnostics.

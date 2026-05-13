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
# # SNF Payroll Approval Value Proof
#
# **Executive takeaway:** Hybrid anomaly ranking is not just a more complicated threshold. Across repeated synthetic SNF payroll worlds, it gives facility administrators a better use of limited review time because it captures more estimated risk per review than broad manual thresholds and it remains stronger than rule-only, statistics-only, and ML-only ranking on the main overtime and premium scenarios.
#
# This notebook is business-facing and explanation-heavy on purpose. Synthetic labels and synthetic anomaly dollars appear only in evaluation sections to prove whether the ranking works. The final concrete output remains review-safe and framed as pre-payroll verification, not confirmed fraud or confirmed payroll error.

# %%
import polars as pl
from common.execution import notebook_fast_mode
from common.plots import (
    LetsPlot,
    aes,
    coord_flip,
    geom_errorbar,
    geom_line,
    geom_point,
    geom_segment,
    geom_tile,
    ggplot,
    ggtitle,
    labs,
    scale_color_gradient,
    scale_fill_gradient,
    theme_minimal,
)

from payroll_anomaly_ranking.columns import (
    MetricCol,
    PayrollCol,
    ReviewCol,
    ScoreCol,
)
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.diagnostics import (
    BUSINESS_PROOF_MAIN_SCENARIOS,
    business_proof_hybrid_win_rates,
    business_proof_metric_intervals,
    business_proof_ranking_units,
    business_proof_threshold_units,
)
from payroll_anomaly_ranking.evaluation import evaluate_scores
from payroll_anomaly_ranking.pipeline import PipelineIncludeConfig, run_pipeline
from payroll_anomaly_ranking.queue_simulation import (
    QueueSimulationSpec,
    simulate_queue_capacity,
    summarize_queue_simulation,
)
from payroll_anomaly_ranking.scenarios import diagnostic_scenario_presets

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=160, pay_periods=12, review_budgets=(5, 10, 25))
FAST_CONFIG = PayrollConfig(employee_count=90, pay_periods=10, review_budgets=(5, 10))
NOTEBOOK_FAST = notebook_fast_mode()
active_config = FAST_CONFIG if NOTEBOOK_FAST else config
active_pipeline_include = (
    PipelineIncludeConfig(
        validation=False,
        aggregations=False,
        evaluation=True,
        backtest=False,
        rolling_origin=True,
        review_queues=True,
        leakage_checks=True,
    )
    if NOTEBOOK_FAST
    else PipelineIncludeConfig.all()
)
proof_seeds = (11, 19) if NOTEBOOK_FAST else (11, 19, 29)
main_scenarios = diagnostic_scenario_presets(BUSINESS_PROOF_MAIN_SCENARIOS)


def _case_study_run(name: str):
    return run_pipeline(
        active_config,
        scenario=diagnostic_scenario_presets((name,))[name],
        include=active_pipeline_include,
    )


def _latest_period(frame: pl.DataFrame) -> pl.DataFrame:
    latest_period = frame.select(pl.max(PayrollCol.PAY_PERIOD_INDEX)).item()
    return frame.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) == latest_period)


def _threshold_missed_hybrid_records(
    scored: pl.DataFrame,
    *,
    limit: int = 10,
) -> pl.DataFrame:
    latest = _latest_period(scored)
    manual_pack_flag = pl.col(ScoreCol.THRESHOLD_MANUAL_PACK_FLAG).fill_null(0)
    return (
        latest.filter(manual_pack_flag == 0)
        .sort(ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE, descending=True)
        .select(
            [
                PayrollCol.FACILITY_ID,
                PayrollCol.ROLE,
                PayrollCol.SHIFT_DATE,
                PayrollCol.SHIFT_TYPE,
                PayrollCol.GROSS_PAY,
                PayrollCol.EXPECTED_SHIFT_GROSS_PAY,
                PayrollCol.SCHEDULED_HOURS,
                PayrollCol.PAID_HOURS,
                PayrollCol.OVERTIME_HOURS,
                PayrollCol.PREMIUM_PAY,
                ScoreCol.ESTIMATED_EXPOSURE,
                ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE,
            ],
        )
        .head(limit)
    )


def _expected_pay_band_rows(scored: pl.DataFrame, *, limit: int = 8) -> pl.DataFrame:
    latest = _latest_period(scored)
    return (
        latest.filter(pl.col(ScoreCol.THRESHOLD_MANUAL_PACK_FLAG).fill_null(0) == 0)
        .sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True)
        .with_row_index("queue_row", offset=1)
        .select(
            [
                "queue_row",
                PayrollCol.FACILITY_ID,
                PayrollCol.ROLE,
                PayrollCol.GROSS_PAY,
                ScoreCol.EXPECTED_GROSS_PAY_P10,
                ScoreCol.EXPECTED_GROSS_PAY_P90,
            ],
        )
        .head(limit)
    )


def _method_labels(frame: pl.DataFrame, column: str = "method") -> pl.DataFrame:
    return frame.with_columns(
        pl.col(column)
        .str.replace_all("_", " ")
        .str.replace("manual threshold pack", "calibrated manual threshold pack")
        .alias(column),
    )


def _scenario_labels(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("scenario").str.replace_all("-", " ").alias("scenario_label"),
    )


def _appendix_queue_stress(frame: pl.DataFrame) -> pl.DataFrame:
    policies = {
        "steady capacity": QueueSimulationSpec(
            iterations=5 if NOTEBOOK_FAST else 12,
            review_budget=active_config.review_budgets[0],
            score_threshold=0.45,
            fixed_capacity=active_config.review_budgets[0],
            capacity_sd=0.0,
            seed=17,
            scenario="queue stress",
        ),
        "capacity shock": QueueSimulationSpec(
            iterations=5 if NOTEBOOK_FAST else 12,
            review_budget=active_config.review_budgets[0],
            score_threshold=0.45,
            fixed_capacity=active_config.review_budgets[0],
            period_capacity_multipliers={
                max(active_config.pay_periods - 2, 2): 0.5,
                max(active_config.pay_periods - 1, 3): 0.5,
            },
            capacity_sd=0.0,
            seed=17,
            scenario="queue stress",
        ),
        "catch-up staffing": QueueSimulationSpec(
            iterations=5 if NOTEBOOK_FAST else 12,
            review_budget=active_config.review_budgets[0],
            score_threshold=0.45,
            fixed_capacity=active_config.review_budgets[0],
            period_capacity_multipliers={
                max(active_config.pay_periods - 2, 2): 1.4,
                max(active_config.pay_periods - 1, 3): 1.4,
            },
            capacity_sd=0.0,
            seed=17,
            scenario="queue stress",
        ),
    }
    rows = []
    for policy_name, spec in policies.items():
        summary = summarize_queue_simulation(
            simulate_queue_capacity(frame, spec),
        ).with_columns(
            pl.lit(policy_name).alias("policy"),
        )
        rows.extend(summary.to_dicts())
    return pl.DataFrame(rows, infer_schema_length=None).with_columns(
        (pl.col("avg_missed_estimated_exposure") / 1_000).alias(
            "avg_missed_estimated_exposure_k",
        ),
    )


# %% [markdown]
# ## Evaluation Design
#
# This notebook asks a facility-admin question, not a generic ML question: if the building can review only a small number of payroll records before approval, which method makes the best use of that limited time?
#
# To keep the proof rigorous rather than anecdotal:
#
# 1. The main evidence is aggregated across repeated synthetic worlds and multiple seeds.
# 2. The main scenarios are `baseline`, `overtime staffing pressure`, and `premium mismatch`.
# 3. Synthetic labels and synthetic anomaly dollars are used only to evaluate whether the methods work. They are not scoring features and they do not appear in the final administrator-facing output.
# 4. The primary manual comparator is a calibrated threshold pack built only from raw operational threshold fields. It is not a learned model.

# %% [markdown]
# ## What Each Method Does
#
# **Manual thresholds** are familiar because they ask simple questions such as "was gross pay unusually high?" or "were paid hours much larger than scheduled hours?" Their strength is clarity. Their weakness is that each threshold sees only one slice of the payroll story.
#
# **Deterministic rules** encode known SNF approval logic such as unsupported premiums, paid-vs-scheduled issues, or double-shift rest-gap concerns. Their strength is policy relevance. Their weakness is that they only catch patterns already translated into explicit rules.
#
# **Robust statistics** ask whether the shift looks unusual relative to prior employee, role, shift, and facility context. Their strength is contextual unusualness. Their weakness is that they can still miss combinations that look ordinary in any one field but unusual when seen together.
#
# **ML-only scoring** asks whether the multivariate combination looks unusual. Its strength is pattern sensitivity. Its weakness is that ML alone is less persuasive to operations teams unless the queue is grounded in payroll logic and action context.
#
# **Hybrid ranking** combines rules, statistics, ML, schedule/timeclock context, premium context, and estimated exposure. Its strength is that it better matches how facility administrators actually review payroll: not just "is one field high?" but "is this shift worth scarce review time?"

# %%
ranking_units = _scenario_labels(
    _method_labels(
        business_proof_ranking_units(
            active_config,
            scenarios=main_scenarios,
            seeds=proof_seeds,
        ),
    ),
)
threshold_units = _scenario_labels(
    _method_labels(
        business_proof_threshold_units(
            active_config,
            scenarios=main_scenarios,
            seeds=proof_seeds,
        ),
        column="method",
    ),
)
ranking_intervals = business_proof_metric_intervals(
    ranking_units,
    metric_columns=(
        MetricCol.EXPOSURE_PER_REVIEW,
        MetricCol.DOLLAR_CAPTURE_RATE,
        MetricCol.PRECISION_AT_K,
    ),
    group_columns=("scenario", "scenario_label", "method", "method_type", MetricCol.K),
)
threshold_intervals = business_proof_metric_intervals(
    threshold_units,
    metric_columns=(
        MetricCol.EXPOSURE_PER_REVIEW,
        MetricCol.NATIVE_REVIEW_BURDEN,
        MetricCol.MISSED_ESTIMATED_EXPOSURE,
    ),
    group_columns=("scenario", "scenario_label", "method", "method_type"),
)
hybrid_win_rates = _scenario_labels(
    _method_labels(
        business_proof_hybrid_win_rates(
            ranking_units,
            metric=MetricCol.EXPOSURE_PER_REVIEW,
        ),
        column="comparator",
    ),
)

# %% [markdown]
# ## Repeated-World Method Value
#
# The chart below compares rankable methods at fixed facility review budgets. That is the fair comparison for rules, robust statistics, ML-only scoring, and hybrid ranking, because each method can produce an ordered queue.
#
# The metric shown is estimated exposure captured per reviewed record. In plain language: if an administrator spends one review on this method, how much likely payroll risk does that review tend to cover?

# %%
exposure_frontier = ranking_intervals.filter(
    pl.col("metric") == MetricCol.EXPOSURE_PER_REVIEW,
)
(
    ggplot(exposure_frontier, aes(MetricCol.K, "mean"))
    + geom_line(aes(color="method"))
    + geom_point(aes(color="method"), size=3)
    + geom_errorbar(aes(ymin="lower_95", ymax="upper_95", color="method"), width=0.4)
    + ggtitle("Repeated-world exposure captured per review")
    + labs(
        x="Facility review budget per pay period",
        y="Estimated exposure per review",
        color="Method",
    )
    + theme_minimal()
)

# %% [markdown]
# **How to read this:** each point is the average across repeated scenario runs, and the error bars show empirical variation across those runs. If the hybrid line stays above the other lines, that means hybrid usually makes better use of scarce facility review time, not just in one favorable simulation.

# %% [markdown]
# ## Hybrid Win Rate Against Simpler Methods
#
# A skeptical facility administrator may reasonably ask whether hybrid only wins in one or two lucky worlds. This heatmap answers that question directly by showing how often hybrid beats each simpler method on the same exposure-per-review metric.

# %%
(
    ggplot(
        hybrid_win_rates,
        aes("comparator", "scenario_label", fill="win_probability"),
    )
    + geom_tile()
    + ggtitle("How often hybrid beats simpler ranking methods")
    + labs(
        x="Comparator",
        y="Scenario",
        fill="Hybrid win probability",
    )
    + scale_fill_gradient(low="#f8fafc", high="#1d4ed8", limits=[0, 1])
    + theme_minimal()
)

# %% [markdown]
# **What this proves:** this is the notebook's anti-"one-off" view. A dark cell means hybrid beats that comparator in most repeated worlds for that scenario and review budget setting.

# %% [markdown]
# ## Manual Threshold Burden Versus Value
#
# Manual thresholds do not naturally produce the same kind of top-K queue as ranking methods. Their native behavior is to create whatever review demand the cutoff produces. For that reason, the fair question is different: how much work do the thresholds create, how much exposure do they capture per review, and how much estimated exposure do they leave behind?

# %%
threshold_burden = threshold_intervals.filter(
    pl.col("metric") == MetricCol.NATIVE_REVIEW_BURDEN,
)
threshold_value = threshold_intervals.filter(
    pl.col("metric") == MetricCol.EXPOSURE_PER_REVIEW,
).select(
    [
        "scenario",
        "scenario_label",
        "method",
        pl.col("mean").alias("mean_exposure_per_review"),
    ],
)
threshold_tradeoff = threshold_burden.join(
    threshold_value,
    on=["scenario", "scenario_label", "method"],
    how="left",
)
(
    ggplot(
        threshold_tradeoff,
        aes("mean", "mean_exposure_per_review"),
    )
    + geom_point(aes(color="method", size="mean_exposure_per_review"), alpha=0.8)
    + ggtitle("Manual threshold burden versus value")
    + labs(
        x="Average native review burden",
        y="Estimated exposure per review",
        color="Manual baseline",
        size="Exposure per review",
    )
    + theme_minimal()
)

# %% [markdown]
# **Why this matters for facility admins:** a threshold can be simple and still be inefficient. A threshold sitting far to the right with modest vertical value means it creates a lot of review work without proportionate risk capture. The calibrated manual threshold pack is the fairest manual baseline because it is tuned to the observed payroll context without using labels.

# %% [markdown]
# ## Case Study 1: Overtime, Double Shifts, And Staffing Pressure
#
# Overtime is common in SNF operations, especially when call-outs, census, or staffing pressure force coverage adjustments. The goal is not to treat overtime itself as suspicious. The goal is to separate supportable staffing exceptions from shifts whose combination of long hours, short rest gaps, and schedule/timeclock evidence deserves review before approval.

# %%
overtime_results = _case_study_run("overtime-staffing-pressure")
overtime_thresholds = _method_labels(
    evaluate_scores(overtime_results.scored, active_config).threshold_baseline_metrics,
    column="baseline",
)
overtime_thresholds.sort(MetricCol.EXPOSURE_PER_REVIEW, descending=True)

# %%
overtime_missed = _threshold_missed_hybrid_records(overtime_results.scored)
(
    ggplot(
        overtime_missed,
        aes(PayrollCol.OVERTIME_HOURS, ScoreCol.ESTIMATED_EXPOSURE),
    )
    + geom_point(
        aes(color=ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE, size=PayrollCol.PAID_HOURS),
        alpha=0.8,
    )
    + ggtitle("Overtime records missed by the manual threshold pack")
    + labs(
        x="Overtime hours",
        y="Estimated exposure",
        color="Hybrid score",
        size="Paid hours",
    )
    + theme_minimal()
)

# %% [markdown]
# **Interpretation:** the missed records are not just "more overtime." They tend to be the records where staffing pressure combines with rest-gap, schedule, timeclock, or context signals in a way that a one-field threshold pack does not fully capture.

# %% [markdown]
# ## Case Study 2: Premium Pay And Shift Differential Mismatch
#
# Premium pay is often legitimate in SNF payroll. The real question is whether the premium fits the shift, weekend, and pay-code context. A useful queue should distinguish normal premium-heavy operations from unsupported premium patterns.

# %%
premium_results = _case_study_run("premium-mismatch")
premium_thresholds = _method_labels(
    evaluate_scores(premium_results.scored, active_config).threshold_baseline_metrics,
    column="baseline",
)
premium_thresholds.sort(MetricCol.EXPOSURE_PER_REVIEW, descending=True)

# %%
premium_missed = _threshold_missed_hybrid_records(premium_results.scored)
(
    ggplot(
        premium_missed,
        aes(PayrollCol.PREMIUM_PAY, ScoreCol.ESTIMATED_EXPOSURE),
    )
    + geom_point(
        aes(color=ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE, size=PayrollCol.PAID_HOURS),
        alpha=0.8,
    )
    + ggtitle("Premium records missed by the manual threshold pack")
    + labs(
        x="Premium pay",
        y="Estimated exposure",
        color="Hybrid score",
        size="Paid hours",
    )
    + theme_minimal()
)

# %% [markdown]
# **Interpretation:** this is where hybrid is especially persuasive to administrators. Many missed records are not the largest premiums. They are the premiums that become questionable when shift type, weekend status, and payroll context do not line up cleanly.

# %% [markdown]
# ## Expected Pay Bands Make The Statistical Logic Concrete
#
# Robust statistics become more persuasive when they are shown as an expected pay band instead of an abstract score. The chart below focuses on threshold-missed records that hybrid still prioritizes.

# %%
expected_pay_bands = _expected_pay_band_rows(premium_results.scored)
(
    ggplot(expected_pay_bands, aes("queue_row", PayrollCol.GROSS_PAY))
    + geom_segment(
        aes(
            x="queue_row",
            xend="queue_row",
            y=ScoreCol.EXPECTED_GROSS_PAY_P10,
            yend=ScoreCol.EXPECTED_GROSS_PAY_P90,
        ),
        size=3,
        color="#cbd5e1",
    )
    + geom_point(color="#1d4ed8", size=3)
    + ggtitle("Threshold-missed records versus expected pay bands")
    + labs(
        x="Highest-ranked threshold-missed records",
        y="Gross pay",
    )
    + theme_minimal()
)

# %% [markdown]
# **How to read this:** the gray segment is the expected gross-pay range for comparable prior context, and the blue point is actual gross pay. Records where the point sits above the band are not just large in absolute terms; they are large relative to the facility-role-shift context that an administrator would usually want to consider.

# %% [markdown]
# ## Stability Over Time
#
# Facility administrators need to trust that the queue does not work only in one pay period. Rolling-origin evaluation is the simplest trust check: when later periods move forward, does each facility still get useful review yield from a fixed review capacity?

# %%
rolling_yield = overtime_results.rolling_origin_metrics
(
    ggplot(rolling_yield, aes("test_period", MetricCol.EXPOSURE_PER_REVIEW))
    + geom_line(color="#1d4ed8")
    + geom_point(color="#1d4ed8", size=3)
    + ggtitle("Rolling-origin review yield over time")
    + labs(
        x="Test pay period",
        y="Estimated exposure per reviewed record",
    )
    + theme_minimal()
)

# %% [markdown]
# **Operational meaning:** this plot is not claiming perfect precision. The rolling-origin calculation ranks records within each facility and pay period, then measures whether the same review capacity continues to surface meaningful estimated exposure as payroll conditions move forward. Precision remains available as evaluation context, but real SNF review will always include legitimate high-risk-looking records that deserve administrator judgment rather than automatic rejection.

# %% [markdown]
# ## Concrete Final Output
#
# The notebook keeps only one final concrete table because the main proof should stay focused on value, not dashboard detail. This is what a facility-admin-safe ranked output looks like in practice.

# %%
final_queue = premium_results.analyst_review_queue.select(
    [
        ReviewCol.RANK,
        PayrollCol.FACILITY_ID,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_DATE,
        PayrollCol.SHIFT_TYPE,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.SOURCE_TO_CHECK,
        ReviewCol.RECOMMENDED_ACTION,
        ReviewCol.DOLLARS_AT_RISK,
    ],
).head(12)
final_queue

# %% [markdown]
# ## Appendix: Stress Diagnostics
#
# The main proof above uses the highest-value recurring scenarios. This appendix is intentionally separate. It does not claim that every stress world is already a polished product scenario. It shows how the review process behaves when demand or payroll conditions shift in harder directions.

# %%
appendix_scored = run_pipeline(
    active_config,
    scenario=diagnostic_scenario_presets(("queue-stress",))["queue-stress"],
    include=PipelineIncludeConfig.scored_only(),
).scored
appendix_queue = _appendix_queue_stress(appendix_scored)

# %%
(
    ggplot(
        appendix_queue,
        aes("policy", PayrollCol.PAY_PERIOD_INDEX, fill="overload_probability"),
    )
    + geom_tile()
    + ggtitle("Appendix stress view: overload probability by queue policy and period")
    + labs(
        x="Queue policy",
        y="Pay period",
        fill="Overload probability",
    )
    + scale_fill_gradient(low="#f8fafc", high="#b91c1c", limits=[0, 1])
    + theme_minimal()
)

# %%
appendix_risk = (
    appendix_queue.group_by("policy")
    .agg(
        pl.max("overload_probability").alias("max_overload_probability"),
        pl.max("avg_missed_estimated_exposure_k").alias("max_missed_exposure_k"),
        pl.mean("avg_candidate_queue_size").alias("mean_candidate_queue_size"),
    )
    .sort("max_missed_exposure_k")
)
(
    ggplot(
        appendix_risk,
        aes("policy", "max_missed_exposure_k"),
    )
    + geom_point(
        aes(color="max_overload_probability", size="mean_candidate_queue_size"),
    )
    + ggtitle("Appendix stress ranking")
    + labs(
        x="Queue policy",
        y="Maximum missed estimated exposure ($K)",
        color="Max overload probability",
        size="Mean candidate queue size",
    )
    + scale_color_gradient(low="#0f766e", high="#b91c1c", limits=[0, 1])
    + coord_flip()
    + theme_minimal()
)

# %% [markdown]
# ## What This Proves
#
# For facility administrators, the persuasive result is not simply that ML produces a higher score. The persuasive result is that hybrid ranking repeatedly captures more review-worthy payroll risk per scarce review than manual thresholds, while still staying explainable in payroll language and grounded in schedule, timeclock, premium, peer, and exposure context.
#
# The next notebook, `09_model_ablation_and_ml_value.py`, remains the technical support notebook. It goes deeper into ablation, uncertainty, and diagnostic detail once the business case is already established.

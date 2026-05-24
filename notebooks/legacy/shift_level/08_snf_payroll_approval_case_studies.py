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
# **Executive takeaway:** Hybrid anomaly ranking is not just a more complicated threshold. Across controlled SNF payroll simulations, it gives facility administrators a better use of limited review time because it captures more estimated risk per review than broad manual thresholds and it remains stronger than rule-only, statistics-only, and ML-only ranking on the main overtime and premium scenarios.
#
# This notebook is business-facing and explanation-heavy on purpose. Synthetic labels and synthetic anomaly dollars appear only in evaluation sections to prove whether the ranking works. The final concrete output remains review-safe and framed as pre-payroll verification, not confirmed fraud or confirmed payroll error.
#
# **What this notebook includes:**
#
# 1. A comparison of hybrid ranking, simpler ranking methods, and manual thresholds.
# 2. A win-rate view showing whether hybrid's advantage persists across scenarios rather than one favorable run.
# 3. A manual threshold burden-versus-value view showing when simple cutoffs create review work efficiently or inefficiently.
# 4. Two case studies: overtime/double-shift staffing pressure and premium-pay mismatch.
# 5. A pay-band diagnostic showing how context-adjusted gross-pay expectations can support practical alert thresholds.
# 6. A rolling-origin stability check, a review-safe final queue example, and an appendix documenting stress diagnostics and simulation assumptions.

# %%
import polars as pl
from common.display import setup_notebook_html
from common.execution import notebook_fast_mode
from common.plots import (
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
    rotated_x_labels,
    scale_color_gradient,
    scale_fill_gradient,
    theme_minimal,
)

from payroll_anomaly_ranking.columns import (
    FeatureCol,
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

setup_notebook_html()

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
primary_scenario = "overtime-staffing-pressure"
primary_scenario_label = primary_scenario.replace("-", " ")


def _format_money(value: float) -> str:
    return f"${value:,.0f}"


def _single_value(frame: pl.DataFrame, column: str) -> float:
    if frame.is_empty():
        return 0.0
    return float(frame.select(pl.col(column).first()).item() or 0.0)


def _ranking_takeaway(frame: pl.DataFrame, budget: int) -> str:
    budget_rows = frame.filter(pl.col(MetricCol.K) == budget)
    hybrid_value = _single_value(
        budget_rows.filter(pl.col("method") == "hybrid"),
        "mean",
    )
    next_best = (
        budget_rows.filter(pl.col("method") != "hybrid")
        .sort("mean", descending=True)
        .head(1)
    )
    next_best_value = _single_value(next_best, "mean")
    next_best_method = (
        next_best.select(pl.col("method").first()).item()
        if not next_best.is_empty()
        else "the next best method"
    )
    lift = hybrid_value - next_best_value
    return (
        f"Takeaway: at {budget} reviews per facility-period in the "
        f"{primary_scenario_label} scenario, hybrid captures "
        f"{_format_money(hybrid_value)} estimated exposure per review, "
        f"{_format_money(lift)} more than {next_best_method}."
    )


def _win_rate_takeaway(frame: pl.DataFrame) -> str:
    weakest = frame.sort("win_probability").head(1)
    comparator = (
        weakest.select(pl.col("comparator").first()).item()
        if not weakest.is_empty()
        else "the closest comparator"
    )
    probability = _single_value(weakest, "win_probability")
    return (
        "Takeaway: hybrid's toughest repeated-world comparison is against "
        f"{comparator}, where it still wins {probability:.0%} of matched "
        "scenario-budget comparisons on exposure per review."
    )


def _threshold_takeaway(frame: pl.DataFrame) -> str:
    manual_pack = frame.filter(pl.col("method") == "calibrated manual threshold pack")
    manual_burden = _single_value(manual_pack, "mean")
    manual_value = _single_value(manual_pack, "mean_exposure_per_review")
    return (
        "Takeaway: in this scenario, the calibrated manual threshold pack "
        f"creates about {manual_burden:.1f} native reviews and captures "
        f"{_format_money(manual_value)} estimated exposure per review. The "
        "plot shows whether simpler threshold rules buy that value efficiently "
        "or mostly expand review work."
    )


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
        .with_columns(
            (pl.col(PayrollCol.PAID_HOURS) - pl.col(PayrollCol.SCHEDULED_HOURS)).alias(
                FeatureCol.PAID_MINUS_SCHEDULED_HOURS,
            ),
        )
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
                FeatureCol.PAID_MINUS_SCHEDULED_HOURS,
                PayrollCol.PREMIUM_PAY,
                PayrollCol.REST_GAP_HOURS,
                PayrollCol.IS_WEEKEND,
                PayrollCol.PAY_CODE,
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
        .with_columns(
            (
                pl.col(PayrollCol.GROSS_PAY) - pl.col(ScoreCol.EXPECTED_GROSS_PAY_P90)
            ).alias("gross_pay_above_p90"),
        )
        .sort("gross_pay_above_p90", descending=True)
        .with_row_index("queue_row", offset=1)
        .select(
            [
                "queue_row",
                PayrollCol.FACILITY_ID,
                PayrollCol.ROLE,
                PayrollCol.GROSS_PAY,
                ScoreCol.EXPECTED_GROSS_PAY_P10,
                ScoreCol.EXPECTED_GROSS_PAY_P90,
                "gross_pay_above_p90",
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
        "fixed top-k capacity": QueueSimulationSpec(
            iterations=5 if NOTEBOOK_FAST else 12,
            review_budget=active_config.review_budgets[0],
            fixed_capacity=active_config.review_budgets[0],
            capacity_sd=0.0,
            seed=17,
            scenario="queue stress",
        ),
        "broad threshold": QueueSimulationSpec(
            iterations=5 if NOTEBOOK_FAST else 12,
            review_budget=active_config.review_budgets[0],
            score_threshold=0.35,
            fixed_capacity=active_config.review_budgets[0],
            capacity_sd=0.0,
            seed=17,
            scenario="queue stress",
        ),
        "adaptive top decile": QueueSimulationSpec(
            iterations=5 if NOTEBOOK_FAST else 12,
            review_budget=active_config.review_budgets[0],
            adaptive_threshold_quantile=0.90,
            fixed_capacity=active_config.review_budgets[0],
            capacity_sd=0.0,
            seed=17,
            scenario="queue stress",
        ),
        "threshold capacity shock": QueueSimulationSpec(
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
        "threshold catch-up staffing": QueueSimulationSpec(
            iterations=5 if NOTEBOOK_FAST else 12,
            review_budget=active_config.review_budgets[0],
            score_threshold=0.45,
            fixed_capacity=round(active_config.review_budgets[0] * 1.5),
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
        (
            pl.col("avg_reviewed_records")
            / pl.max_horizontal(pl.col("avg_candidate_queue_size"), pl.lit(1.0))
        ).alias("reviewed_to_candidate_ratio"),
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
# The chart below compares rankable methods at fixed facility review budgets for the overtime staffing-pressure scenario. That scenario-specific view keeps the comparison readable; the win-rate heatmap that follows shows whether the result generalizes across all main scenarios.
#
# The metric shown is estimated exposure captured per reviewed record. In plain language: if an administrator spends one review on this method, how much likely payroll risk does that review tend to cover?
#
# - **exposure** means <u>estimated payroll dollars at risk</u>. It is an evaluation measure, not a claim that the dollars are confirmed fraud, confirmed overpayment, or automatically recoverable.
#
# - **Exposure per review** means the estimated at-risk dollars surfaced for each payroll record a facility administrator spends time checking.

# %%
exposure_frontier = ranking_intervals.filter(
    (pl.col("metric") == MetricCol.EXPOSURE_PER_REVIEW)
    & (pl.col("scenario") == primary_scenario),
)
(
    ggplot(exposure_frontier, aes(MetricCol.K, "mean"))
    + geom_line(aes(color="method"))
    + geom_point(aes(color="method"), size=3)
    + geom_errorbar(aes(ymin="lower_95", ymax="upper_95", color="method"), width=0.4)
    + ggtitle("exposure captured per review (Repeated-world)")
    + labs(
        x="Facility review budget per pay period",
        y="Estimated exposure per review",
        color="Method",
    )
    + theme_minimal()
)

# %%
print(_ranking_takeaway(exposure_frontier, active_config.review_budgets[0]))

# %% [markdown]
# **How to read this:** each point is the average across repeated overtime staffing-pressure runs, and the error bars show empirical variation across those runs. (If the hybrid line stays above the other lines, that means hybrid usually makes better use of scarce facility review time, not just in one favorable simulation.)

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
    + scale_fill_gradient(low="#f8fafc", high="#1d4ed8", breaks=[0, 0.5, 1])
    + theme_minimal()
)

# %%
print(_win_rate_takeaway(hybrid_win_rates))

# %% [markdown]
# **What this proves:** this is the notebook's anti-"one-off" view. A dark cell means hybrid beats that comparator in most repeated worlds for that scenario and review budget setting.

# %% [markdown]
# ## Manual Threshold Burden Versus Value
#
# Manual thresholds do not naturally produce the same kind of top-K queue as ranking methods. They create a review demand dependant on the cutoff produces. So the fair question is: how much work do the thresholds create, how much exposure do they capture per review, and how much estimated exposure do they leave behind?
#
# - **Review burden**: the number of records a threshold rule selects for review. For example, a gross-pay cutoff does not know that a facility only has time for 5 or 10 reviews; it flags every record above the cutoff. (This review count is the operational burden an admin receives before any extra queue trimming is imposed.)

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
).filter(
    pl.col("scenario") == primary_scenario,
)
(
    ggplot(
        threshold_tradeoff,
        aes("mean", "mean_exposure_per_review"),
    )
    + geom_point(aes(color="method", size="mean_exposure_per_review"), alpha=0.8)
    + ggtitle("Manual threshold\nburden versus value")
    + labs(
        x="Average native review burden",
        y="Estimated exposure per review",
        color="Manual baseline",
        size="Exposure per review",
    )
    + theme_minimal()
)

# %%
print(_threshold_takeaway(threshold_tradeoff))

# %% [markdown]
# **Why this matters for facility admins:** this scenario-specific view isolates the overtime staffing-pressure question. A threshold can be simple and still be inefficient. A threshold sitting far to the right with a low vertical value means it creates a lot of review work without proportionate risk capture. The calibrated manual threshold pack is the fairest manual baseline because it is tuned to the observed payroll context without using labels. on a historical rolling basis.

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
overtime_threshold_top = overtime_thresholds.sort(
    MetricCol.EXPOSURE_PER_REVIEW,
    descending=True,
).head(1)

# %%
print(
    "Overtime case-study baseline check: the strongest threshold baseline is "
    f"{overtime_threshold_top.select(pl.col('baseline').first()).item()}, "
    "but the plot below focuses on high-ranked records the calibrated manual "
    "pack did not send to review.",
)

# %%
overtime_missed = _threshold_missed_hybrid_records(overtime_results.scored)

(
    ggplot(
        overtime_missed,
        aes(FeatureCol.PAID_MINUS_SCHEDULED_HOURS, ScoreCol.ESTIMATED_EXPOSURE),
    )
    + geom_point(
        aes(
            color=ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE,
            size=PayrollCol.REST_GAP_HOURS,
        ),
        alpha=0.8,
    )
    + ggtitle("Overtime records missed by the manual threshold pack")
    + labs(
        x="Paid hours above scheduled hours",
        y="Estimated exposure",
        color="Hybrid score",
        size="Rest gap hours",
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
premium_threshold_top = premium_thresholds.sort(
    MetricCol.EXPOSURE_PER_REVIEW,
    descending=True,
).head(1)

# %%
print(
    "Premium case-study baseline check: the strongest threshold baseline is "
    f"{premium_threshold_top.select(pl.col('baseline').first()).item()}, "
    "but the plot below focuses on high-ranked premium records the calibrated "
    "manual pack did not send to review.",
)

# %%
premium_missed = _threshold_missed_hybrid_records(premium_results.scored)

(
    ggplot(
        premium_missed,
        aes(PayrollCol.PREMIUM_PAY, ScoreCol.ESTIMATED_EXPOSURE),
    )
    + geom_point(
        aes(color=ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE, size=PayrollCol.IS_WEEKEND),
        alpha=0.8,
    )
    + ggtitle("Premium records missed by the manual threshold pack")
    + labs(
        x="Premium pay",
        y="Estimated exposure",
        color="Hybrid score",
        size="Weekend flag",
    )
    + theme_minimal()
)

# %% [markdown]
# **Interpretation:** This shows value of hybrid. Missed records are not the largest premiums. They are the premiums that become questionable when shift type, weekend status, and payroll context do not line up cleanly.

# %% [markdown]
# ## Diagnostic: Expected Pay Bands
#
# Robust statistics become more persuasive when they are shown as an expected pay band instead of an abstract score. The chart below focuses on threshold-missed records that sit furthest above their expected pay band.
#
# An **expected pay band** is the contextual gross-pay range the system would expect for a comparable payroll record. Here, the band is shown from the 10th to 90th percentile of expected gross pay, using prior employee, role, shift, facility, and payroll context rather than one fixed dollar cutoff. The point is diagnostic: it illustrates how a simple system rule could automatically adjust alert thresholds based on previous gross-pay patterns and comparable context, instead of sending alerts from a static gross-pay limit that may be too strict for one role and too loose for another.

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
    + ggtitle("Threshold-missed records above expected pay bands")
    + labs(
        x="Records furthest above expected band",
        y="Gross pay",
    )
    + theme_minimal()
)

# %%
largest_band_overage = _single_value(expected_pay_bands, "gross_pay_above_p90")
print(
    "Expected-pay-band takeaway: the largest threshold-missed record shown is "
    f"{_format_money(largest_band_overage)} above the comparable-context "
    "90th-percentile pay band.",
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

# %%
rolling_min = float(
    rolling_yield.select(pl.min(MetricCol.EXPOSURE_PER_REVIEW)).item() or 0.0,
)
rolling_max = float(
    rolling_yield.select(pl.max(MetricCol.EXPOSURE_PER_REVIEW)).item() or 0.0,
)
print(
    "Rolling-origin takeaway: overtime review yield ranges from "
    f"{_format_money(rolling_min)} to {_format_money(rolling_max)} estimated "
    "exposure per reviewed record as validation and test periods move forward.",
)

# %% [markdown]
# **Operational meaning:** this plot is not claiming perfect precision. The rolling-origin calculation ranks records within each facility and pay period, then measures whether the same review capacity continues to surface meaningful estimated exposure as payroll conditions move forward. Precision remains available as evaluation context, but real SNF review will always include legitimate high-risk-looking records that deserve administrator judgment rather than automatic rejection.

# %% [markdown]
# ## Concrete Final Output
#
# This is what a facility-admin-safe ranked output looks like in practice.

# %%
final_queue = premium_results.analyst_review_queue.select(
    [
        ReviewCol.RANK,
        PayrollCol.FACILITY_ID,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_DATE,
        PayrollCol.SHIFT_TYPE,
        ReviewCol.PRIMARY_REASON,
        ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE,
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

# %% [markdown]
# ### Simulation Assumptions
#
# This notebook uses controlled synthetic SNF payroll simulations so that the evaluation can know which records were intentionally made risky and how much estimated payroll exposure they represent. That makes it possible to compare review methods objectively without using real employee payroll data or treating real people as confirmed errors.
#
# Key assumptions:
#
# 1. Each run creates a synthetic set of facilities, employees, roles, shifts, scheduled hours, paid hours, premiums, and gross pay across multiple pay periods.
# 2. Scenario presets inject specific operational risk patterns, such as overtime staffing pressure, double-shift/rest-gap pressure, premium mismatch, and queue stress.
# 3. Synthetic anomaly labels and synthetic exposure dollars are available only because this is a simulation. They are used to evaluate performance, not to create the administrator-facing score.
# 4. Review budgets represent scarce pre-payroll approval capacity at the facility level. A top-K ranking method is judged by the best records it can place inside that limited capacity.
# 5. Manual thresholds are evaluated by their native behavior: every record crossing the cutoff becomes review demand, even if that creates more work than the facility can comfortably handle.
# 6. Expected pay bands are historical/contextual diagnostics. They show how alert thresholds could adapt to previous gross pay and comparable shift context, but they do not by themselves prove an error.
# 7. Queue stress policies test operational sensitivity: what happens when candidate volume rises, review capacity is fixed, review capacity temporarily drops, or a threshold policy creates more candidate records than reviewers can absorb.

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
        aes(
            "policy",
            PayrollCol.PAY_PERIOD_INDEX,
            fill="avg_missed_estimated_exposure_k",
        ),
    )
    + geom_tile()
    + ggtitle("Appendix stress view:\nmissed exposure by queue policy and period")
    + labs(
        x="Queue policy",
        y="Pay period",
        fill="Missed exposure ($K)",
    )
    + scale_fill_gradient(low="#f8fafc", high="#b91c1c")
    + theme_minimal()
    + rotated_x_labels()
)

# %%
appendix_risk = (
    appendix_queue.group_by("policy")
    .agg(
        pl.max("overload_probability").alias("max_overload_probability"),
        pl.max("avg_missed_estimated_exposure_k").alias("max_missed_exposure_k"),
        pl.mean("avg_candidate_queue_size").alias("mean_candidate_queue_size"),
        pl.mean("reviewed_to_candidate_ratio").alias("mean_reviewed_share"),
    )
    .sort("max_missed_exposure_k")
)
(
    ggplot(
        appendix_risk,
        aes("policy", "max_missed_exposure_k"),
    )
    + geom_point(
        aes(color="max_overload_probability", size="mean_reviewed_share"),
    )
    + ggtitle("Appendix stress ranking")
    + labs(
        x="Queue policy",
        y="Maximum missed estimated exposure ($K)",
        color="Max overload probability",
        size="Mean reviewed share",
    )
    + scale_color_gradient(low="#0f766e", high="#b91c1c", breaks=[0, 0.5, 1])
    + coord_flip()
    + theme_minimal()
)

# %%
best_stress_policy = appendix_risk.sort("max_missed_exposure_k").head(1)
worst_stress_policy = appendix_risk.sort("max_missed_exposure_k", descending=True).head(
    1,
)
print(
    "Appendix stress takeaway: the lowest missed-exposure policy is "
    f"{best_stress_policy.select(pl.col('policy').first()).item()}, while "
    f"{worst_stress_policy.select(pl.col('policy').first()).item()} leaves the "
    "largest maximum missed estimated exposure under queue stress.",
)

# %% [markdown]
# ## What This Proves
#
# For facility administrators, the persuasive result is not simply that ML produces a higher score. The persuasive result is that hybrid ranking repeatedly captures more review-worthy payroll risk per scarce review than manual thresholds, while still staying explainable in payroll language and grounded in schedule, timeclock, premium, peer, and exposure context.
#
# The next legacy notebook, `09_model_ablation_and_ml_value.py`, remains the technical support notebook. It goes deeper into ablation, uncertainty, and diagnostic detail once the business case is already established.

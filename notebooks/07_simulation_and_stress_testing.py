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
# # 07 Simulation And Stress Testing
#
# This internal notebook runs bounded scenario and Monte Carlo queue simulations over synthetic payroll outputs. Scenario metadata remains internal and is not added to analyst-safe review queues.
#
# The queue-capacity section intentionally uses the `queue-stress` synthetic regime so the plots expose operational variation rather than showing a mostly empty baseline queue. Monte Carlo variation comes from repeated simulated analyst-capacity draws across pay periods and threshold policies; scenario variation comes from rerunning the synthetic payroll generator under different controlled anomaly and drift regimes.

# %%
import polars as pl
from common.execution import notebook_fast_mode
from common.plots import (
    LetsPlot,
    aes,
    coord_flip,
    geom_density,
    geom_histogram,
    geom_line,
    geom_point,
    geom_segment,
    geom_tile,
    geom_vline,
    ggplot,
    ggtitle,
    labs,
    scale_color_gradient,
    scale_fill_gradient,
    theme_minimal,
)

from payroll_anomaly_ranking.columns import PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import scenario_sanity_summary
from payroll_anomaly_ranking.pipeline import PipelineIncludeConfig, run_pipeline
from payroll_anomaly_ranking.queue_simulation import (
    compare_scenarios,
    simulate_queue_capacity,
    summarize_queue_simulation,
)
from payroll_anomaly_ranking.scenarios import (
    QueueSimulationSpec,
    diagnostic_scenario_presets,
)

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=220, pay_periods=14, review_budgets=(10, 25))
QUEUE_SCENARIOS = ("baseline", "queue-stress", "calendar-drift", "exposure-heavy")
QUEUE_THRESHOLD_GRID = (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70)
QUEUE_ITERATIONS = 300
OPERATING_THRESHOLD = 0.60
CAPACITY_SHOCK_PERIODS = (8, 9, 10, 11)
CAPACITY_SHOCK_START_GUIDE = min(CAPACITY_SHOCK_PERIODS) - 0.5
CAPACITY_SHOCK_END_GUIDE = max(CAPACITY_SHOCK_PERIODS) + 0.5
FAST_MODE_QUEUE_SCENARIOS = ("baseline", "queue-stress")
FAST_MODE_ITERATIONS = 20
FAST_MODE_NOTE = "Dense defaults: 4 queue scenarios, 220 employees, 14 pay periods, threshold grid (0.30 through 0.70 by 0.05), iterations=300. Fast mode: reduce to FAST_MODE_QUEUE_SCENARIOS or FAST_MODE_ITERATIONS."
NOTEBOOK_FAST = notebook_fast_mode()
active_queue_scenarios = FAST_MODE_QUEUE_SCENARIOS if NOTEBOOK_FAST else QUEUE_SCENARIOS
active_queue_iterations = FAST_MODE_ITERATIONS if NOTEBOOK_FAST else QUEUE_ITERATIONS
active_pipeline_include = (
    PipelineIncludeConfig.scored_only()
    if NOTEBOOK_FAST
    else PipelineIncludeConfig.all()
)
queue_spec = QueueSimulationSpec(
    iterations=active_queue_iterations,
    review_budget=10,
    score_thresholds=QUEUE_THRESHOLD_GRID,
    fixed_capacity=8,
    period_capacity_multipliers={8: 0.6, 9: 0.6, 10: 0.7, 11: 0.7},
    capacity_sd=2.0,
    seed=config.seed,
    scenario="queue-stress",
)
scenarios = diagnostic_scenario_presets(active_queue_scenarios)
queue_focus = run_pipeline(
    config,
    scenario=scenarios["queue-stress"],
    include=active_pipeline_include,
)

# %% [markdown]
# ## Simulation Design
#
# **Experiment setup:** This notebook asks whether a threshold-based review queue remains usable when synthetic payroll data becomes more anomalous and analyst capacity fluctuates.
#
# **Scenario variation:** The synthetic payroll generator is rerun under four internal regimes:
# - `baseline` is the calm reference case.
# - `queue-stress` increases anomaly volume and mix, so it is the primary detailed queue-capacity regime.
# - `calendar-drift` adds late-period targeted anomalies and a pay-code change point.
# - `exposure-heavy` increases synthetic dollar impact so missed-exposure behavior is easier to see.
#
# **Monte Carlo variation:** For each period and threshold policy, the queue membership is fixed by scores, then analyst capacity is redrawn 300 times. Capacity is centered around 8 records with random variation and deliberate shock multipliers in periods 8-11.
#
# **What to look for:** high overload probability means demand exceeds review capacity; high missed estimated exposure means risky records remain outside capacity; scenario differences show whether a policy that works in calm data still works under drift, high exposure, or queue pressure.

# %%
queue_sanity = pl.concat(
    [
        scenario_sanity_summary(
            run_pipeline(
                config,
                scenario=scenario,
                include=active_pipeline_include,
            ).scored,
            scenario=name,
            score_thresholds=QUEUE_THRESHOLD_GRID,
        )
        for name, scenario in scenarios.items()
    ],
)

# %% [markdown]
# ## Scenario Contrast Before Queue Simulation
#
# **Scenario candidate-demand chart:** This plot checks whether the configured scenarios create meaningfully different review demand before capacity is simulated.
#
# How to read it: the x-axis is the score threshold, the y-axis is the number of records that would enter a threshold-based queue, and color identifies the synthetic scenario.
#
# What to look for: `queue-stress` should sit above calmer regimes across thresholds. If all lines overlap, later queue stress plots would mostly reflect capacity noise rather than scenario design.

# %%
candidate_columns = [
    column for column in queue_sanity.columns if column.startswith("candidates_at_")
]
candidate_rows: list[dict[str, object]] = []
for row in queue_sanity.select(["scenario", *candidate_columns]).to_dicts():
    for column in candidate_columns:
        candidate_rows.append(
            {
                "scenario": row["scenario"],
                "threshold": float(column.removeprefix("candidates_at_")),
                "candidates": row[column],
            },
        )
candidate_thresholds = pl.DataFrame(candidate_rows)
(
    ggplot(
        candidate_thresholds,
        aes("threshold", "candidates"),
    )
    + geom_point(aes(color="scenario"), size=3)
    + geom_line(aes(color="scenario"))
    + ggtitle("Candidate Demand by Threshold")
    + labs(
        x="Score threshold",
        y="Candidate records",
        color="Scenario",
    )
    + theme_minimal()
)

# %% [markdown]
# **Scenario anomaly-load chart:** This plot checks whether scenarios differ in anomaly prevalence and evaluation-only synthetic dollar exposure.
#
# How to read it: the y-axis is anomaly rate, point size is total synthetic anomaly dollars, and color is anomaly count. The scenario labels are internal diagnostic regimes only.
#
# What to look for: scenarios with larger or darker points are the regimes most likely to stress queue policy through anomaly volume, dollar impact, or both.

# %%
(
    ggplot(queue_sanity, aes("scenario", "anomaly_rate"))
    + geom_point(aes(size="anomaly_dollars", color="anomaly_count"), alpha=0.8)
    + ggtitle("Anomaly Load and Synthetic Exposure")
    + labs(
        x="Scenario",
        y="Anomaly rate",
        color="Anomaly count",
        size="Synthetic anomaly dollars",
    )
    + theme_minimal()
)

# %%
adaptive_queue_spec = QueueSimulationSpec(
    iterations=QUEUE_ITERATIONS,
    review_budget=10,
    adaptive_threshold_quantile=0.90,
    fixed_capacity=8,
    period_capacity_multipliers={8: 0.6, 9: 0.6, 10: 0.7, 11: 0.7},
    capacity_sd=2.0,
    seed=config.seed,
    scenario="queue-stress",
)

# %% [markdown]
# ## Threshold-Demand Queue Capacity Outcomes
#
# Diagnostic question: how many candidates exceed each operational score threshold, and how much demand remains unreviewed when simulated analyst capacity fluctuates? This is separate from fixed review-budget evaluation metrics because queue demand is allowed to expand or contract with risk concentration.

# %%
simulation = simulate_queue_capacity(queue_focus.scored, queue_spec)
simulation_plot = simulation.with_columns(
    (pl.col("dollars_captured") / 1_000).alias("dollars_captured_k"),
)
summary = summarize_queue_simulation(simulation).with_columns(
    (pl.col("avg_missed_estimated_exposure") / 1_000).alias(
        "avg_missed_estimated_exposure_k",
    ),
    (pl.col("avg_missed_synthetic_anomaly_dollars") / 1_000).alias(
        "avg_missed_synthetic_anomaly_dollars_k",
    ),
)

# %%
adaptive_summary = summarize_queue_simulation(
    simulate_queue_capacity(queue_focus.scored, adaptive_queue_spec),
).with_columns(
    (pl.col("avg_missed_estimated_exposure") / 1_000).alias(
        "avg_missed_estimated_exposure_k",
    ),
)

# %% [markdown]
# **Capacity distribution plot:** This chart shows the Monte Carlo distribution of available review capacity across simulated payroll cycles.
#
# How to read it: the x-axis is available analyst capacity for a period-threshold run; the light bars show integer capacity draws, and the smoothed curve shows the overall simulated distribution.
#
# What to look for: the left tail is the operational risk zone because demand policies must remain acceptable when available capacity drops below the nominal mean.

# %%
(
    ggplot(simulation, aes("capacity"))
    + geom_histogram(aes(y="..density.."), bins=16, alpha=0.25)
    + geom_density(color="#0f766e", size=1.2, adjust=2.0, n=512)
    + ggtitle("Queue Capacity Distribution")
    + labs(
        x="Available analyst capacity",
        y="Density",
    )
    + theme_minimal()
)

# %% [markdown]
# **Overload probability plot:** This chart shows where review demand is likely to exceed available capacity.
#
# How to read it: each point is a period-threshold policy summary from 300 Monte Carlo capacity draws. Color is threshold policy, and point size is average candidate queue size.
#
# What to look for: large, high points identify policies and periods where workload routinely exceeds analyst capacity. The vertical guide lines bracket the deliberately shocked capacity periods 8-11.

# %%
(
    ggplot(
        summary,
        aes(PayrollCol.PAY_PERIOD_INDEX, "overload_probability"),
    )
    + geom_point(aes(color="resolved_threshold", size="avg_candidate_queue_size"))
    + geom_vline(
        xintercept=CAPACITY_SHOCK_START_GUIDE,
        linetype="dashed",
        color="#64748b",
    )
    + geom_vline(
        xintercept=CAPACITY_SHOCK_END_GUIDE,
        linetype="dashed",
        color="#64748b",
    )
    + ggtitle("Overload Probability")
    + labs(
        x="Pay period",
        y="Overload probability",
        color="Score threshold",
        size="Candidate records",
    )
    + theme_minimal()
)

# %% [markdown]
# **Overload heatmap:** This view makes threshold-period hot spots easier to scan than the point chart.
#
# How to read it: threshold is on the x-axis, pay period is on the y-axis, and color intensity is overload probability.
#
# What to look for: vertical hot bands show thresholds that are broadly too permissive; horizontal hot bands show periods where capacity shocks or risk concentration drive overload.

# %%
(
    ggplot(
        summary,
        aes(
            "resolved_threshold",
            PayrollCol.PAY_PERIOD_INDEX,
            fill="overload_probability",
        ),
    )
    + geom_tile()
    + ggtitle("Overload Probability Heatmap")
    + labs(
        x="Score threshold",
        y="Pay period",
        fill="Overload probability",
    )
    + scale_fill_gradient(low="#f8fafc", high="#b91c1c", limits=[0, 1])
    + theme_minimal()
)

# %% [markdown]
# **Queue demand plot:** This chart shows how many records would enter review under each score-threshold policy. It helps us see that threshold-based queues can expand or shrink with risk concentration, unlike a fixed top-K workload.
#
# How to read it: each point is a period-threshold combination; color is threshold and size is the average number of records actually reviewed after capacity is applied.
#
# What to look for: high candidate demand with small reviewed counts indicates queue spillover risk. The shocked capacity periods 8-11 are where this gap is most operationally important.

# %%
(
    ggplot(
        summary,
        aes(PayrollCol.PAY_PERIOD_INDEX, "avg_candidate_queue_size"),
    )
    + geom_point(aes(color="resolved_threshold", size="avg_reviewed_records"))
    + geom_vline(
        xintercept=CAPACITY_SHOCK_START_GUIDE,
        linetype="dashed",
        color="#64748b",
    )
    + geom_vline(
        xintercept=CAPACITY_SHOCK_END_GUIDE,
        linetype="dashed",
        color="#64748b",
    )
    + ggtitle("Scenario Queue Demand")
    + labs(
        x="Pay period",
        y="Candidate records",
        color="Score threshold",
        size="Reviewed records",
    )
    + theme_minimal()
)

# %% [markdown]
# **Dollar-capture distribution plot:** This chart shows the range of evaluation-only synthetic dollar impact captured across repeated queue-capacity simulations.
#
# How to read it: the x-axis is evaluation-only synthetic anomaly dollars captured in a single simulated period-threshold-capacity draw, shown in thousands of dollars, and bar height is frequency.
#
# What to look for: a wide or multi-peaked distribution means operational impact depends strongly on which records fit into capacity.

# %%
(
    ggplot(simulation_plot, aes("dollars_captured_k"))
    + geom_histogram(bins=20)
    + ggtitle("Dollar Capture Distribution")
    + labs(
        x="Synthetic anomaly dollars captured ($K)",
        y="Simulation draws",
    )
    + theme_minimal()
)

# %% [markdown]
# **Queue tornado plot:** This chart ranks threshold policies by the range of missed estimated exposure they produce across pay periods. Estimated exposure is the review-safe proxy for dollars at risk, not the evaluation-only synthetic anomaly dollars.
#
# How to read it: each horizontal bar spans the low-to-high missed estimated exposure for one threshold in thousands of dollars; the dot marks the average.
#
# What to look for: long bars identify policies whose results are highly period-sensitive and therefore operationally fragile.

# %%
queue_tornado = (
    summary.with_columns(
        pl.col("resolved_threshold").cast(pl.String).alias("condition"),
    )
    .group_by("condition")
    .agg(
        pl.min("avg_missed_estimated_exposure_k").alias("low"),
        pl.max("avg_missed_estimated_exposure_k").alias("high"),
        pl.mean("avg_missed_estimated_exposure_k").alias("mean_value"),
    )
    .with_columns((pl.col("high") - pl.col("low")).alias("impact"))
    .sort("impact")
)
(
    ggplot(queue_tornado, aes("low", "condition"))
    + geom_segment(
        aes(x="low", xend="high", y="condition", yend="condition", color="impact"),
        size=5,
    )
    + geom_point(aes(x="mean_value"), color="#111827", size=3)
    + ggtitle("Queue Sensitivity Tornado")
    + labs(
        x="Missed estimated exposure ($K)",
        y="Score threshold",
        color="Range ($K)",
    )
    + theme_minimal()
)

# %% [markdown]
# **Missed exposure plot:** This chart shows estimated exposure that remains outside reviewed capacity by period and threshold policy. Point size uses evaluation-only synthetic anomaly dollars, so it should be interpreted as validation context rather than analyst-facing queue content.
#
# How to read it: the y-axis is missed estimated exposure in thousands of dollars, color is threshold, and point size is missed synthetic anomaly dollars.
#
# What to look for: large high points are the policy-period combinations where limited capacity leaves the most synthetic risk unreviewed.

# %%
(
    ggplot(
        summary,
        aes(PayrollCol.PAY_PERIOD_INDEX, "avg_missed_estimated_exposure_k"),
    )
    + geom_point(
        aes(color="resolved_threshold", size="avg_missed_synthetic_anomaly_dollars_k"),
        alpha=0.75,
    )
    + geom_vline(
        xintercept=CAPACITY_SHOCK_START_GUIDE,
        linetype="dashed",
        color="#64748b",
    )
    + geom_vline(
        xintercept=CAPACITY_SHOCK_END_GUIDE,
        linetype="dashed",
        color="#64748b",
    )
    + ggtitle("Missed Exposure by Period and Policy")
    + labs(
        x="Pay period",
        y="Missed estimated exposure ($K)",
        color="Score threshold",
        size="Missed synthetic anomaly dollars ($K)",
    )
    + theme_minimal()
)

# %% [markdown]
# **Worst overload rows:** This small table keeps the most actionable detail from the simulation summary without dumping every threshold-period row.

# %%
summary.select(
    [
        pl.col("resolved_threshold").alias("threshold"),
        pl.col("pay_period_index"),
        pl.col("avg_candidate_queue_size"),
        pl.col("overload_probability"),
        pl.col("avg_missed_estimated_exposure"),
        pl.col("avg_missed_synthetic_anomaly_dollars"),
    ],
).sort(
    ["overload_probability", "avg_missed_estimated_exposure"],
    descending=[True, True],
).head(8)

# %% [markdown]
# ## Adaptive Threshold Comparison
#
# **Adaptive vs fixed threshold chart:** This plot compares the fixed score-threshold grid with an adaptive 90th-percentile policy.
#
# How to read it: each point is a policy summary. The x-axis is mean overload probability, the y-axis is mean missed estimated exposure in thousands of dollars, and point size is mean candidate queue size.
#
# What to look for: policies closer to the lower-left corner are less overloaded and leave less estimated exposure outside capacity. The adaptive p90 point is a relative upper-tail diagnostic, not a capacity-calibrated operating policy; if it overloads capacity, a future adaptive rule should be calibrated from current period volume and available staffing rather than from a fixed employee count.

# %%
fixed_policy = (
    summary.group_by("resolved_threshold")
    .agg(
        pl.mean("overload_probability").alias("mean_overload_probability"),
        pl.mean("avg_missed_estimated_exposure_k").alias("mean_missed_exposure_k"),
        pl.mean("avg_candidate_queue_size").alias("mean_candidate_queue_size"),
    )
    .with_columns(
        (
            pl.lit("fixed threshold ")
            + pl.col("resolved_threshold").round(2).cast(pl.String)
        ).alias(
            "policy",
        ),
    )
)
adaptive_policy = (
    adaptive_summary.group_by("resolved_threshold")
    .agg(
        pl.mean("overload_probability").alias("mean_overload_probability"),
        pl.mean("avg_missed_estimated_exposure_k").alias("mean_missed_exposure_k"),
        pl.mean("avg_candidate_queue_size").alias("mean_candidate_queue_size"),
    )
    .with_columns(
        (
            pl.lit("adaptive p90 ")
            + pl.col("resolved_threshold").round(2).cast(pl.String)
        ).alias(
            "policy",
        ),
    )
)
policy_comparison = pl.concat([fixed_policy, adaptive_policy])
(
    ggplot(
        policy_comparison,
        aes("mean_overload_probability", "mean_missed_exposure_k"),
    )
    + geom_point(aes(color="policy", size="mean_candidate_queue_size"), alpha=0.8)
    + ggtitle("Adaptive vs Fixed Threshold Queue Risk")
    + labs(
        x="Mean overload probability",
        y="Mean missed estimated exposure ($K)",
        color="Policy",
        size="Mean candidate records",
    )
    + theme_minimal()
)

# %% [markdown]
# ## Operating Recommendation
#
# The queue service-level view is more actionable than a single model metric: a candidate operating policy should keep overload probability acceptable while limiting unreviewed estimated exposure. In this run, permissive thresholds create the clearest overload during the shocked capacity window, while stricter thresholds reduce workload at the cost of leaving more estimated exposure outside analyst capacity.
#
# Estimated exposure is the review-safe dollars-at-risk proxy used for operational decisions. Synthetic anomaly dollars are evaluation-only truth labels used here to validate whether the proxy tracks injected payroll risk; they should not appear in analyst-facing queues.
#
# A practical next operating test is to select a threshold band from the lower-left region of the policy comparison, then rerun the queue simulation under expected staffing, reduced staffing, and catch-up staffing assumptions. Adaptive thresholding should remain relative to the current pay-period population and available capacity rather than assuming a fixed employee count.

# %% [markdown]
# ## Scenario-Dependent Queue Stress Tests
#
# Diagnostic question: which internal stress-test regimes create demand, overload, missed estimated exposure, or missed evaluation-only synthetic anomaly dollars under the same threshold-grid design?

# %%
comparison = compare_scenarios(
    config,
    scenarios,
    queue_spec,
).with_columns(
    (pl.col("avg_missed_estimated_exposure") / 1_000).alias(
        "avg_missed_estimated_exposure_k",
    ),
    (pl.col("avg_missed_synthetic_anomaly_dollars") / 1_000).alias(
        "avg_missed_synthetic_anomaly_dollars_k",
    ),
)
operating_threshold_comparison = comparison.filter(
    pl.col("resolved_threshold") == OPERATING_THRESHOLD,
)

# %% [markdown]
# **Scenario stress-test heatmap:** This chart compares queue outcomes across internal synthetic stress regimes at the selected operating threshold.
#
# How to read it: scenario is on the x-axis, pay period is on the y-axis, and fill color is overload probability after Monte Carlo capacity draws.
#
# What to look for: scenario-period blocks with high overload show where the same threshold policy fails under a different synthetic world. The full threshold grid remains in the worst-row table below; this heatmap is filtered to one operating threshold to avoid overplotting multiple policies into the same tile.

# %%
(
    ggplot(
        operating_threshold_comparison,
        aes("scenario", PayrollCol.PAY_PERIOD_INDEX, fill="overload_probability"),
    )
    + geom_tile()
    + ggtitle(f"Stress-Test Queue Outcomes at Threshold {OPERATING_THRESHOLD:.2f}")
    + labs(
        x="Scenario",
        y="Pay period",
        fill="Overload probability",
    )
    + scale_fill_gradient(low="#f8fafc", high="#b91c1c", limits=[0, 1])
    + theme_minimal()
)

# %% [markdown]
# **Scenario risk ranking:** This chart compresses the scenario comparison into one point per regime.
#
# How to read it: the horizontal axis ranks maximum missed estimated exposure in thousands of dollars, color is maximum overload probability, and size is mean candidate queue size.
#
# What to look for: scenarios with large, high-risk points are the regimes that need threshold changes, staffing buffers, or additional triage rules.

# %%
scenario_risk = (
    comparison.group_by("scenario")
    .agg(
        pl.max("overload_probability").alias("max_overload_probability"),
        pl.max("avg_missed_estimated_exposure_k").alias("max_missed_exposure_k"),
        pl.mean("avg_candidate_queue_size").alias("mean_candidate_queue_size"),
    )
    .sort("max_missed_exposure_k")
)
(
    ggplot(
        scenario_risk,
        aes("scenario", "max_missed_exposure_k"),
    )
    + geom_point(
        aes(color="max_overload_probability", size="mean_candidate_queue_size"),
    )
    + ggtitle("Scenario Queue Risk Ranking")
    + labs(
        x="Scenario",
        y="Maximum missed estimated exposure ($K)",
        color="Max overload probability",
        size="Mean candidate records",
    )
    + scale_color_gradient(low="#0f766e", high="#b91c1c", limits=[0, 1])
    + coord_flip()
    + theme_minimal()
)

# %% [markdown]
# **Worst scenario-period rows:** This small table preserves the highest-risk scenario details for follow-up analysis without showing the full comparison grid.

# %%
comparison.select(
    [
        "scenario",
        pl.col("resolved_threshold").alias("threshold"),
        pl.col("pay_period_index"),
        pl.col("avg_candidate_queue_size"),
        pl.col("overload_probability"),
        pl.col("avg_missed_estimated_exposure"),
        pl.col("avg_missed_synthetic_anomaly_dollars"),
    ],
).sort(
    ["avg_missed_estimated_exposure", "overload_probability"],
    descending=[True, True],
).head(8)

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
from common.plots import (
    LetsPlot,
    aes,
    geom_density,
    geom_histogram,
    geom_line,
    geom_point,
    geom_segment,
    geom_tile,
    ggplot,
    ggtitle,
    theme_minimal,
)

from payroll_anomaly_ranking.columns import PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import scenario_sanity_summary
from payroll_anomaly_ranking.pipeline import run_pipeline
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
FAST_MODE_QUEUE_SCENARIOS = ("baseline", "queue-stress")
FAST_MODE_ITERATIONS = 20
FAST_MODE_NOTE = "Dense defaults: 4 queue scenarios, 220 employees, 14 pay periods, threshold grid (0.30 through 0.70 by 0.05), iterations=300. Fast mode: reduce to FAST_MODE_QUEUE_SCENARIOS or FAST_MODE_ITERATIONS."
queue_spec = QueueSimulationSpec(
    iterations=QUEUE_ITERATIONS,
    review_budget=10,
    score_thresholds=QUEUE_THRESHOLD_GRID,
    fixed_capacity=8,
    period_capacity_multipliers={8: 0.6, 9: 0.6, 10: 0.7, 11: 0.7},
    capacity_sd=2.0,
    seed=config.seed,
    scenario="queue-stress",
)
scenarios = diagnostic_scenario_presets(QUEUE_SCENARIOS)
queue_focus = run_pipeline(config, scenario=scenarios["queue-stress"])

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
            run_pipeline(config, scenario=scenario).scored,
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
# What to look for: `queue-stress` should sit above calmer regimes across thresholds; if all lines overlap, later queue stress plots would mostly reflect capacity noise rather than scenario design.

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
                "threshold": column.removeprefix("candidates_at_"),
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
    + ggtitle("Scenario Candidate Demand by Threshold")
    + theme_minimal()
)

# %% [markdown]
# **Scenario anomaly-load chart:** This plot checks whether scenarios differ in anomaly prevalence and synthetic dollar exposure.
#
# How to read it: the y-axis is anomaly rate, point size is total synthetic anomaly dollars, and color is anomaly count. The scenario labels are internal diagnostic regimes only.
#
# What to look for: scenarios with larger or darker points are the regimes most likely to stress queue policy through anomaly volume, dollar impact, or both.

# %%
(
    ggplot(queue_sanity, aes("scenario", "anomaly_rate"))
    + geom_point(aes(size="anomaly_dollars", color="anomaly_count"), alpha=0.8)
    + ggtitle("Scenario Anomaly Load and Synthetic Exposure")
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
summary = summarize_queue_simulation(simulation)

# %%
adaptive_summary = summarize_queue_simulation(
    simulate_queue_capacity(queue_focus.scored, adaptive_queue_spec),
)

# %% [markdown]
# **Capacity distribution plot:** This chart shows the Monte Carlo distribution of available review capacity across simulated payroll cycles.
#
# How to read it: the x-axis is available analyst capacity for a period-threshold run; the light bars show integer capacity draws, and the smooth curve shows the overall simulated distribution.
#
# What to look for: the left tail is the operational risk zone because demand policies must remain acceptable when available capacity drops below the nominal mean.

# %%
(
    ggplot(simulation, aes("capacity"))
    + geom_histogram(aes(y="..density.."), bins=40, alpha=0.25)
    + geom_density(color="#0f766e", size=1.2)
    + ggtitle("Queue Capacity Distribution")
    + theme_minimal()
)

# %% [markdown]
# **Overload probability plot:** This chart shows where review demand is likely to exceed available capacity.
#
# How to read it: each point is a period-threshold policy summary from 300 Monte Carlo capacity draws. Color is threshold policy, and point size is average candidate queue size.
#
# What to look for: large, high points identify policies and periods where workload routinely exceeds analyst capacity.

# %%
(
    ggplot(
        summary,
        aes(PayrollCol.PAY_PERIOD_INDEX, "overload_probability"),
    )
    + geom_point(aes(color="resolved_threshold", size="avg_candidate_queue_size"))
    + ggtitle("Overload Probability")
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
    + theme_minimal()
)

# %% [markdown]
# **Queue demand plot:** This chart shows how many records would enter review under each score-threshold policy. It helps us see that threshold-based queues can expand or shrink with risk concentration, unlike a fixed top-K workload.
#
# How to read it: each point is a period-threshold combination; color is threshold and size is the average number of records actually reviewed after capacity is applied.
#
# What to look for: high candidate demand with small reviewed counts indicates queue spillover risk.

# %%
(
    ggplot(
        summary,
        aes(PayrollCol.PAY_PERIOD_INDEX, "avg_candidate_queue_size"),
    )
    + geom_point(aes(color="resolved_threshold", size="avg_reviewed_records"))
    + ggtitle("Scenario Queue Demand")
    + theme_minimal()
)

# %% [markdown]
# **Dollar-capture distribution plot:** This chart shows the range of evaluation-only synthetic dollar impact captured across repeated queue-capacity simulations.
#
# How to read it: the x-axis is synthetic anomaly dollars captured in a single simulated period-threshold-capacity draw, and bar height is frequency.
#
# What to look for: a wide or multi-peaked distribution means operational impact depends strongly on which records fit into capacity.

# %%
(
    ggplot(simulation, aes("dollars_captured"))
    + geom_histogram(bins=20)
    + ggtitle("Dollar Capture Distribution")
    + theme_minimal()
)

# %% [markdown]
# **Queue tornado plot:** This chart ranks threshold policies by the range of missed estimated exposure they produce across pay periods.
#
# How to read it: each horizontal bar spans the low-to-high missed estimated exposure for one threshold; the dot marks the average.
#
# What to look for: long bars identify policies whose results are highly period-sensitive and therefore operationally fragile.

# %%
queue_tornado = (
    summary.with_columns(
        pl.col("resolved_threshold").cast(pl.String).alias("condition"),
    )
    .group_by("condition")
    .agg(
        pl.min("avg_missed_estimated_exposure").alias("low"),
        pl.max("avg_missed_estimated_exposure").alias("high"),
        pl.mean("avg_missed_estimated_exposure").alias("mean_value"),
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
    + theme_minimal()
)

# %% [markdown]
# **Missed exposure plot:** This chart shows synthetic exposure that remains outside reviewed capacity by period and threshold policy.
#
# How to read it: the y-axis is missed estimated exposure, color is threshold, and point size is missed synthetic anomaly dollars.
#
# What to look for: large high points are the policy-period combinations where limited capacity leaves the most synthetic risk unreviewed.

# %%
(
    ggplot(
        summary,
        aes(PayrollCol.PAY_PERIOD_INDEX, "avg_missed_estimated_exposure"),
    )
    + geom_point(
        aes(color="resolved_threshold", size="avg_missed_synthetic_anomaly_dollars"),
        alpha=0.75,
    )
    + ggtitle("Missed Exposure by Period and Policy")
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
# How to read it: each point is a policy summary. The x-axis is mean overload probability, the y-axis is mean missed estimated exposure, and point size is mean candidate queue size.
#
# What to look for: policies closer to the lower-left corner are less overloaded and leave less estimated exposure outside capacity. The adaptive point shows whether a relative top-tail policy is more stable than fixed cutoffs.

# %%
fixed_policy = (
    summary.group_by("resolved_threshold")
    .agg(
        pl.mean("overload_probability").alias("mean_overload_probability"),
        pl.mean("avg_missed_estimated_exposure").alias("mean_missed_exposure"),
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
        pl.mean("avg_missed_estimated_exposure").alias("mean_missed_exposure"),
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
        aes("mean_overload_probability", "mean_missed_exposure"),
    )
    + geom_point(aes(color="policy", size="mean_candidate_queue_size"), alpha=0.8)
    + ggtitle("Adaptive vs Fixed Threshold Queue Risk")
    + theme_minimal()
)

# %% [markdown]
# ## Scenario-Dependent Queue Stress Tests
#
# Diagnostic question: which internal stress-test regimes create demand, overload, missed exposure, or missed synthetic anomaly dollars under the same operating policy?

# %%
comparison = compare_scenarios(
    config,
    scenarios,
    queue_spec,
)

# %% [markdown]
# **Scenario stress-test heatmap:** This chart compares queue outcomes across internal synthetic stress regimes under the same operating policy.
#
# How to read it: scenario is on the x-axis, pay period is on the y-axis, and fill color is overload probability after Monte Carlo capacity draws.
#
# What to look for: scenario-period blocks with high overload show where the same queue policy fails under a different synthetic world.

# %%
(
    ggplot(
        comparison,
        aes("scenario", PayrollCol.PAY_PERIOD_INDEX, fill="overload_probability"),
    )
    + geom_tile()
    + ggtitle("Stress-Test Queue Outcomes")
    + theme_minimal()
)

# %% [markdown]
# **Scenario risk ranking:** This chart compresses the scenario comparison into one point per regime.
#
# How to read it: the y-axis ranks maximum missed estimated exposure, color is maximum overload probability, and size is mean candidate queue size.
#
# What to look for: scenarios with large, high-risk points are the regimes that need threshold changes, staffing buffers, or additional triage rules.

# %%
scenario_risk = (
    comparison.group_by("scenario")
    .agg(
        pl.max("overload_probability").alias("max_overload_probability"),
        pl.max("avg_missed_estimated_exposure").alias("max_missed_exposure"),
        pl.mean("avg_candidate_queue_size").alias("mean_candidate_queue_size"),
    )
    .sort("max_missed_exposure")
)
(
    ggplot(
        scenario_risk,
        aes("scenario", "max_missed_exposure"),
    )
    + geom_point(
        aes(color="max_overload_probability", size="mean_candidate_queue_size"),
    )
    + ggtitle("Scenario Queue Risk Ranking")
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

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
from lets_plot import LetsPlot

from payroll_anomaly_ranking.charts import (
    adaptive_threshold_comparison_chart,
    capacity_distribution_chart,
    dollar_capture_distribution_chart,
    missed_exposure_chart,
    overload_probability_chart,
    queue_demand_chart,
    queue_overload_heatmap,
    queue_tornado_chart,
    scenario_anomaly_exposure_chart,
    scenario_candidate_threshold_chart,
    scenario_risk_bar_chart,
    stress_test_heatmap,
)
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
scenario_candidate_threshold_chart(queue_sanity)

# %% [markdown]
# **Scenario anomaly-load chart:** This plot checks whether scenarios differ in anomaly prevalence and synthetic dollar exposure.
#
# How to read it: the y-axis is anomaly rate, point size is total synthetic anomaly dollars, and color is anomaly count. The scenario labels are internal diagnostic regimes only.
#
# What to look for: scenarios with larger or darker points are the regimes most likely to stress queue policy through anomaly volume, dollar impact, or both.

# %%
scenario_anomaly_exposure_chart(queue_sanity)

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
capacity_distribution_chart(simulation)

# %% [markdown]
# **Overload probability plot:** This chart shows where review demand is likely to exceed available capacity.
#
# How to read it: each point is a period-threshold policy summary from 300 Monte Carlo capacity draws. Color is threshold policy, and point size is average candidate queue size.
#
# What to look for: large, high points identify policies and periods where workload routinely exceeds analyst capacity.

# %%
overload_probability_chart(summary)

# %% [markdown]
# **Overload heatmap:** This view makes threshold-period hot spots easier to scan than the point chart.
#
# How to read it: threshold is on the x-axis, pay period is on the y-axis, and color intensity is overload probability.
#
# What to look for: vertical hot bands show thresholds that are broadly too permissive; horizontal hot bands show periods where capacity shocks or risk concentration drive overload.

# %%
queue_overload_heatmap(summary)

# %% [markdown]
# **Queue demand plot:** This chart shows how many records would enter review under each score-threshold policy. It helps us see that threshold-based queues can expand or shrink with risk concentration, unlike a fixed top-K workload.
#
# How to read it: each point is a period-threshold combination; color is threshold and size is the average number of records actually reviewed after capacity is applied.
#
# What to look for: high candidate demand with small reviewed counts indicates queue spillover risk.

# %%
queue_demand_chart(summary)

# %% [markdown]
# **Dollar-capture distribution plot:** This chart shows the range of evaluation-only synthetic dollar impact captured across repeated queue-capacity simulations.
#
# How to read it: the x-axis is synthetic anomaly dollars captured in a single simulated period-threshold-capacity draw, and bar height is frequency.
#
# What to look for: a wide or multi-peaked distribution means operational impact depends strongly on which records fit into capacity.

# %%
dollar_capture_distribution_chart(simulation)

# %% [markdown]
# **Queue tornado plot:** This chart ranks threshold policies by the range of missed estimated exposure they produce across pay periods.
#
# How to read it: each horizontal bar spans the low-to-high missed estimated exposure for one threshold; the dot marks the average.
#
# What to look for: long bars identify policies whose results are highly period-sensitive and therefore operationally fragile.

# %%
queue_tornado_chart(summary)

# %% [markdown]
# **Missed exposure plot:** This chart shows synthetic exposure that remains outside reviewed capacity by period and threshold policy.
#
# How to read it: the y-axis is missed estimated exposure, color is threshold, and point size is missed synthetic anomaly dollars.
#
# What to look for: large high points are the policy-period combinations where limited capacity leaves the most synthetic risk unreviewed.

# %%
missed_exposure_chart(summary)

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
adaptive_threshold_comparison_chart(summary, adaptive_summary)

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
stress_test_heatmap(comparison)

# %% [markdown]
# **Scenario risk ranking:** This chart compresses the scenario comparison into one point per regime.
#
# How to read it: the y-axis ranks maximum missed estimated exposure, color is maximum overload probability, and size is mean candidate queue size.
#
# What to look for: scenarios with large, high-risk points are the regimes that need threshold changes, staffing buffers, or additional triage rules.

# %%
scenario_risk_bar_chart(comparison)

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

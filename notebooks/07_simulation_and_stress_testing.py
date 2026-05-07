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

# %%
import polars as pl
from lets_plot import LetsPlot

from payroll_anomaly_ranking.charts import (
    capacity_distribution_chart,
    dollar_capture_distribution_chart,
    missed_exposure_chart,
    overload_probability_chart,
    queue_demand_chart,
    queue_tornado_chart,
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
QUEUE_THRESHOLD_GRID = (0.35, 0.45, 0.55, 0.65)
QUEUE_ITERATIONS = 60
FAST_MODE_QUEUE_SCENARIOS = ("baseline", "queue-stress")
FAST_MODE_ITERATIONS = 20
FAST_MODE_NOTE = "Dense defaults: 4 queue scenarios, 220 employees, 14 pay periods, threshold grid (0.35, 0.45, 0.55, 0.65), iterations=60. Fast mode: reduce to FAST_MODE_QUEUE_SCENARIOS or FAST_MODE_ITERATIONS."
queue_spec = QueueSimulationSpec(
    iterations=QUEUE_ITERATIONS,
    review_budget=10,
    score_thresholds=QUEUE_THRESHOLD_GRID,
    fixed_capacity=8,
    period_capacity_multipliers={8: 0.6, 9: 0.6, 10: 0.7, 11: 0.7},
    capacity_sd=2.0,
    seed=config.seed,
    scenario="baseline",
)
scenarios = diagnostic_scenario_presets(QUEUE_SCENARIOS)
baseline = run_pipeline(config, scenario=scenarios["baseline"])

# %%
queue_sanity = pl.concat(
    [
        scenario_sanity_summary(
            run_pipeline(config, scenario=scenario)["scored"],
            scenario=name,
            score_thresholds=QUEUE_THRESHOLD_GRID,
        )
        for name, scenario in scenarios.items()
    ],
)
queue_sanity

# %%
adaptive_queue_spec = QueueSimulationSpec(
    iterations=QUEUE_ITERATIONS,
    review_budget=10,
    adaptive_threshold_quantile=0.90,
    fixed_capacity=8,
    period_capacity_multipliers={8: 0.6, 9: 0.6, 10: 0.7, 11: 0.7},
    capacity_sd=2.0,
    seed=config.seed,
    scenario="baseline",
)

# %% [markdown]
# ## Threshold-Demand Queue Capacity Outcomes
#
# Diagnostic question: how many candidates exceed the operational score threshold, and how much demand remains unreviewed when capacity fluctuates? This is separate from fixed review-budget evaluation metrics.

# %%
simulation = simulate_queue_capacity(baseline["scored"], queue_spec)
summary = summarize_queue_simulation(simulation)
summary

# %%
adaptive_summary = summarize_queue_simulation(
    simulate_queue_capacity(baseline["scored"], adaptive_queue_spec),
)
adaptive_summary

# %%
capacity_distribution_chart(simulation)

# %%
overload_probability_chart(summary)

# %%
queue_demand_chart(summary)

# %%
dollar_capture_distribution_chart(simulation)

# %%
queue_tornado_chart(summary)

# %%
missed_exposure_chart(summary)

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
comparison

# %%
stress_test_heatmap(comparison)

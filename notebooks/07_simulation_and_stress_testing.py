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
config = PayrollConfig(employee_count=160, pay_periods=12, review_budgets=(10, 25))
QUEUE_SCENARIOS = ("baseline", "queue-stress", "calendar-drift")
FAST_MODE_NOTE = "Reduce QUEUE_SCENARIOS or QueueSimulationSpec.iterations for faster local execution."
queue_spec = QueueSimulationSpec(
    iterations=40,
    review_budget=10,
    score_threshold=0.55,
    fixed_capacity=8,
    period_capacity_multipliers={8: 0.6, 9: 0.6, 10: 0.7},
    capacity_sd=2.0,
    seed=config.seed,
    scenario="baseline",
)
scenarios = diagnostic_scenario_presets(QUEUE_SCENARIOS)
baseline = run_pipeline(config, scenario=scenarios["baseline"])

# %% [markdown]
# ## Threshold-Demand Queue Capacity Outcomes
#
# Diagnostic question: how many candidates exceed the operational score threshold, and how much demand remains unreviewed when capacity fluctuates? This is separate from fixed review-budget evaluation metrics.

# %%
simulation = simulate_queue_capacity(baseline["scored"], queue_spec)
summary = summarize_queue_simulation(simulation)
summary

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

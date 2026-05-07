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
    overload_probability_chart,
    queue_tornado_chart,
    stress_test_heatmap,
)
from payroll_anomaly_ranking.columns import PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import run_pipeline
from payroll_anomaly_ranking.queue_simulation import (
    compare_scenarios,
    simulate_queue_capacity,
    summarize_queue_simulation,
)
from payroll_anomaly_ranking.scenarios import (
    AnomalyPlan,
    ChangePointEvent,
    DriftPlan,
    QueueSimulationSpec,
    ScenarioSpec,
)

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=160, pay_periods=12, review_budgets=(10, 25))
queue_spec = QueueSimulationSpec(
    iterations=40,
    review_budget=10,
    fixed_capacity=8,
    capacity_sd=2.0,
    seed=config.seed,
)
baseline = run_pipeline(config)

# %% [markdown]
# ## Monte Carlo Queue Capacity Outcomes

# %%
simulation = simulate_queue_capacity(baseline["scored"], queue_spec)
summary = summarize_queue_simulation(simulation)
summary

# %%
capacity_distribution_chart(simulation)

# %%
overload_probability_chart(summary)

# %%
dollar_capture_distribution_chart(simulation)

# %%
queue_tornado_chart(summary)

# %% [markdown]
# ## Drift, Anomaly-Mix, And Change-Point Stress Tests

# %%
stress = ScenarioSpec(
    name="operations_overtime_stress",
    anomaly_plan=AnomalyPlan(
        category_weights={
            "overtime_spike": 3.0,
            "gross_pay_spike": 2.0,
            "missing_deduction": 1.0,
        },
        target_count=40,
        severity_multipliers={"overtime_spike": 1.4, "gross_pay_spike": 1.3},
    ),
    drift_plans=(
        DriftPlan(
            name="operations_pay_code_shift",
            start_period=7,
            subgroup_filters={PayrollCol.DEPARTMENT: "Operations"},
            pay_code_mix_shift={"OT": 0.75, "REG": 0.25},
            overtime_multiplier=1.25,
        ),
    ),
    change_points=(
        ChangePointEvent(
            name="operations_payroll_total_shift",
            start_period=9,
            subgroup_filters={PayrollCol.DEPARTMENT: "Operations"},
            field=PayrollCol.GROSS_PAY,
            multiplier=1.15,
        ),
    ),
)

comparison = compare_scenarios(
    config,
    {"baseline": None, stress.name: stress},
    queue_spec,
)
comparison

# %%
stress_test_heatmap(comparison)

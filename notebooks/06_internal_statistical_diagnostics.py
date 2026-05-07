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
# # 06 Internal Statistical Diagnostics
#
# This notebook is internal-facing. It uses synthetic evaluation labels to examine uncertainty, subgroup behavior, expected-pay calibration, exposure calibration, robustness, and score sensitivity without changing analyst-safe queue outputs.

# %%
import polars as pl
from lets_plot import LetsPlot

from payroll_anomaly_ranking.charts import (
    credible_interval_chart,
    expected_pay_coverage_chart,
    expected_pay_residual_chart,
    performance_instability_pareto_chart,
    posterior_comparison_chart,
    sensitivity_heatmap,
    subgroup_forest_chart,
    subgroup_shrinkage_chart,
)
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.diagnostics import (
    component_superiority_summary,
    expected_pay_calibration,
    exposure_calibration,
    perturbation_sensitivity,
    review_budget_interval_summary,
    robustness_summary,
    subgroup_diagnostics,
)
from payroll_anomaly_ranking.models import score_payroll
from payroll_anomaly_ranking.pipeline import run_pipeline

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=160, pay_periods=12, review_budgets=(10, 25))
results = run_pipeline(config)
scored = results["scored"]

# %% [markdown]
# ## Bayesian-Style Review Budget Intervals And Component Superiority

# %%
intervals = review_budget_interval_summary(scored, k=10, samples=50, seed=config.seed)
superiority = component_superiority_summary(scored, k=10, samples=30, seed=config.seed)
intervals

# %%
credible_interval_chart(intervals)

# %%
posterior_comparison_chart(superiority)

# %% [markdown]
# ## Hierarchical Subgroup Diagnostics

# %%
subgroups = subgroup_diagnostics(scored, k=10)
subgroups.head(10)

# %%
subgroup_forest_chart(subgroups.filter(pl.col("dimension") == "department"))

# %%
subgroup_shrinkage_chart(subgroups)

# %% [markdown]
# ## Expected-Pay And Exposure Calibration

# %%
calibration = expected_pay_calibration(scored, by="department")
exposure = exposure_calibration(scored)
calibration

# %%
expected_pay_coverage_chart(calibration)

# %%
expected_pay_residual_chart(calibration)

# %%
exposure

# %% [markdown]
# ## Robustness And Perturbation Sensitivity

# %%
alt_results = run_pipeline(
    PayrollConfig(
        employee_count=160,
        pay_periods=12,
        review_budgets=(10, 25),
        seed=config.seed + 1,
    ),
)
robustness = robustness_summary(
    {"seed_42": scored, "seed_43": alt_results["scored"]},
    k=10,
)
robustness

# %%
performance_instability_pareto_chart(robustness)


# %%
def perturb_gross_pay(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns((pl.col("gross_pay") * 1.02).alias("gross_pay"))


sensitivity = perturbation_sensitivity(
    scored,
    perturb_gross_pay,
    lambda frame: score_payroll(frame, config),
)
sensitivity.head(10)

# %%
sensitivity_heatmap(sensitivity)

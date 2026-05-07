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
    effect_size_interval_chart,
    expected_pay_coverage_chart,
    expected_pay_residual_chart,
    performance_instability_pareto_chart,
    posterior_comparison_chart,
    sensitivity_heatmap,
    subgroup_forest_chart,
    subgroup_shrinkage_chart,
)
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import scenario_sanity_summary
from payroll_anomaly_ranking.diagnostics import (
    calibration_plot_inputs,
    exposure_calibration,
    pairwise_component_superiority,
    perturbation_sensitivity,
    review_budget_interval_summary,
    robustness_summary,
    run_diagnostic_comparison_units,
    subgroup_diagnostics,
    top_subgroup_diagnostics,
)
from payroll_anomaly_ranking.models import score_payroll
from payroll_anomaly_ranking.pipeline import run_pipeline
from payroll_anomaly_ranking.scenarios import diagnostic_scenario_presets

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=220, pay_periods=14, review_budgets=(10, 25))
DIAGNOSTIC_SCENARIOS = (
    "baseline",
    "rule-friendly",
    "statistical-friendly",
    "ml-friendly",
    "exposure-heavy",
    "subgroup-drift",
    "calendar-drift",
    "queue-stress",
)
DIAGNOSTIC_SEEDS = (42, 43, 44)
INTERVAL_SAMPLES = 75
FAST_MODE_SCENARIOS = ("baseline", "subgroup-drift", "queue-stress")
FAST_MODE_SEEDS = (42,)
FAST_MODE_SAMPLE_COUNT = 25
FAST_MODE_NOTE = "Dense defaults: 8 scenarios, 3 seeds, 220 employees, 14 pay periods, samples=75. Fast mode: reduce to FAST_MODE_SCENARIOS, FAST_MODE_SEEDS, or FAST_MODE_SAMPLE_COUNT."
scenarios = diagnostic_scenario_presets(DIAGNOSTIC_SCENARIOS)
results = run_pipeline(config, scenario=scenarios["subgroup-drift"])
scored = results["scored"]

# %%
sanity = pl.concat(
    [
        scenario_sanity_summary(
            run_pipeline(config, scenario=scenario)["scored"],
            scenario=name,
        )
        for name, scenario in scenarios.items()
    ],
)
sanity

# %% [markdown]
# ## Review Budget Intervals And Multi-Regime Component Superiority
#
# Diagnostic question: which ranking signal wins when the synthetic world changes? These scenario regimes are internal stress tests, not estimates of real payroll frequencies.

# %%
intervals = review_budget_interval_summary(
    scored,
    k=10,
    samples=INTERVAL_SAMPLES,
    seed=config.seed,
)
unit_metrics = run_diagnostic_comparison_units(
    config,
    scenarios=scenarios,
    seeds=DIAGNOSTIC_SEEDS,
    k=10,
)
superiority = pairwise_component_superiority(unit_metrics, metric="precision_at_k")
intervals

# %%
credible_interval_chart(intervals)

# %%
posterior_comparison_chart(superiority)

# %%
effect_size_interval_chart(superiority)

# %% [markdown]
# ## Hierarchical Subgroup Diagnostics
#
# Diagnostic question: where do raw subgroup anomaly rates differ from pooled estimates after targeted subgroup drift?

# %%
subgroups = subgroup_diagnostics(scored, k=10, scenario="subgroup-drift")
top_subgroups = top_subgroup_diagnostics(subgroups, top_n=15)
top_subgroups

# %%
subgroup_forest_chart(top_subgroups.filter(pl.col("dimension") == "department"))

# %%
subgroup_shrinkage_chart(subgroups)

# %% [markdown]
# ## Expected-Pay And Exposure Calibration
#
# Diagnostic question: are expected-pay intervals covering normal variation, and where do residuals or p90 excess concentrate?

# %%
calibration = calibration_plot_inputs(
    scored,
    scenario="subgroup-drift",
    by="department",
)
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
#
# Diagnostic question: which scenario/seed units are unstable enough to affect review queues?

# %%
alt_results = run_pipeline(
    PayrollConfig(
        employee_count=160,
        pay_periods=14,
        review_budgets=(10, 25),
        seed=config.seed + 1,
    ),
)
robustness = robustness_summary(
    {
        "subgroup-drift|seed=42|origin=default": scored,
        "baseline|seed=43|origin=default": alt_results["scored"],
    },
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

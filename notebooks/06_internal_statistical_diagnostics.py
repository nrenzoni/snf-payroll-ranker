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
from common.execution import notebook_fast_mode
from common.plots import (
    LetsPlot,
    aes,
    geom_errorbar,
    geom_point,
    geom_tile,
    ggplot,
    ggtitle,
    theme_minimal,
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
from payroll_anomaly_ranking.pipeline import PipelineIncludeConfig, run_pipeline
from payroll_anomaly_ranking.scenarios import diagnostic_scenario_presets

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=220, pay_periods=14, review_budgets=(10, 25))
FAST_MODE_CONFIG = PayrollConfig(
    employee_count=90,
    pay_periods=10,
    review_budgets=(10, 25),
)
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
FAST_MODE_SCENARIOS = ("baseline", "subgroup-drift")
FAST_MODE_SEEDS = (42,)
FAST_MODE_SAMPLE_COUNT = 10
FAST_MODE_NOTE = "Dense defaults: 8 scenarios, 3 seeds, 220 employees, 14 pay periods, samples=75. Fast mode: reduce to FAST_MODE_CONFIG, FAST_MODE_SCENARIOS, FAST_MODE_SEEDS, or FAST_MODE_SAMPLE_COUNT."
NOTEBOOK_FAST = notebook_fast_mode()
active_config = FAST_MODE_CONFIG if NOTEBOOK_FAST else config
active_scenarios = FAST_MODE_SCENARIOS if NOTEBOOK_FAST else DIAGNOSTIC_SCENARIOS
active_seeds = FAST_MODE_SEEDS if NOTEBOOK_FAST else DIAGNOSTIC_SEEDS
active_interval_samples = FAST_MODE_SAMPLE_COUNT if NOTEBOOK_FAST else INTERVAL_SAMPLES
active_pipeline_include = (
    PipelineIncludeConfig.scored_only()
    if NOTEBOOK_FAST
    else PipelineIncludeConfig.all()
)
scenarios = diagnostic_scenario_presets(active_scenarios)
results = run_pipeline(
    active_config,
    scenario=scenarios["subgroup-drift"],
    include=active_pipeline_include,
)
scored = results.scored

# %%
sanity = pl.concat(
    [
        scenario_sanity_summary(
            run_pipeline(
                active_config,
                scenario=scenario,
                include=active_pipeline_include,
            ).scored,
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
    samples=active_interval_samples,
    seed=active_config.seed,
)
unit_metrics = run_diagnostic_comparison_units(
    active_config,
    scenarios=scenarios,
    seeds=active_seeds,
    k=10,
)
superiority = pairwise_component_superiority(unit_metrics, metric="precision_at_k")
intervals

# %% [markdown]
# **Review-budget interval plot:** This chart shows uncertainty around review-budget performance rather than a single point estimate. The methodology repeatedly resamples synthetic evaluation outcomes to show a plausible range for metrics such as queue precision, recall, and dollar capture under the same review budget.

# %%
(
    ggplot(intervals, aes("metric", "mean"))
    + geom_point()
    + ggtitle("Bayesian-Style Review Budget Intervals")
    + theme_minimal()
)

# %% [markdown]
# **Component superiority plot:** This chart compares which scoring component tends to perform better across internal synthetic regimes. It is useful for model governance because it shows whether rules, statistics, ML, exposure, or the hybrid score are consistently useful or only strong under certain synthetic conditions.

# %%
(
    ggplot(
        superiority,
        aes("left_signal", "right_signal", fill="win_probability"),
    )
    + geom_tile()
    + ggtitle("Pairwise Component Superiority")
    + theme_minimal()
)

# %% [markdown]
# **Effect-size interval plot:** This chart shows not just which component wins, but how large the performance difference appears to be. The methodology compares component metrics across scenario and seed units, then summarizes the uncertainty around those differences.

# %%
(
    ggplot(superiority, aes("left_signal", "mean_delta"))
    + geom_point(aes(size="samples", color="scenario"))
    + geom_errorbar(aes(ymin="lower_95", ymax="upper_95"), width=0.2)
    + ggtitle("Effect-Size Intervals")
    + theme_minimal()
)

# %% [markdown]
# ## Hierarchical Subgroup Diagnostics
#
# Diagnostic question: where do raw subgroup anomaly rates differ from pooled estimates after targeted subgroup drift?

# %%
subgroups = subgroup_diagnostics(scored, k=10, scenario="subgroup-drift")
top_subgroups = top_subgroup_diagnostics(subgroups, top_n=15)
top_subgroups

# %% [markdown]
# **Subgroup forest plot:** This chart highlights where synthetic anomaly-review outcomes differ across payroll subgroups such as departments. Stakeholders should use it as an internal diagnostic for concentration and coverage patterns, not as evidence about real employee groups.

# %%
department_subgroups = top_subgroups.filter(pl.col("dimension") == "department").sort(
    "pooled_anomaly_rate",
)
(
    ggplot(
        department_subgroups,
        aes("subgroup", "pooled_anomaly_rate"),
    )
    + geom_point(aes(size="records", color="scenario"))
    + geom_errorbar(aes(ymin="lower_95", ymax="upper_95"), width=0.2)
    + ggtitle("Subgroup Pooled Anomaly Rates")
    + theme_minimal()
)

# %% [markdown]
# **Subgroup shrinkage plot:** This chart compares raw subgroup results with stabilized estimates that reduce overreaction to small groups. The methodology pulls sparse subgroup estimates toward the overall pattern so internal reviewers can distinguish stronger signals from noisy small-sample variation.

# %%
(
    ggplot(
        subgroups,
        aes("raw_anomaly_rate", "pooled_anomaly_rate"),
    )
    + geom_point(aes(size="records"))
    + ggtitle("Raw vs Pooled Subgroup Rates")
    + theme_minimal()
)

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

# %% [markdown]
# **Expected-pay coverage plot:** This chart shows whether expected gross-pay intervals cover typical synthetic records across subgroups. It helps reviewers assess whether the expected-pay context is broad enough for normal variation without becoming too vague for triage.

# %%
(
    ggplot(calibration, aes("subgroup", "coverage"))
    + geom_point()
    + ggtitle("Expected Pay Coverage")
    + theme_minimal()
)

# %% [markdown]
# **Expected-pay residual plot:** This chart shows where actual gross pay sits relative to expected-pay estimates. Large residual patterns can indicate scenario drift, subgroup-specific pay behavior, or areas where expected-pay context may need recalibration before operational use.

# %%
(
    ggplot(calibration, aes("subgroup", "avg_residual"))
    + geom_point()
    + ggtitle("Expected Pay Residuals")
    + theme_minimal()
)

# %%
exposure

# %% [markdown]
# ## Robustness And Perturbation Sensitivity
#
# Diagnostic question: which scenario/seed units are unstable enough to affect review queues?

# %%
alt_results = run_pipeline(
    PayrollConfig(
        employee_count=80 if NOTEBOOK_FAST else 160,
        pay_periods=10 if NOTEBOOK_FAST else 14,
        review_budgets=(10, 25),
        seed=active_config.seed + 1,
    ),
    include=active_pipeline_include,
)
robustness = robustness_summary(
    {
        "subgroup-drift|seed=42|origin=default": scored,
        "baseline|seed=43|origin=default": alt_results.scored,
    },
    k=10,
)
robustness

# %% [markdown]
# **Instability Pareto plot:** This chart ranks internal scenario and seed units by instability so reviewers can focus on the settings most likely to change queue behavior. The methodology combines performance movement and queue-overlap changes into a diagnostic signal for robustness review.

# %%
(
    ggplot(
        robustness,
        aes("performance_instability", "precision_at_k"),
    )
    + geom_point()
    + ggtitle("Performance vs Instability")
    + theme_minimal()
)


# %%
def perturb_gross_pay(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns((pl.col("gross_pay") * 1.02).alias("gross_pay"))


sensitivity = perturbation_sensitivity(
    scored,
    perturb_gross_pay,
    lambda frame: score_payroll(frame, active_config),
)
sensitivity.head(10)

# %% [markdown]
# **Perturbation sensitivity heatmap:** This chart shows which ranked records move most when a controlled input perturbation is applied. It helps internal reviewers see whether small synthetic input changes materially alter score or rank, which is important for trust in review prioritization.

# %%
(
    ggplot(sensitivity, aes("rank_movement", "score_movement"))
    + geom_point()
    + ggtitle("Perturbation Sensitivity")
    + theme_minimal()
)

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
# # SNF Modeling, Evaluation, And Error Analysis
#
# **Executive takeaway:** SNF payroll approval ranking should be evaluated by temporal approval-budget performance and estimated exposure captured, then compared directly with manual threshold baselines.

# %%
from common.plots import LetsPlot, aes, geom_bar, ggplot, labs, theme_minimal

from payroll_anomaly_ranking.columns import PayrollCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.evaluation import evaluate_scores
from payroll_anomaly_ranking.pipeline import run_pipeline

LetsPlot.setup_html()

results = run_pipeline(
    PayrollConfig(employee_count=180, pay_periods=14, review_budgets=(10, 25, 50)),
)

# %% [markdown]
# ## Temporal Approval-Budget Metrics
#
# Training, baselines, and scoring use earlier pay periods to score later pay periods. Metrics focus on how much value administrators can capture inside realistic weekly review capacity.

# %%
results.metrics

# %% [markdown]
# ## Model Comparison
#
# The hybrid score combines deterministic rules, robust statistics, employee history, peer/facility normalization, schedule/timeclock context, premium eligibility, ML, and estimated exposure.

# %%
results.model_comparison

# %% [markdown]
# ## Manual Threshold Baseline Comparison
#
# Threshold rules are easy to configure but can overflag legitimate staffing pressure while missing unsupported premium or paid-vs-scheduled exceptions. This table measures threshold review volume and exposure captured.

# %%
evaluate_scores(results.scored).threshold_baseline_metrics

# %%
results.scored.select(
    [
        PayrollCol.FACILITY_ID,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_TYPE,
        PayrollCol.GROSS_PAY,
        PayrollCol.PAID_HOURS,
        PayrollCol.OVERTIME_HOURS,
        PayrollCol.PREMIUM_PAY,
        ScoreCol.ESTIMATED_EXPOSURE,
        ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE,
    ],
).sort(ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE, descending=True).head(15)

# %%
category_errors = results.category_error_analysis
(
    ggplot(category_errors, aes(PayrollCol.ANOMALY_CATEGORY, "true_anomalies"))
    + geom_bar(stat="identity", fill="#7a4e9d")
    + labs(
        title="Synthetic SNF exception categories available for evaluation only",
        x="Evaluation-only category",
        y="Synthetic anomalies",
    )
    + theme_minimal()
)

# %% [markdown]
# ## What This Proves
#
# The project evaluates the approval assistant as a ranked queue under constrained weekly review capacity, not as a generic classifier detached from administrator workflow.

# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
# kernelspec:
#   display_name: Python 3
#   language: python
#   name: python3
# ---

# %% [markdown]
# # Payroll Anomaly Detection And Review Queue
#
# Executive summary: this notebook demonstrates a privacy-safe synthetic payroll anomaly workflow that ranks employee-pay-period records for analyst review. The output is a prioritized queue, not a fraud determination.

# %% [markdown]
# ## Privacy Disclaimer
#
# All records are synthetic. The project includes no real employee names, salaries, tax identifiers, banking details, HR comments, company-specific records, or live integrations.

# %% [markdown]
# ## Problem Framing And Anomaly Taxonomy
#
# Payroll teams need to review duplicate payments, overtime spikes, pay after termination, gross pay spikes, incorrect pay rates, missing deductions, negative net pay, retro outliers, department payroll spikes, and unusual new employee payments before payroll is finalized.

# %%
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.explainability import sample_review_language
from payroll_anomaly_ranking.pipeline import run_pipeline

config = PayrollConfig(employee_count=650, pay_periods=26)
results = run_pipeline(config)

# %% [markdown]
# ## Synthetic Data Generation And EDA
#
# The generator creates employee-pay-period rows with departments, job families, locations, pay types, lifecycle dates, pay rates, hours, overtime, bonuses, commissions, retro pay, deductions, manual adjustments, and injected labels retained separately for evaluation.

# %%
results["payroll"].head()

# %%
results["aggregations"]["payroll_volume"].head()

# %% [markdown]
# ## Data Validation
#
# Hard failures stop the pipeline; warnings identify exception-like payroll records such as missing deductions or negative net pay that can be legitimate corrections but deserve review.

# %%
results["validation_failures"], results["validation_warnings"]

# %% [markdown]
# ## Feature Engineering, Baselines, And Hybrid Scoring
#
# Features use prior employee history, peer-relative context, robust statistical outlier scores, deterministic payroll rules, and Isolation Forest scores. Labels are not used as model features.

# %%
results["scored"].select(["employee_id", "pay_period_index", "rule_score", "statistical_score", "ml_score", "final_anomaly_score", "pay_period_rank"]).head()

# %% [markdown]
# ## Model Comparison, Evaluation, And Review Budgets
#
# Evaluation uses temporal splits and review-queue metrics: precision@K, recall@K, F1@K, PR-AUC, average anomaly rank, mean reciprocal rank, and dollars-at-risk captured@K.

# %%
results["metrics"]

# %%
results["model_comparison"]

# %% [markdown]
# ## Review Queue And Explanations
#
# Explanations frame records as requiring review, not confirmed fraud.

# %%
sample_review_language()

# %%
results["review_queue"].head(10)

# %% [markdown]
# ## Error Analysis
#
# Category-level results identify false positives, false negatives, legitimate exceptions, and subtle missed anomalies that should inform analyst feedback loops.

# %%
results["category_error_analysis"]

# %% [markdown]
# ## Production Architecture, Monitoring, Limitations, And Future Improvements
#
# Intended production flow: payroll, HRIS, and timekeeping source extracts feed validation, feature engineering, scoring, analyst review, feedback capture, monitoring, and retraining. This repository does not build or claim live integrations.
#
# Monitoring metrics should include alert count per cycle, alert acceptance rate, false positive rate from reviews, dollars at risk flagged and confirmed, feature drift, score drift, alert concentration, latency, and data freshness.
#
# Limitations: synthetic labels simplify reality, unsupervised scores can flag legitimate high earners or bonus cycles, and hybrid weights should be calibrated against validated business review outcomes. Future work should add analyst feedback, supervised learning when enough reviewed labels exist, stricter governance, and production orchestration.

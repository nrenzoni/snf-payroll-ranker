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
# # Payroll Anomaly Ranking Notebook Index
#
# **Executive takeaway:** This index links the business-facing notebook sequence for synthetic payroll anomaly ranking. The sequence demonstrates review prioritization, not misconduct determination or live production integration.

# %% [markdown]
# ## Notebook Sequence
#
# 1. `01_problem_framing_and_data_maturity.py` frames pre-finalization payroll review, privacy guardrails, taxonomy, data dictionary, validation, quality summaries, and data maturity visuals.
# 2. `02_feature_engineering_and_baselines.py` explains leakage-safe history, peer, rule, robust statistical, ML, dollar, and hybrid score signals.
# 3. `03_modeling_evaluation_and_error_analysis.py` presents temporal evaluation, review-budget metrics, model comparison, dollars captured, backtesting, and category error analysis.
# 4. `04_review_queue_explainability_and_thresholds.py` turns scores into analyst-readable review queues, case cards, thresholds, risk categories, and operating model guidance.
# 5. `05_production_monitoring_and_deployment_path.py` outlines production deployment, monitoring, retraining triggers, limitations, and governance controls without claiming live integrations.

# %% [markdown]
# ## Quick Pipeline Check
#
# This lightweight cell confirms that the synthetic pipeline can generate the same core outputs used by the notebooks.

# %%
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import run_pipeline

results = run_pipeline(PayrollConfig(employee_count=120, pay_periods=12, review_budgets=(5, 10)))
sorted(results.keys())

# %% [markdown]
# ## What This Proves
#
# The repository now has a navigable notebook story from business framing through production readiness, with all examples synthetic and all outputs framed as payroll review prioritization.

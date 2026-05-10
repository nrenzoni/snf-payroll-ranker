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
# # SNF Payroll Approval Anomaly Ranking Notebook Index
#
# **Executive takeaway:** This index links the business-facing notebook sequence for synthetic SNF shift-level payroll approval anomaly ranking. The sequence demonstrates administrator pre-approval prioritization, not misconduct determination or live production integration.

# %% [markdown]
# ## Notebook Sequence
#
# 1. `01_problem_framing_and_data_maturity.py` frames SNF weekly payroll approval, privacy guardrails, synthetic shift-level schema, validation, quality summaries, and data maturity visuals.
# 2. `02_feature_engineering_and_baselines.py` explains leakage-safe SNF history, facility-normalized peer, schedule/timeclock, premium eligibility, fatigue, rule, and threshold baseline signals.
# 3. `03_modeling_evaluation_and_error_analysis.py` presents temporal evaluation, approval-budget metrics, model comparison, threshold baseline comparison, exposure captured, backtesting, and category error analysis.
# 4. `04_review_queue_explainability_and_thresholds.py` turns scores into administrator-readable approval queues, case cards, thresholds, risk categories, recommended actions, and operating model guidance.
# 5. `05_production_monitoring_and_deployment_path.py` outlines production deployment, monitoring, retraining triggers, limitations, and governance controls without claiming live integrations.
# 6. `08_snf_payroll_approval_case_studies.py` highlights the two highest-value SNF case studies: overtime/double-shift staffing pressure and premium pay or shift differential mismatch.

# %% [markdown]
# ## Quick Pipeline Check
#
# This lightweight cell confirms that the synthetic SNF pipeline can generate the same core outputs used by the notebooks.

# %%
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import run_pipeline

results = run_pipeline(
    PayrollConfig(employee_count=120, pay_periods=12, review_budgets=(5, 10)),
)
[
    results.payroll.height,
    results.scored.height,
    results.metrics.height,
    results.analyst_review_queue.height,
    results.facility_approval_summary.height,
]

# %% [markdown]
# ## What This Proves
#
# The repository now has a navigable notebook story from SNF payroll approval framing through production readiness, with all examples synthetic and all outputs framed as pre-approval exception prioritization.

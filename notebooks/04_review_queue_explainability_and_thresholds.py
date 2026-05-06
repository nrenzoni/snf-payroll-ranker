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
# # 04 Review Queue, Explainability, And Thresholds
#
# **Executive takeaway:** The review queue turns model outputs into analyst-readable triage: risk category, reason codes, expected versus actual pay context, dollars at risk, and review-safe explanations for synthetic payroll records.

# %%
import polars as pl

from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.explainability import sample_review_language
from payroll_anomaly_ranking.pipeline import run_pipeline
from payroll_anomaly_ranking.presentation import compact_case_cards

# %%
config = PayrollConfig(employee_count=650, pay_periods=26, review_budgets=(10, 25, 50))
results = run_pipeline(config)
queue = results["review_queue"]
scored = results["scored"]

# %% [markdown]
# ## Review-Safe Language
#
# Queue records are prioritized for payroll review because they differ from expected history, peer context, deterministic payroll rules, or dollar-impact signals. They are not confirmed misconduct findings and should not be treated as automated adverse decisions.

# %%
sample_review_language()

# %% [markdown]
# ## Analyst-Readable Review Queue
#
# The fields below are intended for triage: rank, cycle, risk category, reason codes, expected gross pay, actual gross pay, peer context, dollars at risk, and an explanation.

# %%
queue.select(
    "rank",
    "employee_id",
    "pay_period_index",
    "risk_category",
    "primary_reason",
    "secondary_reason",
    "expected_gross_pay",
    "gross_pay",
    "difference_from_expected",
    "peer_context",
    "dollars_at_risk",
    "rule_reason_codes",
    "explanation",
).head(15)

# %% [markdown]
# ## Compact Case Cards
#
# Case cards summarize the evidence an analyst needs before deciding whether the record is an expected exception, a correction, or an item requiring escalation.

# %%
compact_case_cards(queue, limit=5)

# %% [markdown]
# ## Thresholds And Review Budgets
#
# Teams can choose a fixed top-K review budget per pay period or a score threshold. Top-K gives predictable workload; thresholds adapt to risk concentration but can produce variable queue sizes.

# %%
budget_sizes = scored.group_by("pay_period_index").agg(
    (pl.col("pay_period_rank") <= 10).sum().alias("top_10_queue"),
    (pl.col("pay_period_rank") <= 25).sum().alias("top_25_queue"),
    (pl.col("final_anomaly_score") >= 0.65).sum().alias("score_threshold_065_queue"),
).sort("pay_period_index")
budget_sizes.head(12)

# %%
budget_sizes.select(
    pl.mean("top_10_queue").alias("expected_top_10_per_period"),
    pl.mean("top_25_queue").alias("expected_top_25_per_period"),
    pl.mean("score_threshold_065_queue").alias("expected_threshold_065_per_period"),
)

# %% [markdown]
# ## Risk Categories And Next Actions
#
# | Risk category | Typical analyst action |
# | --- | --- |
# | High | Review before finalization, compare source payroll inputs, and escalate if the reason cannot be reconciled. |
# | Medium | Review when capacity allows, confirm business context such as bonus, retro pay, overtime approval, or lifecycle event. |
# | Low | Monitor trends, sample for quality assurance, or leave unreviewed if capacity is constrained. |

# %%
queue.group_by("risk_category").agg(pl.len().alias("records"), pl.sum("dollars_at_risk").alias("dollars_at_risk")).sort("risk_category")

# %% [markdown]
# ## Payroll Analyst Operating Model
#
# 1. Triage the top-K or threshold queue for each payroll cycle.
# 2. Review the explanation, reason codes, source payroll fields, and supporting HRIS or timekeeping extracts outside this demo.
# 3. Approve known exceptions such as planned bonus, retro adjustment, or authorized overtime.
# 4. Escalate unreconciled high-risk records to payroll leadership or internal controls before finalization.
# 5. Capture review outcome, reason, analyst notes, and final disposition for future calibration.

# %% [markdown]
# ## Conceptual Feedback Capture
#
# A production case-management workflow could capture analyst disposition fields such as `reviewed_at`, `reviewed_by_role`, `disposition`, `confirmed_exception_type`, `approved_business_reason`, `amount_corrected`, and `notes_category`. This notebook does not implement case management or live integrations; it describes the feedback needed to recalibrate thresholds and future supervised models.

# %% [markdown]
# ## What This Proves
#
# The scoring output can be translated into a practical, review-safe payroll queue with explanations, compact case cards, risk categories, workload controls, and a clear analyst operating model.

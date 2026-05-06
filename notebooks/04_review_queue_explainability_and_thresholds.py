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
# **Executive takeaway:** The analyst-safe review queue turns model outputs into triage: risk category, reason codes, expected versus actual pay context, estimated dollars at risk, and review-safe explanations without synthetic evaluation labels.

# %%
import polars as pl

from payroll_anomaly_ranking.columns import AggregateCol, PayrollCol, ReviewCol, RuleCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.explainability import sample_review_language
from payroll_anomaly_ranking.pipeline import run_pipeline
from payroll_anomaly_ranking.presentation import compact_case_cards

# %%
config = PayrollConfig(employee_count=650, pay_periods=26, review_budgets=(10, 25, 50))
results = run_pipeline(config)
queue = results["analyst_review_queue"]
evaluation_queue = results["evaluation_labeled_review_queue"]
scored = results["scored"]

# %% [markdown]
# ## Review-Safe Language
#
# Queue records are prioritized for payroll review because they differ from expected history, peer context, deterministic payroll rules, missing-deduction checks, or estimated-exposure signals. They are not confirmed misconduct findings and should not be treated as automated adverse decisions.

# %%
sample_review_language()

# %% [markdown]
# ## Analyst-Readable Review Queue
#
# The fields below are intended for triage: rank, cycle, risk category, reason codes, expected gross pay, actual gross pay, peer context, dollars at risk, and an explanation.

# %%
queue.select(
    ReviewCol.RANK,
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    ReviewCol.RISK_CATEGORY,
    ReviewCol.PRIMARY_REASON,
    ReviewCol.SECONDARY_REASON,
    ReviewCol.EXPECTED_GROSS_PAY,
    PayrollCol.GROSS_PAY,
    ReviewCol.DIFFERENCE_FROM_EXPECTED,
    ReviewCol.PEER_CONTEXT,
    ReviewCol.DOLLARS_AT_RISK,
    RuleCol.REASON_CODES,
    ReviewCol.EXPLANATION,
).head(15)

# %% [markdown]
# ## Evaluation-Labeled Queue
#
# Synthetic labels and injected dollar impacts are preserved only in the separate evaluation-labeled queue for metrics and category analysis. They are intentionally absent from the analyst-safe queue above.

# %%
evaluation_queue.select(
    ReviewCol.RANK,
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    ReviewCol.DOLLARS_AT_RISK,
    PayrollCol.IS_ANOMALY,
    PayrollCol.ANOMALY_CATEGORY,
    PayrollCol.ANOMALY_DOLLARS,
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
budget_sizes = scored.group_by(PayrollCol.PAY_PERIOD_INDEX).agg(
    (pl.col(ScoreCol.PAY_PERIOD_RANK) <= 10).sum().alias(AggregateCol.TOP_10_QUEUE),
    (pl.col(ScoreCol.PAY_PERIOD_RANK) <= 25).sum().alias(AggregateCol.TOP_25_QUEUE),
    (pl.col(ScoreCol.FINAL_ANOMALY_SCORE) >= 0.65).sum().alias(AggregateCol.SCORE_THRESHOLD_065_QUEUE),
).sort(PayrollCol.PAY_PERIOD_INDEX)
budget_sizes.head(12)

# %%
budget_sizes.select(
    pl.mean(AggregateCol.TOP_10_QUEUE).alias(AggregateCol.EXPECTED_TOP_10_PER_PERIOD),
    pl.mean(AggregateCol.TOP_25_QUEUE).alias(AggregateCol.EXPECTED_TOP_25_PER_PERIOD),
    pl.mean(AggregateCol.SCORE_THRESHOLD_065_QUEUE).alias(AggregateCol.EXPECTED_THRESHOLD_065_PER_PERIOD),
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
queue.group_by(ReviewCol.RISK_CATEGORY).agg(pl.len().alias(AggregateCol.RECORDS), pl.sum(ReviewCol.DOLLARS_AT_RISK).alias(ReviewCol.DOLLARS_AT_RISK)).sort(ReviewCol.RISK_CATEGORY)

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
# The scoring output can be translated into a practical, review-safe payroll queue with explanations, compact case cards, risk categories, workload controls, and a clear analyst operating model while synthetic labels remain isolated for evaluation.

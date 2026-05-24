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
# # SNF Approval Queue, Explainability, And Thresholds
#
# **Executive takeaway:** The administrator-safe approval queue turns model and rule signals into a short weekly checklist: what to review, which source to check, and what action to take before payroll approval.

# %%
from common.display import setup_notebook_html
from common.plots import (
    aes,
    geom_bar,
    ggplot,
    labs,
    rotated_x_labels,
    theme_minimal,
)

from payroll_anomaly_ranking.columns import PayrollCol, ReviewCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import run_pipeline
from payroll_anomaly_ranking.presentation import compact_case_cards

setup_notebook_html()

results = run_pipeline(
    PayrollConfig(employee_count=160, pay_periods=12, review_budgets=(10, 25)),
)
queue = results.analyst_review_queue

# %% [markdown]
# ## Administrator-Safe Approval Queue
#
# The queue excludes synthetic evaluation labels and uses review-safe wording. It does not claim confirmed misconduct, fraud, or payroll error.

# %%
queue.select(
    [
        ReviewCol.RANK,
        PayrollCol.FACILITY_ID,
        PayrollCol.UNIT,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_DATE,
        PayrollCol.SHIFT_TYPE,
        ReviewCol.APPROVAL_RISK_CATEGORY,
        ReviewCol.RECOMMENDED_ACTION,
        ReviewCol.SOURCE_TO_CHECK,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.DOLLARS_AT_RISK,
    ],
).head(15)

# %% [markdown]
# ## Compact Case Cards
#
# Case cards are designed for administrators, business office managers, DON/scheduling partners, or regional operators who need concise evidence before payroll approval.

# %%
compact_case_cards(queue, limit=5)

# %% [markdown]
# ## Facility Approval Summary
#
# Facility summaries let leaders see where the queue is concentrated before drilling into individual shifts.

# %%
results.facility_approval_summary.sort("estimated_exposure", descending=True)

# %%
summary = results.facility_approval_summary
(
    ggplot(summary, aes(PayrollCol.FACILITY_ID, "queue_count"))
    + geom_bar(stat="identity", fill="#c46f38")
    + labs(
        title="Latest-period approval queue count by facility",
        x="Facility",
        y="Queued records",
    )
    + theme_minimal()
    + rotated_x_labels()
)

# %% [markdown]
# ## Weekly Operating Model
#
# 1. Review high-priority records before approval.
# 2. Check the named source: schedule, timeclock, pay code, pay policy, facility assignment, or employee lifecycle.
# 3. Approve known staffing exceptions when supported.
# 4. Escalate questionable payroll-code or lifecycle records.
# 5. Capture feedback for future calibration.

# %% [markdown]
# ## What This Proves
#
# The automated queue translates technical signals into administrator actions while preserving privacy and avoiding confirmed-error language.

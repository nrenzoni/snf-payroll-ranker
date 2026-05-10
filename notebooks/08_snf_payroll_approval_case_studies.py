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
# # SNF Payroll Approval Case Studies
#
# **Executive takeaway:** Automated shift-level approval ranking helps SNF administrator teams focus weekly payroll review on context-rich exceptions instead of chasing broad manual thresholds on gross pay, total hours, overtime, or premium dollars.

# %%
import polars as pl
from common.execution import notebook_fast_mode

from payroll_anomaly_ranking.columns import (
    PayrollCol,
    ReviewCol,
)
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import PipelineIncludeConfig, run_pipeline
from payroll_anomaly_ranking.scenarios import diagnostic_scenario_presets

config = PayrollConfig(employee_count=140, pay_periods=12, review_budgets=(10, 25))
NOTEBOOK_FAST = notebook_fast_mode()
active_pipeline_include = (
    PipelineIncludeConfig(
        validation=False,
        aggregations=False,
        evaluation=True,
        backtest=False,
        rolling_origin=False,
        review_queues=True,
        leakage_checks=False,
    )
    if NOTEBOOK_FAST
    else PipelineIncludeConfig.all()
)


def _case_study_run(name: str):
    scenario = diagnostic_scenario_presets((name,))[name]
    return run_pipeline(
        config,
        scenario=scenario,
        include=active_pipeline_include,
    )


# %% [markdown]
# ## Case Study 1: Overtime, Double Shifts, And Staffing Pressure
#
# Manual overtime thresholds can overflag legitimate staffing pressure and still miss high-risk combinations such as double shifts, short rest gaps, missed punches, and paid-vs-scheduled variance. The automated queue ranks the shifts most worth checking before payroll approval.

# %%
overtime_results = _case_study_run("overtime-staffing-pressure")
overtime_results.analyst_review_queue.select(
    [
        ReviewCol.RANK,
        PayrollCol.FACILITY_ID,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_DATE,
        PayrollCol.SHIFT_TYPE,
        PayrollCol.SCHEDULED_HOURS,
        PayrollCol.PAID_HOURS,
        PayrollCol.OVERTIME_HOURS,
        ReviewCol.RECOMMENDED_ACTION,
        ReviewCol.SOURCE_TO_CHECK,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.DOLLARS_AT_RISK,
    ],
).head(10)

# %%
overtime_results.facility_approval_summary.sort(
    "estimated_exposure",
    descending=True,
).head(10)

# %% [markdown]
# ## Case Study 2: Premium Pay And Shift Differential Mismatch
#
# Gross-pay and premium-dollar thresholds are blunt because many evening, night, weekend, and high-pressure shifts legitimately include premium pay. The automated ranking checks whether the premium is supported by shift, weekend, pay-code, and timeclock context.

# %%
premium_results = _case_study_run("premium-mismatch")
premium_results.analyst_review_queue.select(
    [
        ReviewCol.RANK,
        PayrollCol.FACILITY_ID,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_DATE,
        PayrollCol.SHIFT_TYPE,
        PayrollCol.PREMIUM_PAY,
        ReviewCol.RECOMMENDED_ACTION,
        ReviewCol.SOURCE_TO_CHECK,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.PREMIUM_CONTEXT,
        ReviewCol.DOLLARS_AT_RISK,
    ],
).head(10)

# %%
premium_results.metrics.with_columns(
    pl.lit("automated_hybrid_ranking").alias("method"),
)

# %% [markdown]
# ## Manual Threshold Comparison
#
# The threshold baseline table shows how static field thresholds behave relative to automated ranking. In production, these thresholds would be configurable by each client, but the demonstration keeps them synthetic and reproducible.

# %%
premium_results.model_comparison

# %% [markdown]
# ## What This Proves
#
# The two highest-value initial SNF scenarios are operationally understandable to administrator teams: overtime/double-shift pressure and premium mismatch. Both require schedule, timeclock, facility, role, shift, and pay-code context that static threshold rules do not capture reliably.

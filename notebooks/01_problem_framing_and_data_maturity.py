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
# # SNF Payroll Approval: Problem Framing And Data Maturity
#
# **Executive takeaway:** SNF administrator teams approve payroll under time pressure. A useful automated flagger must prioritize shift-level exceptions using schedule, timeclock, role, facility, and premium-pay context rather than broad gross/net thresholds.

# %%
import polars as pl
from common.display import setup_notebook_html
from common.plots import (
    aes,
    geom_bar,
    ggplot,
    labs,
    rotated_x_labels,
    theme_minimal,
)

from payroll_anomaly_ranking.columns import PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import run_pipeline
from payroll_anomaly_ranking.presentation import (
    data_quality_summary,
    synthetic_schema_dictionary,
)
from payroll_anomaly_ranking.validation import validate_payroll

setup_notebook_html()

results = run_pipeline(
    PayrollConfig(employee_count=160, pay_periods=12, review_budgets=(10, 25)),
)
payroll = results.payroll
validation = validate_payroll(payroll)

# %% [markdown]
# ## Privacy And Governance
#
# All records are synthetic. The data contains no real employees, residents, payroll files, tax data, bank data, HR comments, company data, or live integrations. Synthetic anomaly labels are evaluation-only and are excluded from administrator-safe outputs.

# %%
synthetic_schema_dictionary()

# %% [markdown]
# ## SNF Shift-Level Data Maturity
#
# The generator creates facilities, units, roles, shift dates, shift types, schedule hours, worked hours, pay codes, premium pay, timeclock quality fields, approval status, and derived pay-period/facility rollups.

# %%
data_quality_summary(payroll, validation.warnings)

# %%
facility_volume = (
    payroll.group_by(PayrollCol.FACILITY_ID)
    .agg(
        pl.len().alias("shift_lines"),
        pl.sum(PayrollCol.GROSS_PAY).alias("gross_pay"),
        pl.sum(PayrollCol.OVERTIME_HOURS).alias("overtime_hours"),
    )
    .sort(PayrollCol.FACILITY_ID)
)
facility_volume

# %%
(
    ggplot(facility_volume, aes(PayrollCol.FACILITY_ID, "shift_lines"))
    + geom_bar(stat="identity", fill="#396b6f")
    + labs(
        title="Synthetic SNF shift-line volume by facility",
        x="Facility",
        y="Shift-level payroll lines",
    )
    + theme_minimal()
    + rotated_x_labels()
)

# %% [markdown]
# ## Approval Exception Taxonomy
#
# Initial implemented case-study scenarios focus on overtime/double-shift staffing pressure and premium pay or shift differential mismatch. Future scenario families are documented for agency/float labor, census/acuity, credential/license mismatch, PBJ category mismatch, meal premiums, lifecycle events, retro/rate corrections, union policy variation, new-client bootstrap, and payroll close adjustments.

# %%
payroll.group_by(PayrollCol.ANOMALY_CATEGORY).agg(
    pl.len().alias("records"),
    pl.sum(PayrollCol.IS_ANOMALY).alias("synthetic_anomalies"),
    pl.sum(PayrollCol.ANOMALY_DOLLARS).alias("synthetic_anomaly_dollars"),
).sort(PayrollCol.ANOMALY_CATEGORY)

# %% [markdown]
# ## What This Proves
#
# The synthetic dataset has enough SNF-specific context to support weekly pre-approval triage: facility, unit, role, shift, schedule, timeclock, pay-code, premium, and lifecycle fields are available without exposing real payroll data.

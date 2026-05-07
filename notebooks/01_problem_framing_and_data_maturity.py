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
# # 01 Problem Framing And Data Maturity
#
# **Executive takeaway:** This notebook frames payroll anomaly ranking as a pre-finalization review prioritization workflow. It uses only synthetic payroll records to show whether the data is complete, governed, and mature enough for analyst triage.

# %% [markdown]
# ## Privacy And Governance
#
# All demonstrated records are synthetic. The repository includes no real employee identifiers, salaries, tax IDs, bank details, HR comments, company data, or live payroll, HRIS, timekeeping, banking, tax, vendor, or case-management integrations.
#
# The injected labels support evaluation of the synthetic demonstration. They are not real investigation outcomes and are not used to decide whether an employee or record indicates wrongdoing.

# %% [markdown]
# ## Business Framing
#
# Payroll teams usually have limited time between payroll calculation and final approval. A ranking workflow helps focus review capacity on records with the strongest combination of rule flags, history changes, peer differences, statistical outliers, model scores, and estimated dollars at risk.
#
# The goal is to reduce missed costly exceptions before payroll is finalized. The output is a prioritized review queue, not a misconduct determination, disciplinary recommendation, or automated payroll stop.

# %% [markdown]
# ## Payroll Anomaly Taxonomy
#
# | Category | Example payroll review question |
# | --- | --- |
# | Duplicate payments | Does the same employee-period look paid twice? |
# | Overtime spikes | Are overtime hours unusually high for this employee or peer group? |
# | Pay after termination | Was pay issued after the synthetic termination date? |
# | Gross pay spikes | Did gross pay jump sharply versus prior history? |
# | Incorrect pay rates | Did a pay rate change beyond expected bounds? |
# | Missing deductions | Are deductions zero or missing when expected? |
# | Negative net pay | Did deductions exceed gross pay? |
# | Retro outliers | Is retroactive pay unusually large? |
# | Department payroll spikes | Did a department-period total move materially? |
# | Unusual new employee payments | Is a new employee receiving unusually large pay? |

# %%
import polars as pl
from lets_plot import LetsPlot

from payroll_anomaly_ranking.charts import (
    department_heatmap_data,
    overtime_distribution_chart,
    pay_distribution_chart,
    payroll_trend_chart,
)
from payroll_anomaly_ranking.columns import AggregateCol, PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import run_pipeline
from payroll_anomaly_ranking.presentation import (
    data_quality_summary,
    synthetic_schema_dictionary,
)
from payroll_anomaly_ranking.validation import validate_payroll

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=650, pay_periods=26)
results = run_pipeline(config)
payroll = results.payroll

# %% [markdown]
# ## Schema And Data Dictionary
#
# The fields below describe the synthetic employee-pay-period records, their business meaning, privacy sensitivity, and expected validation behavior.

# %%
synthetic_schema_dictionary()

# %% [markdown]
# ## Validation: Hard Failures Versus Exception Warnings
#
# Hard failures are pipeline-stopping data problems, such as missing required columns or impossible lifecycle dates. Warning-level checks are payroll exceptions that may be legitimate but should be available for analyst review.

# %%
hard_failure_demo = validate_payroll(payroll.drop(PayrollCol.EMPLOYEE_ID))
hard_failure_demo.failures

# %%
results.validation_warnings

# %% [markdown]
# ## Data Quality Summary
#
# The summary checks record volume, cycle coverage, employee counts, missing values, lifecycle consistency, and warning counts.

# %%
data_quality_summary(payroll, results.validation_warnings)

# %%
payroll.select(
    pl.min(PayrollCol.GROSS_PAY).alias(AggregateCol.MIN_GROSS_PAY),
    pl.col(PayrollCol.GROSS_PAY).quantile(0.25).alias(AggregateCol.GROSS_Q25),
    pl.median(PayrollCol.GROSS_PAY).alias(AggregateCol.GROSS_MEDIAN),
    pl.col(PayrollCol.GROSS_PAY).quantile(0.75).alias(AggregateCol.GROSS_Q75),
    pl.max(PayrollCol.GROSS_PAY).alias(AggregateCol.MAX_GROSS_PAY),
    pl.mean(PayrollCol.OVERTIME_HOURS).alias(AggregateCol.MEAN_OVERTIME_HOURS),
    pl.max(PayrollCol.OVERTIME_HOURS).alias(AggregateCol.MAX_OVERTIME_HOURS),
)

# %% [markdown]
# ## Data Maturity Visuals And Tables
#
# These views show payroll trend, gross pay distribution, overtime distribution, and department-period payroll concentration using synthetic data.

# %%
payroll_trend_chart(payroll)

# %%
pay_distribution_chart(payroll)

# %%
overtime_distribution_chart(payroll)

# %%
department_heatmap_data(payroll).pivot(
    index=PayrollCol.PAY_PERIOD_INDEX,
    on=PayrollCol.DEPARTMENT,
    values=AggregateCol.DEPARTMENT_GROSS_PAY,
    aggregate_function="sum",
).sort(PayrollCol.PAY_PERIOD_INDEX).head(10)

# %% [markdown]
# ## What This Proves
#
# The synthetic dataset is privacy-safe, shaped like employee-pay-period payroll data, and covered by validation outputs that separate hard data issues from review-worthy payroll exceptions. The data is mature enough to support ranking demonstrations without using real or sensitive payroll data.

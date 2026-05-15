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
# # SNF Feature Engineering And Threshold Baselines
#
# **Executive takeaway:** The automated flagger uses leakage-safe, facility-normalized SNF features so administrators do not have to rely only on manually configured gross pay, total hours, overtime, or premium-dollar thresholds.

# %%
from common.display import setup_notebook_html
from common.plots import aes, geom_point, ggplot, labs, theme_minimal

from payroll_anomaly_ranking.columns import FeatureCol, PayrollCol, RuleCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.features import build_features
from payroll_anomaly_ranking.pipeline import run_pipeline
from payroll_anomaly_ranking.rules import add_rule_flags

setup_notebook_html()

config = PayrollConfig(employee_count=160, pay_periods=12, review_budgets=(10, 25))
results = run_pipeline(config)
featured = add_rule_flags(build_features(results.payroll))

# %% [markdown]
# ## Leakage-Safe SNF Features
#
# Historical features use prior shifts and prior pay periods. Peer features normalize within facility, role, shift type, unit, and pay-code context. Synthetic labels remain evaluation-only and are not used as model features, threshold baselines, exposure inputs, or administrator queue fields.

# %%
featured.select(
    [
        PayrollCol.EMPLOYEE_ID,
        PayrollCol.FACILITY_ID,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_DATE,
        PayrollCol.SHIFT_TYPE,
        PayrollCol.SCHEDULED_HOURS,
        PayrollCol.PAID_HOURS,
        PayrollCol.OVERTIME_HOURS,
        PayrollCol.PREMIUM_PAY,
        FeatureCol.OVERTIME_PER_SCHEDULED_HOUR,
        FeatureCol.PAID_MINUS_SCHEDULED_HOURS,
        FeatureCol.PREMIUM_PAY_SHARE,
        FeatureCol.GROSS_TO_EXPECTED_SHIFT_PAY,
        FeatureCol.PREMIUM_ELIGIBILITY_MISMATCH,
        FeatureCol.REST_GAP_RISK,
        RuleCol.REASON_CODES,
    ],
).head(12)

# %% [markdown]
# ## Manual Threshold Baselines
#
# These threshold flags approximate what many production workflows do today: configure cutoffs on individual fields. The automated model keeps those baselines for comparison but adds SNF context.

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
        ScoreCol.THRESHOLD_GROSS_PAY_FLAG,
        ScoreCol.THRESHOLD_TOTAL_HOURS_FLAG,
        ScoreCol.THRESHOLD_OVERTIME_HOURS_FLAG,
        ScoreCol.THRESHOLD_PREMIUM_DOLLARS_FLAG,
        ScoreCol.THRESHOLD_PAID_VS_SCHEDULED_FLAG,
        ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE,
    ],
).sort(ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE, descending=True).head(12)

# %%
plot_data = results.scored.select(
    PayrollCol.OVERTIME_HOURS,
    PayrollCol.PREMIUM_PAY,
    ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE,
    PayrollCol.IS_ANOMALY,
)
(
    ggplot(plot_data, aes(PayrollCol.OVERTIME_HOURS, PayrollCol.PREMIUM_PAY))
    + geom_point(aes(color=ScoreCol.FINAL_APPROVAL_EXCEPTION_SCORE), alpha=0.55)
    + labs(
        title="Automated approval score combines overtime and premium context",
        x="Overtime hours",
        y="Premium dollars",
        color="Approval score",
    )
    + theme_minimal()
)

# %% [markdown]
# ## What This Proves
#
# Stationary ratios, premium eligibility checks, rest-gap context, and facility-normalized peer comparisons provide more administrator-relevant signal than one-field threshold rules.

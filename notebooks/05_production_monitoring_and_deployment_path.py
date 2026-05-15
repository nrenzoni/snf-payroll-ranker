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
# # SNF Production Monitoring And Deployment Path
#
# **Executive takeaway:** The repository demonstrates the analytical core of an SNF payroll approval assistant. A production deployment would add governed extracts, scheduling, access controls, review feedback, monitoring, and retraining around that core.

# %%
import polars as pl
from common.display import setup_notebook_html

from payroll_anomaly_ranking.columns import PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import run_pipeline

setup_notebook_html()

results = run_pipeline(
    PayrollConfig(employee_count=140, pay_periods=12, review_budgets=(10, 25)),
)

# %% [markdown]
# ## Intended Production Flow
#
# | Stage | Inputs | Purpose |
# |---|---|---|
# | Source extracts | Payroll, schedule, timeclock, HR lifecycle, facility reference, pay policy | Build governed weekly approval data |
# | Validation | Schema, referential, policy, lifecycle, rollup checks | Fail early on hard data issues and warn on approval exceptions |
# | Feature generation | Prior shifts, facility/role/shift peers, timeclock, premium eligibility | Create leakage-safe SNF approval signals |
# | Scoring | Rules, robust stats, ML, exposure, uncertainty | Rank records for weekly approval review |
# | Administrator review | Approval queue, facility summaries, case cards | Confirm, approve, or escalate exceptions |
# | Feedback and monitoring | Review outcomes, drift, queue yield | Calibrate thresholds, weights, and future supervised layers |

# %% [markdown]
# ## Monitoring Metrics
#
# Production monitoring should track exception count per payroll cycle, approval queue yield, confirmed exception rate from feedback, estimated exposure flagged and confirmed, feature drift, score drift, alert concentration by facility/unit/role/shift, latency, data freshness, validation failures, and threshold-baseline drift.

# %%
monitoring_snapshot = pl.DataFrame(
    [
        {
            "metric": "latest_facilities",
            "value": results.payroll.select(pl.n_unique(PayrollCol.FACILITY_ID)).item(),
        },
        {
            "metric": "latest_queue_records",
            "value": results.analyst_review_queue.height,
        },
        {
            "metric": "facility_summary_rows",
            "value": results.facility_approval_summary.height,
        },
        {"metric": "validation_warnings", "value": results.validation_warnings.height},
        {"metric": "synthetic_shift_lines", "value": results.payroll.height},
    ],
)
monitoring_snapshot

# %% [markdown]
# ## Limitations And Future Scenarios
#
# This demonstration does not include live integrations, access control, dashboards, alert routing, real review feedback, legal compliance advice, resident data, or real payroll data. Future scenario families include agency/float labor, census/acuity, credential/license mismatch, PBJ category mismatch, meal premiums, lifecycle events, retro/rate corrections, union policy variation, new-client bootstrap, and payroll close adjustment concentration.

# %% [markdown]
# ## What This Proves
#
# The SNF approval assistant has a deployable analytical shape: governed extracts, validation, leakage-safe features, automated ranking, administrator review, feedback, monitoring, and retraining.

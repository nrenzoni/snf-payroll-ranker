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
# # Employee-Pay-Cycle Payroll Anomaly Ranking

# %% [markdown]
# ## 0. Executive Summary
#
# This project compares rule-based, classification, regression, expected-value,
# and learning-to-rank approaches for prioritizing SNF payroll records for review.
#
#
# **validate TODO**:
# Main finding:
# Learning-to-rank produced the best top-of-queue severity ordering at tight
# review budgets, while the expected-value model was strongest for calibrated
# dollar recovery. The recommended production design is a hybrid: LTR for queue
# ordering, calibrated probability/impact estimates for reviewer context, and
# rules as hard guardrails.

# %% [markdown]
# ## 1. Problem Framing
#
# Explain why facility-period queues, temporal validation, and review-budget trade-offs define the operational problem more accurately than isolated record scoring.
#
# - unit = payroll record
# - group = facility × payroll cycle
# - business constraint = reviewers can only inspect top K%
# - objective = maximize review utility

# %% [markdown]
# ## 2. Data-Generating Process
#
# This section will describe how synthetic employee-pay-cycle payroll records are generated, how supporting lower-level payroll context is retained, and how scenario controls shape the evaluation worlds.
# It will also document the privacy-safe assumptions behind the synthetic dataset and the limits of synthetic evidence.
#
# Show:
#
# - facility hierarchy,
# - employee generation,
# - payroll cycles,
# - latent true issues,
# - observed historical labels,
# - review bias.

# %%
import polars as pl
from common.plots import (
    LetsPlot,
    aes,
    geom_bar,
    geom_density,
    geom_histogram,
    geom_point,
    geom_tile,
    ggplot,
    labs,
    rotated_x_labels,
    theme_minimal,
)
from graphviz import Digraph

from payroll_anomaly_ranking.columns import PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import generate_employee_pay_cycles
from payroll_anomaly_ranking.features import build_employee_cycle_features

# %%
LetsPlot.setup_html()

# %%
sim_config = PayrollConfig(
    facility_count=75,
    pay_periods=36,
)

data = generate_employee_pay_cycles(sim_config)


# %%
dgp = Digraph("employee_cycle_dgp")
dgp.attr(rankdir="LR", nodesep="0.35", ranksep="0.6", bgcolor="transparent")
dgp.attr(
    "node",
    shape="rect",
    style="rounded,filled",
    fillcolor="#F7F9FC",
    color="#5B6B83",
    fontname="Helvetica",
)
dgp.attr("edge", color="#5B6B83", fontname="Helvetica")

dgp.node(
    "facilities",
    "Facility hierarchy\nregion, size tier, payroll maturity, staffing pressure",
)
dgp.node(
    "employees",
    "Employee generation\nrole, license, tenure, base rate, home facility",
)
dgp.node(
    "schedules",
    "Payroll cycles and shifts\nschedules, timeclock, hours, premiums, edits",
)
dgp.node(
    "latent",
    "Latent true issues\npolicy mismatches, overtime pressure, lifecycle exceptions",
)
dgp.node(
    "observed",
    "Observed history\nreviewed corrections are a biased subset of true issues",
)
dgp.node(
    "cycles",
    "Employee-pay-cycle records\ncycle-level payroll plus supporting lower-level context",
)

dgp.edge("facilities", "employees", label="staffing context")
dgp.edge("facilities", "schedules", label="facility constraints")
dgp.edge("employees", "schedules", label="assign work")
dgp.edge("schedules", "latent", label="generate payable events")
dgp.edge("latent", "observed", label="selective review")
dgp.edge("schedules", "cycles", label="roll up")
dgp.edge("latent", "cycles", label="evaluation labels")
dgp.edge("observed", "cycles", label="historical signal")

dgp


# %% [markdown]
# The active generator creates lower-level schedule, timeclock, and payroll-line
# context first, injects latent anomalies into those records, then rolls them up
# into employee-pay-cycle records for modeling while retaining the supporting
# shift-level evidence for diagnostics and reviewer context.

# %%
data.payroll.select(
    PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.FACILITY_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    PayrollCol.TOTAL_GROSS_PAY,
    PayrollCol.TOTAL_OVERTIME_HOURS,
).head()

# %% [markdown]
# ## 3. Simulation Sanity Checks
#
# These checks confirm that the synthetic employee-pay-cycle world is large
# enough for evaluation, that anomaly prevalence is non-degenerate, and that the
# historical observed-correction signal is a biased subset of the latent truth
# rather than a duplicate of the evaluation labels.

# %%
sanity_overview = pl.DataFrame(
    {
        "metric": [
            "employee-pay-cycle rows",
            "supporting shift rows",
            "facilities",
            "employees",
            "pay periods",
            "true issue rate",
            "observed correction rate",
            "total anomaly dollars",
            "observed correction dollars",
        ],
        "value": [
            f"{data.payroll.height:,}",
            f"{data.supporting_payroll.height:,}",
            f"{data.payroll.select(pl.col(PayrollCol.FACILITY_ID).n_unique()).item():,}",
            f"{data.payroll.select(pl.col(PayrollCol.EMPLOYEE_ID).n_unique()).item():,}",
            f"{data.payroll.select(pl.col(PayrollCol.PAY_PERIOD_INDEX).n_unique()).item():,}",
            f"{100 * data.payroll.select(pl.col(PayrollCol.IS_ANOMALY).mean()).item():.2f}%",
            f"{100 * data.payroll.select(pl.col(PayrollCol.OBSERVED_CORRECTION).mean()).item():.2f}%",
            f"${data.payroll.select(pl.sum(PayrollCol.ANOMALY_DOLLARS)).item():,.0f}",
            f"${data.payroll.select(pl.sum(PayrollCol.OBSERVED_CORRECTION_DOLLARS)).item():,.0f}",
        ],
    },
)

sanity_overview


# %%
facility_issue_rates = (
    data.payroll.group_by([PayrollCol.FACILITY_ID, PayrollCol.FACILITY_NAME])
    .agg(
        pl.len().alias("employee_cycles"),
        pl.mean(PayrollCol.IS_ANOMALY).alias("true_issue_rate"),
        pl.mean(PayrollCol.OBSERVED_CORRECTION).alias("observed_correction_rate"),
        pl.sum(PayrollCol.ANOMALY_DOLLARS).alias("anomaly_dollars"),
    )
    .sort("employee_cycles", descending=True)
)

facility_issue_rates.head(10)

# %%
top_facility_issue_rates = facility_issue_rates.head(20).with_columns(
    (100 * pl.col("true_issue_rate")).round(2).alias("true_issue_rate_pct"),
)

(
    ggplot(
        top_facility_issue_rates,
        aes(x=PayrollCol.FACILITY_ID, y="true_issue_rate_pct"),
    )
    + geom_bar(stat="identity", fill="#4C78A8")
    + labs(
        title="True issue rate by facility",
        x="Facility",
        y="True issue rate (%)",
    )
    + theme_minimal()
    + rotated_x_labels()
)


# %%
overtime_by_role = data.payroll.select(
    PayrollCol.ROLE,
    PayrollCol.TOTAL_OVERTIME_HOURS,
).filter(
    pl.col(PayrollCol.TOTAL_OVERTIME_HOURS) > 0,
)

(
    ggplot(
        overtime_by_role,
        aes(x=PayrollCol.TOTAL_OVERTIME_HOURS, color=PayrollCol.ROLE),
    )
    + geom_density(size=1.0)
    + labs(
        title="Overtime distribution by role",
        x="Total overtime hours in employee-pay-cycle",
        y="Density",
        color="Role",
    )
    + theme_minimal()
)


# %%
pay_rate_by_role = data.payroll.select(
    PayrollCol.ROLE,
    PayrollCol.BASE_PAY_RATE,
)

(
    ggplot(
        pay_rate_by_role,
        aes(x=PayrollCol.BASE_PAY_RATE, color=PayrollCol.ROLE),
    )
    + geom_density(size=1.0)
    + labs(
        title="Base pay-rate distribution by role",
        x="Base hourly rate",
        y="Density",
        color="Role",
    )
    + theme_minimal()
)


# %%
true_vs_observed_rates = facility_issue_rates.select(
    PayrollCol.FACILITY_ID,
    (100 * pl.col("true_issue_rate")).round(2).alias("true_issue_rate_pct"),
    (100 * pl.col("observed_correction_rate"))
    .round(2)
    .alias("observed_correction_rate_pct"),
)

(
    ggplot(
        true_vs_observed_rates,
        aes(x="true_issue_rate_pct", y="observed_correction_rate_pct"),
    )
    + geom_point(color="#E45756", alpha=0.8)
    # + geom_abline(slope=1, intercept=0, linetype="dashed", color="darkgray")
    + labs(
        title="True issue rate vs observed correction rate by facility",
        x="True issue rate (%)",
        y="Observed correction rate (%)",
    )
    + theme_minimal()
)


# %%
facility_cycle_positives = (
    data.payroll.group_by([PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX])
    .agg(pl.sum(PayrollCol.IS_ANOMALY).alias("positive_cycles"))
    .with_columns(pl.col("positive_cycles").clip(0, 8).alias("positive_cycles_capped"))
)

(
    ggplot(
        facility_cycle_positives,
        aes(
            x=PayrollCol.PAY_PERIOD_INDEX,
            y=PayrollCol.FACILITY_ID,
            fill="positive_cycles_capped",
        ),
    )
    + geom_tile()
    + labs(
        title="Positive employee-pay-cycles per facility-period",
        x="Pay period",
        y="Facility",
        fill="Positives\n(capped at 8)",
    )
    + theme_minimal()
)


# %%
anomaly_dollars = data.payroll.select(PayrollCol.ANOMALY_DOLLARS).filter(
    pl.col(PayrollCol.ANOMALY_DOLLARS) > 0,
)

(
    ggplot(anomaly_dollars, aes(x=PayrollCol.ANOMALY_DOLLARS))
    + geom_histogram(bins=30, fill="#72B7B2", color="#3B5C76")
    + labs(
        title="Dollar impact distribution for anomalous employee-pay-cycles",
        x="Injected anomaly dollars",
        y="Count",
    )
    + theme_minimal()
)


# %% [markdown]
# The simulation produces a broad facility-period panel with enough employee-pay-
# cycle volume to support grouped queue evaluation. True issue rates vary across
# facilities, while observed corrections remain lower because review is modeled
# as a selective historical process that favors larger-dollar and more obvious
# exceptions. Overtime and pay-rate distributions also differ meaningfully by
# role, which is useful because the ranking task should separate normal clinical
# workload patterns from unusually risky payroll cycles.

# %% [markdown]
# ## 4. Label Engineering
#
# This section will explain how evaluation-only anomaly labels are constructed at the employee-pay-cycle level and how dominant anomaly categories are assigned when multiple lower-level anomalies roll up into one cycle.
# It will also make clear that labels are retained for evaluation and analysis only and are not part of active scoring inputs.
#
# - y_class = issue flag
# - y_reg = dollar impact
# - y_rank = graded relevance
# - y_utility = business utility

# %% [markdown]
# | Label | Used by | Meaning |
# | --- | --- | --- |
# | **issue_flag** | classifier | any known issue |
# | **dollar_impact** | regressor | estimated financial exposure |
# | **relevance_grade** | ranker | 0–3 review priority |
# | **net_utility** | evaluation | business value of review |

# %% [markdown]
# ## 5. Feature Engineering
#
# This section will describe the leakage-safe historical, peer-relative, normalization, overtime, premium, and payroll-cycle context features used by the employee-pay-cycle workflow.
# It will focus on how these features support stable comparison across periods and facilities without using current-period or future information as reference data.

# %% [markdown]
# | Feature family         | Examples                                 |
# | ---------------------- | ---------------------------------------- |
# | Raw payroll            | hours, OT, gross pay, pay type           |
# | Employee history       | hours vs trailing median, rate changes   |
# | Facility-role baseline | OT vs facility-role norm                 |
# | Timekeeping            | missing punches, manual edits, overrides |
# | SNF context            | census, role HPRD, agency share          |
# | Temporal               | holiday cycle, drift event, seasonality  |

# %%
employee_cycle_features = build_employee_cycle_features(data.payroll)
employee_cycle_features.head()

# %% [markdown]
# ## 6. Model Formulations
#
# This section will introduce the set of active employee-pay-cycle formulations, including classification, regression, expected-value, ranking, ML-only, and final active ranking views.
# It will explain what each formulation is trying to capture and why the workflow compares multiple formulations before making a production recommendation.

# %% [markdown]
# ## 7. Main Queue-Based Results
#
# This section will present the main grouped queue results that matter for payroll review operations.
# It will focus on facility-period review budgets, value capture, ranking quality, and how the active approach performs when review capacity is limited.

# %% [markdown]
# ## 8. Generalization Results
#
# This section will summarize how the employee-pay-cycle workflow generalizes across time, facilities, and synthetic scenario settings.
# It will emphasize temporal evidence, facility transfer behavior, and whether the ranking remains useful outside a single favorable run.

# %% [markdown]
# ## 9. Ablation Studies
#
# This section will compare simpler and more complex formulations to show what each level of modeling adds.
# It will clarify where complexity improves queue prioritization and where simpler baselines remain informative or competitive.

# %% [markdown]
# ## 10. Deep Diagnostics
#
# This section will gather the internal evidence needed to inspect failure modes, leakage safeguards, category behavior, stability, and subgroup behavior in more detail.
# It will provide the technical context needed to understand not only whether the ranking works, but also where it is fragile or incomplete.

# %% [markdown]
# ## 11. Model Explanation and Reviewer UX
#
# This section will explain how the model's output is translated into a reviewer-facing queue with clear reasons, recommended actions, and review-safe language.
# It will focus on making the employee-pay-cycle workflow interpretable and useful for payroll review rather than treating the score as a black box.

# %% [markdown]
# ## 12. Robustness / Stress Tests
#
# This section will describe the stress conditions used to test whether ranking behavior remains usable under scenario drift, queue pressure, and other controlled perturbations.
# It will focus on whether the workflow stays operationally credible when the synthetic environment becomes less favorable.

# %% [markdown]
# ## 13. Final Production Recommendation
#
# This section will summarize whether the current employee-pay-cycle workflow appears promotable into later production work.
# It will tie together the main evidence, identify remaining gaps, and state the current recommendation without overstating what the repository has implemented.

# %% [markdown]
# ## 14. Technical Appendix
#
# This appendix will hold the deeper technical material that supports the main narrative without overwhelming the primary flow of the notebook.
# It will contain the dense evidence and implementation notes needed for technical review of the employee-pay-cycle ranking workflow.

# %% [markdown]
# ### Metric Implementation Details
#
# This appendix section will document how the notebook's ranking, review-budget, exposure, and generalization metrics are defined and interpreted.

# %% [markdown]
# ### Full Ablation Matrix
#
# This appendix section will collect the complete formulation-comparison outputs that are too dense for the main narrative.

# %% [markdown]
# ### Hyperparameter Search Details
#
# This appendix section will document any active-search or tuning evidence used to support the formulation comparisons.

# %% [markdown]
# ### Extra Calibration Plots
#
# This appendix section will gather supplementary calibration or reliability views that support the diagnostic story.

# %% [markdown]
# ### Full Stress-Test Grid
#
# This appendix section will expand the robustness section into a broader grid of stress conditions, thresholds, and queue-demand settings.

# %% [markdown]
# ### Feature Importance by Split
#
# This appendix section will summarize how important features or score drivers vary across temporal or facility splits.

# %% [markdown]
# ### Per-Facility Diagnostics
#
# This appendix section will provide facility-level diagnostic views that are too detailed for the main notebook narrative.

# %% [markdown]
# ### Label-Bias Simulation Variants
#
# This appendix section will describe simulation variants that test how label construction choices influence evaluation conclusions.

# %% [markdown]
# ### Mathematical Ranking Objective Notes
#
# This appendix section will collect mathematical notes about the ranking objective, grouped queue framing, and related technical assumptions.

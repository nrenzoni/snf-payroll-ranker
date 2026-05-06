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
# # 02 Feature Engineering And Baselines
#
# **Executive takeaway:** Leakage-safe employee history, peer context, deterministic rules, robust statistics, ML scores, and dollar impact each capture different payroll review signals. The hybrid rank combines them so analysts are not dependent on a single fragile indicator.

# %%
import polars as pl
from lets_plot import LetsPlot

from payroll_anomaly_ranking.charts import employee_history_chart, score_distribution_chart
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import run_pipeline

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=650, pay_periods=26)
results = run_pipeline(config)
scored = results["scored"]
queue = results["review_queue"]

# %% [markdown]
# ## Concrete Feature Examples
#
# These selected synthetic records show the feature families used for review prioritization: prior employee history, peer-relative comparison, deterministic rule flags, robust statistical outlier features, and component scores.

# %%
example_ids = queue.select("employee_id").head(8)
scored.join(example_ids, on="employee_id", how="semi").sort(["employee_id", "pay_period_index"]).select(
    "employee_id",
    "pay_period_index",
    "gross_pay",
    "gross_pay_rolling_median",
    "gross_pay_pct_change",
    "peer_gross_median",
    "peer_gross_deviation_ratio",
    "gross_pay_robust_z",
    "gross_pay_mad_score",
    "rule_reason_codes",
    "rule_score",
    "statistical_score",
    "ml_score",
    "dollar_score",
    "final_anomaly_score",
    "pay_period_rank",
).filter(pl.col("pay_period_rank") <= 25).head(12)

# %% [markdown]
# ## Leakage-Safe Construction
#
# Historical features use shifted employee history, so current-period and future-period gross pay are excluded from rolling medians and lag changes. Peer features compare the current row to employees in similar synthetic department, job family, pay type, location, and tenure groups.
#
# Injected labels such as `is_anomaly`, `anomaly_category`, and `anomaly_dollars` are retained for evaluation and cost-aware reporting. They are not used as scoring features for the Isolation Forest or as direct inputs to history, peer, rule, or statistical features.

# %% [markdown]
# ## Baseline Ranking Signals
#
# The model comparison output evaluates rule score, statistical score, ML score, and hybrid score under the same review-budget framing. The hybrid score is the operating rank because deterministic compliance issues, statistical outliers, peer context, employee history, and dollar impact represent different review risks.

# %%
results["model_comparison"]

# %%
scored.select(
    "employee_id",
    "pay_period_index",
    "rule_score",
    "statistical_score",
    "ml_score",
    "dollar_score",
    "final_anomaly_score",
    "pay_period_rank",
    "rule_reason_codes",
).sort("final_anomaly_score", descending=True).head(15)

# %% [markdown]
# ## Simple Gross-Pay-Change Baseline
#
# Existing outputs contain the core score comparison. This lightweight table adds a business-intuitive gross-pay-change reference for reviewers who want to see how far a pure change-based baseline would get without rule, peer, ML, or dollar context.

# %%
scored.with_columns(pl.col("gross_pay_pct_change").abs().rank("ordinal", descending=True).over("pay_period_index").alias("gross_pay_change_rank")).select(
    "employee_id",
    "pay_period_index",
    "gross_pay",
    "gross_pay_pct_change",
    "gross_pay_change_rank",
    "final_anomaly_score",
    "pay_period_rank",
).sort("gross_pay_change_rank").head(12)

# %% [markdown]
# ## Score Distribution
#
# The distribution shows whether the hybrid score creates a focused top end for analyst review rather than treating every record as equally risky.

# %%
score_distribution_chart(scored)

# %% [markdown]
# ## Selected Employee History
#
# A flagged employee history helps analysts see whether a current-period value differs from the employee's previous payroll pattern.

# %%
highlight_employee = queue.select("employee_id").item(0, 0)
employee_history_chart(scored, highlight_employee)

# %% [markdown]
# ## What This Proves
#
# The feature layer is built from synthetic payroll history and peer context without label leakage. Baseline comparisons show why a hybrid rank is better suited to payroll review than relying only on rules, statistics, ML, or gross-pay movement.

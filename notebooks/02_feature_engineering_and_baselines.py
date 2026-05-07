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
# **Executive takeaway:** Leakage-safe employee history, period-safe peer context, deterministic rules, robust statistics, ML scores, and estimated exposure each capture different payroll review signals. The hybrid rank combines them so analysts are not dependent on a single fragile indicator.

# %%
import polars as pl
from lets_plot import LetsPlot

from payroll_anomaly_ranking.charts import (
    employee_history_chart,
    score_distribution_chart,
)
from payroll_anomaly_ranking.columns import FeatureCol, PayrollCol, RuleCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import run_pipeline

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=650, pay_periods=26)
results = run_pipeline(config)
scored = results.scored
queue = results.analyst_review_queue

# %% [markdown]
# ## Concrete Feature Examples
#
# These selected synthetic records show the feature families used for review prioritization: prior employee history, peer-relative comparison, deterministic rule flags, robust statistical outlier features, and component scores.

# %%
example_ids = queue.select(PayrollCol.EMPLOYEE_ID).head(8)
scored.join(example_ids, on=PayrollCol.EMPLOYEE_ID, how="semi").sort(
    [PayrollCol.EMPLOYEE_ID, PayrollCol.PAY_PERIOD_INDEX],
).select(
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    PayrollCol.GROSS_PAY,
    FeatureCol.GROSS_PAY_ROLLING_MEDIAN,
    FeatureCol.GROSS_PAY_PCT_CHANGE,
    FeatureCol.PEER_GROSS_MEDIAN,
    FeatureCol.PEER_GROSS_DEVIATION_RATIO,
    FeatureCol.GROSS_PAY_ROBUST_Z,
    FeatureCol.GROSS_PAY_MAD_SCORE,
    RuleCol.REASON_CODES,
    ScoreCol.RULE_SCORE,
    ScoreCol.STATISTICAL_SCORE,
    ScoreCol.ML_SCORE,
    ScoreCol.EXPOSURE_SCORE,
    ScoreCol.ESTIMATED_EXPOSURE,
    ScoreCol.FINAL_ANOMALY_SCORE,
    ScoreCol.PAY_PERIOD_RANK,
).filter(pl.col(ScoreCol.PAY_PERIOD_RANK) <= 25).head(12)

# %% [markdown]
# ## Leakage-Safe Construction
#
# Historical features use shifted employee history, so current-period and future-period gross pay are excluded from rolling medians and lag changes. Peer and robust features use prior pay periods where available, with early-period fallbacks for sparse synthetic history.
#
# Injected labels such as `is_anomaly`, `anomaly_category`, and `anomaly_dollars` are retained for evaluation-only artifacts. They are not used as scoring features, estimated exposure inputs, or analyst-facing queue fields.

# %% [markdown]
# ## Baseline Ranking Signals
#
# The model comparison output evaluates rule score, statistical score, ML score, and hybrid score under the same review-budget framing. The hybrid score is the operating rank because deterministic compliance issues, statistical outliers, peer context, employee history, and estimated exposure represent different review risks.

# %%
results.model_comparison

# %%
scored.select(
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    ScoreCol.RULE_SCORE,
    ScoreCol.STATISTICAL_SCORE,
    ScoreCol.ML_SCORE,
    ScoreCol.EXPOSURE_SCORE,
    ScoreCol.ESTIMATED_EXPOSURE,
    ScoreCol.FINAL_ANOMALY_SCORE,
    ScoreCol.PAY_PERIOD_RANK,
    RuleCol.REASON_CODES,
).sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True).head(15)

# %% [markdown]
# ## Simple Gross-Pay-Change Baseline
#
# Existing outputs contain the core score comparison. This lightweight table adds a business-intuitive gross-pay-change reference for reviewers who want to see how far a pure change-based baseline would get without rule, peer, ML, or dollar context.

# %%
scored.with_columns(
    pl.col(FeatureCol.GROSS_PAY_PCT_CHANGE)
    .abs()
    .rank("ordinal", descending=True)
    .over(PayrollCol.PAY_PERIOD_INDEX)
    .alias(FeatureCol.GROSS_PAY_CHANGE_RANK),
).select(
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    PayrollCol.GROSS_PAY,
    FeatureCol.GROSS_PAY_PCT_CHANGE,
    FeatureCol.GROSS_PAY_CHANGE_RANK,
    ScoreCol.FINAL_ANOMALY_SCORE,
    ScoreCol.PAY_PERIOD_RANK,
).sort(FeatureCol.GROSS_PAY_CHANGE_RANK).head(12)

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
highlight_employee = queue.select(PayrollCol.EMPLOYEE_ID).item(0, 0)
employee_history_chart(scored, highlight_employee)

# %% [markdown]
# ## What This Proves
#
# The feature layer is built from synthetic payroll history and peer context without label leakage. Baseline comparisons show why a hybrid rank is better suited to payroll review than relying only on rules, statistics, ML, or gross-pay movement.

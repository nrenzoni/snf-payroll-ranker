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
# # 03 Modeling, Evaluation, And Error Analysis
#
# **Executive takeaway:** Payroll anomaly ranking should be evaluated against realistic review budgets over time. Hybrid scoring performs best when it captures high-value synthetic exceptions early enough for payroll analysts to review before finalization.

# %%
from lets_plot import LetsPlot, aes, geom_line, geom_point, ggplot, ggtitle, theme_minimal

from payroll_anomaly_ranking.charts import dollars_captured_chart, precision_at_k_chart
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import run_pipeline

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=650, pay_periods=26, review_budgets=(10, 25, 50))
results = run_pipeline(config)
metrics = results["metrics"]
comparison = results["model_comparison"]
backtest = results["backtest"]
category = results["category_error_analysis"]

# %% [markdown]
# ## Temporal Validation Framing
#
# Payroll records are time-dependent: employee history, pay rates, lifecycle state, and peer context change by pay period. Evaluation therefore uses later pay periods as held-out scoring periods and avoids random row splits, which could leak employee history patterns across time.
#
# Injected synthetic labels are kept for evaluation only. They are not used as scoring features, and review metrics are interpreted as demonstration evidence rather than production guarantees.

# %% [markdown]
# ## Review-Budget Metrics
#
# These metrics answer the payroll operations question: if analysts can review the top 10, 25, or 50 records per cycle, how many synthetic exceptions and dollars at risk are captured?

# %%
metrics

# %% [markdown]
# Precision@K shows how concentrated true synthetic exceptions are in the queue. Recall@K and dollar capture rate show whether the queue covers enough total risk. Average anomaly rank and mean reciprocal rank summarize how early anomalies appear in each period.

# %%
precision_at_k_chart(metrics)

# %%
dollars_captured_chart(metrics)

# %% [markdown]
# ## Model Comparison
#
# Rules catch deterministic payroll issues, statistical scores catch unusual values, ML scores capture multivariate outliers, and the hybrid score combines review signals into one operating rank.

# %%
comparison

# %% [markdown]
# The hybrid ranking fits payroll review because compliance-like rule breaks, unusual employee history, peer differences, multivariate ML outliers, and dollar impact all describe different analyst concerns. A single score source can miss costly exceptions that another source catches.

# %% [markdown]
# ## Backtest By Period
#
# Period-level backtesting shows whether queue quality is stable over later payroll cycles rather than strong only in aggregate.

# %%
backtest

# %%
ggplot(backtest.to_dict(as_series=False), aes("pay_period_index", "precision_at_k")) + geom_line() + geom_point() + ggtitle("Backtest Precision@K Over Time") + theme_minimal()

# %% [markdown]
# ## Category-Level Error Analysis
#
# Category analysis shows which synthetic exception types are reviewed, missed, or overrepresented as false positives under a fixed review budget.

# %%
category.sort("false_negatives", descending=True)

# %% [markdown]
# ## Cost-Aware Interpretation
#
# Reviewing more records generally improves recall and dollar capture but can reduce precision as lower-ranked items enter the queue. The practical review budget is the point where additional review effort still captures meaningful dollars at risk without overwhelming payroll analysts with too many low-confidence exceptions.
#
# Category-level false negatives are useful for rule tuning and analyst feedback: a missed high-dollar category may justify more weight, a new deterministic rule, or a lower threshold during sensitive payroll periods.

# %% [markdown]
# ## What This Proves
#
# The evaluation layer supports temporal, review-budget-oriented decisions with precision, recall, F1, PR-AUC, rank, dollar capture, model comparison, period backtesting, and category error analysis. These outputs make the ranking workflow auditable for business review capacity rather than only model accuracy.

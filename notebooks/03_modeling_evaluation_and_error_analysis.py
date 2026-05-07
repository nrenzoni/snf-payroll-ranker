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
# **Executive takeaway:** Payroll anomaly ranking should be evaluated against realistic review budgets over time. Hybrid scoring is stronger when label-free exposure estimates, validation-selected thresholds, and rolling-origin checks are stable enough for payroll analysts to review before finalization.

# %%
import polars as pl
from lets_plot import (
    LetsPlot,
    aes,
    geom_histogram,
    geom_line,
    geom_point,
    ggplot,
    ggtitle,
    theme_minimal,
)
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split

from payroll_anomaly_ranking.charts import dollars_captured_chart, precision_at_k_chart
from payroll_anomaly_ranking.columns import (
    MODEL_FEATURE_COLUMNS,
    AggregateCol,
    MetricCol,
    PayrollCol,
    ReviewCol,
    ScoreCol,
)
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.models import temporal_split
from payroll_anomaly_ranking.pipeline import run_pipeline

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=650, pay_periods=26, review_budgets=(10, 25, 50))
results = run_pipeline(config)
metrics = results["metrics"]
comparison = results["model_comparison"]
backtest = results["backtest"]
category = results["category_error_analysis"]
rolling_origin = results["rolling_origin_metrics"]
validation_settings = results["validation_selected_settings"]
stability = results["stability_summary"]
leakage = results["leakage_checks"]
scored = results["scored"]
uncertainty_bucket_metrics = results["uncertainty_bucket_metrics"]
risk_coverage = results["risk_coverage_analysis"]
interval_metrics = results["expected_gross_pay_interval_metrics"]
review_budget = 25

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
# Precision@K shows how concentrated true synthetic exceptions are in the queue. Recall@K and dollar capture rate show whether the queue covers enough evaluation-only synthetic impact. Average anomaly rank and mean reciprocal rank summarize how early anomalies appear in each period.

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
# The hybrid ranking fits payroll review because compliance-like rule breaks, unusual employee history, peer differences, multivariate ML outliers, and label-free estimated exposure all describe different analyst concerns. A single score source can miss costly exceptions that another source catches.

# %% [markdown]
# ## Backtest By Period
#
# Period-level backtesting shows whether queue quality is stable over later payroll cycles rather than strong only in aggregate.

# %%
backtest

# %%
(
    ggplot(backtest, aes(PayrollCol.PAY_PERIOD_INDEX, MetricCol.PRECISION_AT_K))
    + geom_line()
    + geom_point()
    + ggtitle("Backtest Precision@K Over Time")
    + theme_minimal()
)

# %% [markdown]
# ## Rolling-Origin Validation And Leakage Checks
#
# Rolling-origin evaluation calibrates a threshold on one pay period and reports later test-period metrics. The leakage table explicitly confirms that injected labels and injected dollar impacts are excluded from model features and analyst queues.

# %%
rolling_origin

# %%
validation_settings

# %%
stability

# %%
leakage

# %% [markdown]
# ## Category-Level Error Analysis
#
# Category analysis shows which synthetic exception types are reviewed, missed, or overrepresented as false positives under a fixed review budget.

# %%
category.sort(AggregateCol.FALSE_NEGATIVES, descending=True)

# %% [markdown]
# ## Cost-Aware Interpretation
#
# Reviewing more records generally improves recall and dollar capture but can reduce precision as lower-ranked items enter the queue. The practical review budget is the point where additional review effort still captures meaningful dollars at risk without overwhelming payroll analysts with too many low-confidence exceptions.
#
# Category-level false negatives are useful for rule tuning and analyst feedback: a missed high-exposure category may justify more weight, a new deterministic rule, or a lower threshold during sensitive payroll periods.

# %% [markdown]
# ## Uncertainty Diagnostics
#
# Uncertainty is tracked separately from the final anomaly score. The composite score summarizes model-signal disagreement, bootstrap interval width, expected gross-pay interval width, thin peer or employee history, data quality issues, and out-of-distribution context. Conformal percentile is shown as recent-history anomaly context, not as a composite uncertainty component.

# %%
scored.select(
    ScoreCol.ENSEMBLE_DISAGREEMENT_UNCERTAINTY,
    ScoreCol.BOOTSTRAP_INTERVAL_UNCERTAINTY,
    ScoreCol.EXPECTED_GROSS_PAY_INTERVAL_WIDTH,
    ScoreCol.PEER_GROUP_UNCERTAINTY,
    ScoreCol.EMPLOYEE_HISTORY_UNCERTAINTY,
    ScoreCol.DATA_QUALITY_UNCERTAINTY,
    ScoreCol.OOD_UNCERTAINTY,
    ScoreCol.COMPOSITE_UNCERTAINTY_SCORE,
).describe()

# %%
uncertainty_bucket_metrics

# %%
risk_coverage

# %% [markdown]
# ## Expected Gross-Pay Interval Diagnostics
#
# Expected gross-pay intervals are estimated from the rolling prior-period reference window. Normal-record coverage checks whether typical records fall between p10 and p90; anomaly exceedance over p90 shows whether synthetic exceptions tend to sit above recent expected pay.

# %%
interval_metrics

# %%
scored.group_by(ReviewCol.UNCERTAINTY_BUCKET).agg(
    pl.mean(ScoreCol.EXPECTED_GROSS_PAY_INTERVAL_WIDTH).alias(
        AggregateCol.AVG_INTERVAL_WIDTH,
    ),
    pl.mean(ScoreCol.CONFORMAL_PERCENTILE).alias(
        f"avg_{ScoreCol.CONFORMAL_PERCENTILE}",
    ),
    pl.len().alias(AggregateCol.RECORDS),
).sort(ReviewCol.UNCERTAINTY_BUCKET)

# %% [markdown]
# ## Common Evaluation Mistakes To Avoid
#
# The next cells intentionally show anti-patterns beside corrected methods. The labels are synthetic injected exceptions, so these demos evaluate whether the workflow ranks known synthetic anomalies for review; they do not prove confirmed fraud detection.

# %%
temporal_test = temporal_split(scored)["test"]
random_train_indices, random_row_indices = train_test_split(
    list(range(scored.height)),
    test_size=temporal_test.height,
    random_state=config.seed,
    stratify=scored.get_column(PayrollCol.IS_ANOMALY).to_list(),
)
indexed_scored = scored.with_row_index("demo_row_index")
random_train = indexed_scored.filter(
    pl.col("demo_row_index").is_in(random_train_indices),
).drop("demo_row_index")
random_test = indexed_scored.filter(
    pl.col("demo_row_index").is_in(random_row_indices),
).drop("demo_row_index")
temporal_train = temporal_split(scored)["train"]


def demo_metrics(
    frame: pl.DataFrame,
    score_column: str,
    method: str,
    k: int = review_budget,
) -> dict[str, float | str]:
    labels = frame.get_column(PayrollCol.IS_ANOMALY).to_numpy()
    scores = frame.get_column(score_column).to_numpy()
    try:
        roc_auc = float(roc_auc_score(labels, scores))
    except ValueError:
        roc_auc = 0.0
    try:
        pr_auc = float(average_precision_score(labels, scores))
    except ValueError:
        pr_auc = 0.0
    top = frame.sort(score_column, descending=True).head(k)
    true_positives = top.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    false_positives = top.filter(pl.col(PayrollCol.IS_ANOMALY) == 0).height
    false_negatives = (
        frame.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height - true_positives
    )
    dollars_captured = (
        top.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0
    )
    total_dollars = (
        frame.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0
    )
    return {
        "method": method,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "precision_at_k": true_positives / max(k, 1),
        "false_positives": float(false_positives),
        "false_negatives": float(false_negatives),
        "dollar_capture_rate": float(dollars_captured / total_dollars)
        if total_dollars
        else 0.0,
    }


def model_matrix(frame: pl.DataFrame):
    return frame.select(
        [
            pl.col(column).cast(pl.Float64).fill_null(0)
            for column in MODEL_FEATURE_COLUMNS
        ],
    ).to_numpy()


def minmax(values):
    minimum = values.min()
    maximum = values.max()
    return (
        values * 0 if maximum == minimum else (values - minimum) / (maximum - minimum)
    )


def dollars_for_anomalies(frame: pl.DataFrame) -> float:
    return (
        frame.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0
    )


# %% [markdown]
# ### Mistake 1: Random Train/Test Split
#
# **Anti-pattern:** sample payroll rows randomly and report the result as if it represents future payroll cycles.
#
# **Corrected method:** hold out later pay periods so employee history, peer context, and operational conditions move forward in time.

# %%
random_split_summary = pl.DataFrame(
    [
        demo_metrics(
            random_test,
            ScoreCol.FINAL_ANOMALY_SCORE,
            "Anti-pattern: random row split",
        ),
        demo_metrics(
            temporal_test,
            ScoreCol.FINAL_ANOMALY_SCORE,
            "Corrected: temporal holdout",
        ),
    ],
)
random_split_summary


# %%
def split_leakage_profile(
    method: str,
    train: pl.DataFrame,
    test: pl.DataFrame,
) -> dict[str, float | str]:
    train_periods = set(
        train.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list(),
    )
    test_periods = set(test.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list())
    train_employees = set(train.get_column(PayrollCol.EMPLOYEE_ID).unique().to_list())
    test_employees = set(test.get_column(PayrollCol.EMPLOYEE_ID).unique().to_list())
    overlap_periods = train_periods & test_periods
    overlap_employees = train_employees & test_employees
    return {
        "method": method,
        "test_periods": float(len(test_periods)),
        "test_periods_also_in_train": float(len(overlap_periods)),
        "period_overlap_rate": len(overlap_periods) / max(len(test_periods), 1),
        "employee_overlap_rate": len(overlap_employees) / max(len(test_employees), 1),
    }


split_leakage_summary = pl.DataFrame(
    [
        split_leakage_profile(
            "Anti-pattern: random row split",
            random_train,
            random_test,
        ),
        split_leakage_profile(
            "Corrected: temporal holdout",
            temporal_train,
            temporal_test,
        ),
    ],
)
split_leakage_summary

# %%
test_period_distribution = pl.concat(
    [
        random_test.group_by(PayrollCol.PAY_PERIOD_INDEX)
        .agg(pl.len().alias("test_rows"))
        .with_columns(pl.lit("Anti-pattern: random row split").alias("method")),
        temporal_test.group_by(PayrollCol.PAY_PERIOD_INDEX)
        .agg(pl.len().alias("test_rows"))
        .with_columns(pl.lit("Corrected: temporal holdout").alias("method")),
    ],
).sort(["method", PayrollCol.PAY_PERIOD_INDEX])
(
    ggplot(
        test_period_distribution.to_dict(as_series=False),
        aes(PayrollCol.PAY_PERIOD_INDEX, "test_rows", color="method"),
    )
    + geom_point(size=4)
    + geom_line()
    + ggtitle("Random Test Rows Mix Historical And Future Pay Periods")
    + theme_minimal()
)

# %% [markdown]
# Random row splits can look attractive in review metrics, but the leakage table shows why they are not valid future-cycle evaluation: the random test sample shares pay periods with training data, while the temporal holdout keeps evaluation in later periods only.

# %% [markdown]
# ### Mistake 2: Default-Only Isolation Forest
#
# **Anti-pattern:** fit a default Isolation Forest on all available rows and interpret the score without documenting review capacity, contamination, seed stability, or temporal training assumptions.
#
# **Corrected method:** train on prior periods, set the contamination assumption to the expected review/anomaly rate, fix the seed for reproducibility, and evaluate on later periods with review metrics.

# %%
default_model = IsolationForest(random_state=config.seed)
default_model.fit(model_matrix(scored))
default_scores = minmax(-default_model.decision_function(model_matrix(scored)))
default_test = scored.with_columns(
    pl.Series("demo_default_iforest_score", default_scores),
).filter(
    pl.col(PayrollCol.PAY_PERIOD_INDEX).is_in(
        temporal_test.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list(),
    ),
)

temporal_train = temporal_split(scored)["train"]
configured_model = IsolationForest(
    n_estimators=200,
    contamination=0.03,
    random_state=config.seed,
)
configured_model.fit(model_matrix(temporal_train))
configured_test = temporal_test.with_columns(
    pl.Series(
        "demo_configured_iforest_score",
        minmax(-configured_model.decision_function(model_matrix(temporal_test))),
    ),
)

iforest_summary = pl.DataFrame(
    [
        demo_metrics(
            default_test,
            "demo_default_iforest_score",
            "Anti-pattern: defaults fit on all rows",
        ),
        demo_metrics(
            configured_test,
            "demo_configured_iforest_score",
            "Corrected: configured temporal model",
        ),
    ],
)
iforest_summary

# %%
seed_rows = []
top_by_method_seed = {}
for seed in [3, 11, 23, 42, 97]:
    default_seed_model = IsolationForest(random_state=seed)
    default_seed_model.fit(model_matrix(scored))
    default_seed_scores = minmax(
        -default_seed_model.decision_function(model_matrix(scored)),
    )
    default_seed_test = scored.with_columns(
        pl.Series("demo_seed_score", default_seed_scores),
    ).filter(
        pl.col(PayrollCol.PAY_PERIOD_INDEX).is_in(
            temporal_test.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list(),
        ),
    )

    configured_seed_model = IsolationForest(
        n_estimators=200,
        contamination=0.03,
        random_state=seed,
    )
    configured_seed_model.fit(model_matrix(temporal_train))
    configured_seed_test = temporal_test.with_columns(
        pl.Series(
            "demo_seed_score",
            minmax(
                -configured_seed_model.decision_function(model_matrix(temporal_test)),
            ),
        ),
    )

    for method, frame in [
        ("Anti-pattern: default-only", default_seed_test),
        ("Corrected: configured temporal", configured_seed_test),
    ]:
        top_ids = set(
            frame.sort("demo_seed_score", descending=True)
            .head(review_budget)
            .get_column(PayrollCol.RECORD_ID)
            .to_list(),
        )
        top_by_method_seed[(method, seed)] = top_ids
        metric = demo_metrics(frame, "demo_seed_score", method)
        seed_rows.append(
            {
                "seed": seed,
                "method": method,
                "precision_at_k": metric["precision_at_k"],
                "dollar_capture_rate": metric["dollar_capture_rate"],
            },
        )

seed_stability = pl.DataFrame(seed_rows).with_columns(
    pl.struct(["method", "seed"])
    .map_elements(
        lambda row: (
            len(
                top_by_method_seed[(row["method"], row["seed"])]
                & top_by_method_seed[(row["method"], 42)],
            )
            / review_budget
        ),
        return_dtype=pl.Float64,
    )
    .alias("top_25_overlap_with_seed_42"),
)
seed_stability

# %%
iforest_distribution = pl.concat(
    [
        default_test.select(
            pl.lit("Anti-pattern: default").alias("method"),
            pl.col("demo_default_iforest_score").alias("score"),
        ),
        configured_test.select(
            pl.lit("Corrected: configured").alias("method"),
            pl.col("demo_configured_iforest_score").alias("score"),
        ),
    ],
)
(
    ggplot(iforest_distribution.to_dict(as_series=False), aes("score", fill="method"))
    + geom_histogram(bins=30, alpha=0.55)
    + ggtitle("Isolation Forest Score Distributions Depend On Assumptions")
    + theme_minimal()
)

# %% [markdown]
# ### Mistake 3: ROC-AUC-Only Reporting
#
# **Anti-pattern:** report ROC-AUC alone and ignore whether the top review queue is useful under severe class imbalance.
#
# **Corrected method:** pair ROC-AUC with PR-AUC, Precision@K, and dollar capture so evaluation matches the payroll review workflow.

# %%
roc_only_metric = demo_metrics(
    temporal_test,
    ScoreCol.FINAL_ANOMALY_SCORE,
    "Corrected: operational metrics",
)
anomaly_prevalence = temporal_test.filter(
    pl.col(PayrollCol.IS_ANOMALY) == 1,
).height / max(temporal_test.height, 1)
metric_comparison = pl.DataFrame(
    [
        {
            "metric": "Anomaly prevalence baseline",
            "value": anomaly_prevalence,
            "metric_group": "baseline",
        },
        {
            "metric": "Anti-pattern: ROC-AUC only",
            "value": roc_only_metric["roc_auc"],
            "metric_group": "generic",
        },
        {
            "metric": "Corrected: PR-AUC",
            "value": roc_only_metric["pr_auc"],
            "metric_group": "imbalance-aware",
        },
        {
            "metric": "Corrected: Precision@25",
            "value": roc_only_metric["precision_at_k"],
            "metric_group": "review queue",
        },
        {
            "metric": "Corrected: lift over prevalence",
            "value": roc_only_metric["precision_at_k"] / max(anomaly_prevalence, 1e-9),
            "metric_group": "review queue",
        },
        {
            "metric": "Corrected: dollar capture",
            "value": roc_only_metric["dollar_capture_rate"],
            "metric_group": "business impact",
        },
    ],
)
metric_comparison

# %%
capture_rows = []
for budget in [5, 10, 25, 50, 100]:
    ranked = temporal_test.sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True).head(
        budget,
    )
    capture_rows.append(
        {
            "budget": budget,
            "anomaly_capture_rate": ranked.filter(
                pl.col(PayrollCol.IS_ANOMALY) == 1,
            ).height
            / max(temporal_test.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height, 1),
            "dollar_capture_rate": dollars_for_anomalies(ranked)
            / max(dollars_for_anomalies(temporal_test), 1),
        },
    )
cumulative_capture = pl.DataFrame(capture_rows)
cumulative_capture

# %%
(
    ggplot(cumulative_capture, aes("budget", "dollar_capture_rate"))
    + geom_point(size=5)
    + geom_line()
    + ggtitle("Ranked Review Budgets Capture Dollar Exposure")
    + theme_minimal()
)

# %% [markdown]
# ROC-AUC is a generic ranking measure. For payroll review, the stronger evidence is the gap between anomaly prevalence and Precision@K, plus the cumulative dollars captured inside realistic analyst budgets.

# %% [markdown]
# ### Mistake 4: Neglecting False Positives
#
# **Anti-pattern:** celebrate captured synthetic anomalies while ignoring how many normal payroll records analysts must review.
#
# **Corrected method:** compare true positives with false positives, false negatives, and review load at each budget.

# %%
queue_rows = []
for budget in config.review_budgets:
    ranked = temporal_test.sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True).head(
        budget,
    )
    true_positives = ranked.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    false_positives = ranked.filter(pl.col(PayrollCol.IS_ANOMALY) == 0).height
    false_negatives = (
        temporal_test.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height - true_positives
    )
    queue_rows.append(
        {
            "budget": budget,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "queue_false_positive_rate": false_positives / max(budget, 1),
            "estimated_false_positive_review_minutes": false_positives * 10,
        },
    )
queue_error_summary = pl.DataFrame(queue_rows)
queue_error_summary

# %%
queue_plot = queue_error_summary.unpivot(
    ["true_positives", "false_positives", "false_negatives"],
    index="budget",
    variable_name="outcome",
    value_name="records",
)
(
    ggplot(queue_plot, aes("budget", "records", color="outcome"))
    + geom_point(size=4)
    + geom_line()
    + ggtitle("Review Budgets Trade Off False Positives And Missed Anomalies")
    + theme_minimal()
)

# %% [markdown]
# False positives are not just model errors; they consume analyst capacity. At 10 minutes per review, the queue table converts false positives into approximate operational load.

# %% [markdown]
# ### Mistake 5: Treating All Anomalies As Equally Important
#
# **Anti-pattern:** rank by anomaly likelihood alone and treat every synthetic anomaly as equally important regardless of dollars at risk or review capacity.
#
# **Corrected method:** include severity and label-free estimated exposure when ranking review candidates, then compare captured evaluation impact per reviewed row across fixed review budgets. Impact-aware ranking may not dominate every small queue, so the useful question is the operational tradeoff between anomaly count and estimated exposure.

# %%
importance_rows = []
for budget in config.review_budgets:
    equal_queue = temporal_test.sort(ScoreCol.ML_SCORE, descending=True).head(budget)
    impact_queue = temporal_test.sort(
        ScoreCol.FINAL_ANOMALY_SCORE,
        descending=True,
    ).head(budget)
    for method, queue in [
        ("Anti-pattern: likelihood-only ranking", equal_queue),
        ("Corrected: impact-aware hybrid ranking", impact_queue),
    ]:
        dollars_captured = dollars_for_anomalies(queue)
        reviewed_ids = set(queue.get_column(PayrollCol.RECORD_ID))
        missed_anomalies = temporal_test.filter(
            (pl.col(PayrollCol.IS_ANOMALY) == 1)
            & (~pl.col(PayrollCol.RECORD_ID).is_in(reviewed_ids)),
        )
        max_missed_anomaly_dollars = (
            missed_anomalies.select(pl.col(PayrollCol.ANOMALY_DOLLARS).max()).item()
            or 0.0
        )
        importance_rows.append(
            {
                "budget": budget,
                "method": method,
                "anomaly_count_captured": queue.filter(
                    pl.col(PayrollCol.IS_ANOMALY) == 1,
                ).height,
                "dollars_captured": dollars_captured,
                "dollars_captured_per_review": dollars_captured / budget,
                "max_missed_anomaly_dollars": max_missed_anomaly_dollars,
            },
        )
importance_summary = pl.DataFrame(importance_rows)
importance_summary

# %%
(
    ggplot(
        importance_summary,
        aes("budget", "dollars_captured_per_review", color="method"),
    )
    + geom_point(size=5)
    + geom_line()
    + ggtitle("Review Budget Tradeoff: Likelihood vs Dollar Exposure")
    + theme_minimal()
)

# %% [markdown]
# The corrected ranking is evaluated on exposure captured under fixed review capacity, not on anomaly count alone. `max_missed_anomaly_dollars` remains an evaluation-only synthetic diagnostic for residual risk; it is not an analyst-facing scoring input.

# %% [markdown]
# ### Mistake 6: Overclaiming Fraud Detection
#
# **Anti-pattern:** state that the model detected fraud or that synthetic labels prove real-world fraud outcomes.
#
# **Corrected method:** state that the workflow prioritizes payroll records for analyst review and evaluates against synthetic injected anomalies only.
#
# | Blocked wording | Why it is wrong | Safer replacement |
# | :--- | :--- | :--- |
# | The model detected fraud. | Synthetic labels are not confirmed fraud outcomes. | The workflow ranked records for payroll review. |
# | This proves fraud detection accuracy. | The notebook evaluates injected exceptions in generated data. | This measures how well synthetic exceptions surface in the review queue. |
# | The employee committed misconduct. | A score is an exception triage signal, not an investigation conclusion. | The record needs analyst review before any conclusion. |

# %% [markdown]
# ## Summary Table
#
# | Mistake | Anti-pattern signal | Corrected evidence | Payroll review implication |
# | :--- | :--- | :--- | :--- |
# | Random split | Test rows share periods with training rows | Temporal holdout keeps evaluation in later periods | Use future-cycle validation for payroll scoring |
# | Default Isolation Forest | Hidden fit, contamination, and stability assumptions | Configured temporal model plus seed-stability metrics | Document assumptions behind review queues |
# | ROC-AUC only | One generic metric hides imbalance | PR-AUC, lift, Precision@K, and dollar capture | Judge the ranked analyst queue, not only model discrimination |
# | False-positive neglect | Captured anomalies shown without review burden | False positives, false negatives, and review minutes | Balance recall against analyst capacity |
# | Equal importance | Likelihood-only ranking treats exposure as secondary | Estimated exposure per review and missed high-impact anomalies | Prioritize material payroll risk under fixed budget |
# | Fraud overclaiming | Claims confirmed fraud or misconduct | Review-prioritization language | Keep conclusions within synthetic-data evidence |

# %% [markdown]
# ## What This Proves
#
# The evaluation layer supports temporal, review-budget-oriented decisions with precision, recall, F1, PR-AUC, rank, dollar capture, model comparison, period backtesting, rolling-origin validation, stability summaries, leakage checks, and category error analysis. These outputs make the ranking workflow auditable for business review capacity rather than only model accuracy, and they surface synthetic exceptions as review candidates rather than confirmed fraud.

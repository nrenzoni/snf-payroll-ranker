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
# # SNF Model Ablation And ML Value
#
# **Executive takeaway:** The business notebook shows that automated ranking improves SNF payroll approval workflow. This notebook tests whether the modeling stack earns its complexity by comparing manual thresholds, deterministic rules, robust statistics, unsupervised ML, and the hybrid ranking under approval-budget, dollar-capture, temporal, uncertainty, and robustness views.
#
# Synthetic labels and injected anomaly dollars are used here only for evaluation. They are not scoring features and they should not appear in administrator-facing queues.

# %%
import polars as pl
from common.execution import notebook_fast_mode
from common.plots import (
    LetsPlot,
    aes,
    geom_bar,
    geom_line,
    geom_point,
    geom_tile,
    ggplot,
    labs,
    rotated_x_labels,
    theme_minimal,
)

from payroll_anomaly_ranking.columns import (
    AggregateCol,
    MetricCol,
    PayrollCol,
    ReviewCol,
    ScoreCol,
)
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.evaluation import evaluate_scores
from payroll_anomaly_ranking.pipeline import PipelineIncludeConfig, run_pipeline
from payroll_anomaly_ranking.scenarios import diagnostic_scenario_presets

LetsPlot.setup_html()

# %%
config = PayrollConfig(employee_count=200, pay_periods=14, review_budgets=(10, 25, 50))
FAST_CONFIG = PayrollConfig(employee_count=90, pay_periods=10, review_budgets=(10, 25))
NOTEBOOK_FAST = notebook_fast_mode()
active_config = FAST_CONFIG if NOTEBOOK_FAST else config
active_include = (
    PipelineIncludeConfig(
        validation=False,
        aggregations=False,
        evaluation=True,
        backtest=True,
        rolling_origin=True,
        review_queues=True,
        leakage_checks=True,
    )
    if NOTEBOOK_FAST
    else PipelineIncludeConfig.all()
)
scenario = diagnostic_scenario_presets(("premium-mismatch",))["premium-mismatch"]
results = run_pipeline(active_config, scenario=scenario, include=active_include)

SCORE_METHODS = [
    ("rule score", ScoreCol.RULE_SCORE, "deterministic rules"),
    ("robust statistical score", ScoreCol.STATISTICAL_SCORE, "robust statistics"),
    (
        "schedule/timeclock score",
        ScoreCol.SCHEDULE_TIMECLOCK_SCORE,
        "operational context",
    ),
    (
        "premium eligibility score",
        ScoreCol.PREMIUM_ELIGIBILITY_SCORE,
        "pay policy context",
    ),
    ("ML score", ScoreCol.ML_SCORE, "unsupervised ML"),
    ("hybrid score", ScoreCol.FINAL_ANOMALY_SCORE, "hybrid ranking"),
]
THRESHOLD_FLAGS = [
    ("gross pay threshold", ScoreCol.THRESHOLD_GROSS_PAY_FLAG),
    ("total hours threshold", ScoreCol.THRESHOLD_TOTAL_HOURS_FLAG),
    ("overtime threshold", ScoreCol.THRESHOLD_OVERTIME_HOURS_FLAG),
    ("premium dollars threshold", ScoreCol.THRESHOLD_PREMIUM_DOLLARS_FLAG),
    ("paid-vs-scheduled threshold", ScoreCol.THRESHOLD_PAID_VS_SCHEDULED_FLAG),
]


def _score_method_budget_metrics(scored: pl.DataFrame, budget: int) -> pl.DataFrame:
    total_anomalies = scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    total_dollars = float(
        scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0,
    )
    rows = []
    for method, score_col, method_type in SCORE_METHODS:
        top = (
            scored.sort(
                [PayrollCol.PAY_PERIOD_INDEX, score_col],
                descending=[False, True],
            )
            .group_by(PayrollCol.PAY_PERIOD_INDEX)
            .head(budget)
        )
        true_positives = top.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
        captured_dollars = float(
            top.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
            .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
            .item()
            or 0.0,
        )
        rows.append(
            {
                "method": method,
                "method_type": method_type,
                MetricCol.K: float(budget),
                MetricCol.REVIEW_VOLUME: top.height,
                MetricCol.PRECISION_AT_K: true_positives / max(top.height, 1),
                MetricCol.RECALL_AT_K: true_positives / max(total_anomalies, 1),
                MetricCol.EXPOSURE_CAPTURED_AT_K: float(
                    top.select(pl.sum(ScoreCol.ESTIMATED_EXPOSURE)).item() or 0.0,
                ),
                MetricCol.DOLLARS_CAPTURED_AT_K: captured_dollars,
                MetricCol.DOLLAR_CAPTURE_RATE: captured_dollars / total_dollars
                if total_dollars
                else 0.0,
            },
        )
    return pl.DataFrame(rows)


def _method_ladder(scored: pl.DataFrame) -> pl.DataFrame:
    score_rows = pl.concat(
        [
            _score_method_budget_metrics(scored, budget)
            for budget in active_config.review_budgets
        ],
        how="diagonal",
    )
    threshold_rows = evaluate_scores(scored, active_config).threshold_baseline_metrics
    threshold_rows = threshold_rows.with_columns(
        pl.col("baseline").str.replace("_", " ").alias("method"),
        pl.lit("manual threshold").alias("method_type"),
        pl.lit(float(active_config.review_budgets[0])).alias(MetricCol.K),
        (
            pl.col(MetricCol.DOLLARS_CAPTURED_AT_K)
            / max(
                float(
                    scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
                    .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
                    .item()
                    or 0.0,
                ),
                1.0,
            )
        ).alias(MetricCol.DOLLAR_CAPTURE_RATE),
    ).select(score_rows.columns)
    return pl.concat([threshold_rows, score_rows], how="diagonal")


def _threshold_error_summary(scored: pl.DataFrame) -> pl.DataFrame:
    rows = []
    total_anomalies = scored.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    for method, flag in THRESHOLD_FLAGS:
        reviewed = scored.filter(pl.col(flag) == 1)
        false_negatives = scored.filter(
            (pl.col(flag) == 0) & (pl.col(PayrollCol.IS_ANOMALY) == 1),
        )
        rows.append(
            {
                "method": method,
                MetricCol.REVIEW_VOLUME: reviewed.height,
                AggregateCol.TRUE_ANOMALIES: reviewed.filter(
                    pl.col(PayrollCol.IS_ANOMALY) == 1,
                ).height,
                "false_positives": reviewed.filter(
                    pl.col(PayrollCol.IS_ANOMALY) == 0,
                ).height,
                "false_negatives": false_negatives.height,
                "missed_anomaly_rate": false_negatives.height / max(total_anomalies, 1),
                "missed_synthetic_dollars": float(
                    false_negatives.select(pl.sum(PayrollCol.ANOMALY_DOLLARS)).item()
                    or 0.0,
                ),
            },
        )
    return pl.DataFrame(rows)


def _component_heatmap_data(scored: pl.DataFrame, *, top_n: int = 20) -> pl.DataFrame:
    latest_period = scored.select(pl.max(PayrollCol.PAY_PERIOD_INDEX)).item()
    top = (
        scored.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) == latest_period)
        .sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True)
        .with_row_index("queue_row", offset=1)
        .head(top_n)
        .select(
            [
                "queue_row",
                ScoreCol.RULE_SCORE,
                ScoreCol.STATISTICAL_SCORE,
                ScoreCol.SCHEDULE_TIMECLOCK_SCORE,
                ScoreCol.PREMIUM_ELIGIBILITY_SCORE,
                ScoreCol.ML_SCORE,
                ScoreCol.EXPOSURE_SCORE,
                ScoreCol.FINAL_ANOMALY_SCORE,
            ],
        )
    )
    return top.unpivot(
        index="queue_row",
        variable_name="component",
        value_name="score",
    )


# %% [markdown]
# ## Evaluation Design
#
# The ablation uses later-period synthetic labels only for evaluation. Scoring features remain leakage-safe and exclude injected labels, anomaly categories, and anomaly dollars. The operational metric is approval-budget ranking: what the system captures inside the number of records an administrator can realistically review each payroll cycle.

# %%
results.leakage_checks

# %% [markdown]
# ## Method-Complexity Ladder
#
# The ladder below separates the value of each method family. Manual thresholds are the baseline workflow; rules add deterministic SNF approval logic; robust statistics add peer/history context; ML adds multivariate unusualness; hybrid ranking combines those signals with exposure so the queue is useful under constrained review capacity.

# %%
method_ladder = _method_ladder(results.scored)
method_ladder.sort(
    [MetricCol.K, MetricCol.DOLLAR_CAPTURE_RATE],
    descending=[False, True],
)

# %%
top_budget = float(active_config.review_budgets[0])
budget_ladder = method_ladder.filter(pl.col(MetricCol.K) == top_budget).with_columns(
    (
        pl.col(MetricCol.EXPOSURE_CAPTURED_AT_K)
        / pl.max_horizontal(pl.col(MetricCol.REVIEW_VOLUME), pl.lit(1))
    ).alias("exposure_per_review"),
)
(
    ggplot(budget_ladder, aes("method", "exposure_per_review"))
    + geom_bar(aes(fill="method_type"), stat="identity")
    + labs(
        title="Incremental method value at the first approval budget",
        x="Method",
        y="Estimated exposure per reviewed record",
        fill="Method family",
    )
    + theme_minimal()
    + rotated_x_labels()
)

# %%
(
    ggplot(method_ladder, aes(MetricCol.K, MetricCol.DOLLAR_CAPTURE_RATE))
    + geom_line(aes(color="method"))
    + geom_point(aes(color="method"), size=3)
    + labs(
        title="Dollar capture improves or degrades as review budget changes",
        x="Review budget per pay period",
        y="Synthetic dollar capture rate",
        color="Method",
    )
    + theme_minimal()
)

# %% [markdown]
# ## Component Contribution Heatmap
#
# The heatmap makes hybrid ranking explainable at the record level. Rows are the top latest-period queue records. Columns show the major component scores that contribute to the final approval exception score.

# %%
component_heatmap = _component_heatmap_data(results.scored)
(
    ggplot(component_heatmap, aes("component", "queue_row", fill="score"))
    + geom_tile()
    + labs(
        title="Top queue records by score component",
        x="Score component",
        y="Latest-period queue row",
        fill="Score",
    )
    + theme_minimal()
    + rotated_x_labels()
)

# %% [markdown]
# ## Manual Threshold Error Modes
#
# This section intentionally uses evaluation-only synthetic labels. It shows why threshold review is fragile: a broad threshold can create many false positives, while a narrow threshold can leave synthetic anomaly dollars outside the review queue.

# %%
threshold_errors = _threshold_error_summary(results.scored)
threshold_errors.sort("missed_synthetic_dollars", descending=True)

# %%
(
    ggplot(threshold_errors, aes("method", "missed_synthetic_dollars"))
    + geom_bar(stat="identity", fill="#b45309")
    + labs(
        title="Evaluation-only synthetic dollars missed by manual thresholds",
        x="Manual threshold",
        y="Missed synthetic anomaly dollars",
    )
    + theme_minimal()
    + rotated_x_labels()
)

# %% [markdown]
# ## Temporal, Uncertainty, And Calibration Context
#
# A stronger data-science proof does not stop at one aggregate table. The views below check whether selected thresholds transfer over time, whether uncertainty buckets carry useful signal, and whether expected-pay intervals behave plausibly on synthetic evaluation records.

# %%
results.model_comparison

# %%
results.rolling_origin_metrics

# %%
(
    ggplot(results.rolling_origin_metrics, aes("test_period", MetricCol.PRECISION_AT_K))
    + geom_line()
    + geom_point(size=3)
    + labs(
        title="Rolling-origin approval-budget precision over time",
        x="Test pay period",
        y="Precision at selected budget",
    )
    + theme_minimal()
)

# %%
results.uncertainty_bucket_metrics

# %%
(
    ggplot(
        results.uncertainty_bucket_metrics,
        aes(ReviewCol.UNCERTAINTY_BUCKET, MetricCol.ANOMALY_RATE),
    )
    + geom_bar(stat="identity", fill="#2563eb")
    + labs(
        title="Evaluation anomaly rate by uncertainty bucket",
        x="Uncertainty bucket",
        y="Synthetic anomaly rate",
    )
    + theme_minimal()
)

# %%
results.risk_coverage_analysis

# %%
(
    ggplot(
        results.risk_coverage_analysis,
        aes(MetricCol.COVERAGE, MetricCol.REVIEW_PRECISION),
    )
    + geom_line()
    + geom_point(size=3)
    + labs(
        title="Risk-coverage diagnostic",
        x="Share of least-uncertain records retained",
        y="Review precision",
    )
    + theme_minimal()
)

# %%
results.expected_gross_pay_interval_metrics

# %% [markdown]
# ## What This Proves
#
# The ML score is useful because it can rank unusual multivariate combinations that do not reduce to one raw threshold. The hybrid score is the stronger product signal because payroll approval also needs deterministic policy rules, robust peer/history context, premium eligibility, schedule/timeclock evidence, uncertainty context, and estimated exposure. Simpler components remain valuable: rule and premium signals are strong in premium-heavy scenarios, while hybrid ranking is the deployable approval queue because it balances detection, actionability, and business impact.

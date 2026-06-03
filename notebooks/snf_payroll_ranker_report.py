# ---
# title: "SNF Payroll Ranker"
# format:
#   html:
#     page-layout: full
#     code-fold: true
#     code-tools: true
#     html-table-processing: none
#     include-in-header:
#         text: |
#         <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
#         <script>mermaid.initialize({startOnLoad:true});</script>
# jupyter: python3
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

# %%
# | eval: false
# | echo: false
# %load_ext autoreload
# %autoreload 2

# %%
import polars as pl
import polars.selectors as pl_selectors
from common.display import setup_notebook_html, setup_polars_display
from common.execution import notebook_validation_mode
from common.plots import (
    aes,
    coord_flip,
    geom_bar,
    geom_line,
    geom_point,
    geom_segment,
    geom_tile,
    gggrid,
    ggplot,
    ggtitle,
    labs,
    rotated_x_labels,
    scale_fill_gradient,
    theme_minimal,
)
from IPython.display import display

from payroll_anomaly_ranking.columns import MetricCol, PayrollCol, ReviewCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import (
    employee_cycle_hard_rule_funnel,
    employee_cycle_residual_diagnostics,
    generate_employee_pay_cycles,
)
from payroll_anomaly_ranking.evaluation import (
    bootstrap_residual_model_comparison,
    employee_cycle_backtest_by_period,
    employee_cycle_feature_ablation,
    employee_cycle_grouped_metrics,
    employee_cycle_issue_type_model_performance,
    employee_cycle_label_ablation,
    employee_cycle_severe_miss_examples,
    employee_cycle_training_universe_ablation,
    evaluate_employee_cycle_scores,
)
from payroll_anomaly_ranking.explainability import build_employee_cycle_review_queue
from payroll_anomaly_ranking.models import score_employee_pay_cycles
from payroll_anomaly_ranking.presentation import synthetic_schema_dictionary
from payroll_anomaly_ranking.scenario_benchmark import (
    run_employee_cycle_scenario_benchmark,
)
from payroll_anomaly_ranking.scenarios import diagnostic_scenario_catalog

# %%
setup_notebook_html()
setup_polars_display()
validation_mode = notebook_validation_mode()


# %%
def format_review_budget_pct(budget: float) -> str:
    return f"{budget:.0%}" if budget <= 1 else str(int(budget))


def build_residual_issue_rate_plot(facility_issue_rate: pl.DataFrame) -> object:
    plot_data = facility_issue_rate.with_columns(
        pl.col(PayrollCol.FACILITY_ID).cast(pl.String).alias("facility_id"),
        pl.col("residual_issue_rate").round(4),
    ).sort("residual_issue_rate")
    return (
        ggplot(
            plot_data,
            aes(x="facility_id", y="residual_issue_rate"),
        )
        + geom_bar(stat="identity", fill="#2563eb")
        + coord_flip()
        + theme_minimal()
        + labs(
            x="Facility",
            y="Residual issue rate",
        )
        + ggtitle("Residual Issue Rate by Facility")
    )


def build_severe_residual_heatmap(severe_counts: pl.DataFrame) -> object:
    plot_data = severe_counts.with_columns(
        pl.col(PayrollCol.FACILITY_ID).cast(pl.String).alias("facility_id"),
        pl.col(PayrollCol.PAY_PERIOD_INDEX).alias("pay_period"),
    )
    return (
        ggplot(
            plot_data,
            aes(
                x="pay_period",
                y="facility_id",
                fill="severe_residual_issues",
            ),
        )
        + geom_tile()
        + theme_minimal()
        + labs(
            x="Pay period",
            y="Facility",
            fill="Severe issues",
        )
        + scale_fill_gradient(low="#f8fafc", high="#b91c1c")
        + ggtitle("Severe Residual Issues by Facility-Cycle")
    )


def build_issue_type_mix_plot(issue_type_mix: pl.DataFrame) -> object:
    plot_data = issue_type_mix.with_columns(
        pl.col(PayrollCol.ANOMALY_CATEGORY).cast(pl.String).alias("anomaly_category"),
    ).sort([PayrollCol.ANOMALY_CATEGORY, "population"])
    return (
        ggplot(
            plot_data,
            aes(
                x="anomaly_category",
                y="records",
                fill="population",
            ),
        )
        + geom_bar(stat="identity", position="dodge")
        + coord_flip()
        + theme_minimal()
        + labs(
            x="Anomaly family",
            y="Records",
            fill="Population",
        )
        + ggtitle("Issue-Type Mix Across Hard-Rule and Residual Populations")
    )


def bootstrap_metric_title(metric_name: str) -> str:
    return {
        str(MetricCol.RESIDUAL_NDCG_AT_K): "Residual NDCG",
        str(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K): "Severe Recall",
        str(MetricCol.DOLLARS_CAPTURED_AT_K): "Dollars Captured",
        str(MetricCol.REVIEWER_YIELD_AT_K): "Reviewer Yield",
        str(MetricCol.INCREMENTAL_UTILITY_AT_K): "Incremental Utility",
    }.get(metric_name, metric_name)


def build_bootstrap_interval_plot(
    bootstrap_results: pl.DataFrame,
    metric_name: str,
    budget: float,
) -> object:
    plot_data = (
        bootstrap_results.filter(
            (pl.col("summary_type") == "model_metric")
            & (pl.col("budget") == budget)
            & (pl.col("metric") == metric_name),
        )
        .select("model", "point_estimate", "lower_95", "upper_95")
        .sort("point_estimate")
    )
    return (
        ggplot(
            plot_data,
            aes(x="model", y="point_estimate", color="model"),
        )
        + geom_segment(
            aes(
                x="model",
                xend="model",
                y="lower_95",
                yend="upper_95",
            ),
            size=1.1,
            alpha=0.7,
        )
        + geom_point(size=3)
        + coord_flip()
        + theme_minimal()
        + labs(
            x="Model",
            y="Point estimate with 95% interval",
            color="Model",
        )
        + ggtitle(
            f"{bootstrap_metric_title(metric_name)} at {format_review_budget_pct(budget)} Review",
        )
    )


def build_similarity_matrix(
    similarity_diagnostics: pl.DataFrame,
    value_col: str,
) -> pl.DataFrame:
    models = sorted(
        {
            *similarity_diagnostics.get_column("model_a").to_list(),
            *similarity_diagnostics.get_column("model_b").to_list(),
        },
    )
    pair_values = {
        frozenset((row["model_a"], row["model_b"])): float(row[value_col] or 0.0)
        for row in similarity_diagnostics.select(
            "model_a",
            "model_b",
            value_col,
        ).to_dicts()
    }
    rows: list[dict[str, float | str]] = []
    for left_model in models:
        for right_model in models:
            rows.append(
                {
                    "model_x": left_model,
                    "model_y": right_model,
                    value_col: 1.0
                    if left_model == right_model
                    else pair_values.get(frozenset((left_model, right_model)), 0.0),
                },
            )
    return pl.DataFrame(rows)


def build_similarity_heatmap(
    similarity_diagnostics: pl.DataFrame,
    value_col: str,
    title: str,
) -> object:
    plot_data = build_similarity_matrix(similarity_diagnostics, value_col)
    return (
        ggplot(
            plot_data,
            aes(x="model_x", y="model_y", fill=value_col),
        )
        + geom_tile()
        + theme_minimal()
        + rotated_x_labels()
        + scale_fill_gradient(low="#f8fafc", high="#0f766e")
        + labs(x="Model", y="Model", fill="Value")
        + ggtitle(title)
    )


# %% [markdown]
# ## 0. Executive Summary
#
# This notebook presents the SNF Payroll Ranker: an ML workflow for the second
# stage of SNF payroll review prioritization.
#
# Critical hard rules first remove obvious payroll violations. The remaining
# records form a residual queue of ambiguous payroll risks. The modeling
# question is:
#
# > Among payroll records not caught by hard rules, which ML formulation best
# > prioritizes records for human review under limited reviewer capacity?
#
# **Models compared**
#
# - classifier: ranks by probability of payroll issue
# - cost-sensitive classifier: ranks by severity-weighted issue probability
# - regressor: ranks by predicted dollar impact
# - expected-value model: ranks by probability x expected impact
# - learning-to-rank: ranks by graded residual relevance
#
# **Primary metrics**
#
# - residual NDCG@K
# - rule-missed severe recall@K
# - residual dollars captured@K
# - reviewer yield@K
# - incremental utility@K
#
# **Main finding**
#
# The main study evaluates model performance across multiple synthetic SNF
# payroll data-generating processes. In the current one-seed interim holdout
# benchmark, expected-value scoring is the most robust default for dollar
# recovery and incremental utility. Learning-to-rank is the strongest
# challenger when review capacity is tight and the objective is top-of-queue
# severity ordering.
#
# **Interpretation**
#
# There is no universal winner. Model choice depends on the operating
# objective: expected value for financial recovery, learning-to-rank for
# severity ordering, and classifier scores for calibrated issue-probability
# context.

# %% [markdown]
# ## 1. Problem Framing: Residual Payroll Review After Hard Rules
#
# Does ML add value after hard rules have already removed
# the obvious cases?
#
# **Production assumption**
#
# hard rules already catch impossible or obvious payroll records before
# the ML stage begins.
#
# **Modeling question**
#
# Among employee-pay-cycle records not caught by hard rules, which ML
# formulation best ranks the remaining payroll review candidates?
#
# **Queue framing**
#
# - item: employee-pay-cycle payroll record
# - group: facility x payroll cycle
# - business constraint: reviewers can inspect only a limited share of each residual queue
# - objective: maximize review value within the reviewed share of each residual queue
#
# **Scope discipline**
#
# This is a payroll loss-prevention project, not a staffing compliance project.
#
# Excluded from target and evaluation:
#
# - PBJ compliance labels
# - HPRD staffing metrics
# - regulatory staffing-risk scores
# - compliance severity weights
#
# Allowed as payroll context:
#
# - facility
# - role
# - pay period
# - timekeeping signals
# - payroll history
# - facility-role peer baselines
#
# **Out of scope**
#
# - optimizing the hard rules
# - ranking all payroll records before hard rules
# - evaluating a full hybrid production policy end to end
# - UI or workflow implementation
# - compliance, PBJ, and HPRD staffing metrics

# %% [markdown]
# ## 2. Synthetic DGP Design and Scenario Suite
#
# This section documents the synthetic DGP family used for the main study.
#
# The synthetic data supports two distinct populations:
#
# - hard-rule-caught obvious payroll issues
# - rule-missed residual issues that remain ambiguous after gating

# %% [markdown]
# ```mermaid
# flowchart LR
#     classDef source fill:#F8FAFC,stroke:#64748B,stroke-width:1px,color:#0F172A;
#     classDef gate fill:#FEF2F2,stroke:#DC2626,stroke-width:1px,color:#7F1D1D;
#     classDef residual fill:#F0FDF4,stroke:#16A34A,stroke-width:1px,color:#14532D;
#     classDef bias fill:#FFFBEB,stroke:#D97706,stroke-width:1px,color:#78350F,stroke-dasharray: 5 3;
#
#     subgraph world["Synthetic payroll world"]
#         facilities["Facility context<br/>region, size tier, payroll maturity"]:::source
#         employees["Employee population<br/>role, tenure, home facility"]:::source
#         payroll["Payroll and timekeeping generation<br/>hours, overtime, rate changes, edits"]:::source
#         facilities --> payroll
#         employees --> payroll
#     end
#
#     subgraph gate_stage["Hard-rule gate"]
#         critical["Critical rule violations"]:::gate
#         excluded["Excluded before ML"]:::gate
#     end
#
#     subgraph residual_stage["Residual ranking setup"]
#         residual["Residual payroll issues<br/>ambiguous risks that survive the gate"]:::residual
#         truth["Latent truth for evaluation"]:::residual
#         cycles["Employee-pay-cycle modeling table<br/>active ranking grain"]:::residual
#     end
#
#     observed["Observed corrections<br/>(biased reviewed subset)"]:::bias
#
#     payroll --> critical
#     payroll --> residual
#     critical --> excluded
#     residual -->|survives gate| cycles
#     residual --> truth
#     residual -->|historically reviewed subset| observed
#     observed -->|auxiliary historical signal| cycles
# ```
# %%
sim_config = PayrollConfig(
    facility_count=4 if validation_mode else 25,
    employee_count=150 if validation_mode else 1500,
    pay_periods=8 if validation_mode else 36,
    employee_cycle_review_budget_percents=(
        (0.01, 0.05) if validation_mode else (0.01, 0.03, 0.05, 0.10)
    ),
)
review_budget_percents = sim_config.employee_cycle_review_budget_percents or tuple(
    float(budget) for budget in sim_config.review_budgets
)

data = generate_employee_pay_cycles(sim_config)
funnel = employee_cycle_hard_rule_funnel(data.payroll)
residual_diagnostics = employee_cycle_residual_diagnostics(data.payroll)
residual_payroll = data.payroll.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)
hard_rule_flagged = data.payroll.filter(pl.col(PayrollCol.CRITICAL_HARD_RULE_FLAG) == 1)
scenario_benchmark = run_employee_cycle_scenario_benchmark(
    sim_config,
    seeds=(sim_config.seed,),
)
benchmark_recommendation_budget = (
    0.05 if 0.05 in review_budget_percents else review_budget_percents[0]
)


# %% [markdown]
# The scenario suite varies the synthetic data-generating process, not the
# model objective or review capacity. Review capacity is evaluated separately as
# an operating point.

# %%
scenario_benchmark.scenario_catalog.select(
    "display_name",
    "what_changes",
    "status",
)

# %% [markdown]
# ### snapshot

# %%
pl.DataFrame(
    {
        "metric": [
            "employee-pay-cycle records",
            "hard-rule flagged",
            "residual records",
            "residual issue rate",
            "residual severe issues",
            "residual dollars",
        ],
        "value": [
            float(data.payroll.height),
            float(hard_rule_flagged.height),
            float(residual_payroll.height),
            round(
                float(
                    residual_payroll.select(pl.mean(PayrollCol.Y_ISSUE)).item() or 0.0,
                ),
                4,
            ),
            float(
                residual_payroll.select(
                    pl.sum(PayrollCol.RULE_MISSED_SEVERE_ISSUE),
                ).item()
                or 0,
            ),
            round(
                float(
                    residual_payroll.select(pl.sum(PayrollCol.Y_DOLLAR)).item() or 0.0,
                ),
                2,
            ),
        ],
    },
)

# %% [markdown]
# ### schema example:

# %%
data.payroll.select(
    PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.FACILITY_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    PayrollCol.TOTAL_GROSS_PAY,
    PayrollCol.TOTAL_OVERTIME_HOURS,
    PayrollCol.CRITICAL_HARD_RULE_FLAG,
    PayrollCol.RESIDUAL_RECORD,
    PayrollCol.Y_ISSUE,
    PayrollCol.Y_DOLLAR,
).head()

# %% [markdown]
# ## 3. Hard Rule Gate: Defining the Residual Universe
#
# Hard rules are an upstream gate, not a competing model.
#
# **Critical hard rules**
#
# These filter records out of the ML universe. Examples include:
#
# - duplicate or overlapping shift
# - negative hours
# - gross pay equal to zero with positive hours
# - missing pay rate
# - physically impossible hours
# - terminated employee paid regular hours
#
# **Soft warning signals**
#
# These do not remove a record from the ML universe. They remain candidate input
# features because they are contextual info.
#
# Examples:
#
# - overtime above threshold
# - manual edit
# - missing punch
# - unusual facility pattern
# - pay-rate change
# - high gross pay versus employee baseline
#
# **Residual universe**
#
# The hard-rule gate removes records with critical deterministic violations. The
# remaining residual universe still contains a meaningful share of true issues
# and severe payroll-loss cases, but these cases are less obvious and require
# contextual ranking.
#
# The ML task is therefore:
#
# > Rank residual records within each facility x payroll cycle by expected
# > review value.

# %% [markdown]
# **Observed funnel summary**

# %%
funnel.with_columns(
    pl.col("pct_of_total").round(4),
    pl.col("dollar_impact").round(2),
)

# %% [markdown]
# ## 4. Simulation Sanity Checks for the Residual Dataset
#
# Before comparing models, the notebook checks whether the residual-ranking task
# changes meaningfully across the DGP suite.
#
# `Label-bias strength` measures the gap in observed-correction rates between
# higher-signal residual positives and lower-signal residual positives. Larger
# values mean historical review behavior is more selectively concentrated on the
# obvious end of the residual queue.

# %%
scenario_benchmark.scenario_summary.select(
    "display_name",
    "residual_issue_rate",
    "severe_issue_rate",
    "residual_dollars",
    "dominant_issue_family",
    "label_bias_strength",
).rename(
    {
        "display_name": "Scenario",
        "residual_issue_rate": "Residual issue rate",
        "severe_issue_rate": "Severe issue rate",
        "residual_dollars": "Residual dollars",
        "dominant_issue_family": "Dominant issue family",
        "label_bias_strength": "Label-bias strength",
    },
)

# %% [markdown]
# The detailed plots below stay focused on the baseline scenario as compact
# examples. The main experimental evidence comes from cross-scenario aggregation,
# not from any single residual dataset snapshot.

# %% [markdown]
# ### baseline example: residual issue rate by facility

# %%
build_residual_issue_rate_plot(residual_diagnostics["facility_residual_issue_rate"])

# %% [markdown]
# ### baseline example: severe residual issues by facility-cycle

# %%
build_severe_residual_heatmap(
    residual_diagnostics["facility_cycle_residual_severe_counts"],
)

# %% [markdown]
# ### baseline example: issue-type mix

# %%
build_issue_type_mix_plot(residual_diagnostics["issue_type_mix"])

# %% [markdown]
# ### top residual dollar records

# %% [markdown]
# Taken together, the scenario summary table and baseline illustrations show
# that the residual queue is not random cleanup noise. Residual issue density,
# severe tails, dominant issue families, and observed-label bias all move across
# DGP scenarios, which is why the main benchmark aggregates over scenario and
# seed units instead of picking a winner from one synthetic world.

# %%
residual_diagnostics["residual_dollar_distribution"].head(10)

# %% [markdown]
# ## 5. Label Engineering for Residual Ranking
#
# The labels in this notebook are defined for the post-gate ranking problem
# rather than the full payroll universe. In this run, the residual universe
# contains 46,307 records, including 2,314 residual issues and 211 rule-missed
# severe issues, so the label design needs to separate common ambiguous issues
# from the smaller severe tail.
#
# **Core labels**
#
# - `y_issue`: latent residual issue truth used by classifier models
# - `y_dollar`: residual dollar impact used by regression-style models
# - `severe_issue`: overall severe anomaly label used for funnel and upstream
#   gate reporting across all employee-pay-cycles
# - `relevance_grade`: graded residual relevance used by learning-to-rank
# - `rule_missed_severe_issue`: severe residual issue slice used in evaluation
# - `net_utility`: evaluation-only business value after review cost
# - `observed_correction`: biased historical review signal retained only for
#   bias analysis or auxiliary comparisons
#
# **Relevance grade definition**
#
# - `0`: no known residual issue
# - `1`: minor residual issue
# - `2`: material residual issue
# - `3`: severe rule-missed residual issue
#
# **Important note**
#
# `y_issue` means latent residual issue truth. It is not mixed with observed
# historical review outcomes. `severe_issue` tracks the full severe anomaly
# population for funnel accounting, while `rule_missed_severe_issue` is the
# narrower severe residual slice that survives the hard-rule gate and remains
# relevant for stage-2 model evaluation.

# %% [markdown]
# | Label | Column | Used by | Meaning |
# | --- | --- | --- | --- |
# | **residual issue** | `y_issue` | classifier, cost-sensitive classifier | latent residual issue truth after the hard-rule gate |
# | **residual dollar impact** | `y_dollar` | regressor, expected-value | financial impact if the residual issue is ignored |
# | **overall severe issue** | `severe_issue` | funnel reporting, gate diagnostics | severe anomaly regardless of whether a hard rule caught it |
# | **dominant category** | `anomaly_category` | diagnostics | highest-impact anomaly category still attached to the employee-pay-cycle |
# | **relevance grade** | `relevance_grade` | learning-to-rank | 0 to 3 residual review priority |
# | **rule-missed severe issue** | `rule_missed_severe_issue` | evaluation | key severe-issue slice that survived the hard-rule gate |
# | **observed correction** | `observed_correction` | bias analysis | biased reviewed-and-corrected historical subset |
# | **net utility** | `net_utility` | evaluation | residual business value minus review cost |

# %% [markdown]
# label examples

# %%
residual_payroll.select(
    PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
    PayrollCol.ANOMALY_CATEGORY,
    PayrollCol.CRITICAL_HARD_RULE_FLAG,
    PayrollCol.RESIDUAL_RECORD,
    PayrollCol.Y_ISSUE,
    PayrollCol.Y_DOLLAR,
    PayrollCol.RULE_MISSED_SEVERE_ISSUE,
    PayrollCol.RELEVANCE_GRADE,
    PayrollCol.OBSERVED_CORRECTION,
    PayrollCol.NET_UTILITY,
).unique(
    pl_selectors.all()
    - pl_selectors.matches("employee_pay_cycle_id|y_dollar|net_utility"),
).head(10)

# %% [markdown]
# ### label summary

# %%
residual_payroll.select(
    pl.len().alias("residual_records"),
    pl.sum(PayrollCol.Y_ISSUE).alias("residual_issues"),
    pl.sum(PayrollCol.RULE_MISSED_SEVERE_ISSUE).alias("rule_missed_severe_issues"),
    pl.mean(PayrollCol.Y_DOLLAR).round(2).alias("avg_residual_dollars"),
    pl.mean(PayrollCol.NET_UTILITY).round(2).alias("avg_net_utility"),
)


# %%
def build_residual_label_diagnostics(residual_records: pl.DataFrame) -> pl.DataFrame:
    positive_residual = residual_records.filter(pl.col(PayrollCol.Y_ISSUE) == 1)
    residual_issue_count = max(positive_residual.height, 1)
    grade_counts = {
        int(row[PayrollCol.RELEVANCE_GRADE]): int(row["records"])
        for row in positive_residual.group_by(PayrollCol.RELEVANCE_GRADE)
        .agg(pl.len().alias("records"))
        .to_dicts()
    }
    severe_count = int(
        positive_residual.select(pl.sum(PayrollCol.RULE_MISSED_SEVERE_ISSUE)).item()
        or 0,
    )
    return pl.DataFrame(
        {
            "diagnostic": [
                "residual issue count",
                "severe share of residual issues",
                "grade 1 share of residual issues",
                "grade 2 share of residual issues",
                "grade 3 share of residual issues",
                "distinct residual anomaly families",
            ],
            "value": [
                float(positive_residual.height),
                round(severe_count / residual_issue_count, 4),
                round(grade_counts.get(1, 0) / residual_issue_count, 4),
                round(grade_counts.get(2, 0) / residual_issue_count, 4),
                round(grade_counts.get(3, 0) / residual_issue_count, 4),
                float(
                    positive_residual.get_column(
                        PayrollCol.ANOMALY_CATEGORY,
                    ).n_unique(),
                ),
            ],
        },
    )


def build_residual_family_mix(residual_records: pl.DataFrame) -> pl.DataFrame:
    positive_residual = residual_records.filter(pl.col(PayrollCol.Y_ISSUE) == 1)
    issue_count = max(positive_residual.height, 1)
    return (
        positive_residual.group_by(PayrollCol.ANOMALY_CATEGORY)
        .agg(
            pl.len().alias("records"),
            pl.mean(PayrollCol.Y_DOLLAR).round(2).alias("avg_residual_dollars"),
            pl.mean(PayrollCol.RULE_MISSED_SEVERE_ISSUE).round(4).alias("severe_share"),
        )
        .with_columns(
            (pl.col("records") / issue_count)
            .round(4)
            .alias("share_of_residual_issues"),
        )
        .sort(["records", PayrollCol.ANOMALY_CATEGORY], descending=[True, False])
    )


residual_label_diagnostics = build_residual_label_diagnostics(residual_payroll)
residual_family_mix = build_residual_family_mix(residual_payroll)

# %% [markdown]
# ### residual label diagnostics

# %%
residual_label_diagnostics

# %% [markdown]
# ### residual anomaly-family mix

# %% [markdown]
# The residual label mix is dominated by material but non-severe issues: grade
# 2 accounts for most residual issues, while the severe grade-3 slice is much
# smaller. The residual problem is therefore broader than severe-case
# detection; it is a prioritization task with a smaller but important severe
# tail.
#
# The anomaly-family mix is also concentrated. `paid_vs_scheduled_mismatch` is
# the largest family by count, while `overtime_double_shift` is the most severe
# and dollar-heavy family, making it disproportionately important for top-of-
# queue review quality.

# %%
residual_family_mix

# %% [markdown]
# ## 6. Feature Engineering for Ambiguous Payroll Records

# %% [markdown]
# Because hard rules already remove obvious violations, the residual ranking
# problem depends on contextual and comparative features rather than
# deterministic failure signals. The feature set is designed to answer a
# narrower question: which surviving employee-pay-cycle records look most
# abnormal relative to the employee's history, local peers, and current-cycle
# context?

# %% [markdown]
# | Feature family | Examples | Why it matters in the residual queue |
# | --- | --- | --- |
# | Raw payroll | hours, overtime, gross pay, pay rate | baseline cycle-level payroll signal |
# | Employee history | hours versus trailing median, pay-rate change versus prior cycle | captures deviations from the employee's recent baseline |
# | Facility-role baseline | pay rate versus facility-role median, overtime versus role norm | captures local peer anomalies |
# | Timekeeping | missing punch, manual edit count, late entry | soft risk signals |
# | Cross-facility | unusual facility, same-day multi-facility pattern | duplicate or allocation risk |
# | Temporal | holiday cycle, vendor drift, staffing shock | seasonality and drift context |

# %%
scoring_results = score_employee_pay_cycles(data.payroll, sim_config)
scored = scoring_results.scored
residual_scored = scored.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)

# %% [markdown]
# ### feature families

# %% [markdown]
# | feature_family | examples | why_it_matters |
# | :--- | :--- | :--- |
# | raw payroll | total gross pay, total overtime hours, total premium pay, total paid hours | captures the basic cycle-level payroll signal that remains after hard-rule gating |
# | employee history | lag gross pay, gross pay pct change, prior employee pay-period count | catches employee-specific deviations from recent payroll history |
# | facility-role baseline | peer gross deviation ratio, peer overtime deviation ratio, facility premium share median | shows whether a cycle looks unusual relative to local role peers |
# | timekeeping and soft warnings | paid minus scheduled hours, premium eligibility mismatch, rest gap risk | retains ambiguous warning signals without treating them as deterministic failures |
# | cross-facility and peer context | cross-facility role median, peer gross median, effective peer reference size | detects unusual facility placement or peer-context changes |
# | temporal and robust context | gross pay robust z, gross pay mad score, gross pay percentile | adds stable outlier context that is less sensitive to raw dollar levels |

# %% [markdown]
# ### residual feature examples

# %%
residual_scored.sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True).select(
    PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
    PayrollCol.FACILITY_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    PayrollCol.TOTAL_GROSS_PAY,
    PayrollCol.TOTAL_EXPECTED_GROSS_PAY,
    PayrollCol.TOTAL_OVERTIME_HOURS,
    PayrollCol.TOTAL_PREMIUM_PAY,
    "gross_pay_pct_change",
    "peer_gross_deviation_ratio",
    "paid_minus_scheduled_hours",
    "gross_pay_robust_z",
    "premium_eligibility_mismatch",
).head(10)

# %% [markdown]
# ### leakage-safe contract

# %% [markdown]
# In other words, these features are meant to separate ambiguous-but-benign
# residual records from ambiguous-and-costly ones.

# %% [markdown]
# | contract_point | active_behavior |
# | :--- | :--- |
# | historical features | exclude the current and future pay periods |
# | peer baselines | use only scoring-time-available employee and facility context |
# | evaluation labels | remain excluded from employee-cycle model features |
# | hard-rule gate | defines the residual universe before model comparison begins |
# | soft warning features | remain allowed as ambiguous feature inputs after gating |
# | out-of-scope metrics | PBJ, HPRD, and compliance staffing metrics are excluded |

# %% [markdown]
# ## 7. Model Formulations
#
# This section compares alternative ML formulations on the same residual
# universe. Hard rules are the fixed upstream gate; the question here is which
# scoring objective produces the best review queue once obvious violations have
# already been removed.
#
# The comparison covers probability-first models, dollar-first models, and
# relevance-ranking models on the same residual universe. The goal here is to
# define the candidate formulations cleanly before interpreting queue results.

# %% [markdown]
# | Model | Training target | Queue score | Why it is included |
# | --- | --- | --- | --- |
# | Classifier | `y_issue` | `P(issue)` | baseline supervised model |
# | Cost-sensitive classifier | `y_issue` with severity-aware weights | weighted `P(issue)` | emphasizes costly or severe residual errors |
# | Regressor | `y_dollar` | predicted dollar impact | captures financial exposure |
# | Expected-value model | issue + impact | `P(issue) x E(impact \| issue)` | strong traditional ML baseline |
# | Learning-to-rank | `relevance_grade` | ranking score | directly optimizes residual queue order |

# %% [markdown]
# **Fair comparison rules**
#
# - same residual universe
# - same facility x payroll cycle grouping
# - same train and test splits
# - same top-K evaluation budgets
# - same leakage rules
#
# The notebook also reports `final_active_ranking`, a blended score used as a
# candidate production-style ranking. It is not treated as a separate modeling
# family; it is included later to show whether a blended production score adds
# value over the individual formulations.


# %%
def build_model_budget_metrics(
    scored_frame: pl.DataFrame,
    review_budgets: tuple[float, ...],
) -> pl.DataFrame:
    rows: list[dict[str, float | str]] = []
    for model_name, score_col in [
        ("classifier", ScoreCol.CLASSIFICATION_SCORE),
        ("cost_sensitive_classifier", ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE),
        ("regressor", ScoreCol.REGRESSION_SCORE),
        ("expected_value", ScoreCol.EXPECTED_VALUE_SCORE),
        ("learning_to_rank", ScoreCol.RANKING_SCORE),
        ("final_active_ranking", ScoreCol.FINAL_ANOMALY_SCORE),
    ]:
        scored_for_model = scored_frame.with_columns(
            pl.col(score_col).alias(ScoreCol.FINAL_ANOMALY_SCORE),
        )
        for budget in review_budgets:
            rows.append(
                {
                    "model": model_name,
                    "review_budget_label": format_review_budget_pct(budget),
                    **employee_cycle_grouped_metrics(scored_for_model, budget),
                },
            )
    return pl.DataFrame(rows)


def build_model_similarity_diagnostics(
    scored_frame: pl.DataFrame,
    review_budgets: tuple[float, ...],
) -> pl.DataFrame:
    residual_scored = scored_frame.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)
    comparison_budget = 0.05 if 0.05 in review_budgets else review_budgets[0]
    model_scores = [
        ("classifier", ScoreCol.CLASSIFICATION_SCORE),
        ("cost_sensitive_classifier", ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE),
        ("regressor", ScoreCol.REGRESSION_SCORE),
        ("expected_value", ScoreCol.EXPECTED_VALUE_SCORE),
        ("learning_to_rank", ScoreCol.RANKING_SCORE),
        ("final_active_ranking", ScoreCol.FINAL_ANOMALY_SCORE),
    ]
    group_cols = [PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX]

    def reviewed_records(score_col: ScoreCol, budget: float) -> pl.DataFrame:
        ranked = residual_scored.with_columns(
            pl.col(score_col)
            .rank("ordinal", descending=True)
            .over(group_cols)
            .alias("_group_rank"),
            pl.len().over(group_cols).alias("_group_size"),
        ).with_columns(
            (pl.col("_group_size") * budget)
            .ceil()
            .cast(pl.Int64)
            .clip(1, None)
            .alias("_group_budget_count"),
        )
        return ranked.filter(
            pl.col("_group_rank") <= pl.col("_group_budget_count"),
        ).select(
            *group_cols,
            PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
        )

    top_1_records = {
        model_name: reviewed_records(score_col, 0.01)
        for model_name, score_col in model_scores
    }
    budget_records = {
        model_name: reviewed_records(score_col, comparison_budget)
        for model_name, score_col in model_scores
    }

    rows: list[dict[str, float | str]] = []
    for index, (left_name, left_score) in enumerate(model_scores):
        for right_name, right_score in model_scores[index + 1 :]:
            top_1_overlap = top_1_records[left_name].join(
                top_1_records[right_name],
                on=group_cols + [PayrollCol.EMPLOYEE_PAY_CYCLE_ID],
                how="inner",
            ).height / max(top_1_records[left_name].height, 1)
            budget_overlap = budget_records[left_name].join(
                budget_records[right_name],
                on=group_cols + [PayrollCol.EMPLOYEE_PAY_CYCLE_ID],
                how="inner",
            ).height / max(budget_records[left_name].height, 1)
            correlation = float(
                residual_scored.select(
                    pl.corr(left_score, right_score).alias("correlation"),
                ).item()
                or 0.0,
            )
            rows.append(
                {
                    "model_a": left_name,
                    "model_b": right_name,
                    "score_correlation": round(correlation, 4),
                    "top_1_overlap": round(top_1_overlap, 4),
                    f"top_{format_review_budget_pct(comparison_budget)}_overlap": round(
                        budget_overlap,
                        4,
                    ),
                },
            )
    return pl.DataFrame(rows)


def notebook_model_label(model_name: str) -> str:
    return {
        str(ScoreCol.CLASSIFICATION_SCORE): "classifier",
        str(ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE): "cost_sensitive_classifier",
        str(ScoreCol.REGRESSION_SCORE): "regressor",
        str(ScoreCol.EXPECTED_VALUE_SCORE): "expected_value",
        str(ScoreCol.RANKING_SCORE): "learning_to_rank",
        "active_ranking": "final_active_ranking",
        str(ScoreCol.ML_SCORE): "isolation_forest",
    }.get(model_name, model_name)


evaluation = evaluate_employee_cycle_scores(scored, sim_config)
model_similarity_diagnostics = build_model_similarity_diagnostics(
    scored,
    review_budget_percents,
)
comparison_for_summary = evaluation.model_comparison.with_columns(
    pl.col("model").map_elements(notebook_model_label, return_dtype=pl.String),
)

# %%
bootstrap_summary = bootstrap_residual_model_comparison(
    scored,
    score_cols={
        "classifier": ScoreCol.CLASSIFICATION_SCORE,
        "cost_sensitive_classifier": ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
        "regressor": ScoreCol.REGRESSION_SCORE,
        "expected_value": ScoreCol.EXPECTED_VALUE_SCORE,
        "learning_to_rank": ScoreCol.RANKING_SCORE,
        "final_active_ranking": ScoreCol.FINAL_ANOMALY_SCORE,
    },
    budgets=(0.05,),
    n_bootstrap=10 if validation_mode else 500,
    seed=sim_config.seed,
)

# %% [markdown]
# ### formulation summary

# %%
pl.DataFrame(
    {
        "model": [
            "classifier",
            "cost_sensitive_classifier",
            "regressor",
            "expected_value",
            "learning_to_rank",
        ],
        "training_target": [
            str(PayrollCol.Y_ISSUE),
            f"{PayrollCol.Y_ISSUE} with severity-aware weights",
            str(PayrollCol.Y_DOLLAR),
            "y_issue + estimated exposure",
            str(PayrollCol.RELEVANCE_GRADE),
        ],
        "score_column": [
            str(ScoreCol.CLASSIFICATION_SCORE),
            str(ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE),
            str(ScoreCol.REGRESSION_SCORE),
            str(ScoreCol.EXPECTED_VALUE_SCORE),
            str(ScoreCol.RANKING_SCORE),
        ],
        "business_question": [
            "Which residual records are most likely to still contain a payroll issue?",
            "Which residual issue records deserve extra weight when severity and dollars matter?",
            "Which residual records imply the largest unresolved dollar impact?",
            "Which residual records combine issue likelihood with financial exposure?",
            "Which residual records deserve the strongest top-of-queue priority?",
        ],
    },
)

# %% [markdown]
# ### fair comparison rules

# %%
pl.DataFrame(
    {
        "rule": [
            "scoring universe",
            "queue grouping",
            "review budgets",
            "temporal framing",
            "leakage control",
            "cost-sensitive coverage",
        ],
        "applied_setting": [
            "residual records only for notebook comparison outputs",
            "facility x payroll cycle",
            ", ".join(format_review_budget_pct(k) for k in review_budget_percents),
            "same employee-cycle temporal split logic for all formulations",
            "evaluation labels remain excluded from feature columns",
            "cost-sensitive classifier is included alongside the standard classifier",
        ],
    },
)

# %% [markdown]
# ## 8. Main Study: DGP Scenario-Based Residual Ranking Benchmark
#
# The main study evaluates employee-pay-cycle residual ranking across DGP
# scenarios and seeds, then aggregates by model, review-budget operating point,
# and objective.
#
# Each DGP scenario is evaluated over multiple random seeds. Seeds estimate
# random-draw stability within the same payroll-generating process. They do not
# fix structural DGP bias. Structural robustness is assessed by comparing across
# DGP scenarios. The current rendered notebook keeps that design but runs an
# interim one-seed holdout benchmark for faster iteration.


# %%
def build_review_budget_diagnostics(
    residual_records_per_group: pl.DataFrame,
    review_budgets: tuple[float, ...],
) -> pl.DataFrame:
    rows: list[dict[str, float | str]] = []
    total_groups = max(residual_records_per_group.height, 1)
    for budget in review_budgets:
        reviewed_counts = residual_records_per_group.with_columns(
            (pl.col("residual_records") * budget if budget <= 1 else pl.lit(budget))
            .ceil()
            .cast(pl.Int64)
            .clip(1, None)
            .alias("reviewed_records"),
        )
        rows.append(
            {
                "review_budget_pct": format_review_budget_pct(budget),
                "avg_records_reviewed_per_group": round(
                    float(
                        reviewed_counts.select(pl.mean("reviewed_records")).item()
                        or 0.0,
                    ),
                    2,
                ),
                "pct_groups_fully_reviewed": round(
                    reviewed_counts.filter(
                        pl.col("reviewed_records") >= pl.col("residual_records"),
                    ).height
                    / total_groups,
                    4,
                ),
                "max_group_size": float(
                    reviewed_counts.select(pl.max("residual_records")).item() or 0,
                ),
            },
        )
    return pl.DataFrame(rows)


def build_model_budget_plot(
    metric_col: str,
    title: str,
    y_label: str,
) -> object:
    return (
        ggplot(
            model_budget_metrics,
            aes(
                x="review_budget_label",
                y=metric_col,
                color="model",
            ),
        )
        + geom_line()
        + geom_point()
        + theme_minimal()
        + rotated_x_labels()
        + labs(x="Residual queue reviewed", y=y_label, color="Model")
        + ggtitle(title)
    )


model_budget_metrics = build_model_budget_metrics(scored, review_budget_percents)
budget_diagnostics = build_review_budget_diagnostics(
    residual_diagnostics["residual_records_per_facility_cycle"],
    review_budget_percents,
)
backtest: pl.DataFrame | None = None
if not validation_mode:
    backtest = employee_cycle_backtest_by_period(scored, sim_config)

aggregate_winner_frequency = scenario_benchmark.winner_frequency
median_metric_summary = scenario_benchmark.median_metric_summary
winner_map = scenario_benchmark.winner_map

# %% [markdown]
# ### DGP scenario catalog

# %%
scenario_benchmark.scenario_catalog

# %% [markdown]
# ### scenario x seed design

# %%
scenario_benchmark.scenario_seed_design

# %% [markdown]
# ### aggregate winner frequency

# %%
aggregate_winner_frequency

# %% [markdown]
# ### median metric table with intervals

# %%
median_metric_summary

# %% [markdown]
# ### winner map by objective and review budget

# %%
(
    ggplot(
        winner_map,
        aes(x="review_budget_label", y="objective", fill="selection_value"),
    )
    + geom_tile()
    + theme_minimal()
    + rotated_x_labels()
    + labs(x="Review budget", y="Objective", fill="Winner value")
    + ggtitle("Winner Map by Objective and Review Budget")
)

# %% [markdown]
# The aggregated benchmark shows a split leaderboard rather than one universal
# winner. Expected value is the strongest default when dollar recovery and
# incremental utility matter most, while learning-to-rank is a stronger
# challenger when queue ordering at tight review budgets is the main objective.

# %%
winner_map

# %% [markdown]
# ### score comparison on residual records

# %%
residual_scored.select(
    PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
    PayrollCol.ANOMALY_CATEGORY,
    PayrollCol.Y_ISSUE,
    PayrollCol.Y_DOLLAR,
    PayrollCol.RELEVANCE_GRADE,
    ScoreCol.CLASSIFICATION_SCORE,
    ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
    ScoreCol.REGRESSION_SCORE,
    ScoreCol.EXPECTED_VALUE_SCORE,
    ScoreCol.RANKING_SCORE,
    ScoreCol.FINAL_ANOMALY_SCORE,
).sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True).head(10)

# %% [markdown]
# ### model similarity diagnostics

# %%
gggrid(
    [
        build_similarity_heatmap(
            model_similarity_diagnostics,
            "score_correlation",
            "Model Score Correlation",
        ),
        build_similarity_heatmap(
            model_similarity_diagnostics,
            "top_1_overlap",
            "Model Overlap at 1% Review",
        ),
        build_similarity_heatmap(
            model_similarity_diagnostics,
            f"top_{format_review_budget_pct(0.05 if 0.05 in review_budget_percents else review_budget_percents[0])}_overlap",
            "Model Overlap at Active Review Budget",
        ),
    ],
    ncol=2,
)

# %% [markdown]
# The overlap table shows a tight cluster at the top of the leaderboard. The
# blended `final_active_ranking` is extremely close to `learning_to_rank` and
# still highly correlated with the classifier, while the regressor is more
# behaviorally distinct. That is why expected value can win business metrics
# without requiring a radically different queue ordering.

# %% [markdown]
# ### temporal stability context

# %%
if backtest is not None:
    display(
        backtest.select(
            PayrollCol.PAY_PERIOD_INDEX,
            MetricCol.RESIDUAL_NDCG_AT_K,
            MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K,
            MetricCol.DOLLARS_CAPTURED_AT_K,
            MetricCol.REVIEWER_YIELD_AT_K,
            MetricCol.INCREMENTAL_UTILITY_AT_K,
        ).sort(PayrollCol.PAY_PERIOD_INDEX),
    )

# %% [markdown]
# The expected-value model wins because the residual task is heavily financial:
# high-priority records are not merely likely to be wrong, but costly when
# ignored. The learning-to-rank model is competitive on graded relevance, but
# expected-value better balances issue probability and dollar impact in the
# holdout benchmark. For payroll loss prevention, direct business-value scoring
# can matter as much as ranking-specific objectives.

# %% [markdown]
# The severe residual tail is concentrated rather than broad. `overtime_double_shift`
# accounts for a small share of residual issues but a disproportionate share of
# severe and high-dollar cases in this simulation. Severe-recall results should
# therefore be interpreted as performance on a concentrated high-dollar tail
# rather than broad severe-risk detection. The issue-family diagnostics and
# ablations are included to keep that dependency visible. A severe-family
# diversification stress test would be the next robustness extension if this
# benchmark is expanded.

# %% [markdown]
# ## 9. Ablation Studies
#
# Ablations in this notebook are residual-specific.
#
# **9.1 Feature ablation**
#
# Which feature families still matter after hard rules remove obvious records?
# In the full run, raw payroll alone is weak, employee history and facility-role
# baselines add only modest lift, and the biggest performance jump comes from
# timekeeping and soft-warning context. Temporal robust-stat features do not add
# further lift beyond that larger timekeeping improvement in this run.
#
# **9.2 Label ablation**
#
# Does the model winner change depending on how residual risk is defined? Yes,
# but the changes are interpretable. The classifier remains the strongest pure
# issue-probability signal, expected value wins the dollar- and utility-aware
# views, and the active blended ranking performs best on graded queue-ordering
# views built around latent residual truth.
#
# **9.3 Training universe ablation**
#
# Should models be trained on all records or only residual records? The updated
# holdout-only ablation now shows a real difference: training on all records is
# slightly worse than specializing to residual records, while training on all
# records with the hard-rule flag available recovers part of that gap without
# overtaking the residual-only setup. That suggests the broad universe is only
# modestly helpful when the model can explicitly adapt to the gate, and that the
# residual-only training universe remains the strongest option in this holdout
# ablation.
#
# **9.4 Validation split ablation**
#
# Does the residual model generalize to future cycles and unseen facilities? The
# temporal backtest still shows useful residual ranking value across many future
# pay periods, but severe recall is episodic and varies substantially by period,
# so the recommendation should be framed as strong but not uniform across every
# holdout cycle.

# %%
feature_ablation: pl.DataFrame | None = None
training_universe_ablation: pl.DataFrame | None = None
label_ablation: pl.DataFrame | None = None
if not validation_mode:
    feature_ablation = employee_cycle_feature_ablation(data.payroll, sim_config)
    training_universe_ablation = employee_cycle_training_universe_ablation(
        data.payroll,
        sim_config,
    )
    label_ablation = employee_cycle_label_ablation(scored, sim_config)

# %% [markdown]
# ### 9.1 feature-family ablation
#
# Question: after hard rules remove obvious violations, do contextual features
# still add value?
#
# Why it matters: if raw payroll features perform nearly as well, the residual
# problem is probably too easy. If contextual features create most of the lift,
# the simulation provides a better case for ML.

# %%
if feature_ablation is not None:
    display(
        feature_ablation.with_columns(
            pl.col(MetricCol.RESIDUAL_NDCG_AT_K).round(4),
            pl.col(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K).round(4),
            pl.col(MetricCol.DOLLARS_CAPTURED_AT_K).round(2),
            pl.col(MetricCol.REVIEWER_YIELD_AT_K).round(4),
            pl.col(MetricCol.INCREMENTAL_UTILITY_AT_K).round(2),
        ),
    )

# %% [markdown]
# ### 9.2 label-oriented winner summary
#
# Question: does the model winner change depending on how residual risk is
# defined?
#
# Why it matters: the notebook should show whether the recommendation is robust
# to issue-oriented, dollar-oriented, or graded-priority formulations.

# %%
if label_ablation is not None:
    display(
        label_ablation.with_columns(
            pl.col("selection_value").round(4),
        ),
    )

# %% [markdown]
# ### 9.3 training-universe ablation
#
# Question: should a residual-stage model train on all payroll records or
# specialize to records that survive the hard-rule gate?
#
# Why it matters: this directly tests the strategic choice between broader
# training coverage and a residual-only model tuned to the stage-2 queue.

# %%
if training_universe_ablation is not None:
    display(
        training_universe_ablation.with_columns(
            pl.col("train_hard_rule_share").round(4),
            pl.col(MetricCol.RESIDUAL_NDCG_AT_K).round(4),
            pl.col(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K).round(4),
            pl.col(MetricCol.DOLLARS_CAPTURED_AT_K).round(2),
            pl.col(MetricCol.REVIEWER_YIELD_AT_K).round(4),
            pl.col(MetricCol.INCREMENTAL_UTILITY_AT_K).round(2),
        ),
    )

# %% [markdown]
# ### 9.4 validation split ablation via temporal backtest
#
# Question: does the residual model generalize to future payroll cycles instead
# of only fitting the current synthetic sample?
#
# Why it matters: a good residual queue model must hold up under temporal shift,
# not just within a single pooled split.

# %%
if backtest is not None:
    display(
        pl.DataFrame(
            {
                "diagnostic": [
                    "evaluated pay periods",
                    "min residual ndcg",
                    "max residual ndcg",
                    "min severe recall",
                    "max severe recall",
                ],
                "value": [
                    float(backtest.height),
                    round(
                        float(
                            backtest.select(pl.min(MetricCol.RESIDUAL_NDCG_AT_K)).item()
                            or 0.0,
                        ),
                        4,
                    ),
                    round(
                        float(
                            backtest.select(pl.max(MetricCol.RESIDUAL_NDCG_AT_K)).item()
                            or 0.0,
                        ),
                        4,
                    ),
                    round(
                        float(
                            backtest.select(
                                pl.min(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K),
                            ).item()
                            or 0.0,
                        ),
                        4,
                    ),
                    round(
                        float(
                            backtest.select(
                                pl.max(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K),
                            ).item()
                            or 0.0,
                        ),
                        4,
                    ),
                ],
            },
        ),
    )

# %% [markdown]
# The ablation pattern answers a different question than the main comparison.
# In this run, raw payroll alone is weak and far below the best feature sets,
# even though it remains utility-positive. Most of the lift comes from adding
# timekeeping and soft-warning context, which materially improves NDCG, severe
# recall, and business value. The training-universe comparison stays fairly
# tight even on holdout periods, which suggests the hard-rule gate is
# functioning as a clean upstream filter rather than a source of ambiguous
# examples the models still need to learn around.

# %% [markdown]
# ## 10. Diagnostics, Explanations, and Final Recommendation
#
# This section brings together the residual-task diagnostics, reviewer-facing
# examples, and the final recommendation. The goal is to explain not only which
# model wins, but also why the winner is plausible and where the remaining
# misses still come from.

# %%
review_queue_examples = build_employee_cycle_review_queue(
    scored,
    top_k=0.05 if 0.05 in review_budget_percents else review_budget_percents[0],
)
issue_type_model_performance: pl.DataFrame | None = None
severe_miss_examples: pl.DataFrame | None = None
if not validation_mode:
    issue_type_model_performance = employee_cycle_issue_type_model_performance(
        scored,
        0.05 if 0.05 in review_budget_percents else review_budget_percents[0],
    )
    severe_miss_examples = employee_cycle_severe_miss_examples(
        scored,
        0.05 if 0.05 in review_budget_percents else review_budget_percents[0],
        limit_per_model=3,
    )

final_recommendation_summary = pl.DataFrame(
    {
        "objective": [
            "best residual severity ordering",
            "best residual dollar recovery",
            "strongest issue-probability diagnostic",
            "best production default",
        ],
        "recommended_model": [
            winner_map.filter(
                (pl.col("objective") == "severity_ordering")
                & (pl.col(MetricCol.K) == benchmark_recommendation_budget),
            )["winner"][0],
            winner_map.filter(
                (pl.col("objective") == "dollar_recovery")
                & (pl.col(MetricCol.K) == benchmark_recommendation_budget),
            )["winner"][0],
            comparison_for_summary.top_k(1, by=MetricCol.PR_AUC)["model"][0],
            winner_map.filter(
                (pl.col("objective") == "incremental_utility")
                & (pl.col(MetricCol.K) == benchmark_recommendation_budget),
            )["winner"][0],
        ],
        "why": [
            "Strongest aggregate severity ordering across scenario-seed holdout benchmark units.",
            "Best aggregate recovery of residual dollar impact across DGP scenarios at the active benchmark budget.",
            "Strongest residual issue-probability ranking among comparable models.",
            "Most robust default for incremental utility across the holdout scenario benchmark.",
        ],
    },
)

# %% [markdown]
# ### issue-type performance by model

# %%
if issue_type_model_performance is not None:
    display(
        issue_type_model_performance.with_columns(
            pl.col(MetricCol.RECALL_AT_K).round(4),
            pl.col(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K).round(4),
            pl.col(MetricCol.DOLLAR_CAPTURE_RATE).round(4),
        ),
    )

# %% [markdown]
# ### severe residual miss examples

# %%
if severe_miss_examples is not None:
    display(severe_miss_examples)

# %% [markdown]
# ### reviewer-facing queue examples

# %%
review_queue_examples.select(
    ReviewCol.RANK,
    PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.FACILITY_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    ReviewCol.APPROVAL_RISK_CATEGORY,
    ReviewCol.RECOMMENDED_ACTION,
    ReviewCol.SOURCE_TO_CHECK,
    ReviewCol.PRIMARY_REASON,
    ReviewCol.SECONDARY_REASON,
    ScoreCol.FINAL_ANOMALY_SCORE,
    ScoreCol.CLASSIFICATION_SCORE,
    ScoreCol.EXPECTED_VALUE_SCORE,
    ScoreCol.RANKING_SCORE,
    ReviewCol.EXPLANATION,
).head(10)

# %% [markdown]
# ### limitations
#
# This benchmark uses synthetic payroll data, so model conclusions should be
# interpreted as evidence about modeling strategy rather than production
# performance claims.
#
# Key limitations:
#
# - issue rates and dollar impacts are simulation assumptions
# - severe residual issues are concentrated in a small number of anomaly families
# - observed corrections are simulated rather than real reviewer actions
# - feature distributions may not fully match a real SNF operator
# - real deployment would require adjudicated review samples and monitoring by facility, role, and pay period

# %% [markdown]
# ### final recommendation

# %%
final_recommendation_summary

# %% [markdown]
# ## Final Recommendation
#
# For residual SNF payroll loss prevention after hard-rule screening,
# `expected_value` remains the strongest production default in the aggregated
# synthetic benchmark because it is the most robust model for dollar recovery
# and incremental utility across DGP scenarios. `learning_to_rank` remains the
# strongest challenger when top-of-queue severity ordering is the main goal.
#
# Recommended deployment pattern:
#
# 1. Keep critical hard rules upstream as deterministic controls.
# 2. Score only the residual universe with ML.
# 3. Use expected-value scoring as the default residual queue ranker.
# 4. Track learning-to-rank as a challenger for top-of-queue severity ordering.
# 5. Display reviewer-facing reason codes, issue probability, and expected dollar impact.
# 6. Monitor performance by facility, pay period, and issue family.
# 7. Periodically audit random residual records to reduce label bias.

# %% [markdown]
# ## 11. Technical Appendix


# %%
def build_appendix_data_dictionary() -> pl.DataFrame:
    base_dictionary = synthetic_schema_dictionary().with_columns(
        pl.col("field_name").cast(pl.String),
        pl.lit("base_synthetic_payroll").alias("section_role"),
        pl.lit("schema_and_validation").alias("used_for"),
        pl.when(pl.col("type_or_category") == "evaluation label")
        .then(pl.lit("yes"))
        .otherwise(pl.lit("no"))
        .alias("evaluation_only"),
    )
    employee_cycle_rows = pl.DataFrame(
        [
            {
                "field_name": str(PayrollCol.EMPLOYEE_PAY_CYCLE_ID),
                "business_meaning": "Synthetic employee-pay-cycle identifier",
                "type_or_category": "identifier",
                "privacy_sensitivity": "Low; synthetic only",
                "validation_expectation": "Required and non-null",
                "section_role": "queue_item",
                "used_for": "grouped ranking and review queue",
                "evaluation_only": "no",
            },
            {
                "field_name": str(PayrollCol.PAY_PERIOD_INDEX),
                "business_meaning": "Synthetic payroll cycle index",
                "type_or_category": "time index",
                "privacy_sensitivity": "Low",
                "validation_expectation": "Required and ordered for temporal evaluation",
                "section_role": "queue_group",
                "used_for": "temporal split and grouped ranking",
                "evaluation_only": "no",
            },
            {
                "field_name": str(PayrollCol.TOTAL_GROSS_PAY),
                "business_meaning": "Employee-pay-cycle total gross pay",
                "type_or_category": "numeric",
                "privacy_sensitivity": "Medium synthetic compensation",
                "validation_expectation": "Non-negative under normal cases",
                "section_role": "cycle_rollup",
                "used_for": "features, examples, and diagnostics",
                "evaluation_only": "no",
            },
            {
                "field_name": str(PayrollCol.TOTAL_EXPECTED_GROSS_PAY),
                "business_meaning": "Expected employee-pay-cycle gross pay baseline",
                "type_or_category": "numeric",
                "privacy_sensitivity": "Medium synthetic compensation",
                "validation_expectation": "Available for each cycle",
                "section_role": "expected_pay_context",
                "used_for": "gross-gap diagnostics and exposure context",
                "evaluation_only": "no",
            },
            {
                "field_name": str(PayrollCol.TOTAL_OVERTIME_HOURS),
                "business_meaning": "Employee-pay-cycle total overtime hours",
                "type_or_category": "numeric",
                "privacy_sensitivity": "Medium",
                "validation_expectation": "Non-negative",
                "section_role": "cycle_rollup",
                "used_for": "features and review context",
                "evaluation_only": "no",
            },
            {
                "field_name": str(PayrollCol.CRITICAL_HARD_RULE_FLAG),
                "business_meaning": "Critical gate flag that removes obvious cycles before ML",
                "type_or_category": "gate flag",
                "privacy_sensitivity": "Low",
                "validation_expectation": "Binary indicator",
                "section_role": "gate",
                "used_for": "defines the residual ML universe",
                "evaluation_only": "no",
            },
            {
                "field_name": str(PayrollCol.RESIDUAL_RECORD),
                "business_meaning": "Indicator that the cycle survives the hard-rule gate",
                "type_or_category": "gate flag",
                "privacy_sensitivity": "Low",
                "validation_expectation": "Binary indicator",
                "section_role": "gate",
                "used_for": "residual-only evaluation scope",
                "evaluation_only": "no",
            },
            {
                "field_name": str(PayrollCol.Y_ISSUE),
                "business_meaning": "Latent residual issue truth after the hard-rule gate",
                "type_or_category": "evaluation label",
                "privacy_sensitivity": "Internal synthetic label",
                "validation_expectation": "Binary indicator",
                "section_role": "label",
                "used_for": "classification targets and evaluation",
                "evaluation_only": "yes",
            },
            {
                "field_name": str(PayrollCol.Y_DOLLAR),
                "business_meaning": "Residual dollar impact if the issue is not reviewed",
                "type_or_category": "evaluation label",
                "privacy_sensitivity": "Internal synthetic label",
                "validation_expectation": "Non-negative for positive residual issues",
                "section_role": "label",
                "used_for": "regression targets and dollar capture evaluation",
                "evaluation_only": "yes",
            },
            {
                "field_name": str(PayrollCol.RULE_MISSED_SEVERE_ISSUE),
                "business_meaning": "Severe residual issue that survives the hard-rule gate",
                "type_or_category": "evaluation label",
                "privacy_sensitivity": "Internal synthetic label",
                "validation_expectation": "Binary indicator",
                "section_role": "label",
                "used_for": "severe recall evaluation",
                "evaluation_only": "yes",
            },
            {
                "field_name": str(PayrollCol.RELEVANCE_GRADE),
                "business_meaning": "Residual review priority grade from 0 to 3",
                "type_or_category": "graded label",
                "privacy_sensitivity": "Internal synthetic label",
                "validation_expectation": "Integer in [0, 3]",
                "section_role": "label",
                "used_for": "learning-to-rank target and NDCG evaluation",
                "evaluation_only": "yes",
            },
            {
                "field_name": str(PayrollCol.NET_UTILITY),
                "business_meaning": "Residual business value net of review cost",
                "type_or_category": "evaluation label",
                "privacy_sensitivity": "Internal synthetic label",
                "validation_expectation": "Signed numeric value",
                "section_role": "label",
                "used_for": "incremental utility evaluation",
                "evaluation_only": "yes",
            },
            {
                "field_name": str(ScoreCol.CLASSIFICATION_SCORE),
                "business_meaning": "Predicted residual issue probability",
                "type_or_category": "model score",
                "privacy_sensitivity": "Low",
                "validation_expectation": "Bounded to [0, 1] after scoring",
                "section_role": "score",
                "used_for": "classifier queue ordering",
                "evaluation_only": "no",
            },
            {
                "field_name": str(ScoreCol.EXPECTED_VALUE_SCORE),
                "business_meaning": "Expected-value ranking score combining issue likelihood and exposure",
                "type_or_category": "model score",
                "privacy_sensitivity": "Low",
                "validation_expectation": "Bounded to [0, 1] after scoring",
                "section_role": "score",
                "used_for": "dollar-aware queue ordering",
                "evaluation_only": "no",
            },
            {
                "field_name": str(ScoreCol.RANKING_SCORE),
                "business_meaning": "Learning-to-rank score trained on graded residual priority",
                "type_or_category": "model score",
                "privacy_sensitivity": "Low",
                "validation_expectation": "Bounded to [0, 1] after scoring",
                "section_role": "score",
                "used_for": "graded queue ordering",
                "evaluation_only": "no",
            },
            {
                "field_name": str(ScoreCol.FINAL_ANOMALY_SCORE),
                "business_meaning": "Final active blended ranking score used for queue examples",
                "type_or_category": "model score",
                "privacy_sensitivity": "Low",
                "validation_expectation": "Bounded to [0, 1] after scoring",
                "section_role": "score",
                "used_for": "active queue ordering",
                "evaluation_only": "no",
            },
            {
                "field_name": str(ScoreCol.ESTIMATED_EXPOSURE),
                "business_meaning": "Estimated employee-pay-cycle exposure used for value-aware ranking",
                "type_or_category": "derived score input",
                "privacy_sensitivity": "Medium synthetic compensation",
                "validation_expectation": "Non-negative",
                "section_role": "score_context",
                "used_for": "expected-value scoring and evaluation context",
                "evaluation_only": "no",
            },
        ],
    )
    return (
        pl.concat([base_dictionary, employee_cycle_rows], how="diagonal_relaxed")
        .unique(subset=["field_name"], keep="first")
        .sort(["section_role", "field_name"])
    )


def build_appendix_hard_rule_definitions() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "rule_name": "terminated_employee_paid",
                "code_condition": "employment_status == terminated and gross_pay > 0",
                "gate_effect": "critical_hard_rule_flag = 1",
                "why_critical": "Obvious lifecycle violation removed before residual ranking",
            },
            {
                "rule_name": "duplicate_signature",
                "code_condition": "duplicate employee x shift_date x shift_type x facility x pay_code x gross_pay signature",
                "gate_effect": "critical_hard_rule_flag = 1",
                "why_critical": "Obvious duplicate payroll signature should not compete in ML ranking",
            },
            {
                "rule_name": "nonpositive_active_pay",
                "code_condition": "employment_status == active and gross_pay <= 0",
                "gate_effect": "critical_hard_rule_flag = 1",
                "why_critical": "Active paid cycle with nonpositive gross pay is treated as a hard failure",
            },
            {
                "rule_name": "negative_net_pay",
                "code_condition": "net_pay < 0",
                "gate_effect": "critical_hard_rule_flag = 1",
                "why_critical": "Negative net pay is too obvious for residual ranking",
            },
            {
                "rule_name": "net_exceeds_gross",
                "code_condition": "net_pay > gross_pay * 1.05",
                "gate_effect": "critical_hard_rule_flag = 1",
                "why_critical": "Implausible net-to-gross relationship is gated out upstream",
            },
            {
                "rule_name": "physically_impossible_paid_hours",
                "code_condition": "paid_hours > 24.0",
                "gate_effect": "critical_hard_rule_flag = 1",
                "why_critical": "Impossible within-day hours are removed before ML",
            },
            {
                "rule_name": "paid_hours_missing_rate",
                "code_condition": "paid_hours > 0 and pay_rate <= 0 or missing",
                "gate_effect": "critical_hard_rule_flag = 1",
                "why_critical": "Paid work without a valid rate is treated as a hard payroll defect",
            },
            {
                "rule_name": "paid_minus_scheduled_exceeds_threshold",
                "code_condition": "worked_hours - scheduled_hours > paid_vs_scheduled_threshold",
                "gate_effect": "critical_hard_rule_flag = 1",
                "why_critical": "Large schedule mismatch is handled as an upstream gate rather than residual ambiguity",
            },
        ],
    )


def build_appendix_metric_definitions() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "metric": str(MetricCol.RESIDUAL_NDCG_AT_K),
                "scope": "residual only",
                "aggregation": "mean across facility x pay_period groups",
                "numerator_or_gain": "DCG of ranked relevance_grade values within each group budget",
                "denominator_or_reference": "ideal DCG for the same group budget",
                "zero_positive_behavior": "group contributes 0 when ideal DCG is 0",
            },
            {
                "metric": str(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K),
                "scope": "residual only",
                "aggregation": "global over reviewed residual rows",
                "numerator_or_gain": "reviewed rule_missed_severe_issue count",
                "denominator_or_reference": "all rule_missed_severe_issue count in residual evaluation frame",
                "zero_positive_behavior": "returns 0 when total severe count is 0",
            },
            {
                "metric": str(MetricCol.DOLLARS_CAPTURED_AT_K),
                "scope": "residual positives only",
                "aggregation": "global sum over reviewed residual rows",
                "numerator_or_gain": "sum of y_dollar on reviewed residual issue rows",
                "denominator_or_reference": "reported directly; capture rate uses total residual y_dollar",
                "zero_positive_behavior": "returns 0 when no residual dollars exist",
            },
            {
                "metric": str(MetricCol.REVIEWER_YIELD_AT_K),
                "scope": "residual only",
                "aggregation": "global reviewed share",
                "numerator_or_gain": "reviewed residual rows with y_issue == 1",
                "denominator_or_reference": "all reviewed residual rows",
                "zero_positive_behavior": "returns 0 when no rows are reviewed",
            },
            {
                "metric": str(MetricCol.INCREMENTAL_UTILITY_AT_K),
                "scope": "residual only",
                "aggregation": "global sum over reviewed residual rows",
                "numerator_or_gain": "sum of net_utility on reviewed rows",
                "denominator_or_reference": "reported directly rather than normalized",
                "zero_positive_behavior": "returns 0 when no rows are reviewed",
            },
            {
                "metric": str(MetricCol.PRECISION_AT_K),
                "scope": "residual only",
                "aggregation": "mean across facility x pay_period groups",
                "numerator_or_gain": "group true positives",
                "denominator_or_reference": "group reviewed rows",
                "zero_positive_behavior": "group denominator clipped to at least 1",
            },
            {
                "metric": str(MetricCol.RECALL_AT_K),
                "scope": "residual only",
                "aggregation": "mean across facility x pay_period groups",
                "numerator_or_gain": "group true positives",
                "denominator_or_reference": "group residual positives",
                "zero_positive_behavior": "group denominator clipped to at least 1",
            },
            {
                "metric": str(MetricCol.PR_AUC),
                "scope": "residual only",
                "aggregation": "single residual-frame summary",
                "numerator_or_gain": "average_precision_score over y_issue and final score",
                "denominator_or_reference": "not a ratio table metric",
                "zero_positive_behavior": "falls back to 0 on degenerate label cases",
            },
        ],
    )


def build_appendix_group_construction(
    review_budgets: tuple[float, ...],
) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "component": "ranking item",
                "active_definition": str(PayrollCol.EMPLOYEE_PAY_CYCLE_ID),
            },
            {
                "component": "ranking group",
                "active_definition": f"{PayrollCol.FACILITY_ID} x {PayrollCol.PAY_PERIOD_INDEX}",
            },
            {
                "component": "evaluation scope",
                "active_definition": f"{PayrollCol.RESIDUAL_RECORD} == 1 only",
            },
            {
                "component": "default budget framing",
                "active_definition": ", ".join(
                    format_review_budget_pct(budget) for budget in review_budgets
                ),
            },
            {
                "component": "percent budget conversion",
                "active_definition": "ceil(group_size * budget) with minimum 1 reviewed row per non-empty group",
            },
            {
                "component": "score ordering",
                "active_definition": f"descending {ScoreCol.FINAL_ANOMALY_SCORE} within each group",
            },
        ],
    )


def build_appendix_zero_positive_policy() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "case": "group recall with zero residual positives",
                "implemented_behavior": "group_anomalies denominator is clipped to at least 1",
                "result": "group recall becomes 0 instead of undefined",
            },
            {
                "case": "group NDCG with zero ideal gain",
                "implemented_behavior": "if ideal DCG is 0, group NDCG is set to 0",
                "result": "all-negative groups remain in the grouped average",
            },
            {
                "case": "global severe recall with zero severe residual issues",
                "implemented_behavior": "denominator uses max(total_severe, 1.0)",
                "result": "reported severe recall is 0 instead of undefined",
            },
            {
                "case": "PR-AUC on degenerate residual labels",
                "implemented_behavior": "ValueError is caught and PR-AUC is set to 0",
                "result": "notebook remains executable under degenerate slices",
            },
            {
                "case": "tiny percent budgets on non-empty groups",
                "implemented_behavior": "review budget count is clipped to a minimum of 1",
                "result": "every non-empty facility-cycle group contributes at least one reviewed row",
            },
        ],
    )


def build_appendix_model_settings() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "model": "classifier",
                "estimator_or_logic": "HistGradientBoostingClassifier",
                "current_fixed_settings": "max_depth=3, random_state=config.seed",
                "documented_future_tuning_space": "max_depth, learning_rate, max_leaf_nodes, min_samples_leaf",
            },
            {
                "model": "cost_sensitive_classifier",
                "estimator_or_logic": "HistGradientBoostingClassifier with sample weights",
                "current_fixed_settings": "max_depth=3 plus issue-dollar-severity weighting",
                "documented_future_tuning_space": "classifier settings plus weight multipliers",
            },
            {
                "model": "regressor",
                "estimator_or_logic": "HistGradientBoostingRegressor",
                "current_fixed_settings": "max_depth=3, lower_bound=0.0, random_state=config.seed",
                "documented_future_tuning_space": "max_depth, learning_rate, max_leaf_nodes, min_samples_leaf",
            },
            {
                "model": "learning_to_rank proxy",
                "estimator_or_logic": "HistGradientBoostingRegressor on relevance_grade",
                "current_fixed_settings": "max_depth=3, lower_bound=0.0, upper_bound=3.0",
                "documented_future_tuning_space": "same regressor settings plus alternative graded targets",
            },
            {
                "model": "expected_value",
                "estimator_or_logic": "minmax(estimated_exposure * clip(classification, 0.05, 1.0))",
                "current_fixed_settings": "classification floor=0.05 before multiplication",
                "documented_future_tuning_space": "classification floor, exposure formula, calibration strategy",
            },
            {
                "model": "final_active_ranking",
                "estimator_or_logic": "weighted blend",
                "current_fixed_settings": "0.45 ranking + 0.15 classification + 0.15 cost_sensitive + 0.10 regression + 0.15 expected_value",
                "documented_future_tuning_space": "blend weights selected on validation periods rather than fixed constants",
            },
            {
                "model": "isolation_forest",
                "estimator_or_logic": "IsolationForest",
                "current_fixed_settings": "n_estimators=100, contamination=0.03, random_state=config.seed",
                "documented_future_tuning_space": "n_estimators, contamination, max_samples",
            },
        ],
    )


def build_appendix_score_bucket_calibration(
    scored_frame: pl.DataFrame,
    bucket_count: int = 10,
) -> pl.DataFrame:
    residual_frame = scored_frame.filter(
        pl.col(PayrollCol.RESIDUAL_RECORD) == 1,
    ).with_columns(
        pl.col(ScoreCol.FINAL_ANOMALY_SCORE)
        .qcut(bucket_count, allow_duplicates=True)
        .alias("score_bucket"),
        (
            pl.col(PayrollCol.TOTAL_GROSS_PAY)
            - pl.col(PayrollCol.TOTAL_EXPECTED_GROSS_PAY)
        ).alias("gross_gap"),
    )
    return (
        residual_frame.group_by("score_bucket", maintain_order=True)
        .agg(
            pl.len().alias("records"),
            pl.mean(ScoreCol.FINAL_ANOMALY_SCORE).round(4).alias("avg_score"),
            pl.mean(PayrollCol.Y_ISSUE).round(4).alias("issue_rate"),
            pl.mean(PayrollCol.Y_DOLLAR).round(2).alias("avg_residual_dollars"),
            pl.mean("gross_gap").round(2).alias("avg_gross_gap"),
            pl.mean(ScoreCol.ESTIMATED_EXPOSURE)
            .round(2)
            .alias("avg_estimated_exposure"),
        )
        .with_row_index("bucket_rank", offset=1)
    )


def build_appendix_stress_test_config(
    config: PayrollConfig,
    review_budgets: tuple[float, ...],
    validation_mode: bool,
) -> pl.DataFrame:
    scenario_catalog = diagnostic_scenario_catalog()
    scenario_rows = [
        {
            "artifact": "scenario_catalog",
            "name": scenario.name,
            "status": str(scenario.metadata.get("status", "unknown")),
            "detail": str(scenario.metadata.get("description", "")),
        }
        for scenario in scenario_catalog.values()
    ]
    config_rows = [
        {
            "artifact": "runtime_config",
            "name": "validation_mode",
            "status": "enabled" if validation_mode else "disabled",
            "detail": "Reduced workload for notebook execution checks"
            if validation_mode
            else "Full notebook research workload",
        },
        {
            "artifact": "runtime_config",
            "name": "facility_count",
            "status": str(config.facility_count),
            "detail": "Synthetic facility count for this notebook run",
        },
        {
            "artifact": "runtime_config",
            "name": "employee_count",
            "status": str(config.employee_count),
            "detail": "Synthetic employee population for this notebook run",
        },
        {
            "artifact": "runtime_config",
            "name": "pay_periods",
            "status": str(config.pay_periods),
            "detail": "Synthetic payroll cycles used for temporal evaluation",
        },
        {
            "artifact": "runtime_config",
            "name": "review_budget_percents",
            "status": ", ".join(
                format_review_budget_pct(budget) for budget in review_budgets
            ),
            "detail": "Grouped review budgets for the scenario-based residual ranking benchmark",
        },
        {
            "artifact": "runtime_config",
            "name": "scenario_seed_design",
            "status": "1 seed x 8 scenarios",
            "detail": "Interim notebook default; benchmark helper remains multi-seed capable for expanded runs",
        },
        {
            "artifact": "runtime_config",
            "name": "reference_window_periods",
            "status": str(config.reference_window_periods),
            "detail": "Prior periods used for scoring-time context",
        },
        {
            "artifact": "runtime_config",
            "name": "bootstrap_samples",
            "status": str(config.bootstrap_samples),
            "detail": "Configured uncertainty bootstrap count available in project config",
        },
    ]
    return pl.DataFrame(config_rows + scenario_rows)


appendix_data_dictionary = build_appendix_data_dictionary()
appendix_hard_rule_definitions = build_appendix_hard_rule_definitions()
appendix_metric_definitions = build_appendix_metric_definitions()
appendix_group_construction = build_appendix_group_construction(review_budget_percents)
appendix_zero_positive_policy = build_appendix_zero_positive_policy()
appendix_model_settings = build_appendix_model_settings()
appendix_score_bucket_calibration = build_appendix_score_bucket_calibration(scored)
appendix_stress_test_config = build_appendix_stress_test_config(
    sim_config,
    review_budget_percents,
    validation_mode,
)

# %% [markdown]
# ### A. data dictionary

# %%
appendix_data_dictionary

# %% [markdown]
# ### B. hard rule definitions

# %%
appendix_hard_rule_definitions

# %% [markdown]
# ### C. metric definitions

# %%
appendix_metric_definitions

# %% [markdown]
# ### D. ranking group construction

# %%
appendix_group_construction

# %% [markdown]
# ### E. handling zero-positive residual groups

# %%
appendix_zero_positive_policy

# %% [markdown]
# ### F. model settings and documented tuning space

# %%
appendix_model_settings

# %% [markdown]
# ### G. additional ablation tables

# %%
if feature_ablation is not None:
    display(feature_ablation)

# %%
if training_universe_ablation is not None:
    display(training_universe_ablation)

# %%
if label_ablation is not None:
    display(label_ablation)

# %%
if backtest is not None:
    display(backtest)

# %% [markdown]
# ### H. score-bucket calibration diagnostics

# %%
appendix_score_bucket_calibration

# %%
(
    ggplot(
        appendix_score_bucket_calibration,
        aes(x="bucket_rank", y="issue_rate"),
    )
    + geom_line()
    + geom_point()
    + theme_minimal()
    + labs(x="Score bucket", y="Residual issue rate")
    + ggtitle("Residual Issue Rate by Final-Score Bucket")
)

# %%
(
    ggplot(
        appendix_score_bucket_calibration,
        aes(x="bucket_rank", y="avg_residual_dollars"),
    )
    + geom_line()
    + geom_point()
    + theme_minimal()
    + labs(x="Score bucket", y="Average residual dollars")
    + ggtitle("Residual Dollars by Final-Score Bucket")
)

# %%
(
    ggplot(
        appendix_score_bucket_calibration,
        aes(x="bucket_rank", y="avg_gross_gap"),
    )
    + geom_line()
    + geom_point()
    + theme_minimal()
    + labs(x="Score bucket", y="Average gross gap")
    + ggtitle("Gross Gap by Final-Score Bucket")
)

# %% [markdown]
# ### I. stress-test configurations

# %%
appendix_stress_test_config

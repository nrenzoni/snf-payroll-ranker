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
import json
import shutil
from dataclasses import replace
from pathlib import Path

import polars as pl
from common.display import setup_notebook_html, setup_polars_display
from common.execution import load_cached_or_calc, notebook_validation_mode
from common.plots import (
    aes,
    coord_flip,
    geom_bar,
    geom_errorbar,
    geom_line,
    geom_point,
    geom_tile,
    gggrid,
    ggplot,
    ggtitle,
    labs,
    rotated_x_labels,
    scale_fill_gradient,
    theme_minimal,
)
from common.progress import TqdmProgress
from IPython.display import display

from payroll_anomaly_ranking.columns import MetricCol, PayrollCol, ReviewCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import (
    employee_cycle_hard_rule_funnel,
    employee_cycle_residual_diagnostics,
    generate_employee_pay_cycles,
)
from payroll_anomaly_ranking.evaluation import (
    employee_cycle_backtest_by_period,
    employee_cycle_feature_ablation,
    employee_cycle_issue_type_model_performance,
    employee_cycle_label_ablation,
    employee_cycle_model_comparison,
    employee_cycle_severe_miss_examples,
    employee_cycle_training_universe_ablation,
    evaluate_employee_cycle_scores,
)
from payroll_anomaly_ranking.explainability import build_employee_cycle_review_queue
from payroll_anomaly_ranking.models import score_employee_pay_cycles
from payroll_anomaly_ranking.scenario_benchmark import (
    ScenarioBenchmarkResults,
    run_employee_cycle_scenario_benchmark,
)
from payroll_anomaly_ranking.scenarios import (
    diagnostic_scenario_catalog,
    implemented_dgp_scenario_catalog,
)

# %%
setup_notebook_html()
setup_polars_display()
validation_mode = notebook_validation_mode()
progress = TqdmProgress(disable=validation_mode)

# LightGBM learning-to-rank can otherwise use all host CPU threads during full
# benchmark runs. Increase only when the host has spare cores and memory.
NOTEBOOK_LTR_NUM_THREADS = 1 if validation_mode else 8


# %%
def format_review_budget_pct(budget: float) -> str:
    return f"{budget:.0%}" if budget <= 1 else str(int(budget))


NOTEBOOK_DIR = (
    Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
)
CACHE_DIR = NOTEBOOK_DIR / "data" / "cache"


SCENARIO_BENCHMARK_CACHE_FRAMES = (
    "scenario_catalog",
    "scenario_seed_design",
    "scenario_summary",
    "metric_units",
    "winner_frequency",
    "median_metric_summary",
    "winner_map",
)


def read_scenario_benchmark_cache(cache_path: Path) -> ScenarioBenchmarkResults:
    missing_frames = [
        frame_name
        for frame_name in SCENARIO_BENCHMARK_CACHE_FRAMES
        if not (cache_path / f"{frame_name}.parquet").exists()
    ]
    if missing_frames:
        missing = ", ".join(missing_frames)
        raise FileNotFoundError(
            f"Incomplete scenario benchmark cache at {cache_path}; missing {missing}",
        )

    frames = {
        frame_name: pl.read_parquet(cache_path / f"{frame_name}.parquet")
        for frame_name in SCENARIO_BENCHMARK_CACHE_FRAMES
    }
    return ScenarioBenchmarkResults(**frames)


def write_scenario_benchmark_cache(
    cache_path: Path,
    result: ScenarioBenchmarkResults,
) -> None:
    tmp_path = cache_path.with_name(f".{cache_path.name}.tmp")
    if tmp_path.exists():
        shutil.rmtree(tmp_path)
    tmp_path.mkdir(parents=True)

    for frame_name in SCENARIO_BENCHMARK_CACHE_FRAMES:
        frame = getattr(result, frame_name)
        frame.write_parquet(tmp_path / f"{frame_name}.parquet")

    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "cache_type": "ScenarioBenchmarkResults",
                "format": "polars-parquet-directory",
                "frames": list(SCENARIO_BENCHMARK_CACHE_FRAMES),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    tmp_path.replace(cache_path)


# %% [markdown]
# ## 0. Executive Summary
#
# Decision question: after deterministic hard rules remove obvious payroll
# violations, which model should rank the remaining SNF payroll records for
# limited human review?
#
# Across the current scenario benchmark, probability-based models -- especially
# the cost-sensitive classifier -- are the most robust winners for queue quality
# and utility under the implemented DGPs. Expected-value scoring remains the
# most conceptually aligned model for payroll loss prevention, but its current
# implementation does not consistently beat the classifier family across
# scenario-seed results. The next modeling iteration should focus on improving
# expected-value calibration and exposure estimation.

# %% [markdown]
# ## 1. Decision Context: Residual Review After Hard Rules
#
# Hard rules are the first-stage control. They catch impossible or obvious
# payroll defects before ML begins. The model ranks only the **residual review
# queue**: employee-pay-cycle records that survive the gate, grouped within
# facility x payroll cycle review queues.
#
# The objective is payroll loss prevention, not staffing compliance. PBJ, HPRD,
# and regulatory staffing-risk metrics are excluded from targets and evaluation;
# facility, role, pay-period, timekeeping, payroll-history, and peer context
# remain allowed as payroll signals.

# %% [markdown]
# ## 2. Benchmark Design: Stressing Residual Review Conditions
#
# The benchmark uses synthetic SNF payroll data so latent residual truth,
# dollar impact, severe misses, and label bias are observable for evaluation.
# Scenarios vary issue density, severe-tail rate, dollar exposure, issue mix,
# and historical label bias. Review budget and model objective are evaluated as
# operating choices, not scenario definitions.

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
# Validation mode is a CI execution check, not an analytical run. Keep enough
# data to exercise model training, grouped ranking, temporal splits, and plot
# code while avoiding the full scenario x seed x model workload.
#
# `pay_periods=6` is intentional: below 6 periods, rolling-origin temporal
# diagnostics are empty by design, so 6 is the smallest useful setting for
# validating temporal-path assumptions without paying full notebook cost.
# A single review budget is enough to cover grouped-budget code paths in CI.
sim_config = PayrollConfig(
    facility_count=3 if validation_mode else 25,
    employee_count=60 if validation_mode else 1500,
    pay_periods=6 if validation_mode else 36,
    ltr_num_threads=NOTEBOOK_LTR_NUM_THREADS,
    employee_cycle_review_budget_percents=(
        (0.05,) if validation_mode else (0.01, 0.03, 0.05, 0.10)
    ),
)
review_budget_percents = sim_config.employee_cycle_review_budget_percents or tuple(
    float(budget) for budget in sim_config.review_budgets
)
# The scenario benchmark uses the default holdout splitter, which needs eight
# periods for its 4-period validation and 4-period test windows. Keep the main
# validation data at six periods, but raise only the reduced benchmark workload.
scenario_benchmark_config = replace(
    sim_config,
    pay_periods=8 if validation_mode else sim_config.pay_periods,
)

# %%
data = generate_employee_pay_cycles(sim_config, progress=progress)

# %%
funnel = employee_cycle_hard_rule_funnel(data.payroll)
residual_diagnostics = employee_cycle_residual_diagnostics(data.payroll)

# %%
residual_payroll = data.payroll.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)
hard_rule_flagged = data.payroll.filter(pl.col(PayrollCol.CRITICAL_HARD_RULE_FLAG) == 1)

# %%
scenario_benchmark_seeds = (
    (sim_config.seed,)
    if validation_mode
    else tuple(sim_config.seed + offset for offset in range(5))
)
# In validation mode, exercise the default scenario plus one scenario with drift
# controls. The full implemented scenario catalog is analysis-oriented and is
# the dominant CI runtime cost because each scenario retrains every model family.
scenario_benchmark_scenarios = None
if validation_mode:
    implemented_scenarios = implemented_dgp_scenario_catalog()
    scenario_benchmark_scenarios = {
        name: implemented_scenarios[name]
        for name in ("baseline-operations", "temporal-payroll-drift")
    }

# %%
scenario_benchmark = load_cached_or_calc(
    CACHE_DIR
    / (
        "scenario_benchmark_validation"
        if validation_mode
        else "scenario_benchmark_full"
    ),
    lambda: run_employee_cycle_scenario_benchmark(
        scenario_benchmark_config,
        scenarios=scenario_benchmark_scenarios,
        seeds=scenario_benchmark_seeds,
        progress=progress,
    ),
    read=read_scenario_benchmark_cache,
    write=write_scenario_benchmark_cache,
)

# %%
benchmark_recommendation_budget = (
    0.05 if 0.05 in review_budget_percents else review_budget_percents[0]
)


# %% [markdown]
# ## 3. Hard-Rule Gate: Defining the Residual Review Queue
#
# Hard rules are an upstream gate, not a competing model. They remove critical
# deterministic violations before ML ranking. Soft warnings remain eligible as
# contextual model features because they are ambiguous after gating.
#
# The model task is therefore:
#
# > Rank residual review queue records within each facility x payroll cycle by
# > expected review value.

# %% [markdown]
# **Observed funnel summary**


# %%
hard_rule_funnel_plot_data = funnel.with_columns(
    pl.col("stage").cast(pl.String),
    pl.col("records").cast(pl.Float64),
)
(
    ggplot(hard_rule_funnel_plot_data, aes(x="stage", y="records", fill="stage"))
    + geom_bar(stat="identity")
    + coord_flip()
    + theme_minimal()
    + labs(x="Gate stage", y="Employee-pay-cycle records", fill="Stage")
    + ggtitle("Hard-Rule Gate Narrows the ML Review Universe")
)

# %% [markdown]
# ## 4. Residual Ranking Setup
#
# The residual review queue is not a simple fraud/no-fraud problem. The same
# record can matter because it is likely wrong, because it has high dollar
# impact, or because it is a severe miss that survived hard rules.
#
# The benchmark therefore compares three practical model families:
#
# - **Probability models**: rank records by residual issue likelihood.
# - **Value models**: rank records by issue likelihood combined with dollar exposure.
# - **Learning-to-rank models**: rank records by graded residual review priority within facility x payroll cycle.
#
# Historical observed corrections are retained for bias analysis only. They are
# not treated as ground truth.hard_rule_funnel_plot_data = funnel.with_columns(
#     pl.col("stage").cast(pl.String),
#     pl.col("records").cast(pl.Float64),
# )
# (
#     ggplot(hard_rule_funnel_plot_data, aes(x="stage", y="records", fill="stage"))
#     + geom_bar(stat="identity")
#     + coord_flip()
#     + theme_minimal()
#     + labs(x="Gate stage", y="Employee-pay-cycle records", fill="Stage")
#     + ggtitle("Hard-Rule Gate Narrows the ML Review Universe")
# )

# %%
scenario_summary_compact = scenario_benchmark.scenario_summary.select(
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


# %%
scenario_landscape_plot_data = scenario_benchmark.scenario_summary.with_columns(
    pl.col("display_name").cast(pl.String).alias("scenario"),
    pl.col("dominant_issue_family").cast(pl.String),
    pl.col("residual_issue_rate").round(4),
    pl.col("severe_issue_rate").round(4),
    pl.col("residual_dollars").round(2),
)
(
    ggplot(
        scenario_landscape_plot_data,
        aes(
            x="residual_issue_rate",
            y="severe_issue_rate",
            size="residual_dollars",
            color="dominant_issue_family",
        ),
    )
    + geom_point(alpha=0.75)
    + theme_minimal()
    + labs(
        x="Residual issue rate",
        y="Severe residual issue rate",
        size="Residual dollars",
        color="Dominant issue family",
    )
    + ggtitle("Scenario Landscape: Density, Severity, Dollars, and Mix")
)

# %% [markdown]
# The scenario landscape shows why the benchmark aggregates over scenario and
# seed units instead of picking a winner from one synthetic world. The residual
# issue mix below explains why the same model need not win every objective.


# %%
positive_residual = residual_payroll.filter(pl.col(PayrollCol.Y_ISSUE) == 1)
residual_issue_count = max(positive_residual.height, 1)
grade_counts = {
    int(row[PayrollCol.RELEVANCE_GRADE]): int(row["records"])
    for row in positive_residual.group_by(PayrollCol.RELEVANCE_GRADE)
    .agg(pl.len().alias("records"))
    .to_dicts()
}
severe_count = int(
    positive_residual.select(pl.sum(PayrollCol.RULE_MISSED_SEVERE_ISSUE)).item() or 0,
)
residual_label_diagnostics = pl.DataFrame(
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
residual_family_mix = (
    positive_residual.group_by(PayrollCol.ANOMALY_CATEGORY)
    .agg(
        pl.len().alias("records"),
        pl.mean(PayrollCol.Y_DOLLAR).round(2).alias("avg_residual_dollars"),
        pl.mean(PayrollCol.RULE_MISSED_SEVERE_ISSUE).round(4).alias("severe_share"),
    )
    .with_columns(
        (pl.col("records") / residual_issue_count)
        .round(4)
        .alias("share_of_residual_issues"),
    )
    .sort(["records", PayrollCol.ANOMALY_CATEGORY], descending=[True, False])
)


# %%
residual_family_pareto_plot_data = residual_family_mix.with_columns(
    pl.col(PayrollCol.ANOMALY_CATEGORY).cast(pl.String).alias("anomaly_family"),
    pl.col("share_of_residual_issues").round(4),
).sort("share_of_residual_issues")
(
    ggplot(
        residual_family_pareto_plot_data,
        aes(
            x="anomaly_family",
            y="share_of_residual_issues",
            fill="severe_share",
        ),
    )
    + geom_bar(stat="identity")
    + coord_flip()
    + theme_minimal()
    + scale_fill_gradient(low="#dbeafe", high="#991b1b")
    + labs(
        x="Residual anomaly family",
        y="Share of residual issues",
        fill="Severe share",
    )
    + ggtitle("Residual Issue Mix Is Concentrated but Not One-Dimensional")
)

# %% [markdown]
# Most residual issues are material but non-severe; the severe tail is smaller
# but operationally important. The ranking problem is therefore broader than
# severe-case detection.
#
# `paid_vs_scheduled_mismatch` is the largest family by count, while
# `overtime_double_shift` is the most severe and dollar-heavy family. That split
# is the main reason probability, value, and severity objectives can point to
# different rankers.

# %%
scoring_results = score_employee_pay_cycles(data.payroll, sim_config, progress=progress)

# %%
scored = scoring_results.scored
residual_scored = scored.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)

# %% [markdown]
# Contextual features separate ambiguous-but-benign residual records from
# ambiguous-and-costly ones. The comparison uses the same residual scoring
# universe, train/test split, facility x payroll cycle grouping, review budgets,
# and leakage rules for every primary model family.

# %% [markdown]
# ## 5. Main Results: Which Ranker Wins By Objective
#
# The main study evaluates residual review queues across DGP scenarios and
# seeds, then aggregates by model, review budget, and operating objective.
#
# Seeds estimate random-draw stability within a scenario. Scenario comparisons
# test structural robustness across different payroll-generating conditions.


# %%
# Full employee-cycle evaluation includes rolling-origin and production-readiness
# diagnostics that are useful for analysis but redundant for CI notebook runtime
# checks. Validation mode only needs the downstream model-comparison contract.
if validation_mode:
    model_comparison = employee_cycle_model_comparison(scored, sim_config)
else:
    evaluation = evaluate_employee_cycle_scores(scored, sim_config, progress=progress)
    model_comparison = evaluation.model_comparison

# %%
comparison_budget = (
    0.05 if 0.05 in review_budget_percents else review_budget_percents[0]
)
model_scores = [
    ("classifier", ScoreCol.CLASSIFICATION_SCORE),
    ("cost_sensitive_classifier", ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE),
    ("regressor", ScoreCol.REGRESSION_SCORE),
    ("expected_value", ScoreCol.EXPECTED_VALUE_SCORE),
    ("learning_to_rank", ScoreCol.RANKING_SCORE),
]
group_cols = [PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX]
top_1_records = {
    model_name: residual_scored.with_columns(
        pl.col(score_col)
        .rank("ordinal", descending=True)
        .over(group_cols)
        .alias("_group_rank"),
        pl.len().over(group_cols).alias("_group_size"),
    )
    .with_columns(
        (pl.col("_group_size") * 0.01)
        .ceil()
        .cast(pl.Int64)
        .clip(1, None)
        .alias("_group_budget_count"),
    )
    .filter(pl.col("_group_rank") <= pl.col("_group_budget_count"))
    .select(*group_cols, PayrollCol.EMPLOYEE_PAY_CYCLE_ID)
    for model_name, score_col in model_scores
}
budget_records = {
    model_name: residual_scored.with_columns(
        pl.col(score_col)
        .rank("ordinal", descending=True)
        .over(group_cols)
        .alias("_group_rank"),
        pl.len().over(group_cols).alias("_group_size"),
    )
    .with_columns(
        (pl.col("_group_size") * comparison_budget)
        .ceil()
        .cast(pl.Int64)
        .clip(1, None)
        .alias("_group_budget_count"),
    )
    .filter(pl.col("_group_rank") <= pl.col("_group_budget_count"))
    .select(*group_cols, PayrollCol.EMPLOYEE_PAY_CYCLE_ID)
    for model_name, score_col in model_scores
}
similarity_rows: list[dict[str, float | str]] = []
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
        similarity_rows.append(
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
model_similarity_diagnostics = pl.DataFrame(similarity_rows)

# %%
notebook_model_labels = {
    str(ScoreCol.CLASSIFICATION_SCORE): "classifier",
    str(ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE): "cost_sensitive_classifier",
    str(ScoreCol.REGRESSION_SCORE): "regressor",
    str(ScoreCol.EXPECTED_VALUE_SCORE): "expected_value",
    str(ScoreCol.RANKING_SCORE): "learning_to_rank",
}
comparison_for_summary = model_comparison.with_columns(
    pl.col("model").replace_strict(
        notebook_model_labels,
        default=pl.col("model"),
        return_dtype=pl.String,
    ),
).filter(
    pl.col("model").is_in(
        [
            "classifier",
            "cost_sensitive_classifier",
            "regressor",
            "expected_value",
            "learning_to_rank",
        ],
    ),
)

# %%
backtest: pl.DataFrame | None = None
if not validation_mode:
    backtest = employee_cycle_backtest_by_period(scored, sim_config, progress=progress)

# %%
primary_benchmark_models = [
    "classifier",
    "cost_sensitive_classifier",
    "regressor",
    "expected_value",
    "learning_to_rank",
]
primary_objective_map = pl.DataFrame(
    {
        "objective": [
            "severity_ordering",
            "dollar_recovery",
            "incremental_utility",
            "queue_quality",
        ],
        "metric": [
            str(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K),
            str(MetricCol.DOLLARS_CAPTURED_AT_K),
            str(MetricCol.INCREMENTAL_UTILITY_AT_K),
            str(MetricCol.RESIDUAL_NDCG_AT_K),
        ],
    },
)
primary_metric_units = scenario_benchmark.metric_units.filter(
    pl.col("model").is_in(primary_benchmark_models),
)


primary_metric_units_with_objectives = primary_metric_units.join(
    primary_objective_map,
    on="metric",
    how="inner",
)
primary_unit_winners = (
    primary_metric_units_with_objectives.sort(
        ["objective", MetricCol.K, "unit", "value", "model"],
        descending=[False, False, False, True, False],
    )
    .group_by(["objective", MetricCol.K, "unit"], maintain_order=True)
    .head(1)
)
primary_total_units = max(
    primary_unit_winners.select(pl.n_unique("unit")).item() or 0,
    1,
)
aggregate_winner_frequency = (
    primary_unit_winners.group_by(
        ["objective", MetricCol.K, "review_budget_label", "model"],
    )
    .agg(
        pl.len().alias("win_count"),
        (pl.len() / primary_total_units).round(4).alias("win_frequency"),
    )
    .sort(
        ["objective", MetricCol.K, "win_count", "model"],
        descending=[False, False, True, False],
    )
)
median_metric_summary = (
    primary_metric_units.group_by(
        ["model", MetricCol.K, "review_budget_label", "metric"],
    )
    .agg(
        pl.median("value").alias("median"),
        pl.col("value").quantile(0.10).alias("lower_interval"),
        pl.col("value").quantile(0.90).alias("upper_interval"),
        pl.len().alias("study_units"),
    )
    .sort(
        ["metric", MetricCol.K, "median", "model"],
        descending=[False, False, True, False],
    )
)
winner_map = (
    median_metric_summary.join(primary_objective_map, on="metric", how="inner")
    .sort(
        ["objective", MetricCol.K, "median", "model"],
        descending=[False, False, True, False],
    )
    .group_by(
        ["objective", MetricCol.K, "review_budget_label"],
        maintain_order=True,
    )
    .head(1)
    .rename({"median": "selection_value", "model": "winner"})
    .sort(["objective", MetricCol.K])
)

pairwise_lift_specs = pl.DataFrame(
    [
        {
            "Comparison": "cost-sensitive - expected_value",
            "Objective": "utility",
            "Budget": "5%",
            "challenger_model": "cost_sensitive_classifier",
            "metric": str(MetricCol.INCREMENTAL_UTILITY_AT_K),
            "k": 0.05,
        },
        {
            "Comparison": "classifier - expected_value",
            "Objective": "dollars",
            "Budget": "5%",
            "challenger_model": "classifier",
            "metric": str(MetricCol.DOLLARS_CAPTURED_AT_K),
            "k": 0.05,
        },
        {
            "Comparison": "LTR - expected_value",
            "Objective": "severe recall",
            "Budget": "1%",
            "challenger_model": "learning_to_rank",
            "metric": str(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K),
            "k": 0.01,
        },
    ],
)
pairwise_lift_values = (
    pairwise_lift_specs.join(
        primary_metric_units.select(
            "unit",
            "model",
            "metric",
            MetricCol.K,
            "review_budget_label",
            pl.col("value").alias("challenger_value"),
        ),
        left_on=["challenger_model", "metric", "k", "Budget"],
        right_on=["model", "metric", MetricCol.K, "review_budget_label"],
        how="left",
    )
    .join(
        primary_metric_units.filter(pl.col("model") == "expected_value").select(
            "unit",
            "metric",
            MetricCol.K,
            "review_budget_label",
            pl.col("value").alias("expected_value"),
        ),
        left_on=["unit", "metric", "k", "Budget"],
        right_on=["unit", "metric", MetricCol.K, "review_budget_label"],
        how="left",
    )
    .with_columns((pl.col("challenger_value") - pl.col("expected_value")).alias("lift"))
)
pairwise_lift_summary = (
    pairwise_lift_values.group_by(
        "Comparison",
        "Objective",
        "Budget",
        maintain_order=True,
    )
    .agg(
        pl.median("lift").alias("Median lift"),
        pl.col("lift").quantile(0.10).alias("P10"),
        pl.col("lift").quantile(0.90).alias("P90"),
        (pl.col("lift") > 0).mean().alias("P(lift > 0)"),
    )
    .with_columns(
        pl.col("Median lift").round(4),
        pl.col("P10").round(4),
        pl.col("P90").round(4),
        pl.col("P(lift > 0)").round(4),
    )
)

# %% [markdown]
# ### Winner Frequency
#
# Pairwise lifts compare challenger performance against expected value on the
# same scenario-seed units, making winner-frequency gaps easier to size.


# %%
pairwise_lift_summary


# %%
winner_frequency_plot_data = aggregate_winner_frequency.with_columns(
    pl.col("model").str.replace_all("_", " "),
    pl.col("objective").str.replace_all("_", " "),
)
(
    ggplot(
        winner_frequency_plot_data,
        aes(x="objective", y="win_frequency", fill="model"),
    )
    + geom_bar(stat="identity", position="dodge")
    + coord_flip()
    + theme_minimal()
    + labs(
        x="Operating objective",
        y="Share of scenario-seed units won",
        fill="Model",
    )
    + ggtitle("Winner Frequency Across Scenario-Seed Holdout Units")
)

# %% [markdown]
# ### Median Metrics With Intervals


# %%
metric_interval_titles = {
    str(MetricCol.RESIDUAL_NDCG_AT_K): "Queue Quality: Residual NDCG",
    str(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K): "Severity: Severe Recall",
    str(MetricCol.DOLLARS_CAPTURED_AT_K): "Dollar Recovery",
    str(MetricCol.INCREMENTAL_UTILITY_AT_K): "Incremental Utility",
}
metric_interval_plots = []
for metric, title in metric_interval_titles.items():
    metric_interval_plot_data = median_metric_summary.filter(
        pl.col("metric") == metric,
    ).with_columns(
        pl.col("model").str.replace_all("_", " "),
    )
    metric_interval_plots.append(
        (
            ggplot(
                metric_interval_plot_data,
                aes(x="review_budget_label", y="median", color="model"),
            )
            + geom_line()
            + geom_point()
            + geom_errorbar(
                aes(ymin="lower_interval", ymax="upper_interval"),
                width=0.15,
            )
            + theme_minimal()
            + rotated_x_labels()
            + labs(
                x="Review budget",
                y="Median with 10th-90th interval",
                color="Model",
            )
            + ggtitle(title)
        ),
    )
gggrid(metric_interval_plots, ncol=1)

# %% [markdown]
# ### Winner Map By Objective And Review Budget


# %%
winner_map_plot_data = winner_map.with_columns(
    pl.col("winner").str.replace_all("_", " "),
    pl.col("objective").str.replace_all("_", " "),
)
(
    ggplot(
        winner_map_plot_data,
        aes(x="review_budget_label", y="objective", fill="winner"),
    )
    + geom_tile()
    + theme_minimal()
    + rotated_x_labels()
    + labs(x="Review budget", y="Objective", fill="Winning model")
    + ggtitle("Winner Map by Objective and Review Budget")
)

# %% [markdown]
# The benchmark shows a split leaderboard rather than one universal winner.
# That is expected: issue probability, dollar recovery, utility, and severity
# ordering reward different queue behavior. For the production loss-prevention
# decision, value-aware ranking is the best default because wasted review time
# and missed dollars both matter.


# %%
def build_similarity_heatmap(
    similarity_diagnostics: pl.DataFrame,
    value_col: str,
    title: str,
) -> object:
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
    plot_data = pl.DataFrame(
        [
            {
                "model_x": left_model,
                "model_y": right_model,
                value_col: 1.0
                if left_model == right_model
                else pair_values.get(frozenset((left_model, right_model)), 0.0),
            }
            for left_model in models
            for right_model in models
        ],
    )
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
# Expected value is the production default because the residual task is
# financial: high-priority records are not merely likely to be wrong, they are
# costly when ignored. Learning to rank remains the challenger for operating
# modes that prioritize severe top-of-queue ordering over dollar-weighted net
# value.

# %% [markdown]
# ## 6. Why Results Differ By Objective
#
# Three ablation findings explain the split results:
#
# - Timekeeping and soft-warning context drive most of the feature lift after hard rules remove obvious defects.
# - Residual-only training remains preferable because the deployed model scores the residual review queue, not all payroll records.
# - Label choice changes the winner: classifiers are strongest for pure issue probability, expected value wins dollar/utility views, and learning to rank is the clearest graded queue-ordering challenger.

# %%
feature_ablation: pl.DataFrame | None = None
feature_ablation_lift: pl.DataFrame | None = None
training_universe_ablation: pl.DataFrame | None = None
label_ablation: pl.DataFrame | None = None

# %%
if not validation_mode:
    feature_ablation = employee_cycle_feature_ablation(
        data.payroll,
        sim_config,
        progress=progress,
    )
    feature_ablation_baseline = feature_ablation.filter(
        pl.col("feature_set") == "raw_payroll",
    ).select(
        "model",
        pl.col(MetricCol.RESIDUAL_NDCG_AT_K).alias("baseline_residual_ndcg_at_k"),
        pl.col(MetricCol.INCREMENTAL_UTILITY_AT_K).alias(
            "baseline_incremental_utility_at_k",
        ),
    )
    feature_ablation_lift = feature_ablation.join(
        feature_ablation_baseline,
        on="model",
        how="left",
    ).with_columns(
        (
            pl.col(MetricCol.RESIDUAL_NDCG_AT_K) - pl.col("baseline_residual_ndcg_at_k")
        ).alias("residual_ndcg_lift_vs_raw_payroll"),
        (
            pl.col(MetricCol.INCREMENTAL_UTILITY_AT_K)
            - pl.col("baseline_incremental_utility_at_k")
        ).alias("incremental_utility_improvement_vs_raw_payroll"),
    )

# %%
if not validation_mode:
    training_universe_ablation = employee_cycle_training_universe_ablation(
        data.payroll,
        sim_config,
        progress=progress,
    )

# %%
if not validation_mode:
    label_ablation = employee_cycle_label_ablation(
        scored,
        sim_config,
        progress=progress,
    )

# %%
feature_lift_endpoint: pl.DataFrame | None = None
if feature_ablation_lift is not None:
    final_feature_set = feature_ablation_lift.get_column("feature_set").to_list()[-1]
    feature_lift_endpoint = feature_ablation_lift.filter(
        pl.col("feature_set") == final_feature_set,
    ).with_columns(
        pl.col("residual_ndcg_lift_vs_raw_payroll").round(4),
        pl.col("incremental_utility_improvement_vs_raw_payroll").round(2),
    )

# %% [markdown]
# Detailed ablation rows stay in the appendix; the main implication is simple:
# expected value is not winning because it sees obvious hard-rule failures. It
# wins because value-aware ranking remains useful inside the ambiguous residual
# queue.

# %% [markdown]
# ## 7. Recommended Deployment Pattern
#
# Deploy the ranker as a second-stage residual review queue, not as a replacement
# for hard rules. Keep the decision surface small: default model, challenger,
# reviewer context, and monitoring slices.

# %%
review_queue_examples = build_employee_cycle_review_queue(
    scored,
    top_k=0.05 if 0.05 in review_budget_percents else review_budget_percents[0],
)

# %%
issue_type_model_performance: pl.DataFrame | None = None
severe_miss_examples: pl.DataFrame | None = None
if not validation_mode:
    issue_type_model_performance = employee_cycle_issue_type_model_performance(
        scored,
        0.05 if 0.05 in review_budget_percents else review_budget_percents[0],
        progress=progress,
    )

# %%
if not validation_mode:
    severe_miss_examples = employee_cycle_severe_miss_examples(
        scored,
        0.05 if 0.05 in review_budget_percents else review_budget_percents[0],
        limit_per_model=3,
        progress=progress,
    )

# %% [markdown]
# ### Decision Card
#
# | decision | recommendation | reader_takeaway |
# | :--- | :--- | :--- |
# | Default residual ranker | Expected value | Use for the production queue when payroll loss prevention is the operating goal. |
# | Primary challenger | Learning to rank | Track when severity ordering at tight review budgets becomes the primary goal. |
# | Diagnostic companion | Classifier | Show issue probability for reviewer context and calibration checks. |
# | Required monitoring | facility x pay period x issue family | Monitor drift, severe misses, and issue-family blind spots after deployment. |

# %% [markdown]
# For residual SNF payroll loss prevention after hard-rule screening, use
# expected-value scoring as the default residual queue ranker. Keep learning to
# rank as the challenger for severe-case ordering, and keep classifier
# probability visible for reviewer context rather than primary ordering.
#
# Deployment pattern:
#
# 1. Keep critical hard rules upstream as deterministic controls.
# 2. Score only the residual review queue with ML.
# 3. Use expected-value scoring as the default residual queue ranker.
# 4. Track learning-to-rank as a challenger for top-of-queue severity ordering.
# 5. Display reviewer-facing reason codes, issue probability, and expected dollar impact.
# 6. Monitor performance by facility, pay period, and issue family.
# 7. Periodically audit random residual records to reduce label bias.

# %% [markdown]
# ## 8. Limitations
#
# This benchmark uses synthetic payroll data, so model conclusions are evidence
# about modeling strategy rather than production performance claims.
#
# Key limitations:
#
# - issue rates and dollar impacts are simulation assumptions
# - severe residual issues are concentrated in a small number of anomaly families
# - observed corrections are simulated rather than real reviewer actions
# - feature distributions may not fully match a real SNF operator
# - real deployment requires adjudicated review samples and monitoring by facility, role, and pay period

# %% [markdown]
# ## 9. Technical Appendix

# %% [markdown]
# ### A. residual dataset diagnostics
#
# These baseline diagnostics support the compact stress-design view in section
# 4. They are useful for auditing the synthetic residual queue, but they are kept
# out of the main narrative so the model-comparison story stays concise.

# %% [markdown]
# #### dataset snapshot

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
# #### label summary

# %%
residual_payroll.select(
    pl.len().alias("residual_records"),
    pl.sum(PayrollCol.Y_ISSUE).alias("residual_issues"),
    pl.sum(PayrollCol.RULE_MISSED_SEVERE_ISSUE).alias("rule_missed_severe_issues"),
    pl.mean(PayrollCol.Y_DOLLAR).round(2).alias("avg_residual_dollars"),
    pl.mean(PayrollCol.NET_UTILITY).round(2).alias("avg_net_utility"),
)

# %% [markdown]
# #### residual label diagnostics

# %%
residual_label_diagnostics

# %% [markdown]
# #### residual anomaly-family mix

# %%
residual_family_mix


# %% [markdown]
# #### residual issue rate by facility

# %%
residual_issue_rate_plot_data = (
    residual_diagnostics["facility_residual_issue_rate"]
    .with_columns(
        pl.col(PayrollCol.FACILITY_ID).cast(pl.String).alias("facility_id"),
        pl.col("residual_issue_rate").round(4),
    )
    .sort("residual_issue_rate")
)
(
    ggplot(
        residual_issue_rate_plot_data,
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

# %% [markdown]
# #### severe residual issues by facility-cycle

# %%
severe_residual_heatmap_data = residual_diagnostics[
    "facility_cycle_residual_severe_counts"
].with_columns(
    pl.col(PayrollCol.FACILITY_ID).cast(pl.String).alias("facility_id"),
    pl.col(PayrollCol.PAY_PERIOD_INDEX).alias("pay_period"),
)
(
    ggplot(
        severe_residual_heatmap_data,
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

# %% [markdown]
# #### issue-type mix
#
# This chart excludes normal records and compares each population's share of
# true issue records by anomaly family. The companion table keeps raw counts,
# but the visual uses shares so the large normal residual review queue does not hide
# the issue-family pattern.

# %%
issue_type_mix_plot_data = (
    residual_diagnostics["issue_type_mix"]
    .with_columns(
        pl.col(PayrollCol.ANOMALY_CATEGORY).cast(pl.String).alias("anomaly_category"),
    )
    .sort(["population_issue_share", PayrollCol.ANOMALY_CATEGORY])
)
(
    ggplot(
        issue_type_mix_plot_data,
        aes(
            x="anomaly_category",
            y="population_issue_share",
            fill="population",
        ),
    )
    + geom_bar(stat="identity", position="dodge")
    + coord_flip()
    + theme_minimal()
    + labs(
        x="Anomaly family",
        y="Share of true issue records",
        fill="Population",
    )
    + ggtitle("Issue-Family Mix Among True Issues")
)

# %%
residual_diagnostics["issue_type_mix"]

# %% [markdown]
# #### top residual dollar records

# %%
residual_diagnostics["residual_dollar_distribution"].head(10)

# %% [markdown]
# ### B. feature contracts

# %% [markdown]
# #### feature families

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
# #### leakage-safe contract

# %% [markdown]
# | contract_point | active_behavior |
# | :--- | :--- |
# | historical features | exclude the current and future pay periods |
# | peer baselines | use only scoring-time-available employee and facility context |
# | evaluation labels | remain excluded from employee-cycle model features |
# | hard-rule gate | defines the residual review queue before model comparison begins |
# | soft warning features | remain allowed as ambiguous feature inputs after gating |
# | out-of-scope metrics | PBJ, HPRD, and compliance staffing metrics are excluded |

# %% [markdown]
# ### C. hard rule definitions
#
# | rule_name | code_condition | gate_effect | why_critical |
# | :--- | :--- | :--- | :--- |
# | terminated_employee_paid | employment_status == terminated and gross_pay > 0 | critical_hard_rule_flag = 1 | Obvious lifecycle violation removed before residual ranking |
# | duplicate_signature | duplicate employee x shift_date x shift_type x facility x pay_code x gross_pay signature | critical_hard_rule_flag = 1 | Obvious duplicate payroll signature should not compete in ML ranking |
# | nonpositive_active_pay | employment_status == active and gross_pay <= 0 | critical_hard_rule_flag = 1 | Active paid cycle with nonpositive gross pay is treated as a hard failure |
# | negative_net_pay | net_pay < 0 | critical_hard_rule_flag = 1 | Negative net pay is too obvious for residual ranking |
# | net_exceeds_gross | net_pay > gross_pay * 1.05 | critical_hard_rule_flag = 1 | Implausible net-to-gross relationship is gated out upstream |
# | physically_impossible_paid_hours | paid_hours > 24.0 | critical_hard_rule_flag = 1 | Impossible within-day hours are removed before ML |
# | paid_hours_missing_rate | paid_hours > 0 and pay_rate <= 0 or missing | critical_hard_rule_flag = 1 | Paid work without a valid rate is treated as a hard payroll defect |
# | paid_minus_scheduled_exceeds_threshold | worked_hours - scheduled_hours > paid_vs_scheduled_threshold | critical_hard_rule_flag = 1 | Large schedule mismatch is handled as an upstream gate rather than residual ambiguity |

# %% [markdown]
# ### D. metric definitions


# %%
appendix_metric_definitions = pl.DataFrame(
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
appendix_metric_definitions

# %% [markdown]
# ### E. ranking group construction


# %%
appendix_group_construction = pl.DataFrame(
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
                format_review_budget_pct(budget) for budget in review_budget_percents
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
appendix_group_construction

# %% [markdown]
# ### F. handling zero-positive residual groups
#
# | case | implemented_behavior | result |
# | :--- | :--- | :--- |
# | group recall with zero residual positives | group_anomalies denominator is clipped to at least 1 | group recall becomes 0 instead of undefined |
# | group NDCG with zero ideal gain | if ideal DCG is 0, group NDCG is set to 0 | all-negative groups remain in the grouped average |
# | global severe recall with zero severe residual issues | denominator uses max(total_severe, 1.0) | reported severe recall is 0 instead of undefined |
# | PR-AUC on degenerate residual labels | ValueError is caught and PR-AUC is set to 0 | notebook remains executable under degenerate slices |
# | tiny percent budgets on non-empty groups | review budget count is clipped to a minimum of 1 | every non-empty facility-cycle group contributes at least one reviewed row |

# %% [markdown]
# ### G. model settings and documented tuning space

# %% [markdown]
# #### formulation summary

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
            f"{PayrollCol.Y_ISSUE} on residual records",
            f"{PayrollCol.Y_ISSUE} with severity-aware weights on residual records",
            f"{PayrollCol.Y_DOLLAR} on residual records",
            "y_issue + estimated exposure on residual records",
            f"{PayrollCol.RELEVANCE_GRADE}, grouped by facility x pay period",
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
# #### fair comparison rules

# %%
pl.DataFrame(
    {
        "rule": [
            "scoring universe",
            "queue grouping",
            "review budgets",
            "temporal framing",
            "training universe",
            "leakage control",
            "cost-sensitive coverage",
        ],
        "applied_setting": [
            "residual records only for notebook comparison outputs",
            "facility x payroll cycle",
            ", ".join(format_review_budget_pct(k) for k in review_budget_percents),
            "same employee-cycle temporal split logic for all formulations",
            "primary supervised training rows are residual records only",
            "evaluation labels remain excluded from feature columns",
            "cost-sensitive classifier is included alongside the standard classifier",
        ],
    },
)

# %% [markdown]
# #### model settings
#
# | model | estimator_or_logic | current_fixed_settings | documented_future_tuning_space |
# | :--- | :--- | :--- | :--- |
# | classifier | HistGradientBoostingClassifier | max_depth=3, random_state=config.seed | max_depth, learning_rate, max_leaf_nodes, min_samples_leaf |
# | cost_sensitive_classifier | HistGradientBoostingClassifier with sample weights | max_depth=3 plus issue-dollar-severity weighting | classifier settings plus weight multipliers |
# | regressor | HistGradientBoostingRegressor | max_depth=3, lower_bound=0.0, random_state=config.seed | max_depth, learning_rate, max_leaf_nodes, min_samples_leaf |
# | learning_to_rank | LightGBM LambdaRank on relevance_grade, grouped by facility x pay period | objective=lambdarank, metric=ndcg, num_iterations=80, learning_rate=0.05, max_depth=3, min_child_samples=5, num_threads=config.ltr_num_threads, seed=config.seed | num_iterations, learning_rate, max_depth, min_child_samples, num_leaves, LambdaRank objective or NDCG settings |
# | expected_value | minmax(estimated_exposure * clip(classification, 0.05, 1.0)) | classification floor=0.05 before multiplication | classification floor, exposure formula, calibration strategy |

# %% [markdown]
# ### H. score-bucket calibration diagnostics


# %%
score_bucket_count = 10
score_bucket_residual_frame = scored.filter(
    pl.col(PayrollCol.RESIDUAL_RECORD) == 1,
).with_columns(
    pl.col(ScoreCol.FINAL_ANOMALY_SCORE)
    .qcut(score_bucket_count, allow_duplicates=True)
    .alias("score_bucket"),
    (
        pl.col(PayrollCol.TOTAL_GROSS_PAY) - pl.col(PayrollCol.TOTAL_EXPECTED_GROSS_PAY)
    ).alias("gross_gap"),
)
appendix_score_bucket_calibration = (
    score_bucket_residual_frame.group_by("score_bucket", maintain_order=True)
    .agg(
        pl.len().alias("records"),
        pl.mean(ScoreCol.FINAL_ANOMALY_SCORE).round(4).alias("avg_score"),
        pl.mean(PayrollCol.Y_ISSUE).round(4).alias("issue_rate"),
        pl.mean(PayrollCol.Y_DOLLAR).round(2).alias("avg_residual_dollars"),
        pl.mean("gross_gap").round(2).alias("avg_gross_gap"),
        pl.mean(ScoreCol.ESTIMATED_EXPOSURE).round(2).alias("avg_estimated_exposure"),
    )
    .with_row_index("bucket_rank", offset=1)
)
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
#
# These tables support the compact stress-design and benchmark visuals in the
# main narrative. They are kept here so the main report can stay decision-first
# while the scenario design remains auditable.

# %% [markdown]
# #### cross-scenario residual sanity summary

# %%
scenario_summary_compact

# %% [markdown]
# #### DGP scenario catalog

# %%
scenario_benchmark.scenario_catalog.drop(
    "scenario",
    "status",
)

# %% [markdown]
# #### scenario x seed design

# %%
scenario_benchmark.scenario_seed_design


# %%
diagnostic_scenario_rows = [
    {
        "artifact": "scenario_catalog",
        "name": scenario.name,
        "status": str(scenario.metadata.get("status", "unknown")),
        "detail": str(scenario.metadata.get("description", "")),
    }
    for scenario in diagnostic_scenario_catalog().values()
]
runtime_config_rows = [
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
        "status": str(sim_config.facility_count),
        "detail": "Synthetic facility count for this notebook run",
    },
    {
        "artifact": "runtime_config",
        "name": "employee_count",
        "status": str(sim_config.employee_count),
        "detail": "Synthetic employee population for this notebook run",
    },
    {
        "artifact": "runtime_config",
        "name": "pay_periods",
        "status": str(sim_config.pay_periods),
        "detail": "Synthetic payroll cycles used for temporal evaluation",
    },
    {
        "artifact": "runtime_config",
        "name": "review_budget_percents",
        "status": ", ".join(
            format_review_budget_pct(budget) for budget in review_budget_percents
        ),
        "detail": "Grouped review budgets for the scenario-based residual ranking benchmark",
    },
    {
        "artifact": "runtime_config",
        "name": "scenario_seed_design",
        "status": (
            f"{len(scenario_benchmark_seeds)} seeds x "
            f"{scenario_benchmark.scenario_catalog.height} scenarios"
        ),
        "detail": "Configured scenario-seed benchmark design",
    },
    {
        "artifact": "runtime_config",
        "name": "reference_window_periods",
        "status": str(sim_config.reference_window_periods),
        "detail": "Prior periods used for scoring-time context",
    },
]
appendix_stress_test_config = pl.DataFrame(
    runtime_config_rows + diagnostic_scenario_rows,
)
appendix_stress_test_config

# %% [markdown]
# ### J. additional ablation tables

# %% [markdown]
# #### feature-family ablation

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
# #### feature-family ablation lift by model

# %%
if feature_lift_endpoint is not None:
    display(
        feature_lift_endpoint.select(
            "feature_set",
            "model",
            "residual_ndcg_lift_vs_raw_payroll",
            "incremental_utility_improvement_vs_raw_payroll",
        ),
    )

# %%
if feature_lift_endpoint is not None:
    display(
        gggrid(
            [
                (
                    ggplot(
                        feature_lift_endpoint,
                        aes(x="model", y="residual_ndcg_lift_vs_raw_payroll"),
                    )
                    + geom_bar(stat="identity", fill="#0f766e")
                    + theme_minimal()
                    + rotated_x_labels()
                    + labs(x="Model", y="NDCG lift vs raw payroll")
                    + ggtitle("Feature Ablation Lift by Model")
                ),
                (
                    ggplot(
                        feature_lift_endpoint,
                        aes(
                            x="model",
                            y="incremental_utility_improvement_vs_raw_payroll",
                        ),
                    )
                    + geom_bar(stat="identity", fill="#1d4ed8")
                    + theme_minimal()
                    + rotated_x_labels()
                    + labs(x="Model", y="Utility improvement vs raw payroll")
                    + ggtitle("Feature Ablation Utility Improvement by Model")
                ),
            ],
            ncol=1,
        ),
    )

# %% [markdown]
# #### training-universe ablation

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
# #### label-oriented winner summary

# %%
if label_ablation is not None:
    display(
        label_ablation.with_columns(
            pl.col("selection_value").round(4),
        ),
    )

# %% [markdown]
# ### K. model diagnostics and examples

# %% [markdown]
# #### aggregate winner-frequency rows

# %%
aggregate_winner_frequency.select(
    "objective",
    "review_budget_label",
    "model",
    "win_count",
    "win_frequency",
)

# %% [markdown]
# #### median metric rows with intervals

# %%
median_metric_summary.select(
    "model",
    "review_budget_label",
    "metric",
    pl.col("median").round(4),
    pl.col("lower_interval").round(4),
    pl.col("upper_interval").round(4),
    "study_units",
)

# %% [markdown]
# #### full winner map rows

# %%
winner_map

# %% [markdown]
# #### primary score comparison on residual records

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
).sort(ScoreCol.EXPECTED_VALUE_SCORE, descending=True).head(10)

# %% [markdown]
# #### model similarity diagnostics

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
    ncol=1,
)

# %% [markdown]
# #### temporal stability context

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
# #### issue-type performance by model

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
# #### severe residual miss examples

# %%
if severe_miss_examples is not None:
    display(severe_miss_examples)

# %% [markdown]
# #### reviewer-facing queue examples

# %%
review_queue_examples.select(
    ReviewCol.RANK,
    PayrollCol.FACILITY_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    ReviewCol.APPROVAL_RISK_CATEGORY,
    ReviewCol.RECOMMENDED_ACTION,
    ReviewCol.PRIMARY_REASON,
    ScoreCol.FINAL_ANOMALY_SCORE,
    ScoreCol.CLASSIFICATION_SCORE,
    ScoreCol.EXPECTED_VALUE_SCORE,
).head(5)

# %% [markdown]
# #### expected-value top residual examples

# %%
residual_scored.sort(ScoreCol.EXPECTED_VALUE_SCORE, descending=True).select(
    PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.FACILITY_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    PayrollCol.ANOMALY_CATEGORY,
    PayrollCol.Y_ISSUE,
    PayrollCol.Y_DOLLAR,
    PayrollCol.RELEVANCE_GRADE,
    ScoreCol.CLASSIFICATION_SCORE,
    ScoreCol.EXPECTED_VALUE_SCORE,
    ScoreCol.RANKING_SCORE,
).head(10)

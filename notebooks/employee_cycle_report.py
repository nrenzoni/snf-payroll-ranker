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
# # Residual Payroll Review After Hard Rules

# %% [markdown]
# ## 0. Executive Summary
#
# **Goal**
#
# Rank ambiguous SNF payroll records that were not caught by critical hard rules.
#
# **Workflow setup**
#
# Critical hard rules remove obvious payroll violations first. ML models compete
# only on the residual queue.
#
# **Models compared**
#
# - classifier
# - cost-sensitive classifier
# - regressor
# - expected-value model
# - learning-to-rank
#
# **Primary metrics**
#
# - residual NDCG by review-budget percentage
# - rule-missed severe recall by review-budget percentage
# - residual dollars caught by review-budget percentage
# - reviewer yield by review-budget percentage
# - incremental utility by review-budget percentage
#
# **Working conclusion placeholder**
#
# Learning-to-rank is expected to be strongest for top-of-queue severity
# ordering, while the expected-value model is expected to remain highly
# competitive for residual dollar recovery. The final recommendation should
# depend on whether the review team prioritizes severe-risk coverage or
# financial recovery.

# %% [markdown]
# ## 1. Problem Framing: Residual Payroll Review After Hard Rules
#
# This notebook does not ask whether ML can beat hard rules on obvious payroll
# problems. It asks whether ML adds value after hard rules have already removed
# the obvious cases.
#
# **Production assumption**
#
# Critical hard rules already catch impossible or obvious payroll records before
# the ML stage begins.
#
# **Modeling question**
#
# Among employee-pay-cycle records not caught by critical hard rules, which ML
# formulation best ranks the remaining payroll review candidates?
#
# **Queue framing**
#
# - item: employee-pay-cycle payroll record
# - group: facility x payroll cycle
# - business constraint: reviewers can inspect only a limited share of each residual queue
# - objective: maximize review value within the reviewed share of each residual queue
#
# **Out of scope**
#
# - optimizing the hard rules themselves
# - ranking all payroll records before hard rules
# - evaluating a full hybrid production policy end to end
# - UI or workflow implementation
# - compliance, PBJ, and HPRD staffing metrics

# %% [markdown]
# ## 2. Synthetic SNF Payroll Data Generation
#
# This section documents the simulated world only to the extent needed for the
# residual-ranking experiment.
#
# The synthetic data should support two distinct populations:
#
# - hard-rule-caught obvious payroll issues
# - rule-missed residual issues that remain ambiguous after gating
#
# The notebook will show the generator setup, a compact process diagram, and a
# small schema example rather than all generator internals.

# %% [markdown]
# ```mermaid
# flowchart TD
#     classDef default fill:#F7F9FC,stroke:#5B6B83,stroke-width:1px,font-family:Helvetica,color:#000000;
#     linkStyle default stroke:#5B6B83,font-family:Helvetica;
#     facilities["<b>Facility hierarchy</b><br/>region, size tier, payroll maturity, local pay patterns"]
#     employees["<b>Employee generation</b><br/>role, tenure, base rate, home facility, lifecycle state"]
#     payroll["<b>Payroll cycles and timekeeping</b><br/>hours, overtime, rate changes, punches, edits"]
#     critical["<b>Critical hard-rule issues</b><br/>duplicate or impossible records removed before ML"]
#     residual["<b>Residual latent issues</b><br/>ambiguous payroll risks that survive the hard-rule gate"]
#     observed["<b>Observed history</b><br/>reviewed corrections are a biased subset of true issues"]
#     cycles["<b>Employee-pay-cycle records</b><br/>active modeling grain for residual ranking"]
#     facilities -->|work context| employees
#     facilities -->|facility effects| payroll
#     employees -->|employee behavior| payroll
#     payroll -->|obvious violations| critical
#     payroll -->|subtle issues| residual
#     critical -->|gate out| cycles
#     residual -->|evaluation labels| cycles
#     residual -->|selective review| observed
#     observed -->|historical signal| cycles
# ```
# %%
import polars as pl
import polars.selectors as pl_selectors
from common.display import setup_notebook_html
from common.execution import notebook_fast_mode
from common.plots import (
    aes,
    geom_line,
    geom_point,
    ggplot,
    ggtitle,
    labs,
    rotated_x_labels,
    theme_minimal,
)

from payroll_anomaly_ranking.columns import MetricCol, PayrollCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import (
    employee_cycle_hard_rule_funnel,
    employee_cycle_residual_diagnostics,
    generate_employee_pay_cycles,
)
from payroll_anomaly_ranking.evaluation import (
    employee_cycle_backtest_by_period,
    employee_cycle_grouped_metrics,
    evaluate_employee_cycle_scores,
)
from payroll_anomaly_ranking.features import build_employee_cycle_features
from payroll_anomaly_ranking.models import score_employee_pay_cycles

# %%
setup_notebook_html()
fast_mode = notebook_fast_mode()

# %%
sim_config = PayrollConfig(
    facility_count=25,
    employee_count=650,
    pay_periods=16 if fast_mode else 36,
    employee_cycle_review_budget_percents=(0.01, 0.03, 0.05, 0.10),
)
review_budget_percents = sim_config.employee_cycle_review_budget_percents or tuple(
    float(budget) for budget in sim_config.review_budgets
)

data = generate_employee_pay_cycles(sim_config)
funnel = employee_cycle_hard_rule_funnel(data.payroll)
residual_diagnostics = employee_cycle_residual_diagnostics(data.payroll)
residual_payroll = data.payroll.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)
hard_rule_flagged = data.payroll.filter(pl.col(PayrollCol.CRITICAL_HARD_RULE_FLAG) == 1)


def build_model_budget_metrics(
    scored_frame: pl.DataFrame,
    review_budgets: tuple[float, ...],
) -> pl.DataFrame:
    rows: list[dict[str, float | str]] = []
    for model_name, score_col in [
        ("classifier", ScoreCol.CLASSIFICATION_SCORE),
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


def format_review_budget_pct(budget: float) -> str:
    return f"{budget:.0%}" if budget <= 1 else str(int(budget))


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


# %% [markdown]
# snapshot

# %%
pl.DataFrame(
    {
        "metric": [
            "employee-pay-cycle records",
            "critical hard-rule flagged",
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
# Section 1 framing
#
# | Workflow Assumption | Active Contract |
# | --- | --- |
# | **Modeling Grain** | employee-pay-cycle |
# | **Hard-Rule Role** | remove obvious payroll problems before ML |
# | **Scoring Universe** | only residual records not flagged by critical hard rules |
# | **Queue Group** | facility x payroll cycle |
# | **Review Objective** | prioritize ambiguous payroll records under limited review capacity |
# | **Out Of Scope** | PBJ, HPRD, and compliance staffing metrics |

# %% [markdown]
# schema example:

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
# These records leave the ML universe entirely. Examples include:
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
# features because they are ambiguous contextual warnings rather than definitive
# failures.
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
# `residual_record = not critical_hard_rule_flagged`
#
# The ML task is to rank residual records within each facility x payroll cycle.
#
# **Planned funnel summary**
#
# | Stage | Records | % of total | True issues | Severe issues | Dollar impact |
# | --- | ---: | ---: | ---: | ---: | ---: |
# | All payroll records |  | 100% |  |  |  |
# | Critical hard-rule flagged |  |  |  |  |  |
# | Residual ML universe |  |  |  |  |  |

# %% [markdown]
# hard-rule funnel

# %%
(
    funnel.with_columns(
        pl.col("pct_of_total").round(4),
        pl.col("dollar_impact").round(2),
    )
)

# %% [markdown]
# ## 4. Simulation Sanity Checks for the Residual Dataset
#
# This section should answer one question: after hard rules, is there still
# enough signal and enough risk for ML ranking to matter?
#
# Planned residual-only checks:
#
# 1. residual issue rate by facility
# 2. residual severe issue count per facility-cycle
# 3. dollar impact distribution in residual records
# 4. issue-type mix: hard-rule flagged versus residual
# 5. residual records per facility-cycle
#
# Existing full-dataset plots were removed because they do not answer the
# residual-universe question cleanly.

# %% [markdown]
# ### residual issue rate by facility

# %%
residual_diagnostics["facility_residual_issue_rate"].head(10)

# %% [markdown]
# ### severe residual issues by facility-cycle

# %%
residual_diagnostics["facility_cycle_residual_severe_counts"].head(10)

# %% [markdown]
# ### issue-type mix

# %%
residual_diagnostics["issue_type_mix"]

# %% [markdown]
# ### top residual dollar records

# %%
residual_diagnostics["residual_dollar_distribution"].head(10)

# %% [markdown]
# ## 5. Label Engineering for Residual Ranking
#
# Labels in this notebook are residual-aware. They are defined after the
# critical hard-rule gate and are aligned to the stage-2 ranking problem.
#
# **Core labels**
#
# - `y_issue`: latent residual issue truth used by classifier models
# - `y_dollar`: residual dollar impact used by regression-style models
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
# historical review outcomes.

# %% [markdown]
# | Label | Column | Used by | Meaning |
# | --- | --- | --- | --- |
# | **residual issue** | `y_issue` | classifier, cost-sensitive classifier | latent residual issue truth after the hard-rule gate |
# | **residual dollar impact** | `y_dollar` | regressor, expected-value | financial impact if the residual issue is ignored |
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

# %% [markdown]
# ## 6. Feature Engineering for Ambiguous Payroll Records

# %% [markdown]
# | Feature family | Examples | Why it matters in the residual queue |
# | --- | --- | --- |
# | Raw payroll | hours, overtime, gross pay, pay rate | basic residual signal |
# | Employee history | hours versus trailing median, pay-rate change versus prior cycle | catches personal deviations |
# | Facility-role baseline | pay rate versus facility-role median, overtime versus role norm | catches local anomalies |
# | Timekeeping | missing punch, manual edit count, late entry | soft risk signals |
# | Cross-facility | unusual facility, same-day multi-facility pattern | duplicate or allocation risk |
# | Temporal | holiday cycle, vendor drift, staffing shock | seasonality and drift context |

# %%
employee_cycle_features = build_employee_cycle_features(data.payroll)
scoring_results = score_employee_pay_cycles(data.payroll, sim_config)
scored = scoring_results.scored
residual_scored = scored.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)
evaluation = evaluate_employee_cycle_scores(scored, sim_config)
backtest = employee_cycle_backtest_by_period(scored, sim_config)
model_budget_metrics = build_model_budget_metrics(scored, review_budget_percents)
budget_diagnostics = build_review_budget_diagnostics(
    residual_diagnostics["residual_records_per_facility_cycle"],
    review_budget_percents,
)

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
# This section compares only ML models on the residual universe.
#
# Hard rules are the upstream gate. They are not a competing model in this
# section.

# %% [markdown]
# | Model | Training target | Queue score | Why include |
# | --- | --- | --- | --- |
# | Classifier | `y_issue` | `P(issue)` | baseline supervised model |
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

# %% [markdown]
# ### formulation summary

# %%
pl.DataFrame(
    {
        "model": [
            "classifier",
            "regressor",
            "expected_value",
            "learning_to_rank",
        ],
        "training_target": [
            str(PayrollCol.Y_ISSUE),
            str(PayrollCol.Y_DOLLAR),
            "y_issue + estimated exposure",
            str(PayrollCol.RELEVANCE_GRADE),
        ],
        "score_column": [
            str(ScoreCol.CLASSIFICATION_SCORE),
            str(ScoreCol.REGRESSION_SCORE),
            str(ScoreCol.EXPECTED_VALUE_SCORE),
            str(ScoreCol.RANKING_SCORE),
        ],
        "business_question": [
            "Which residual records are most likely to still contain a payroll issue?",
            "Which residual records imply the largest unresolved dollar impact?",
            "Which residual records combine issue likelihood with financial exposure?",
            "Which residual records deserve the strongest top-of-queue priority?",
        ],
    },
)

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
    ScoreCol.REGRESSION_SCORE,
    ScoreCol.EXPECTED_VALUE_SCORE,
    ScoreCol.RANKING_SCORE,
    ScoreCol.FINAL_ANOMALY_SCORE,
).sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True).head(10)

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
            "deferred formulation",
        ],
        "applied_setting": [
            "residual records only for notebook comparison outputs",
            "facility x payroll cycle",
            ", ".join(format_review_budget_pct(k) for k in review_budget_percents),
            "same employee-cycle temporal split logic for all formulations",
            "evaluation labels remain excluded from feature columns",
            "cost-sensitive classifier intentionally excluded from this pass",
        ],
    },
)

# %% [markdown]
# ### residual metrics by review-budget percentage

# %%
evaluation.metrics.select(
    pl.col(MetricCol.K)
    .map_elements(
        format_review_budget_pct,
        return_dtype=pl.String,
    )
    .alias("review_budget_pct"),
    MetricCol.RESIDUAL_NDCG_AT_K,
    MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K,
    MetricCol.DOLLARS_CAPTURED_AT_K,
    MetricCol.REVIEWER_YIELD_AT_K,
    MetricCol.INCREMENTAL_UTILITY_AT_K,
    MetricCol.PR_AUC,
)

# %% [markdown]
# ### review-budget diagnostics

# %%
budget_diagnostics

# %% [markdown]
# ### model comparison

# %%
evaluation.model_comparison.select(
    "model",
    MetricCol.RESIDUAL_NDCG_AT_K,
    MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K,
    MetricCol.DOLLARS_CAPTURED_AT_K,
    MetricCol.REVIEWER_YIELD_AT_K,
    MetricCol.INCREMENTAL_UTILITY_AT_K,
    MetricCol.PR_AUC,
).sort(MetricCol.RESIDUAL_NDCG_AT_K, descending=True)

# %% [markdown]
# ### backtest by period

# %%
backtest.select(
    PayrollCol.PAY_PERIOD_INDEX,
    MetricCol.RESIDUAL_NDCG_AT_K,
    MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K,
    MetricCol.DOLLARS_CAPTURED_AT_K,
    MetricCol.REVIEWER_YIELD_AT_K,
    MetricCol.INCREMENTAL_UTILITY_AT_K,
).sort(PayrollCol.PAY_PERIOD_INDEX).head()

# %% [markdown]
# ### winner summary

# %%
comparison_for_summary = evaluation.model_comparison
pl.DataFrame(
    {
        "objective": [
            "best residual severity ordering",
            "best residual dollar recovery",
            "best residual utility",
            "best overall default in this run",
        ],
        "winner": [
            comparison_for_summary.sort(
                MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K,
                descending=True,
            ).row(0, named=True)["model"],
            comparison_for_summary.sort(
                MetricCol.DOLLARS_CAPTURED_AT_K,
                descending=True,
            ).row(0, named=True)["model"],
            comparison_for_summary.sort(
                MetricCol.INCREMENTAL_UTILITY_AT_K,
                descending=True,
            ).row(0, named=True)["model"],
            comparison_for_summary.sort(
                [MetricCol.RESIDUAL_NDCG_AT_K, MetricCol.INCREMENTAL_UTILITY_AT_K],
                descending=[True, True],
            ).row(0, named=True)["model"],
        ],
    },
)

# %% [markdown]
# ### residual dollars captured by review-budget percentage

# %%
(
    ggplot(
        model_budget_metrics,
        aes(
            x="review_budget_label",
            y=MetricCol.DOLLARS_CAPTURED_AT_K,
            color="model",
        ),
    )
    + geom_line()
    + geom_point()
    + theme_minimal()
    + rotated_x_labels()
    + labs(x="Residual queue reviewed", y="Residual dollars captured", color="Model")
    + ggtitle("Residual Dollars Captured by Review-Budget Percentage")
)

# %% [markdown]
# ### severe recall by review-budget percentage

# %%
(
    ggplot(
        model_budget_metrics,
        aes(
            x="review_budget_label",
            y=MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K,
            color="model",
        ),
    )
    + geom_line()
    + geom_point()
    + theme_minimal()
    + rotated_x_labels()
    + labs(x="Residual queue reviewed", y="Rule-missed severe recall", color="Model")
    + ggtitle("Residual Severe-Issue Recall by Review-Budget Percentage")
)

# %% [markdown]
# ## 8. Main Results: Residual Queue Evaluation
#
# All headline metrics in this section should be computed only on residual
# records within facility x payroll cycle groups.
#
# Planned primary outputs:
#
# 1. residual dollars caught versus percent residual reviewed
# 2. rule-missed severe recall versus percent residual reviewed
# 3. residual NDCG versus percent residual reviewed
# 4. reviewer yield versus percent residual reviewed
# 5. residual net utility versus percent residual reviewed
#
# The winner framing should stay specific: learning-to-rank may win top-of-queue
# severity ordering, while expected-value may remain more competitive on dollar
# recovery.

# %% [markdown]
# ## 9. Ablation Studies
#
# Ablations in this notebook are residual-specific.
#
# **9.1 Feature ablation**
#
# Which feature families matter after hard rules remove obvious records?
#
# | Feature set | NDCG@5% | Rule-missed severe recall@5% | Residual dollars@5% |
# | --- | ---: | ---: | ---: |
# | Raw payroll only |  |  |  |
# | + employee history |  |  |  |
# | + facility-role baselines |  |  |  |
# | + timekeeping signals |  |  |  |
# | + temporal context |  |  |  |
#
# **9.2 Label ablation**
#
# Does the model winner change depending on how residual risk is defined?
#
# | Label | Best model | Interpretation |
# | --- | --- | --- |
# | binary issue | classifier | best for issue probability |
# | dollar impact | regressor / EV | best for financial exposure |
# | graded relevance | LTR | best for queue order |
# | utility label | EV / LTR | best for business value |
# | observed historical label | classifier | may inherit old review bias |
# | latent true label | LTR / EV | better at missed residual risk |
#
# **9.3 Training universe ablation**
#
# Should models be trained on all records or only residual records?
#
# | Training universe | Scoring universe | Purpose |
# | --- | --- | --- |
# | all records | residual only | uses broader risk signal |
# | residual records only | residual only | specialized ambiguous-case model |
# | all records with hard-rule flag features | residual only | learns full context but adapts to the gate |
#
# **9.4 Validation split ablation**
#
# Does the residual model generalize to future cycles and unseen facilities?

# %% [markdown]
# ## 10. Diagnostics, Explanations, and Final Recommendation
#
# This section combines diagnostic plots, reviewer-facing explanation examples,
# and the final production recommendation into one compact decision section.
#
# **Planned diagnostics**
#
# - issue-type performance heatmap
# - top-K overlap heatmap
# - severe misses table
#
# **Reviewer-facing explanation template**
#
# ```text
# Priority: High
# Residual risk type: subtle pay-rate or role mismatch
# Expected dollar impact: $430
# Issue probability: 0.62
# Queue rank: 8 of 740
#
# Reason codes:
# - Pay rate is 19% above facility-role median
# - Employee changed job code this cycle
# - Manual edit count is above facility baseline
# - Employee rarely works this facility
#
# Recommended action:
# Verify job code, rate authorization, and facility allocation.
# ```
#
# **Final recommendation template**
#
# | Objective | Recommended model |
# | --- | --- |
# | Best residual severity ordering | LTR |
# | Best residual dollar recovery | Expected-value model |
# | Best calibrated residual risk | Classifier / EV |
# | Best new-facility robustness | holdout winner |
# | Best production default | LTR or EV, depending on objective |

# %% [markdown]
# ## 11. Technical Appendix
#
# Appendix sections planned for the active notebook:
#
# - A. Data dictionary
# - B. Hard rule definitions
# - C. Metric definitions
# - D. Ranking group construction
# - E. Handling zero-positive residual groups
# - F. Hyperparameter search space
# - G. Additional ablation tables
# - H. Additional calibration plots
# - I. Stress-test configurations

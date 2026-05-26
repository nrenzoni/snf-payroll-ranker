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
# - residual NDCG@K
# - rule-missed severe recall@K
# - residual dollars caught@K
# - reviewer yield@K
# - incremental utility@K
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
# - business constraint: reviewers can inspect only the top K residual records
# - objective: maximize review value in the top K residual records
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
from payroll_anomaly_ranking.columns import PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import generate_employee_pay_cycles
from payroll_anomaly_ranking.features import build_employee_cycle_features

# %%
sim_config = PayrollConfig(
    facility_count=75,
    pay_periods=36,
)

data = generate_employee_pay_cycles(sim_config)

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
# ## 6. Feature Engineering for Ambiguous Payroll Records
#
# Because the obvious records are removed first, the residual task depends more
# on contextual deviation features than on raw threshold signals alone.
#
# Soft warning signals may remain as features. Compliance, PBJ, and HPRD metrics
# are intentionally excluded.

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
employee_cycle_features.head()

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
# | Cost-sensitive classifier | weighted `y_issue` | weighted risk score | prioritizes severe residual issues |
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
# ## 8. Main Results: Residual Queue Evaluation
#
# All headline metrics in this section should be computed only on residual
# records within facility x payroll cycle groups.
#
# Planned primary outputs:
#
# 1. residual dollars caught versus percent residual reviewed
# 2. rule-missed severe recall versus percent residual reviewed
# 3. residual NDCG@K versus percent residual reviewed
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

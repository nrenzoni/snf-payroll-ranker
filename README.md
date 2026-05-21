# SNF Payroll Anomaly Ranking

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![uv](https://img.shields.io/badge/uv-managed-purple.svg)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/ruff-formatted-brightgreen.svg)](https://docs.astral.sh/ruff/)
[![Pyrefly](https://img.shields.io/badge/pyrefly-checked-blueviolet.svg)](https://pyrefly.org/)

A production-oriented, privacy-safe ML pipeline that prioritizes shift-level payroll exceptions for skilled nursing facility (SNF) administrators. Combines deterministic compliance rules, robust statistical outlier detection, unsupervised multivariate anomaly scoring, and estimated-exposure signals into a hybrid approval-exception rank. Built with temporal validation, leakage-safe feature engineering, and full uncertainty quantification.

![Pipeline Architecture](docs/assets/pipeline_architecture.svg)

*See [ARCHITECTURE.md](ARCHITECTURE.md) for system design details and [DECISIONS.md](DECISIONS.md) for the rationale behind key technical choices.*

---

## Table of Contents

- [What Makes This Different](#what-makes-this-different)
- [Quick Start](#quick-start)
- [What The Workflow Covers](#what-the-workflow-covers)
- [Sample Outputs](#sample-outputs)
- [SNF Case Studies](#snf-case-studies)
- [Notebook Reporting](#notebook-reporting)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Intended Production Flow](#intended-production-flow)
- [Development Checks](#development-checks)
- [Engineering Process](#engineering-process)
- [Limitations](#limitations)

---

## What Makes This Different

- **Leakage-safe temporal validation**: Data is split by pay period, not random rows. Historical features exclude the current and all future periods. Peer baselines are built from prior windows only.
- **Facility-normalized, transferable features**: Stationary ratios (overtime per scheduled hour, premium pay share, gross pay vs. expected role-shift pay) allow new SNF clients with different pay scales to be bootstrapped without recalibration.
- **Uncertainty quantification**: Every scored record carries ensemble disagreement, bootstrap intervals, expected gross-pay intervals, peer-group sample-size uncertainty, data-quality flags, and out-of-distribution detection. Risk and uncertainty are reported separately so high-risk records are not hidden solely because uncertainty is high.
- **Explainable hybrid ranking**: The final score is a weighted combination of rule, statistical, ML, peer, history, schedule/timeclock, premium eligibility, and estimated-exposure components. Administrators can see *which* signals drove a record to the top of the queue.
- **Administrator-safe outputs**: Review queues include recommended actions, sources to check, SNF context, and review-safe explanations. They do not label employees as confirmed misconduct.

---

## Quick Start

### Core Pipeline Setup

```bash
uv sync
```

### Run The Pipeline

```bash
uv run python -m payroll_anomaly_ranking.pipeline
```

Expected generated files include:

- `data/synthetic/synthetic_payroll.csv`
- `data/synthetic/synthetic_snf_shift_payroll.csv`
- `data/synthetic/synthetic_payroll_labels.csv`
- `outputs/evaluation/scored_payroll.csv`
- `outputs/evaluation/review_budget_metrics.csv`
- `outputs/evaluation/model_comparison.csv`
- `outputs/evaluation/category_error_analysis.csv`
- `outputs/evaluation/backtest_metrics.csv`
- `outputs/evaluation/rolling_origin_metrics.csv`
- `outputs/evaluation/leakage_checks.csv`
- `outputs/evaluation/admin_approval_queue.csv`
- `outputs/evaluation/analyst_review_queue.csv`
- `outputs/evaluation/evaluation_labeled_review_queue.csv`
- `outputs/evaluation/facility_approval_summary.csv`

### Notebook Reporting Setup

Install optional notebook/reporting dependencies before executing Jupytext notebooks or rendering Lets-Plot visuals.

```bash
uv sync --extra notebooks
```

---

## What The Workflow Covers

- Shift-level SNF payroll generation with facilities, units, roles, license types, shift types, schedule context, timeclock context, pay-code categories, premium pay, approval status, lifecycle dates, and pay-period/facility rollups.
- Implemented synthetic exception scenarios for overtime/double-shift staffing pressure and premium pay or shift differential mismatch.
- Future scenario catalog entries for agency/float labor, census/acuity, credential/license mismatch, PBJ category mismatch, meal premiums, new hire orientation, termination/final pay, retro/rate corrections, union policy variation, new-client bootstrap, and payroll close adjustment concentration.
- Leakage-safe employee history, role/shift peer, facility-normalized, stationary ratio, schedule/timeclock, premium eligibility, fatigue/rest-gap, and exposure-estimate features.
- Deterministic SNF approval rules, robust statistical scoring, unsupervised outlier detection, and hybrid automated approval exception ranking.
- Manual threshold baselines for gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance.
- Administrator-safe pre-approval queues with recommended action, source to check, approval risk category, SNF context, estimated exposure, and review-safe explanations.

---

## Sample Outputs

### Ranked Approval Queue (Top 5)

A preview of the administrator-facing queue after scoring:

| rank | employee_id | facility_id | role | shift_type | gross_pay | final_anomaly_score | approval_risk_category | primary_reason | rule_reason_codes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SYN-SNF-E00028 | SNF-F001 | Therapy | Double | 727.89 | 0.690 | review before approval | Gross pay materially differs from similar SNF role/shift peers | none |
| 2 | SYN-SNF-E00020 | SNF-F001 | Med Aide | Evening | 372.94 | 0.564 | confirm if time permits | Paid hours materially exceed scheduled hours | paid_exceeds_scheduled |
| 3 | SYN-SNF-E00037 | SNF-F001 | LPN | Day | 288.66 | 0.514 | confirm if time permits | Paid hours materially exceed scheduled hours | paid_exceeds_scheduled |
| 4 | SYN-SNF-E00023 | SNF-F001 | CNA | Night | 275.29 | 0.494 | confirm if time permits | Paid hours materially exceed scheduled hours | paid_exceeds_scheduled |
| 5 | SYN-SNF-E00023 | SNF-F001 | CNA | Day | 266.63 | 0.457 | confirm if time permits | Paid hours materially exceed scheduled hours | paid_exceeds_scheduled |

### High-Scoring Shift Records

Examples of shifts flagged by the hybrid score with rule and context detail:

| record_id | employee_id | pay_period_index | facility_id | role | shift_type | gross_pay | final_anomaly_score | pay_period_rank | rule_reason_codes |
|---|---|---|---|---|---|---|---|---|---|
| 69 | SYN-SNF-E00002 | 1 | SNF-F006 | CNA | Double | 452.15 | 0.599 | 1 | extreme_overtime;double_shift_rest_gap |
| 191 | SYN-SNF-E00004 | 1 | SNF-F006 | LPN | Double | 737.09 | 0.533 | 3 | extreme_overtime |
| 194 | SYN-SNF-E00004 | 1 | SNF-F006 | LPN | Day | 429.67 | 0.412 | 6 | paid_exceeds_scheduled |
| 313 | SYN-SNF-E00006 | 1 | SNF-F005 | CNA | Double | 470.44 | 0.490 | 3 | extreme_overtime |
| 556 | SYN-SNF-E00011 | 1 | SNF-F002 | Dietary | Evening | 269.70 | 0.456 | 2 | paid_exceeds_scheduled |

### Model Comparison at Review Budget k=5

Precision, recall, and PR-AUC for each scoring component on synthetic validation data:

| model | precision_at_k | recall_at_k | f1_at_k | pr_auc |
|---|---|---|---|---|
| rule_score | 0.517 | 0.775 | 0.620 | 0.848 |
| statistical_score | 0.467 | 0.700 | 0.560 | 0.422 |
| ml_score | 0.567 | 0.850 | 0.680 | 0.869 |
| hybrid_score | 0.550 | 0.825 | 0.660 | 0.839 |

*Note: Values are from a single representative synthetic run. Full ablation and temporal stability evidence are available in the notebook sequence.*

---

## SNF Case Studies

The initial SNF value story focuses on two case studies that are most useful to weekly facility payroll approval teams:

- **Overtime, double shifts, and staffing pressure:** shows how automated ranking prioritizes unusual overtime, double-shift, short rest-gap, and paid-vs-scheduled exceptions better than static overtime or total-hours thresholds.
- **Premium pay and shift differential mismatch:** shows how automated ranking detects unsupported shift differentials, weekend premium mismatches, duplicate premiums, or premium-without-support records that gross-pay or premium-dollar thresholds miss or overflag.

---

## Notebook Reporting

Rendered notebooks and case-study walkthroughs are hosted at:

**https://nrenzoni.github.io/payroll-anomaly-ranking/**

The Jupytext-paired notebook index is `notebooks/payroll_anomaly_detection.py`. The existing notebook sequence is being reoriented around SNF payroll approval:

- `notebooks/01_problem_framing_and_data_maturity.py`: SNF payroll approval framing, synthetic-data privacy, schema dictionary, validation warnings, and data maturity visuals.
- `notebooks/02_feature_engineering_and_baselines.py`: leakage-safe SNF shift-level features, facility normalization, rule flags, and manual threshold baselines.
- `notebooks/03_modeling_evaluation_and_error_analysis.py`: temporal validation, automated ranking, manual-threshold comparison, approval-budget metrics, and error analysis.
- `notebooks/04_review_queue_explainability_and_thresholds.py`: administrator-safe approval queue, case cards, recommended actions, thresholds, and feedback workflow.
- `notebooks/06_internal_statistical_diagnostics.py`: internal statistical diagnostics for review-budget uncertainty, subgroup behavior, expected-pay calibration, robustness, and perturbation sensitivity.
- `notebooks/07_simulation_and_stress_testing.py`: internal queue-capacity and scenario stress testing for threshold policy, overload probability, and missed exposure.
- `notebooks/08_snf_payroll_approval_case_studies.py`: business-facing SNF proof notebook showing how hybrid ranking improves overtime and premium review compared with manual thresholds.
- `notebooks/09_model_ablation_and_ml_value.py`: data-science validation notebook covering ablation, incremental ML value, temporal validation evidence, uncertainty, and robustness diagnostics.

Notebook-only plotting code lives in Jupytext notebook sources and shared plotting adapters under `notebooks/common/`. The runtime package remains free of Jupyter and Lets-Plot imports.

For fast notebook checks, supported internal notebooks can use reduced diagnostic workload settings and scored-only pipeline artifacts under `NOTEBOOK_FAST=1` so execution checks do not refresh paired `.ipynb` outputs.

```bash
NOTEBOOK_FAST=1 uv run jupytext --to ipynb --execute --run-path notebooks --output /tmp/06_internal_statistical_diagnostics.fast.ipynb notebooks/06_internal_statistical_diagnostics.py
```

---

## Project Structure

```
payroll-anomaly-ranking/
├── src/payroll_anomaly_ranking/    # Runtime package (no Jupyter deps)
│   ├── data.py                     # Synthetic SNF payroll generation
│   ├── features.py                 # Leakage-safe feature engineering
│   ├── models.py                   # Scoring + uncertainty quantification
│   ├── rules.py                    # Deterministic SNF rule flags
│   ├── evaluation.py               # Temporal validation & metrics
│   ├── explainability.py           # Review queues & summaries
│   ├── pipeline.py                 # Orchestration & artifact management
│   └── ...
├── notebooks/                      # Jupytext-paired narrative notebooks
│   ├── 01_problem_framing_and_data_maturity.py
│   ├── 02_feature_engineering_and_baselines.py
│   ├── 03_modeling_evaluation_and_error_analysis.py
│   ├── 04_review_queue_explainability_and_thresholds.py
│   ├── 06_internal_statistical_diagnostics.py
│   ├── 07_simulation_and_stress_testing.py
│   ├── 08_snf_payroll_approval_case_studies.py
│   ├── 09_model_ablation_and_ml_value.py
│   └── common/plots.py             # Shared plotting adapters
├── tests/
│   ├── smoke/                      # Fast sanity checks
│   └── integration/                # Regression tests
├── openspec/                       # Spec-driven design artifacts
├── docs/assets/                    # Architecture diagrams
├── ARCHITECTURE.md                 # High-level system design
├── DECISIONS.md                    # Technical decision log (ADRs)
└── data/ & outputs/                # Generated artifacts
```

---

## Tech Stack

| Layer | Tools |
|---|---|
| Data & Features | Polars, NumPy |
| ML & Stats | scikit-learn (unsupervised outlier detection), robust z-scores, MAD, IQR |
| Validation | Temporal splits, rolling-origin evaluation, backtesting |
| Uncertainty | Bootstrap intervals, conformal p-values, OOD detection, ensemble disagreement |
| Notebooks | Jupytext (git-friendly), Lets-Plot |
| Quality | Ruff, Pyrefly, pre-commit, pytest (smoke + integration) |
| Workflow | UV, OpenSpec (spec-driven development) |

---

## Intended Production Flow

A production implementation would ingest payroll, schedule, timeclock, HR lifecycle, facility reference, pay policy, and administrator feedback extracts into validation, feature engineering, scoring, pre-approval queue export, monitoring, and retraining workflows. This repository does not implement or claim live integrations.

Monitoring should track exception count per payroll cycle, approval queue yield, confirmed exception rate from feedback, estimated exposure flagged and confirmed, feature drift, score drift, alert concentration by facility/unit/role/shift, latency, data freshness, validation failures, and threshold-baseline drift.

---

## Development Checks

Use the smoke suite for a quick sanity check after small code changes:

```bash
uv run pytest tests/smoke
```

Run targeted integration checks for affected areas when changing pipeline behavior, scoring, diagnostics, scenarios, queue simulation, or notebook contracts:

```bash
uv run pytest tests/integration/test_regression.py -k "generation or scenario or feature or rule or scoring or evaluation or notebook"
```

Run repository hooks after code or notebook edits:

```bash
uv run prek run --all-files
```

---

## Engineering Process

Non-trivial behavior changes follow a propose / apply / archive cycle tracked under `openspec/`. Design documents, spec artifacts, and archived changes are versioned alongside code. This ensures that feature additions, scoring changes, and evaluation criteria remain traceable and reviewable.

See `ARCHITECTURE.md` for system context and component design, and `DECISIONS.md` for the rationale behind major technical choices such as Polars over pandas, shift-level grain, synthetic data, hybrid scoring, and Jupytext over raw `.ipynb`.

---

## Limitations

- Synthetic labels are useful for demonstration but simpler than real SNF payroll operations.
- Unsupervised anomaly scores can prioritize legitimate staffing exceptions, high-pressure shifts, or approved premium pay that administrators should confirm rather than reject.
- Hybrid weights and thresholds are configurable examples and should be calibrated with real review feedback before production use.
- The MVP includes optional notebook reporting and does not include live dashboards, access control, alerting, scheduling, payroll vendor integrations, or case-management workflows.

---

## Repository Guidance

**Suggested GitHub topics / tags:** `skilled-nursing-facility`, `payroll-anomaly-detection`, `polars`, `scikit-learn`, `machine-learning`, `healthcare-analytics`, `temporal-validation`, `uncertainty-quantification`, `synthetic-data`

**Recommended release cadence:** Tag a `v1.0.0` release after the README and architecture docs are merged. This gives a stable permalink for CVs and portfolio links.

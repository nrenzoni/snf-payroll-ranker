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

- [Key Points](#key-points)
- [Quick Start](#quick-start)
- [What The Workflow Covers](#what-the-workflow-covers)
- [Sample Outputs](#sample-outputs)
- [SNF Case Studies](#snf-case-studies)
- [Notebook Reporting](#notebook-reporting)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Intended Production Flow](#intended-production-flow)
- [Development Checks](#development-checks)
- [Agentic Development](#agentic-development)
- [Engineering Process](#engineering-process)
- [Limitations](#limitations)

---

## Key Points

- **Leakage-safe temporal validation**: pay-period splits, no random row sampling; historical features exclude current/future periods.
- **Facility-normalized, transferable features**: stationary ratios bootstrappable across new SNF clients with different pay scales.
- **Uncertainty quantification**: every record carries ensemble disagreement, bootstrap intervals, expected-pay bands, peer/history sample-size uncertainty, data-quality flags, and OOD detection — risk and uncertainty reported separately.
- **Explainable hybrid ranking**: weighted combination of rule, statistical, ML, peer, history, schedule/timeclock, premium eligibility, and exposure components.
- **Administrator-safe outputs**: recommended actions, sources to check, SNF context, review-safe explanations — no confirmed-misconduct labeling.

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

Expected generated files:

- `data/synthetic/*.csv`
- `outputs/evaluation/*.csv`

### Notebook Reporting Setup

Install optional notebook/reporting dependencies before executing Jupytext notebooks or rendering Lets-Plot visuals.

```bash
uv sync --extra notebooks
```

---

## What The Workflow Covers

- Shift-level SNF payroll generation with facility, unit, role, shift, schedule, timeclock, pay-code, premium, and lifecycle context.
- Synthetic exception scenarios: overtime/double-shift staffing pressure, premium pay / shift differential mismatch.
- Future scenario catalog: agency/float labor, census/acuity, credential/license mismatch, PBJ category, meal premiums, lifecycle, retro/rate corrections, union policy, new-client bootstrap, payroll close adjustments.
- Leakage-safe features: employee history, role/shift peer, facility-normalized ratios, schedule/timeclock mismatch, premium eligibility, fatigue/rest-gap, exposure estimates.
- Deterministic rules, robust statistics, unsupervised outlier detection, and hybrid ranking with manual threshold baselines.
- Administrator-safe pre-approval queues with recommended actions, sources to check, risk categories, and review-safe explanations.

---

## Sample Outputs

### Ranked Approval Queue

| rank | employee_id | facility_id | role | shift_type | gross_pay | final_anomaly_score | approval_risk_category | primary_reason | rule_reason_codes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SYN-SNF-E00028 | SNF-F001 | Therapy | Double | 727.89 | 0.690 | review before approval | Gross pay materially differs from similar SNF role/shift peers | none |
| 2 | SYN-SNF-E00020 | SNF-F001 | Med Aide | Evening | 372.94 | 0.564 | confirm if time permits | Paid hours materially exceed scheduled hours | paid_exceeds_scheduled |

### High-Scoring Shift Records

| record_id | employee_id | pay_period_index | facility_id | role | shift_type | gross_pay | final_anomaly_score | pay_period_rank | rule_reason_codes |
|---|---|---|---|---|---|---|---|---|---|
| 69 | SYN-SNF-E00002 | 1 | SNF-F006 | CNA | Double | 452.15 | 0.599 | 1 | extreme_overtime;double_shift_rest_gap |
| 191 | SYN-SNF-E00004 | 1 | SNF-F006 | LPN | Double | 737.09 | 0.533 | 3 | extreme_overtime |

### Model Comparison at Review Budget k=5

| model | precision_at_k | recall_at_k | f1_at_k | pr_auc |
|---|---|---|---|---|
| rule_score | 0.517 | 0.775 | 0.620 | 0.848 |
| hybrid_score | 0.550 | 0.825 | 0.660 | 0.839 |

*Values from a representative synthetic run. Full ablation and temporal stability evidence in the notebooks.*

---

## SNF Case Studies

The initial SNF value story focuses on two case studies that are most useful to weekly facility payroll approval teams:

- **Overtime, double shifts, and staffing pressure:** shows how automated ranking prioritizes unusual overtime, double-shift, short rest-gap, and paid-vs-scheduled exceptions better than static overtime or total-hours thresholds.
- **Premium pay and shift differential mismatch:** shows how automated ranking detects unsupported shift differentials, weekend premium mismatches, duplicate premiums, or premium-without-support records that gross-pay or premium-dollar thresholds miss or overflag.

---

## Notebook Reporting

Rendered notebooks and case-study walkthroughs are hosted at:

**https://nrenzoni.github.io/payroll-anomaly-ranking/**

Active notebooks:

- `notebooks/08_snf_payroll_approval_case_studies.py`: business-facing proof showing how hybrid ranking improves overtime and premium review vs. manual thresholds.
- `notebooks/09_model_ablation_and_ml_value.py`: ablation, incremental ML value, temporal validation evidence, uncertainty, and robustness diagnostics.

Notebook-only plotting code lives in Jupytext notebook sources and shared plotting adapters under `notebooks/common/`. The runtime package remains free of Jupyter and Lets-Plot imports.

Fast-path notebook validation (reduced workload, `/tmp` output, no paired `.ipynb` churn):

```bash
NOTEBOOK_FAST=1 uv run jupytext --to ipynb --execute --run-path notebooks --output /tmp/notebook.fast.ipynb notebooks/08_snf_payroll_approval_case_studies.py
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
| Quality | Ruff, Pyrefly, prek, pytest (smoke + integration) |
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

## Agentic Development

The project is designed for agentic iteration. See [`AGENTS.md`](AGENTS.md) for the full workflow contract.

- **Fast-path notebook validation**: `NOTEBOOK_FAST=1` runs reduced diagnostic workloads and writes executed notebooks only under `/tmp`, avoiding paired `.ipynb` churn on every check.
- **Pre-commit quality gates**: `uv run prek run --all-files` enforces Ruff lint/format, Pyrefly type checking, YAML validation, and trailing-comma consistency automatically.
- **Tiered testing**: smoke suite for quick sanity; targeted integration filters (`-k "scoring or uncertainty"`) for focused validation; full suite for pipeline-wide changes.
- **Lets-Plot render failures surface as exceptions**: `notebooks/common/plots.py` wraps `CheckedPlot` around Lets-Plot to parse generated HTML for embedded error messages and raise `LetsPlotRenderError`, so agent/CI loops detect broken plots instead of accepting silent render failures.
- **Visualization dependency boundary**: Lets-Plot and Jupyter dependencies are notebook-only; the runtime package under `src/` has zero plotting imports.
- **Spec-driven changes**: non-trivial behavior changes follow a propose / apply / archive cycle tracked under `openspec/`.
- **Code standards**: strict typing, named dataclasses for public multi-value returns, Polars expressions over row-wise Python callbacks, schema enums from `columns.py` instead of raw column strings.

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

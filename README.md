# SNF Payroll Approval Anomaly Ranking

This project demonstrates a privacy-safe, synthetic skilled nursing facility payroll approval assistant. It generates shift-level SNF payroll, schedule, and timeclock records for a multi-facility chain; injects known synthetic exceptions; builds leakage-safe, facility-normalized features; compares automated ranking against manual threshold rules; and exports administrator-safe weekly payroll approval queues.

## Privacy Guardrails

- The dataset is fully synthetic and reproducible from code.
- No real employee identifiers, resident data, payroll records, tax records, bank details, HR comments, company data, or production integrations are included.
- Review outputs describe records requiring pre-payroll approval review; they do not label employees or records as confirmed misconduct, fraud, or payroll error.
- Synthetic pay policies are illustrative and are not legal, payroll, union-contract, or state-specific compliance guidance.

## Core Pipeline Setup

```bash
uv sync
```

## Notebook Reporting Setup

Install optional notebook/reporting dependencies before executing Jupytext notebooks or rendering Lets-Plot visuals.

```bash
uv sync --extra notebooks
```

## Run The Pipeline

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

## What The Workflow Covers

- Shift-level SNF payroll generation with facilities, units, roles, license types, shift types, schedule context, timeclock context, pay-code categories, premium pay, approval status, lifecycle dates, and pay-period/facility rollups.
- Implemented synthetic exception scenarios for overtime/double-shift staffing pressure and premium pay or shift differential mismatch.
- Future scenario catalog entries for agency/float labor, census/acuity, credential/license mismatch, PBJ category mismatch, meal premiums, new hire orientation, termination/final pay, retro/rate corrections, union policy variation, new-client bootstrap, and payroll close adjustment concentration.
- Leakage-safe employee history, role/shift peer, facility-normalized, stationary ratio, schedule/timeclock, premium eligibility, fatigue/rest-gap, and exposure-estimate features.
- Deterministic SNF approval rules, robust statistical scoring, Isolation Forest scoring, and hybrid automated approval exception ranking.
- Manual threshold baselines for gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance.
- Administrator-safe pre-approval queues with recommended action, source to check, approval risk category, SNF context, estimated exposure, and review-safe explanations.

## SNF Case Studies

The initial SNF value story focuses on two case studies that are most useful to weekly facility payroll approval teams:

- **Overtime, double shifts, and staffing pressure:** shows how automated ranking prioritizes unusual overtime, double-shift, short rest-gap, and paid-vs-scheduled exceptions better than static overtime or total-hours thresholds.
- **Premium pay and shift differential mismatch:** shows how automated ranking detects unsupported shift differentials, weekend premium mismatches, duplicate premiums, or premium-without-support records that gross-pay or premium-dollar thresholds miss or overflag.

## Notebook Sequence

The Jupytext-paired notebook index is `notebooks/payroll_anomaly_detection.py`. The existing notebook sequence is being reoriented around SNF payroll approval:

- `notebooks/01_problem_framing_and_data_maturity.py`: SNF payroll approval framing, synthetic-data privacy, schema dictionary, validation warnings, and data maturity visuals.
- `notebooks/02_feature_engineering_and_baselines.py`: leakage-safe SNF shift-level features, facility normalization, rule flags, and manual threshold baselines.
- `notebooks/03_modeling_evaluation_and_error_analysis.py`: temporal validation, automated ranking, manual-threshold comparison, approval-budget metrics, and error analysis.
- `notebooks/04_review_queue_explainability_and_thresholds.py`: administrator-safe approval queue, case cards, recommended actions, thresholds, and feedback workflow.
- `notebooks/05_production_monitoring_and_deployment_path.py`: intended production flow from payroll, schedule, timeclock, HR lifecycle, and facility reference extracts through validation, scoring, administrator review, feedback, monitoring, and retraining.
- `notebooks/06_internal_statistical_diagnostics.py`: internal statistical diagnostics for review-budget uncertainty, subgroup behavior, expected-pay calibration, robustness, and perturbation sensitivity.
- `notebooks/07_simulation_and_stress_testing.py`: internal queue-capacity and scenario stress testing for threshold policy, overload probability, and missed exposure.
- `notebooks/08_snf_payroll_approval_case_studies.py`: business-facing SNF proof notebook showing how hybrid ranking improves overtime and premium review compared with manual thresholds.
- `notebooks/09_model_ablation_and_ml_value.py`: data-science validation notebook covering ablation, incremental ML value, temporal validation evidence, uncertainty, and robustness diagnostics.

Notebook-only plotting code lives in Jupytext notebook sources and shared plotting adapters under `notebooks/common/`. The runtime package remains free of Jupyter and Lets-Plot imports.

For fast notebook checks, supported internal notebooks can use reduced diagnostic workload settings and scored-only pipeline artifacts under `NOTEBOOK_FAST=1` so execution checks do not refresh paired `.ipynb` outputs.

```bash
NOTEBOOK_FAST=1 uv run jupytext --to ipynb --execute --run-path notebooks --output /tmp/06_internal_statistical_diagnostics.fast.ipynb notebooks/06_internal_statistical_diagnostics.py
```

## Intended Production Flow

A production implementation would ingest payroll, schedule, timeclock, HR lifecycle, facility reference, pay policy, and administrator feedback extracts into validation, feature engineering, scoring, pre-approval queue export, monitoring, and retraining workflows. This repository does not implement or claim live integrations.

Monitoring should track exception count per payroll cycle, approval queue yield, confirmed exception rate from feedback, estimated exposure flagged and confirmed, feature drift, score drift, alert concentration by facility/unit/role/shift, latency, data freshness, validation failures, and threshold-baseline drift.

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

## Limitations

- Synthetic labels are useful for demonstration but simpler than real SNF payroll operations.
- Unsupervised anomaly scores can prioritize legitimate staffing exceptions, high-pressure shifts, or approved premium pay that administrators should confirm rather than reject.
- Hybrid weights and thresholds are configurable examples and should be calibrated with real review feedback before production use.
- The MVP includes optional notebook reporting and does not include live dashboards, access control, alerting, scheduling, payroll vendor integrations, or case-management workflows.

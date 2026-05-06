# Payroll Anomaly Ranking

This project demonstrates a privacy-safe payroll anomaly detection workflow using synthetic employee-pay-period data. It generates payroll-like records, injects known anomaly categories, builds leakage-safe features, compares rule/statistical/Isolation Forest/hybrid scoring approaches, and exports an analyst-ready review queue.

## Privacy Guardrails

- The dataset is fully synthetic and reproducible from code.
- No real employee identifiers, salaries, tax records, bank details, HR comments, company data, or production integrations are included.
- Review queue outputs describe records requiring payroll review; they do not label employees or records as confirmed misconduct.

## Setup

```bash
uv sync
```

## Run The Pipeline

```bash
uv run python -m payroll_anomaly_ranking.pipeline
```

Expected generated files:

- `data/synthetic/synthetic_payroll.csv`
- `data/synthetic/synthetic_payroll_labels.csv`
- `outputs/evaluation/scored_payroll.csv`
- `outputs/evaluation/review_budget_metrics.csv`
- `outputs/evaluation/model_comparison.csv`
- `outputs/evaluation/category_error_analysis.csv`
- `outputs/evaluation/backtest_metrics.csv`
- `outputs/evaluation/review_queue.csv`

## Notebook Sequence

The Jupytext-paired notebook index is `notebooks/payroll_anomaly_detection.py`. The business-facing sequence is:

- `notebooks/01_problem_framing_and_data_maturity.py`: business framing, synthetic-data privacy, payroll anomaly taxonomy, schema dictionary, validation failures versus warnings, quality summaries, and data maturity visuals.
- `notebooks/02_feature_engineering_and_baselines.py`: leakage-safe employee history features, peer-relative context, rule flags, robust statistical features, score components, baseline comparison, score distribution, and selected employee history.
- `notebooks/03_modeling_evaluation_and_error_analysis.py`: temporal validation framing, precision@K, recall@K, F1@K, PR-AUC, average anomaly rank, mean reciprocal rank, dollars captured@K, model comparison, backtesting, and category error analysis.
- `notebooks/04_review_queue_explainability_and_thresholds.py`: analyst-readable review queue, review-safe explanations, compact case cards, top-K and threshold workload views, risk categories, operating model, and conceptual feedback capture.
- `notebooks/05_production_monitoring_and_deployment_path.py`: realistic deployment path, architecture table, monitoring metrics, retraining triggers, limitations, and governance controls without claiming live integrations.

Run a notebook from a clean checkout with:

```bash
uv run jupytext --to ipynb notebooks/01_problem_framing_and_data_maturity.py
uv run jupyter nbconvert --to notebook --execute notebooks/01_problem_framing_and_data_maturity.ipynb --output 01_problem_framing_and_data_maturity.executed.ipynb --output-dir notebooks
```

## What The Workflow Covers

- Synthetic employee and payroll-period generation with departments, job families, locations, pay types, tenure, lifecycle dates, pay rates, status changes, payroll values, and controlled imperfections.
- Injected anomaly labels for duplicate payment, overtime spike, pay after termination, gross pay spike, incorrect pay rate, missing deduction, negative net pay, retro pay outlier, department payroll spike, and new employee large payment.
- Validation checks that separate hard data failures from warning-level payroll exceptions.
- Prior-period history features, peer-relative features, robust statistical features, deterministic rule flags, Isolation Forest scores, and configurable hybrid ranking.
- Temporal evaluation, review-budget metrics, dollars-at-risk capture, model comparison, backtesting-style summaries, category error analysis, and review queue explanations.

## Intended Production Flow

A production implementation would ingest payroll, HRIS, and timekeeping source extracts into validation, feature engineering, scoring, analyst review, feedback capture, monitoring, and retraining workflows. This repository does not implement or claim live integrations.

Likely integration points include batch payroll extracts, HR lifecycle tables, timekeeping/overtime feeds, approved adjustment records, case-management feedback, and governed model monitoring outputs.

Monitoring should track alert count per cycle, alert acceptance rate, false positive rate from reviews, dollars at risk flagged and confirmed, feature drift, score drift, alert concentration, latency, and data freshness.

Retraining should be triggered by feature drift, score drift, business rule changes, payroll calendar changes, sustained review feedback degradation, or enough newly reviewed labels to support supervised calibration.

## Limitations

- Synthetic labels are useful for demonstration but simpler than real payroll operations.
- Unsupervised anomaly scores can prioritize legitimate bonuses, high earners, or approved corrections.
- Hybrid weights are configurable examples and should be tuned against validation outcomes and business review capacity.
- The MVP is notebook-first and does not include live dashboards, access control, alerting, scheduling, or vendor integrations.

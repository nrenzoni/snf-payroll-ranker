# Payroll Anomaly Ranking

This project demonstrates a privacy-safe payroll anomaly detection workflow using synthetic employee-pay-period data. It generates payroll-like records, injects known anomaly categories, builds leakage-safe features, compares rule/statistical/Isolation Forest/hybrid scoring approaches, and exports separate analyst-safe and evaluation-labeled review queues.

## Privacy Guardrails

- The dataset is fully synthetic and reproducible from code.
- No real employee identifiers, salaries, tax records, bank details, HR comments, company data, or production integrations are included.
- Review queue outputs describe records requiring payroll review; they do not label employees or records as confirmed misconduct.

## Core Pipeline Setup

The core runtime installs only pipeline dependencies needed by downstream payroll anomaly ranking workflows. Notebook and plotting tools are optional.

```bash
uv sync
```

## Notebook Reporting Setup

Install the notebook/reporting extra before executing Jupytext notebooks or rendering Lets-Plot visuals.

```bash
uv sync --extra notebooks
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
- `outputs/evaluation/rolling_origin_metrics.csv`
- `outputs/evaluation/validation_selected_settings.csv`
- `outputs/evaluation/stability_summary.csv`
- `outputs/evaluation/leakage_checks.csv`
- `outputs/evaluation/analyst_review_queue.csv`
- `outputs/evaluation/evaluation_labeled_review_queue.csv`
- `outputs/evaluation/scenario_metadata.json` when a scenario-controlled run is written

## Development Checks

Use the smoke suite for a quick sanity check after small code changes:

```bash
uv run pytest tests/smoke
```

Run targeted integration checks for the affected area when changing pipeline behavior, scoring, diagnostics, scenarios, queue simulation, or notebook contracts. Run the full suite for large behavior changes or release-level validation:

```bash
uv run pytest
```

Run repository hooks after code or notebook edits:

```bash
uv run prek run --all-files
```

## Notebook Sequence

The Jupytext-paired notebook index is `notebooks/payroll_anomaly_detection.py`. The business-facing sequence is:

- `notebooks/01_problem_framing_and_data_maturity.py`: business framing, synthetic-data privacy, payroll anomaly taxonomy, schema dictionary, validation failures versus warnings, quality summaries, and data maturity visuals.
- `notebooks/02_feature_engineering_and_baselines.py`: leakage-safe employee history features, period-safe peer context, rule flags, robust statistical features, estimated exposure, score components, baseline comparison, score distribution, and selected employee history.
- `notebooks/03_modeling_evaluation_and_error_analysis.py`: temporal validation framing, rolling-origin validation, validation-selected thresholds, stability summaries, leakage checks, precision@K, recall@K, F1@K, PR-AUC, average anomaly rank, mean reciprocal rank, dollars captured@K, model comparison, backtesting, and category error analysis.
- `notebooks/04_review_queue_explainability_and_thresholds.py`: analyst-safe review queue, separate evaluation-labeled queue, review-safe explanations, compact case cards, top-K and threshold workload views, risk categories, operating model, and conceptual feedback capture.
- `notebooks/05_production_monitoring_and_deployment_path.py`: realistic deployment path, architecture table, monitoring metrics, retraining triggers, limitations, and governance controls without claiming live integrations.

Internal diagnostic notebooks are separate from the business-facing sequence:

- `notebooks/06_internal_statistical_diagnostics.py`: Bayesian-style review-budget intervals, component superiority diagnostics, subgroup shrinkage summaries, expected-pay calibration, exposure calibration, robustness checks, and perturbation sensitivity.
- `notebooks/07_simulation_and_stress_testing.py`: Monte Carlo queue-capacity outcomes, drift scenario comparisons, anomaly-mix stress tests, change-point diagnostics, and stress-test heatmaps.

The internal notebooks use synthetic evaluation labels and injected anomaly dollar impacts for diagnostics only. Those fields do not alter model feature columns or analyst-safe review queue outputs.

Run a notebook from a clean checkout after installing the notebook/reporting extra with:

```bash
uv run jupytext --set-formats ipynb,py:percent --execute notebooks/01_problem_framing_and_data_maturity.py
```

Notebook-only plotting code lives in the Jupytext notebook sources, with shared plotting adapters in `notebooks/common/plots.py`. The `src/payroll_anomaly_ranking/` package is kept free of Jupyter and Lets-Plot imports so downstream ML pipelines can use the runtime package without reporting dependencies.

Internal notebooks use bounded but denser local defaults. Notebook `06` runs eight internal diagnostic scenarios (`baseline`, `rule-friendly`, `statistical-friendly`, `ml-friendly`, `exposure-heavy`, `subgroup-drift`, `calendar-drift`, `queue-stress`) across three seeds with 220 employees, 14 pay periods, and `INTERVAL_SAMPLES = 75`. Notebook `07` runs four queue scenarios (`baseline`, `queue-stress`, `calendar-drift`, `exposure-heavy`) with 220 employees, 14 pay periods, `QUEUE_ITERATIONS = 60`, `review_budget=10`, and threshold-grid demand at `QUEUE_THRESHOLD_GRID = (0.35, 0.45, 0.55, 0.65)`, plus an adaptive 90th-percentile threshold view. For faster local execution, reduce `DIAGNOSTIC_SCENARIOS`, `DIAGNOSTIC_SEEDS`, or `INTERVAL_SAMPLES` in notebook `06`, and reduce `QUEUE_SCENARIOS`, `QUEUE_ITERATIONS`, or `QUEUE_THRESHOLD_GRID` in notebook `07`.

## What The Workflow Covers

- Synthetic employee and payroll-period generation with departments, job families, locations, pay types, tenure, lifecycle dates, pay rates, status changes, payroll values, and controlled imperfections.
- Injected anomaly labels for duplicate payment, overtime spike, pay after termination, gross pay spike, incorrect pay rate, missing deduction, negative net pay, retro pay outlier, department payroll spike, and new employee large payment.
- Validation checks that separate hard data failures from warning-level payroll exceptions.
- Prior-period history features, period-safe peer-relative features, robust statistical features, deterministic rule flags including missing deductions, Isolation Forest scores, estimated exposure, and configurable hybrid ranking.
- Temporal evaluation, rolling-origin validation, review-budget metrics, dollars-at-risk capture, model comparison, backtesting-style summaries, leakage checks, category error analysis, and review queue explanations.

## Intended Production Flow

A production implementation would ingest payroll, HRIS, and timekeeping source extracts into validation, feature engineering, scoring, analyst review, feedback capture, monitoring, and retraining workflows. This repository does not implement or claim live integrations.

Likely integration points include batch payroll extracts, HR lifecycle tables, timekeeping/overtime feeds, approved adjustment records, case-management feedback, and governed model monitoring outputs.

Monitoring should track alert count per cycle, alert acceptance rate, false positive rate from reviews, dollars at risk flagged and confirmed, feature drift, score drift, alert concentration, latency, and data freshness.

Retraining should be triggered by feature drift, score drift, business rule changes, payroll calendar changes, sustained review feedback degradation, or enough newly reviewed labels to support supervised calibration.

## Limitations

- Synthetic labels are useful for demonstration but simpler than real payroll operations.
- Unsupervised anomaly scores can prioritize legitimate bonuses, high earners, or approved corrections.
- Hybrid weights are configurable examples and should be tuned against validation outcomes and business review capacity.
- The MVP includes optional notebook reporting and does not include live dashboards, access control, alerting, scheduling, or vendor integrations.

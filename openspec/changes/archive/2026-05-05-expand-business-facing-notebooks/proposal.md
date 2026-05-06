## Why

The current notebook describes the payroll anomaly ranking workflow but does not demonstrate the repository as a complete, business-facing case study. A focused notebook sequence will make the existing synthetic data, validation, scoring, evaluation, review queue, explainability, and production-readiness capabilities easier to understand, verify, and present.

## What Changes

- Add a polished Jupytext-paired notebook sequence under `notebooks/` that walks through the payroll anomaly ranking pipeline from business framing through production monitoring.
- Replace the single compressed narrative with focused notebooks for problem framing, data maturity, feature engineering, baselines, modeling, evaluation, error analysis, review queues, explainability, thresholds, and deployment path.
- Keep all examples synthetic and avoid any claim that fraud is determined or live production integrations are implemented.
- Reuse existing modules for synthetic data generation, validation, features, rules, models, evaluation, explainability, and charts wherever possible.
- Add only minimal notebook-local or small shared helper code if needed for business-facing tables, case cards, or visuals.
- Update `README.md` to list the notebook sequence and explain the purpose of each notebook.
- Preserve `notebooks/payroll_anomaly_detection.py` as a short index or overview notebook when practical.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `synthetic-payroll-data`: Extend documentation and notebook demonstrations for privacy, governance, schema/data dictionary, validation failures, payroll exception warnings, and data quality summaries.
- `payroll-anomaly-scoring`: Extend notebook demonstrations for leakage-safe historical features, peer-relative features, deterministic rule flags, robust statistical features, baseline scoring, ML scoring, and hybrid ranking.
- `payroll-anomaly-evaluation`: Extend notebook demonstrations for temporal validation, review-budget metrics, model comparison, cost-aware interpretation, backtesting by period, and category-level error analysis.
- `payroll-review-queue`: Extend notebook demonstrations for analyst-readable review queues, case cards, thresholds, risk categories, operating model, explainability, and production-readiness guidance.

## Impact

- Affected notebooks: new files `notebooks/01_problem_framing_and_data_maturity.py`, `notebooks/02_feature_engineering_and_baselines.py`, `notebooks/03_modeling_evaluation_and_error_analysis.py`, `notebooks/04_review_queue_explainability_and_thresholds.py`, `notebooks/05_production_monitoring_and_deployment_path.py`, and optionally a shortened `notebooks/payroll_anomaly_detection.py` index.
- Affected documentation: `README.md` notebook sequence overview.
- Affected outputs: notebooks should generate or reuse synthetic data under `data/synthetic` and evaluation artifacts under `outputs/evaluation`.
- No real or sensitive payroll data, new external integrations, or breaking API changes are introduced.

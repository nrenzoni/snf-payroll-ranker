## Why

Payroll anomaly detection is a high-value operational risk problem. This project must avoid exposing sensitive payroll data and must go beyond training a single unsupervised model. This change creates a privacy-safe, business-oriented notebook and supporting project structure that demonstrates synthetic data generation, defensible anomaly scoring, evaluation under sparse labels, and production-minded review workflows.

## What Changes

- Add a payroll anomaly detection notebook centered on employee-pay-period records and a ranked analyst review queue.
- Generate realistic synthetic payroll data with employee, department, job, pay-period, compensation, deduction, overtime, lifecycle, and adjustment patterns.
- Inject known anomaly categories such as duplicate payments, overtime spikes, post-termination pay, gross pay spikes, incorrect pay rates, missing deductions, negative net pay, retro pay outliers, department payroll spikes, and new-employee large payments.
- Add payroll-specific EDA, data validation checks, leakage-safe feature engineering, rule-based baselines, robust statistical scoring, Isolation Forest scoring, hybrid scoring, and model comparison.
- Evaluate with temporal/backtesting-style splits, precision@K, recall@K, PR-AUC where applicable, review-capacity analysis, and dollars-at-risk captured@K.
- Produce explainable anomaly outputs with risk categories, primary/secondary reasons, rule flags, expected values, peer-relative context, and dollars at risk.
- Document privacy guardrails, production architecture, monitoring, retraining, limitations, and next steps.

## Capabilities

### New Capabilities
- `synthetic-payroll-data`: Generate privacy-safe synthetic payroll records and injected anomaly labels suitable for notebook analysis and repeatable tests.
- `payroll-anomaly-scoring`: Build leakage-safe payroll features, deterministic rules, statistical anomaly scores, ML anomaly scores, and a configurable hybrid ranking score.
- `payroll-anomaly-evaluation`: Evaluate ranked payroll anomaly outputs using temporal validation, review-budget metrics, anomaly-category analysis, and dollars-at-risk capture.
- `payroll-review-queue`: Produce analyst-ready anomaly explanations and review queue artifacts suitable for a business deliverable.

### Modified Capabilities
- None.

## Impact

- Adds a reproducible notebook, modular Python source files, generated synthetic sample data, and output artifacts.
- Adds or updates project documentation and dependency metadata for running the notebook and pipeline.
- No external payroll systems or real employee data are introduced.
- No breaking API or persisted-data changes are expected.

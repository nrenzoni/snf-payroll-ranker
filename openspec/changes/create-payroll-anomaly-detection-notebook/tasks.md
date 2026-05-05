## 1. Project Setup

- [ ] 1.1 Add runtime dependencies for Polars, numpy, scikit-learn, lets-plot, jupyter, and notebook export support to `pyproject.toml` using UV conventions.
- [ ] 1.2 Create the source package structure under `src/payroll_anomaly_ranking/` with modules for data generation, validation, features, rules, models, evaluation, and explainability.
- [ ] 1.3 Create output directories for generated synthetic data, model/evaluation outputs, and notebook images or charts.
- [ ] 1.4 Add package initialization and lightweight configuration defaults for random seed, pay periods, employee count, review budgets, and hybrid score weights.

## 2. Synthetic Payroll Data

- [ ] 2.1 Implement employee and payroll-period generation with synthetic identifiers, departments, job families, locations, pay types, tenure, lifecycle dates, pay rates, and status changes.
- [ ] 2.2 Generate realistic employee-pay-period payroll values for regular hours, overtime, gross pay, bonus, commission, retro pay, deductions, net pay, and manual adjustments.
- [ ] 2.3 Add seasonality, department/job-level variation, promotions, terminations, hourly/salaried differences, and controlled data quality imperfections.
- [ ] 2.4 Inject labeled anomaly categories including duplicate payment, overtime spike, pay after termination, gross pay spike, incorrect pay rate, missing deduction, negative net pay, retro pay outlier, department payroll spike, and new employee large payment.
- [ ] 2.5 Persist a reproducible synthetic sample dataset and label metadata without real payroll identifiers or sensitive fields.

## 3. Data Validation And EDA Support

- [ ] 3.1 Implement validation checks for required columns, null identifiers, pay-period ordering, valid lifecycle dates, nonnegative normal payroll values, and suspicious net-to-gross relationships.
- [ ] 3.2 Distinguish hard validation failures from warning-level payroll exceptions that may be legitimate corrections or adjustments.
- [ ] 3.3 Add reusable aggregation helpers for payroll volume, active employee counts, department payroll, overtime, manual adjustments, pay-rate changes, and distribution summaries.
- [ ] 3.4 Add lets-plot chart helpers for payroll trends, pay distributions, overtime distributions, department heatmaps, score distributions, precision@K, dollars captured@K, and highlighted employee histories.

## 4. Leakage-Safe Features And Rules

- [ ] 4.1 Implement prior-period employee history features such as lagged gross pay, rolling medians, rolling standard deviations, percent changes, overtime baselines, deduction ratios, and net-to-gross ratios.
- [ ] 4.2 Implement peer-relative features by department, job family, pay type, location, and tenure bucket without using future periods.
- [ ] 4.3 Implement robust statistical features including robust z-scores, median absolute deviation scores, IQR outlier flags, percentiles, and deviation ratios.
- [ ] 4.4 Implement deterministic payroll rule flags for lifecycle, duplicate, negative/zero pay, extreme overtime, large adjustment, pay-rate change, and net-pay consistency anomalies.
- [ ] 4.5 Add a rule severity score and reason codes that can be reused by scoring, explanations, and evaluation.

## 5. Model Scoring And Hybrid Ranking

- [ ] 5.1 Build temporal train/validation/test split utilities based on pay periods rather than random row splits.
- [ ] 5.2 Implement robust statistical anomaly scoring from engineered features and rule outputs.
- [ ] 5.3 Train and apply an Isolation Forest model using only leakage-safe numeric features and no injected labels as predictors.
- [ ] 5.4 Normalize component scores to comparable scales for rule, employee-history, peer-relative, ML, and dollar-impact components.
- [ ] 5.5 Implement configurable hybrid scoring and per-pay-period ranking for review queue prioritization.

## 6. Evaluation

- [ ] 6.1 Implement precision@K, recall@K, F1 where applicable, PR-AUC where applicable, average anomaly rank, and mean reciprocal rank for injected labels.
- [ ] 6.2 Implement dollars-at-risk captured@K and percent of injected anomaly dollar impact captured under configured review budgets.
- [ ] 6.3 Implement temporal holdout evaluation and optional backtesting-style evaluation that scores each pay period using prior periods only.
- [ ] 6.4 Produce model comparison outputs for rule-only, statistical-only, Isolation Forest, and hybrid scoring approaches.
- [ ] 6.5 Produce category-level evaluation and error-analysis tables for false positives, false negatives, legitimate exceptions, and subtle missed anomalies.

## 7. Explainability And Review Queue

- [ ] 7.1 Generate primary and secondary anomaly reasons from rule flags, score drivers, historical baselines, peer comparisons, and dollar-impact estimates.
- [ ] 7.2 Create an analyst-ready review queue with rank, synthetic employee identifier, pay period, score, category, explanation, expected value context, rule flags, and dollars at risk.
- [ ] 7.3 Export review queue and model comparison result CSV files to the outputs directory.
- [ ] 7.4 Include sample explanation text that frames anomalies as records requiring review rather than confirmed fraud.

## 8. Notebook And Documentation

- [ ] 8.1 Create a Jupytext-paired notebook for `payroll_anomaly_detection` that can be executed reproducibly from a clean checkout.
- [ ] 8.2 Add notebook sections for executive summary, privacy disclaimer, problem framing, anomaly taxonomy, synthetic data generation, EDA, feature engineering, baselines, model comparison, hybrid scoring, evaluation, review queue, error analysis, production architecture, monitoring, limitations, and future improvements.
- [ ] 8.3 Update `README.md` with project purpose, privacy guardrails, setup commands, how to run the notebook/pipeline, expected outputs, and limitations.
- [ ] 8.4 Document intended production flow, likely integration points, analyst feedback loop, monitoring metrics, and retraining triggers without claiming live integrations.

## 9. Verification

- [ ] 9.1 Add smoke tests or executable checks for data generation, validation, feature generation, rule scoring, evaluation metrics, and review queue creation.
- [ ] 9.2 Run formatting and tests with the repository's UV-based workflow.
- [ ] 9.3 Execute the notebook or paired script end-to-end and verify generated datasets, charts, metrics, and output CSVs are created.
- [ ] 9.4 Confirm no real payroll data, personal identifiers, secrets, or sensitive HR fields are committed.

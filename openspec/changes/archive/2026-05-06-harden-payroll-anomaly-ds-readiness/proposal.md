## Why

The payroll anomaly workflow already tells a strong business-facing story, but several data-science robustness gaps make the reported performance easier to overstate than a production review workflow would support. This change hardens the demo by removing label-derived scoring leakage, making reference features temporally honest, separating analyst-safe outputs from evaluation labels, and adding stronger validation/backtesting expectations.

## What Changes

- Replace label-derived dollar scoring with production-observable estimated exposure based on expected pay, peer context, rule flags, and payroll field deltas.
- Strengthen leakage safety so employee history, peer baselines, robust distribution statistics, and model training use only information available at the scored pay period.
- Add deterministic rule and explanation coverage for missing or zero deductions so all supported synthetic anomaly categories have visible scoring/error-analysis behavior.
- Split operational analyst review outputs from synthetic evaluation-labeled outputs so labels and injected dollar impacts are not presented as fields that would be known before review.
- Expand evaluation from aggregate temporal metrics to rolling-origin validation, validation-period threshold/weight tuning, confidence or stability summaries, and explicit leakage checks.
- Improve reproducibility and communication by adding clean notebook execution expectations and clearer notebook interpretation of robust data-science choices.

## Capabilities

### New Capabilities

- `notebook-reproducibility`: Defines clean execution and saved-output expectations for the notebook sequence as an engineering deliverable.

### Modified Capabilities

- `payroll-anomaly-scoring`: Require label-free exposure scoring, period-safe peer/robust features, and missing-deduction rule scoring.
- `payroll-anomaly-evaluation`: Require rolling-origin validation, validation-based operating-point selection, stability summaries, and leakage checks.
- `payroll-review-queue`: Require separate analyst-safe and evaluation-labeled queues with clear reason-code/component context.
- `synthetic-payroll-data`: Clarify that injected labels and injected dollar impacts are evaluation-only and must not appear in production-facing scoring or analyst outputs.

## Impact

- Affects `src/payroll_anomaly_ranking/features.py`, `models.py`, `rules.py`, `evaluation.py`, `explainability.py`, `pipeline.py`, and related column definitions.
- Affects notebooks `02_feature_engineering_and_baselines.py`, `03_modeling_evaluation_and_error_analysis.py`, `04_review_queue_explainability_and_thresholds.py`, and `05_production_monitoring_and_deployment_path.py`.
- Affects generated CSV outputs under `outputs/evaluation/` and notebook-facing saved outputs.
- Adds or expands tests for leakage prevention, missing-deduction behavior, queue field separation, rolling-origin metrics, and notebook/output reproducibility.

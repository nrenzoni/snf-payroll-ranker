## 1. Synthetic Data And Schema

- [ ] 1.1 Add `pay_code` and any evaluation-only OOD metadata constants to `columns.py` while keeping metadata out of model features and analyst queues.
- [ ] 1.2 Update synthetic payroll generation to emit reproducible `pay_code` values for every payroll row.
- [ ] 1.3 Add late-period `pay_code` novelty and rarity drift using the configured seed so OOD examples exist in the synthetic data.
- [ ] 1.4 Update validation, schema dictionary, and data quality summaries to document `pay_code` and its OOD expectations.

## 2. Scoring Data Model And Configuration

- [ ] 2.1 Add uncertainty-related score, review, metric, and aggregate column constants to `columns.py`.
- [ ] 2.2 Add configurable uncertainty component weights, bucket thresholds, bootstrap settings, OOD settings, and `reference_window_periods=6` to `PayrollConfig`.
- [ ] 2.3 Add reusable fields for strict peer-group size, effective peer-reference size, and prior employee pay-period count.
- [ ] 2.4 Add expected gross-pay interval output columns for p10, p50, p90, interval width, and excess over p90.

## 3. Uncertainty And Interval Implementation

- [ ] 3.1 Implement rolling prior-period reference helpers that exclude the scored period and future periods and default to the last 6 prior pay periods.
- [ ] 3.2 Implement ensemble disagreement using configurable weighted dispersion across available rule, history, peer, statistical, ML, and exposure score signals.
- [ ] 3.3 Implement efficient bootstrap Isolation Forest score interval calculation using NumPy bootstrap index arrays and the rolling prior-period reference window.
- [ ] 3.4 Implement conformal p-value and conformal percentile calculation from rolling prior-period calibration scores as explanation-only context.
- [ ] 3.5 Implement expected `gross_pay` interval prediction with p10, p50, p90, interval width, and excess over p90 using the rolling prior-period reference window.
- [ ] 3.6 Implement peer-group and employee-history sample-size uncertainty components and Low/Medium/High helper buckets where useful.
- [ ] 3.7 Implement data-quality uncertainty from explicit missing, invalid, unknown, inconsistent, or stale payroll input indicators available in the synthetic workflow.
- [ ] 3.8 Implement OOD uncertainty using unseen `pay_code`, rare `pay_code`, rare pay-code combinations, out-of-range checks, and nearest-neighbor distance over normalized model features.
- [ ] 3.9 Implement composite uncertainty score, uncertainty bucket, primary uncertainty reason, and detailed uncertainty driver fields excluding conformal values from the composite.
- [ ] 3.10 Wire uncertainty and expected-pay interval calculation into the scoring pipeline after component scores are available while keeping `final_anomaly_score` separate from uncertainty.

## 4. Review Queue And Explanations

- [ ] 4.1 Update analyst-safe review queue generation to return latest-pay-period records only.
- [ ] 4.2 Update analyst-safe review queue fields to include risk score, uncertainty bucket, composite uncertainty score, primary uncertainty reason, conformal context, and gross-pay interval context without synthetic evaluation labels or OOD labels.
- [ ] 4.3 Add a human-readable pay-period date or label to review queue and case-card outputs.
- [ ] 4.4 Update case-card and explanation helpers to include why-risky and why-uncertain text using review-safe language.
- [ ] 4.5 Ensure high-risk records with medium or high uncertainty remain visible in ranked latest-period review outputs rather than being suppressed by uncertainty.

## 5. Evaluation And Notebook Updates

- [ ] 5.1 Add evaluation functions for precision or anomaly rate by uncertainty bucket.
- [ ] 5.2 Add risk-coverage and abstention-impact evaluation outputs for evaluation-labeled synthetic data.
- [ ] 5.3 Add expected gross-pay interval evaluation for normal-record coverage, anomaly exceedance over p90, and interval-width summaries.
- [ ] 5.4 Update `03_modeling_evaluation_and_error_analysis.py` to show uncertainty component summaries, expected gross-pay interval diagnostics, precision by uncertainty bucket, and risk-coverage outputs.
- [ ] 5.5 Update `04_review_queue_explainability_and_thresholds.py` to show latest-period risk plus uncertainty in the review queue and selected case cards.
- [ ] 5.6 Update `05_production_monitoring_and_deployment_path.py` to document uncertainty monitoring, pay-code OOD monitoring, calibration uncertainty as future analyst-feedback work, and production limitations.

## 6. Verification

- [ ] 6.1 Add or update tests covering Polars-first uncertainty scoring outputs, label-free uncertainty scoring, conformal context exclusion from composite uncertainty, uncertainty bucket assignment, and analyst queue label exclusion.
- [ ] 6.2 Add tests covering `pay_code` generation, late-period pay-code OOD drift, rolling 6-prior-period references, expected gross-pay interval outputs, and latest-period-only analyst queue behavior.
- [ ] 6.3 Run the project test command and fix any failures.
- [ ] 6.4 Execute or smoke-check the affected Jupytext notebooks to verify tables and visuals render without errors.
- [ ] 6.5 Validate OpenSpec status for the change after implementation.

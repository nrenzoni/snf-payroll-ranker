## Context

The project already generates synthetic payroll data, engineers leakage-safe features, computes rule/statistical/ML/hybrid anomaly scores, evaluates ranked outputs, and presents analyst-safe review queues. This change adds explicit uncertainty around the risk score so payroll analysts can distinguish high-risk/high-confidence records from high-risk records that need cautious interpretation because evidence is inconsistent, context is thin, or the record is out of distribution.

The existing notebook sequence remains the right structure. Uncertainty scoring, expected-pay intervals, and evaluation diagnostics fit into `03_modeling_evaluation_and_error_analysis.py`. Latest-period analyst presentation fits into `04_review_queue_explainability_and_thresholds.py`. Production caveats, calibration labels, OOD monitoring, and feedback-driven tuning fit into `05_production_monitoring_and_deployment_path.py`.

## Goals / Non-Goals

**Goals:**

- Add record-level uncertainty components for ensemble disagreement, bootstrap interval width, gross-pay interval width, peer-group sample size, employee-history sample size, data quality issues, and out-of-distribution context.
- Add expected-pay interval prediction for `gross_pay` only, with p10, p50, p90, interval width, and excess over p90 outputs.
- Add conformal p-values and conformal percentiles as explanation-only anomaly context.
- Produce a configurable composite uncertainty score and Low/Medium/High uncertainty bucket.
- Add analyst-readable uncertainty reasons that explain the largest uncertainty drivers without implying confirmed fraud or misconduct.
- Use a configurable rolling reference window of the last 6 prior pay periods for calibration, OOD references, bootstrap references, and expected-pay interval references.
- Extend synthetic payroll data with `pay_code` and reproducible late-period pay-code drift or novelty so OOD behavior can be demonstrated.
- Limit analyst-safe review queues to the latest pay period while keeping historical scored records available for evaluation and notebooks.
- Keep calculations leakage-safe: training, calibration, interval, and neighbor references must use only records available before the scored pay period.

**Non-Goals:**

- Do not implement calibration uncertainty until analyst feedback or comparable labels exist.
- Do not implement expected-pay intervals for net pay, overtime hours, bonus pay, deductions, or adjustment amounts in this change.
- Do not expand synthetic OOD schema beyond `pay_code` in this change.
- Do not claim live production integrations, analyst feedback capture, or real payroll validation beyond the synthetic workflow.
- Do not add a separate uncertainty notebook.
- Do not expose injected synthetic labels or injected anomaly dollars in analyst-safe review queue outputs.

## Decisions

1. Use Polars-first library implementation with notebook presentation.

   Implement reusable data transforms, aggregations, queue shaping, and evaluation tables with Polars in `src/payroll_anomaly_ranking/`. Use NumPy and scikit-learn only at model boundaries where arrays or estimators are required. Notebooks should present results and narrative rather than duplicating formulas.

   Alternative considered: use pandas for selected uncertainty calculations. The codebase is Polars-first, so mixing dataframe engines would add conversion overhead and inconsistent semantics.

2. Treat uncertainty as separate from risk.

   Keep `final_anomaly_score` as the ranking score and add separate uncertainty columns. Analysts should be able to see a high-risk record with medium uncertainty, such as highly anomalous overtime with a small peer group, without uncertainty suppressing the record.

   Alternative considered: directly penalize risk by uncertainty. That can hide risky records and makes it unclear whether a lower rank means lower risk or lower confidence.

3. Use rolling last 6 prior pay periods as the default reference window.

   Add `reference_window_periods=6` to configuration and use it for conformal calibration context, bootstrap model-reference data, OOD rarity/novelty references, and gross-pay interval references. For a scored period, only records from prior periods in that window are eligible references.

   Alternative considered: use the existing fixed train/validation/test split for all uncertainty calculations. That is simpler, but it does not reflect the per-pay-period operational scoring point.

4. Compute ensemble disagreement from configured score signals.

   Use weighted disagreement across available rule, history, peer, statistical, ML, and exposure score signals. The weights should be configurable separately from hybrid risk weights because some signals overlap and disagreement is an uncertainty concept rather than the ranking objective.

   Alternative considered: rely only on existing hybrid weights. That is simpler, but it hides the distinction between risk contribution and signal disagreement.

5. Implement bootstrap uncertainty around Isolation Forest with bounded runtime.

   Generate bootstrap index arrays with NumPy and fit multiple Isolation Forest models over sampled reference matrices to produce raw or normalized ML-score interval statistics. Model fitting still requires one estimator per bootstrap sample, so defaults should be modest and configurable.

   Alternative considered: skip bootstrap because repeated model fitting can be slow. Bootstrap sensitivity is part of the requested uncertainty story, so keep it with runtime controls.

6. Add expected gross-pay interval prediction for v1.

   Produce `expected_gross_pay_p10`, `expected_gross_pay_p50`, `expected_gross_pay_p90`, `expected_gross_pay_interval_width`, and `gross_pay_excess_vs_p90` using only the last 6 prior periods as reference or training context. Excess over p90 is risk context; interval width contributes to uncertainty.

   Alternative considered: model intervals for gross pay, net pay, overtime hours, bonus pay, deductions, and adjustments at once. That is broader than needed for this change and would dilute the review queue story.

7. Use conformal outputs as explanation-only context.

   Compute conformal p-values from last-6-prior-period calibration scores where higher scores mean more anomalous records, then expose `conformal_percentile` as an analyst-readable statement about recent payroll history. Do not include conformal values in the composite uncertainty score.

   Alternative considered: use conformal p-values as an uncertainty component. Low conformal p-values indicate unusualness, not necessarily model uncertainty, so including them in the composite would conflate risk context with confidence.

8. Add synthetic `pay_code` for OOD realism.

   Extend generated payroll records with `pay_code`. Later periods should introduce new or rare pay codes and shifts in pay-code mix so OOD detection can identify unseen pay codes and rare pay-code combinations using the same rolling 6-period reference window. Evaluation-only OOD metadata may be generated for notebook diagnostics, but it must not be used as a scoring feature or analyst queue field.

   Alternative considered: detect OOD only through numeric nearest-neighbor distance. Numeric distance is useful but does not demonstrate common payroll OOD cases such as new pay codes.

9. Limit analyst-safe queues to the latest pay period.

   The operational analyst queue should surface only the latest pay period, with a human-readable pay-period date or label. Historical scored rows remain available for backtesting, risk-coverage analysis, and evaluation-labeled outputs.

   Alternative considered: continue returning top-K rows for every period in the analyst queue. That is useful for demos but less realistic as an operational review artifact.

10. Add uncertainty evaluation only to evaluation-labeled contexts.

   Compute precision by uncertainty bucket, risk-coverage curves, abstention analysis, and interval diagnostics only where synthetic labels are intentionally available for evaluation. Analyst-safe queues must not include `is_anomaly`, `anomaly_category`, injected anomaly dollars, or evaluation-only OOD labels.

   Alternative considered: include evaluation-derived uncertainty diagnostics in queue rows. That would leak synthetic truth into an operational artifact.

## Risks / Trade-offs

- Bootstrap model fitting can slow notebook execution -> keep bootstrap count configurable and use modest defaults.
- Composite uncertainty weights are heuristic -> centralize weights in configuration and state that they should be tuned with analyst feedback when available.
- Expected gross-pay intervals will not explain every anomaly type -> scope v1 to gross pay and use other score components for overtime, lifecycle, deductions, and adjustment reasons.
- Conformal calibration can be misleading under distribution shift -> present conformal as recent-history context and monitor OOD separately.
- OOD nearest-neighbor distance can be scale-sensitive -> compute it over normalized/filled model features and separately track `pay_code` novelty.
- Adding `pay_code` changes the synthetic schema -> update the data dictionary, validation expectations, and tests.
- Latest-period queue behavior changes existing queue semantics -> keep historical metrics and scored outputs available so notebooks can still evaluate past periods.

## Why

Payroll analysts need to know not only which records are high risk, but also how reliable the score is and why that reliability may be limited. The current review queue prioritizes anomalies, but it does not explicitly surface uncertainty from conflicting model signals, small peer groups, limited employee history, data quality issues, or out-of-distribution records.

## What Changes

- Add transparent uncertainty scoring alongside the final payroll anomaly risk score.
- Compute uncertainty components for ensemble disagreement, bootstrap score interval width, gross-pay interval width, peer-group sample size, employee-history sample size, data quality issues, and out-of-distribution distance using Polars-first data transformations.
- Add expected gross-pay interval prediction for `gross_pay` only, including p10, p50, p90, interval width, and excess over p90 context.
- Add conformal p-values and conformal percentiles as analyst-readable anomaly context, but exclude conformal values from the composite uncertainty score.
- Use a configurable rolling reference window of the last 6 prior pay periods for calibration, OOD references, bootstrap references, and expected-pay interval references.
- Extend synthetic payroll data with `pay_code` and late-period pay-code novelty or rarity so out-of-distribution behavior is visible and reproducible.
- Skip calibration uncertainty until analyst feedback labels are available, but document where it will fit once review outcomes exist.
- Update the analyst review queue to include only the latest pay period with uncertainty bucket, uncertainty reason, conformal context, gross-pay interval context, and concise risk/uncertainty explanations.
- Extend evaluation outputs with precision by uncertainty bucket and risk-coverage analysis in addition to existing precision@K and dollars captured@K.
- Keep the work in the existing notebook sequence rather than adding a new notebook: scoring and uncertainty calculations belong with modeling/evaluation, while queue presentation belongs with review queue explainability and thresholds.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `payroll-anomaly-scoring`: Add uncertainty component calculations and composite uncertainty buckets to payroll anomaly scoring outputs.
- `payroll-review-queue`: Surface uncertainty, conformal context, and uncertainty-aware reasons in analyst-safe review queue rows and case cards.
- `payroll-anomaly-evaluation`: Add uncertainty quality metrics, including precision by uncertainty bucket and risk-coverage analysis.
- `synthetic-payroll-data`: Add `pay_code` and reproducible late-period pay-code drift or novelty for OOD demonstrations.

## Impact

- Affected Python modules likely include `src/payroll_anomaly_ranking/data.py`, `src/payroll_anomaly_ranking/features.py`, `src/payroll_anomaly_ranking/models.py`, `src/payroll_anomaly_ranking/evaluation.py`, `src/payroll_anomaly_ranking/explainability.py`, `src/payroll_anomaly_ranking/presentation.py`, and supporting column/config definitions.
- Affected notebooks likely include `notebooks/03_modeling_evaluation_and_error_analysis.py`, `notebooks/04_review_queue_explainability_and_thresholds.py`, and `notebooks/05_production_monitoring_and_deployment_path.py`.
- No production API or persisted data migration is expected.
- Dependencies should remain within the existing Python/scikit-learn/Polars stack unless implementation discovers a concrete gap.

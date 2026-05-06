## Why

The project needs explicit notebook demonstrations that teach why common anomaly-detection shortcuts produce misleading payroll risk conclusions. Adding side-by-side anti-pattern and corrected examples will make the modeling notebooks more defensible for technical and stakeholder audiences.

## What Changes

- Add notebook content that demonstrates six common mistakes with plots, explicit anti-pattern examples, and comparisons against corrected methods.
- Cover random train/test splitting, default-only Isolation Forest usage, ROC-AUC-only reporting, false-positive neglect, equal anomaly prioritization, and overclaiming fraud detection.
- Keep the demonstrations reproducible in the existing Jupytext notebook workflow and aligned with existing payroll anomaly ranking terminology.
- Avoid introducing breaking changes to existing APIs or data contracts.

## Capabilities

### New Capabilities
- `notebook-mistake-demonstrations`: Educational notebook demonstrations for payroll anomaly modeling and evaluation mistakes, including visual comparisons between anti-patterns and corrected approaches.

### Modified Capabilities

## Impact

- Affects notebook files under `notebooks/`, most likely the modeling/evaluation notebook and any needed sibling helper module.
- May reuse existing library functions from `src/payroll_anomaly_ranking/` for data generation, modeling, evaluation, and plotting.
- No API, dependency, or persisted data changes are expected.

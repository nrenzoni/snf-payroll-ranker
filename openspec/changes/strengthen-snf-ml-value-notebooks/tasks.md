## 1. Business Case-Study Notebook

- [ ] 1.1 Add Lets-Plot imports and setup to `notebooks/08_snf_payroll_approval_case_studies.py` while preserving `NOTEBOOK_FAST` execution controls.
- [ ] 1.2 Add narrative sections that frame notebook 08 as the SNF administrator/business proof of automated approval ranking value.
- [ ] 1.3 Build threshold-vs-hybrid scorecard tables for the overtime and premium case-study scenarios using existing evaluation outputs.
- [ ] 1.4 Add business-facing visuals or tables for exposure captured per reviewed record, false-positive avoidance, missed high-risk records, and facility approval concentration.
- [ ] 1.5 Add overtime-specific visual evidence showing staffing pressure, double-shift/rest-gap, paid-vs-scheduled, and estimated exposure context.
- [ ] 1.6 Add premium-specific visual evidence showing premium support, shift differential or weekend context, premium eligibility mismatch, and estimated exposure context.
- [ ] 1.7 Add administrator-safe case cards and selected queue tables that include recommended action, source to check, primary reason, expected-vs-actual context, risk category, uncertainty context where available, and estimated exposure.
- [ ] 1.8 Add a closing bridge from notebook 08 to the technical ML value notebook.

## 2. Technical ML Value Notebook

- [ ] 2.1 Create `notebooks/09_model_ablation_and_ml_value.py` as a Jupytext percent-format notebook with bounded defaults and `NOTEBOOK_FAST` support.
- [ ] 2.2 Add narrative framing that distinguishes business proof from technical validation and explains the method-complexity ladder.
- [ ] 2.3 Compare manual thresholds, deterministic rule score, robust statistical score, ML score, and hybrid score using approval-budget metrics, PR-AUC, rank metrics, exposure capture, and dollar capture where available.
- [ ] 2.4 Add incremental method-complexity visuals such as a lift table, waterfall, bar chart, or heatmap that makes component contribution visible.
- [ ] 2.5 Add threshold-miss and false-positive summaries using clearly labeled evaluation-only synthetic labels and dollar impacts where needed.
- [ ] 2.6 Add temporal validation, rolling-origin, uncertainty, risk-coverage, expected-pay interval, or robustness evidence from existing pipeline outputs where available without duplicating the full internal diagnostics notebooks.
- [ ] 2.7 Add a final technical proof summary that explains where ML-only helps, where hybrid improves beyond ML-only, and where simpler rule/statistical signals remain valuable.

## 3. Supporting Presentation Helpers

- [ ] 3.1 Identify duplicated notebook-local table shaping or plotting code and decide whether it should remain notebook-local or move to `notebooks/common/`.
- [ ] 3.2 If shared helpers are needed, implement them under `notebooks/common/` using Polars and Lets-Plot only at presentation boundaries.
- [ ] 3.3 Ensure all new or changed code uses column enums/constants from `columns.py` rather than raw project schema strings.

## 4. Documentation

- [ ] 4.1 Update README notebook sequence documentation to include notebook 09 and clarify the role of notebook 08 vs notebook 09.
- [ ] 4.2 Ensure notebook narratives avoid confirmed fraud, misconduct, or confirmed-error claims and maintain review-safe wording.

## 5. Verification

- [ ] 5.1 Run `NOTEBOOK_FAST=1 uv run jupytext --to ipynb --execute --run-path notebooks --output /tmp/08_snf_payroll_approval_case_studies.fast.ipynb notebooks/08_snf_payroll_approval_case_studies.py`.
- [ ] 5.2 Run `NOTEBOOK_FAST=1 uv run jupytext --to ipynb --execute --run-path notebooks --output /tmp/09_model_ablation_and_ml_value.fast.ipynb notebooks/09_model_ablation_and_ml_value.py`.
- [ ] 5.3 Run `uv run pytest tests/smoke`.
- [ ] 5.4 Run `uv run pytest tests/integration/test_regression.py -k "notebook or plotting or evaluation or diagnostic"` if supporting helpers, diagnostics, or evaluation paths change.
- [ ] 5.5 Run `uv run prek run --all-files` and resolve all reported issues.

## 1. Threshold Scoring And Evaluation

- [x] 1.1 Implement `ScoreCol.THRESHOLD_FACILITY_VARIANCE_FLAG` in scoring using scoring-time-available facility-relative pay context and the configured facility variance threshold.
- [x] 1.2 Extend threshold baseline evaluation outputs to include the facility payroll variance threshold alongside the existing threshold baselines.
- [x] 1.3 Add a calibrated manual threshold pack baseline that derives label-free cutoffs from reference payroll context using only raw administrator-style threshold fields.
- [x] 1.4 Expose review-burden, exposure-per-review, and missed-risk metrics needed for manual baseline versus ranking comparisons in notebook `08`.

## 2. Repeated-World Business-Proof Diagnostics

- [x] 2.1 Add plot-ready repeated-world comparison helpers for `baseline`, `overtime-staffing-pressure`, and `premium-mismatch` scenario-by-seed summaries.
- [x] 2.2 Add comparison outputs for per-method win rates, empirical intervals or mean deltas, and budget-level comparison series used by the business-proof notebook.
- [x] 2.3 Scope appendix stress diagnostics to true queue-stress or targeted stress constructions rather than simple scenario aliases.

## 3. Business-Facing Notebook Rewrite

- [x] 3.1 Rewrite `notebooks/08_snf_payroll_approval_case_studies.py` so the main flow leads with evaluation design, method explanations, and repeated-world proof plots.
- [x] 3.2 Replace dashboard-style intermediate tables with concise summaries and keep one final concrete ranked-output table with review-safe fields.
- [x] 3.3 Add appendix sections for stress diagnostics and make the notebook narrative explicit about evaluation-only labels, manual baseline calibration, and method limitations.

## 4. Verification

- [x] 4.1 Add or update targeted tests for threshold scoring and evaluation behavior, including the facility variance threshold baseline and calibrated manual threshold pack outputs.
- [x] 4.2 Run `NOTEBOOK_FAST=1 uv run jupytext --to ipynb --execute --run-path notebooks --output /tmp/08_snf_payroll_approval_case_studies.fast.ipynb notebooks/08_snf_payroll_approval_case_studies.py`.
- [x] 4.3 Run `uv run pytest tests/smoke` and any targeted regression coverage for scoring or evaluation changes.
- [x] 4.4 Run `uv run prek run --all-files`.

## 5. Realistic Rolling-Origin Business Proof

- [x] 5.1 Extend rolling-origin evaluation with facility-period review metrics, including exposure per review and dollar capture, so stability evidence matches facility-admin review capacity.
- [x] 5.2 Replace the business-facing rolling precision plot in notebook `08` with a yield-focused rolling-origin stability view and narrative that does not imply perfect operational precision.
- [x] 5.3 Add targeted regression coverage for the new rolling-origin facility-period metrics.
- [x] 5.4 Re-run notebook `08`, smoke tests, targeted evaluation tests, and `uv run prek run --all-files`.

## 6. Analyst Deliverable Polish

- [x] 6.1 Remove dashboard-like raw DataFrame outputs from the main notebook flow so `08` keeps only one concrete final ranked-output table.
- [x] 6.2 Make the main repeated-world and manual-threshold proof plots scenario-clear, either by explicit scenario aesthetics, scenario-specific filtering, or concise scenario summaries.
- [x] 6.3 Add concise quantified takeaway callouts after major proof visuals so the deliverable states the operational implication rather than requiring readers to infer it.
- [x] 6.4 Rework appendix queue-stress policies and metrics so stress evidence shows meaningful contrast across review policies instead of uniformly saturated overload probability.
- [x] 6.5 Remove remaining hard probability gradient limits from notebook plots and keep Lets-Plot scales render-safe.
- [x] 6.6 Refine case-study visuals and the final queue table so they explain why records rank highly while preserving review-safe, administrator-facing language.
- [x] 6.7 Re-run notebook `08`, targeted notebook/diagnostic tests, smoke tests, and `uv run prek run --all-files`.

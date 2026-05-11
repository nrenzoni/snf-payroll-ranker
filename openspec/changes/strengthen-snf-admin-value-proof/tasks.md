## 1. Threshold Scoring And Evaluation

- [ ] 1.1 Implement `ScoreCol.THRESHOLD_FACILITY_VARIANCE_FLAG` in scoring using scoring-time-available facility-relative pay context and the configured facility variance threshold.
- [ ] 1.2 Extend threshold baseline evaluation outputs to include the facility payroll variance threshold alongside the existing threshold baselines.
- [ ] 1.3 Add a calibrated manual threshold pack baseline that derives label-free cutoffs from reference payroll context using only raw administrator-style threshold fields.
- [ ] 1.4 Expose review-burden, exposure-per-review, and missed-risk metrics needed for manual baseline versus ranking comparisons in notebook `08`.

## 2. Repeated-World Business-Proof Diagnostics

- [ ] 2.1 Add plot-ready repeated-world comparison helpers for `baseline`, `overtime-staffing-pressure`, and `premium-mismatch` scenario-by-seed summaries.
- [ ] 2.2 Add comparison outputs for per-method win rates, empirical intervals or mean deltas, and budget-level comparison series used by the business-proof notebook.
- [ ] 2.3 Scope appendix stress diagnostics to true queue-stress or targeted stress constructions rather than simple scenario aliases.

## 3. Business-Facing Notebook Rewrite

- [ ] 3.1 Rewrite `notebooks/08_snf_payroll_approval_case_studies.py` so the main flow leads with evaluation design, method explanations, and repeated-world proof plots.
- [ ] 3.2 Replace dashboard-style intermediate tables with concise summaries and keep one final concrete ranked-output table with review-safe fields.
- [ ] 3.3 Add appendix sections for stress diagnostics and make the notebook narrative explicit about evaluation-only labels, manual baseline calibration, and method limitations.

## 4. Verification

- [ ] 4.1 Add or update targeted tests for threshold scoring and evaluation behavior, including the facility variance threshold baseline and calibrated manual threshold pack outputs.
- [ ] 4.2 Run `NOTEBOOK_FAST=1 uv run jupytext --to ipynb --execute --run-path notebooks --output /tmp/08_snf_payroll_approval_case_studies.fast.ipynb notebooks/08_snf_payroll_approval_case_studies.py`.
- [ ] 4.3 Run `uv run pytest tests/smoke` and any targeted regression coverage for scoring or evaluation changes.
- [ ] 4.4 Run `uv run prek run --all-files`.

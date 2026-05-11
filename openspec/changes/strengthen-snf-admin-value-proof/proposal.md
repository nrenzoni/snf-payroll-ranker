## Why

The current SNF case-study notebook demonstrates that the review queue is usable, but it does not yet provide the repeated, explanation-rich business proof that savvy facility administrators need before trusting hybrid anomaly ranking over familiar threshold review. The current manual-threshold comparison is also incomplete and not sufficiently realistic for scenario-scaled payroll worlds because the facility payroll variance threshold baseline is missing and the business notebook does not center a calibrated combined manual baseline.

## What Changes

- Reframe `notebooks/08_snf_payroll_approval_case_studies.py` as a facility-admin business-proof notebook that leads with rigorous repeated-world comparison instead of queue walkthroughs.
- Add explanation-heavy narrative that defines what manual thresholds, deterministic rules, robust statistics, ML-only scoring, and hybrid ranking each do, what each method is good at, and where each method is limited in SNF payroll approval.
- Introduce a calibrated combined manual threshold baseline that uses raw operational threshold fields only, calibrates from reference payroll context without labels, and serves as the primary manual comparator in business-facing notebook evidence.
- Implement and report the missing facility payroll variance threshold baseline so manual-threshold evaluation matches the existing spec surface.
- Expand notebook proof structure to compare repeated scenario and seed worlds across baseline, overtime staffing pressure, and premium mismatch scenarios, while moving stress variants into an appendix-style section.
- Keep one concrete final ranked-output table in the business notebook while demoting dense queue tables and dashboard-style detail from the main narrative.

## Capabilities

### New Capabilities
- `snf-admin-business-proof`: Business-facing repeated-world proof notebook coverage for facility-admin review decisions, calibrated manual baseline comparison, and explanation-rich method narrative.

### Modified Capabilities
- `snf-payroll-approval-workflow`: Change the business-facing case-study notebook requirements so `08` becomes a facility-admin proof notebook with one concrete output table and appendix stress diagnostics.
- `payroll-anomaly-evaluation`: Extend threshold baseline evaluation requirements to include the combined calibrated manual baseline, repeated-world business-proof summaries, and the missing facility payroll variance threshold baseline.
- `payroll-anomaly-scoring`: Require generation of the facility payroll variance threshold flag used by evaluation and business-proof notebook comparisons.

## Impact

- Affected code: notebook `08`, threshold scoring in `src/payroll_anomaly_ranking/models.py`, evaluation helpers in `src/payroll_anomaly_ranking/evaluation.py`, and supporting diagnostics or notebook utilities for repeated scenario-by-seed comparison.
- Affected specs: `snf-payroll-approval-workflow`, `payroll-anomaly-evaluation`, `payroll-anomaly-scoring`, plus one new capability spec for the business-proof notebook contract.
- No external API or dependency changes are expected.
- Verification will need notebook fast execution, `uv run prek run --all-files`, and relevant pytest coverage for scoring and evaluation updates.

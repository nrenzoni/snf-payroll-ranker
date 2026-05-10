## 1. SNF Domain Schema And Contracts

- [ ] 1.1 Replace generic payroll schema constants with SNF shift-level, payroll-line, schedule, timeclock, facility-rollup, approval, feature, rule, score, metric, and review column enums/constants.
- [ ] 1.2 Add `StrEnum` controlled vocabularies for SNF roles, license types, unit types, shift types, labor sources, pay-code categories, approval statuses, source-to-check values, recommendations, scenario families, and anomaly categories.
- [ ] 1.3 Add typed dataclasses for SNF generator config, facility profiles, pay policy config, scenario config, generated data results, validation results, scored results, and threshold baseline results.
- [ ] 1.4 Add config and policy validation helpers that fail early for invalid counts, periods, policy windows, enum values, target counts, and unsupported scenario names.
- [ ] 1.5 Update public API exports and imports to use named dataclass result objects and attribute access only.

## 2. Shift-Level SNF Synthetic Generator

- [ ] 2.1 Implement facility generation for a synthetic multi-facility SNF chain with size tier, region, payroll maturity, staffing pressure, units, and facility profile metadata.
- [ ] 2.2 Implement employee generation with synthetic identifiers, home facility, role, license type, tenure, employment status, base rate, shift preference, and lifecycle dates.
- [ ] 2.3 Implement schedule generation with facility, unit, role, shift date, shift type, scheduled start/end context, scheduled hours, and pay period assignment.
- [ ] 2.4 Implement timeclock generation with worked hours, clock variance, missed punches, manual edits, approval status, paid-without-schedule context, and schedule exception flags.
- [ ] 2.5 Implement payroll line generation from schedule, timeclock, and policy context with pay code, pay-code category, hours, rate, multiplier, gross pay, premium amount, and net-pay or deduction proxy if retained.
- [ ] 2.6 Implement pay-period/facility and pay-period/employee rollups derived from shift-level payroll lines.
- [ ] 2.7 Add reconciliation validation that verifies rollup hours, gross pay, overtime hours, and premium dollars match underlying shift-level payroll lines within tolerance.
- [ ] 2.8 Update synthetic data writers to export SNF shift-level payroll, labels, rollups, metadata, and validation artifacts to stable output paths.

## 3. SNF Scenarios And Labels

- [ ] 3.1 Replace generic scenario catalog entries with SNF implemented scenarios for overtime/double-shift staffing pressure and premium pay or shift differential mismatch.
- [ ] 3.2 Add documented future scenario catalog entries for agency/float labor, census/acuity, credential/license mismatch, PBJ category mismatch, meal break premiums, new hire orientation, termination/final pay, retro/rate corrections, union policy variation, new-client bootstrap, and payroll close adjustment concentration.
- [ ] 3.3 Implement targeted anomaly controls by facility, unit, role, shift type, pay-code category, period, and exposure range.
- [ ] 3.4 Implement overtime/double-shift anomaly injection by modifying observable schedule, timeclock, hours, rest-gap, or payroll context while retaining evaluation-only labels.
- [ ] 3.5 Implement premium mismatch anomaly injection by modifying observable pay-code, premium, shift-window, weekend, duplicate premium, or eligibility context while retaining evaluation-only labels.
- [ ] 3.6 Ensure injected labels, anomaly categories, anomaly dollars, and scenario truth metadata are excluded from scoring features, threshold baselines, exposure estimates, and administrator-safe outputs.

## 4. Validation And Data Quality

- [ ] 4.1 Replace generic payroll validation with SNF schema, referential, policy, lifecycle, schedule, timeclock, payroll-line, and rollup validation checks.
- [ ] 4.2 Add warning-level checks for paid hours exceeding scheduled hours, missing approval context, unsupported premium context, duplicate shift signatures, extreme overtime, rest-gap risk, missed punches, and manual edits.
- [ ] 4.3 Update data dictionaries and quality summaries to document synthetic SNF fields, privacy sensitivity, validation expectations, and scenario metadata.
- [ ] 4.4 Maintain or create `RESEARCH_LOG.md` entries for SNF domain assumptions, synthetic policy choices, and feature normalization decisions that influence implementation.

## 5. Feature Engineering

- [ ] 5.1 Rebuild history features for shift-level SNF records using leakage-safe prior pay periods and prior shifts only.
- [ ] 5.2 Add stationary ratio features for overtime per scheduled hour, worked hours per scheduled hour, premium pay share, gross pay versus expected role-shift pay, manual edit rate where available, and exposure relative to expected pay.
- [ ] 5.3 Add facility-normalized features using facility-relative, comparable-facility, role-shift peer, unit-role, pay-code-category, and cross-facility references.
- [ ] 5.4 Add schedule/timeclock reconciliation features for paid-vs-scheduled variance, clock variance, missed punch context, manual edit context, approval status, paid-without-schedule, and schedule exception context.
- [ ] 5.5 Add premium eligibility features for shift differential, weekend premium, holiday premium if implemented, callback, duplicate premium, pay-code eligibility, and premium amount deviation.
- [ ] 5.6 Add fatigue and staffing-pressure features for trailing hours, same-day shift count, double-shift indicator, rest-gap hours, consecutive worked days, and prior-period double-shift count.
- [ ] 5.7 Update model feature column lists to include only leakage-safe SNF production-observable columns and exclude all evaluation truth fields.

## 6. Rules, Scoring, And Threshold Baselines

- [ ] 6.1 Replace generic rule flags with SNF approval rule flags for paid-vs-scheduled exceptions, overtime/double-shift/rest-gap risk, unsupported premiums, duplicate premium codes, pay after termination, duplicate shift payment signatures, nonpositive active pay, and deduction/net-pay checks where retained.
- [ ] 6.2 Rebuild robust statistical, history, peer, schedule/timeclock, premium eligibility, exposure, ML, and hybrid approval exception scores for shift-level records.
- [ ] 6.3 Preserve risk and uncertainty separation while updating uncertainty components and reasons for SNF facility, peer, employee history, data quality, and OOD context.
- [ ] 6.4 Implement administrator-style threshold baselines for gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance.
- [ ] 6.5 Update temporal split, backtesting, ranking, and rolling-origin behavior to work at shift-level grain and facility/pay-period grouping where applicable.

## 7. Evaluation And Diagnostics

- [ ] 7.1 Update review-budget metrics to approval-budget metrics for shift-level records and facility/pay-period summaries.
- [ ] 7.2 Add threshold baseline comparison metrics for review volume, precision, recall, F1, PR-AUC, average anomaly rank, mean reciprocal rank, estimated exposure captured, synthetic dollars captured, false positives avoided, and missed high-exposure exceptions.
- [ ] 7.3 Add case-study-specific evaluation outputs for overtime/double-shift scenarios versus overtime and total-hours thresholds.
- [ ] 7.4 Add case-study-specific evaluation outputs for premium mismatch scenarios versus gross-pay and premium-dollar thresholds.
- [ ] 7.5 Update subgroup diagnostics to use SNF hierarchy fields such as facility, unit, role, license type, shift type, pay-code category, approval status, tenure band, and anomaly category.
- [ ] 7.6 Update internal diagnostics and queue simulation outputs to consume SNF scenarios or clearly mark unsupported diagnostics as future work during the transition.

## 8. Administrator Approval Outputs

- [ ] 8.1 Replace analyst review queue outputs with administrator-safe pre-approval exception queues for the latest pay period by default.
- [ ] 8.2 Add approval queue fields for facility, unit, role, shift date, shift type, approval risk category, recommended action, source to check, scheduled hours, worked hours, overtime context, premium context, estimated exposure, and review-safe explanations.
- [ ] 8.3 Add facility/pay-period approval summary outputs with total shifts, total gross pay, total paid hours, overtime hours, premium dollars, queue count, high-priority count, estimated exposure, top reason categories, and approval readiness context.
- [ ] 8.4 Add evaluation-labeled queue variants for synthetic diagnostics only and verify administrator-safe outputs exclude labels and injected dollars.
- [ ] 8.5 Update case-card presentation helpers to use administrator language and avoid fraud, misconduct, or confirmed-error claims.

## 9. Notebooks And Documentation

- [ ] 9.1 Replace README narrative, expected outputs, limitations, and production flow with SNF weekly payroll approval framing.
- [ ] 9.2 Replace business-facing Jupytext notebooks with SNF payroll approval story, schema/data maturity, feature engineering, threshold baselines, modeling/evaluation, approval queue, two case studies, and production monitoring.
- [ ] 9.3 Include overtime/double-shift staffing pressure case-study tables or visuals comparing automated ranking to manual overtime and total-hours thresholds.
- [ ] 9.4 Include premium pay and shift differential mismatch case-study tables or visuals comparing automated ranking to manual gross-pay and premium-dollar thresholds.
- [ ] 9.5 Update notebook visuals to use SNF fields, administrator summaries, facility/pay-period rollups, threshold baseline comparisons, and review-safe case cards with Lets-Plot only.
- [ ] 9.6 Update internal diagnostic notebooks or skip paths so fast notebook checks remain reproducible without editing `.ipynb` artifacts directly.

## 10. Tests And Verification

- [ ] 10.1 Update smoke tests for the SNF pipeline outputs, generated files, administrator-safe queue, evaluation-labeled queue, and facility/pay-period summaries.
- [ ] 10.2 Add integration tests for SNF generator schema, controlled vocabularies, early validation failures, scenario injection, and rollup reconciliation.
- [ ] 10.3 Add integration tests for leakage-safe SNF features, premium eligibility features, fatigue features, facility normalization, and model feature column exclusions.
- [ ] 10.4 Add integration tests for SNF rules, hybrid scoring, threshold baselines, approval-budget evaluation, and queue label safety.
- [ ] 10.5 Run targeted tests for generation/scenarios, features/rules, scoring/evaluation, and notebook contracts with `uv run pytest tests/integration/test_regression.py -k "generation or scenario or feature or rule or scoring or evaluation or notebook"`.
- [ ] 10.6 Run `uv run pytest tests/smoke` after runtime changes.
- [ ] 10.7 Run `uv run prek run --all-files` after code or notebook changes and resolve all reported issues.

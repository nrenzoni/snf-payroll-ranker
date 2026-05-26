## 1. Runtime Alignment

- [x] 1.1 Remove evaluation-truth leakage from employee-pay-cycle scoring so active formulations do not use `anomaly_dollars`, labels, or other evaluation-only fields as scoring inputs.
- [x] 1.1a Add explicit employee-pay-cycle label engineering for `relevance_grade` and `net_utility`, including deterministic formulas, output columns, and label-only documentation.
- [x] 1.2 Fix employee-pay-cycle pipeline artifact wiring so uncertainty, risk-coverage, expected-interval, and production-candidacy outputs are written to the correct result fields.
- [x] 1.2a Extend employee-cycle evaluation outputs so ranking and review-budget summaries report utility-aware metrics sourced from `net_utility`.
- [x] 1.3 Implement or adapt critical hard-rule gating artifacts so the active notebook can define the residual universe, funnel summaries, and residual-only scoring datasets.
- [ ] 1.4 Add residual-specific diagnostic helpers needed for hard-rule funnel tables, issue-type diagnostics, top-K overlap views, severe-miss examples, and plot-ready notebook outputs.
- [ ] 1.5 Port any queue-stress, rolling validation, and comparison helpers needed by the residual notebook away from deprecated shift-level pipeline dependencies to active employee-pay-cycle outputs.

## 2. Notebook Contract Replacement

- [x] 2.1 Create the new primary Jupytext percent-format employee-pay-cycle notebook under `notebooks/` with the exact required section order from `0` through `11`.
- [x] 2.2 Implement the main narrative sections using active employee-pay-cycle runtime artifacts for residual problem framing, data generation, hard-rule gating, label engineering, feature engineering, model formulations, queue results, and final recommendation.
- [x] 2.2a Replace section 5 label-engineering scaffolding with implemented formulas, tables, and examples for residual `y_issue`, residual `y_dollar`, `anomaly_category`, `relevance_grade`, `rule_missed_severe_issue`, `observed_correction`, and `net_utility`.
- [x] 2.2b Remove compliance, PBJ, and HPRD framing from notebook text, targets, features, and evaluation metrics.
- [ ] 2.3 Implement ablation, diagnostics, explanations, and appendix sections using active employee-pay-cycle diagnostics or notebook-owned assembly built from active outputs.
- [x] 2.4 Ensure the notebook supports `NOTEBOOK_FAST=1` and still produces representative outputs for all required sections during fast validation.

## 3. Spec And Documentation Updates

- [x] 3.1 Update active docs to identify the single employee-pay-cycle notebook as the only active reporting contract and mark legacy notebook sequences as historical reference only.
- [x] 3.2 Update `README.md` and `notebooks/README.md` so they describe the new active residual-ranking notebook, its appendix role, and the correct execution or validation commands.
- [x] 3.3 Remove or revise remaining notebook-sequence references in active contributor-facing documentation where they conflict with the new contract.

## 4. Verification

- [ ] 4.1 Add or update tests that cover the new active notebook contract, residual-gating artifact integrity, and any new diagnostic helper behavior.
- [x] 4.1a Add or update tests that cover `relevance_grade`, `net_utility`, utility-aware metrics, and employee-cycle leakage checks.
- [x] 4.2 Run fast notebook validation for the new Jupytext notebook using `NOTEBOOK_FAST=1 uv run jupytext --to ipynb --execute --run-path notebooks --output /tmp/...`.
- [x] 4.3 Run `uv run pytest tests/smoke` and targeted regression checks for scoring, evaluation, and notebook behavior affected by the change.
- [ ] 4.4 Run `uv run prek run --all-files` and resolve all reported issues.

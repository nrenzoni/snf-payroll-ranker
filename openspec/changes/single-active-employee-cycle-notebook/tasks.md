## 1. Runtime Alignment

- [ ] 1.1 Remove evaluation-truth leakage from employee-pay-cycle scoring so active formulations do not use `anomaly_dollars`, labels, or other evaluation-only fields as scoring inputs.
- [ ] 1.2 Fix employee-pay-cycle pipeline artifact wiring so uncertainty, risk-coverage, expected-interval, and production-candidacy outputs are written to the correct result fields.
- [ ] 1.3 Add or adapt employee-pay-cycle diagnostic helpers needed for deep diagnostics, appendix evidence, and plot-ready notebook outputs.
- [ ] 1.4 Port queue-stress and repeated-world comparison helpers away from deprecated shift-level pipeline dependencies to active employee-pay-cycle outputs where those sections depend on them.

## 2. Notebook Contract Replacement

- [ ] 2.1 Create the new primary Jupytext percent-format employee-pay-cycle notebook under `notebooks/` with the exact required section order from `0` through `14`.
- [ ] 2.2 Implement the main narrative sections using active employee-pay-cycle runtime artifacts for problem framing, data generation, label engineering, feature engineering, model formulations, queue results, generalization, and production recommendation.
- [ ] 2.3 Implement deep diagnostics, robustness or stress-test, and appendix sections using active employee-pay-cycle diagnostics or notebook-owned assembly built from active outputs.
- [ ] 2.4 Ensure the notebook supports `NOTEBOOK_FAST=1` and still produces representative outputs for all required sections during fast validation.

## 3. Spec And Documentation Updates

- [ ] 3.1 Update active docs to identify the single employee-pay-cycle notebook as the only active reporting contract and mark legacy notebook sequences as historical reference only.
- [ ] 3.2 Update `README.md` and `notebooks/README.md` so they describe the new active notebook, its appendix role, and the correct execution or validation commands.
- [ ] 3.3 Remove or revise remaining notebook-sequence references in active contributor-facing documentation where they conflict with the new contract.

## 4. Verification

- [ ] 4.1 Add or update tests that cover the new active notebook contract, employee-pay-cycle artifact integrity, and any new diagnostic helper behavior.
- [ ] 4.2 Run fast notebook validation for the new Jupytext notebook using `NOTEBOOK_FAST=1 uv run jupytext --to ipynb --execute --run-path notebooks --output /tmp/...`.
- [ ] 4.3 Run `uv run pytest tests/smoke` and targeted regression checks for scoring, evaluation, and notebook behavior affected by the change.
- [ ] 4.4 Run `uv run prek run --all-files` and resolve all reported issues.

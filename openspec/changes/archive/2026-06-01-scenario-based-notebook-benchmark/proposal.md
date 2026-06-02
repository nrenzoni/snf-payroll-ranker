## Why

The active employee-pay-cycle notebook still presents its headline evidence as a single synthetic run, even though the project already has scenario-driven generation hooks and stability-oriented evaluation requirements. That framing now conflicts with the intended interpretation of the study: model conclusions should be based on aggregation across multiple synthetic data-generating processes and seeds, not on one baseline world.

## What Changes

- Reframe the active notebook's main narrative from a single-run residual evaluation to a DGP scenario-based residual ranking benchmark.
- Replace the current section 8 main-results contract with an aggregated study organized by `DGP scenario x seed x model x review budget x metric`.
- Rename and update notebook sections so section 2 describes the synthetic DGP family and section 4 presents scenario-aware sanity checks rather than only one residual dataset snapshot.
- Expand the implemented synthetic DGP scenario catalog to cover baseline operations, high timekeeping noise, high facility heterogeneity, heavy dollar tail, subtle residual issues, biased historical corrections, diversified severe issues, and temporal payroll drift.
- Add notebook-backed aggregation outputs for scenario catalog coverage, scenario-seed study design, winner frequency, median metric summaries with intervals, and winner maps by objective and review budget.
- Preserve percent-budget framing, leakage controls, and employee-cycle runtime evidence while shifting notebook conclusions to scenario-seed aggregation.

## Capabilities

### New Capabilities

- `scenario-based-notebook-benchmark`: Defines the notebook-facing aggregated DGP scenario benchmark outputs, study unit, and interpretation rules for scenario-seed model comparison.

### Modified Capabilities

- `employee-cycle-notebook-reporting`: Change the fixed notebook section contract and main-results reporting requirements from single-run framing to scenario-aware narrative and aggregated benchmark outputs.
- `synthetic-payroll-data`: Expand the implemented scenario catalog and scenario-controlled generator requirements to cover the new DGP suite and notebook-visible scenario summaries.
- `payroll-anomaly-evaluation`: Extend evaluation reporting requirements so active notebook conclusions and stability summaries can be aggregated across scenarios, seeds, and review-budget operating points.

## Impact

- Affected notebook: `notebooks/snf_payroll_ranker_report.py`
- Affected generator and scenario definitions: `src/payroll_anomaly_ranking/scenarios.py`, `src/payroll_anomaly_ranking/data.py`
- Affected evaluation and diagnostics assembly: employee-cycle scenario/seed aggregation helpers under `src/payroll_anomaly_ranking/`
- Affected OpenSpec contracts: notebook reporting, synthetic payroll scenario generation, and evaluation stability/reporting
- Verification impact: requires notebook validation execution, `uv run prek run --all-files`, smoke tests, and targeted notebook/reporting regression coverage

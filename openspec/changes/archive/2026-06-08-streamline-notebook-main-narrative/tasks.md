## 1. Main Narrative Restructure

- [x] 1.1 Review `notebooks/snf_payroll_ranker_report.py` for current main-narrative raw dataframe outputs and identify which outputs are decision-critical versus audit-support.
- [x] 1.2 Rename or reframe section 4 as `Residual Benchmark Stress Design`, or merge its content into adjacent sections while preserving the required top-to-bottom decision flow.
- [x] 1.3 Replace broad main-narrative simulation sanity tables with concise prose, plot-first evidence, or compact cards that summarize scenario variation in issue rate, severe rate, dollars, dominant family, and label bias.
- [x] 1.4 Ensure the main narrative flows through residual gate, labels/features, model formulations, scenario benchmark results, diagnostics, and recommendation without table-heavy interruptions.

## 2. Appendix and Audit Evidence

- [x] 2.1 Move detailed scenario catalog rows, scenario-seed design rows, cross-scenario sanity tables, full winner-frequency rows, and full median metric tables to the technical appendix or another clearly labeled audit-support location.
- [x] 2.2 Keep synthetic-data transparency artifacts available, including data dictionary, hard-rule definitions, metric definitions, ranking group construction, zero-positive policy, stress-test configuration, calibration diagnostics, and examples.
- [x] 2.3 Confirm appendix wording makes clear which detailed tables support the compact main-narrative visuals.

## 3. Benchmark Presentation

- [x] 3.1 Present aggregate winner frequency in the main benchmark section as a reader-facing plot or compact decision summary.
- [x] 3.2 Present median benchmark metrics with interval evidence using plot-first or compact table-first output that avoids mixing incompatible metric scales in one chart.
- [x] 3.3 Render the winner map by winning model and review-budget percentage, while preserving selection metric values in appendix tables or annotations.
- [x] 3.4 Keep seed-versus-scenario interpretation in the main benchmark narrative without requiring broad raw scenario-seed tables before the appendix.

## 4. Recommendation and Examples

- [x] 4.1 Replace wide reviewer queue examples in the main narrative with a compact reviewer-facing view focused on action, reason, risk, and key score context.
- [x] 4.2 Present the final recommendation as a compact decision card or equivalent narrative summary, with detailed recommendation rows retained only if useful for appendix support.

## 5. Verification

- [x] 5.1 Run `uv run prek run --all-files` after notebook source edits and keep any hook-applied changes.
- [x] 5.2 Run reduced notebook validation on the final formatted source: `NOTEBOOK_VALIDATE=1 uv run jupytext --to ipynb --execute --run-path notebooks --output tmp/snf_payroll_ranker_report.validate.ipynb notebooks/snf_payroll_ranker_report.py`.
- [x] 5.3 Run `uv run pytest tests/smoke`.
- [x] 5.4 Run `uv run pytest tests/integration/test_regression.py -k "notebook or plotting"`.
- [x] 5.5 Inspect `git diff` to confirm the change is limited to intended spec and notebook narrative files.

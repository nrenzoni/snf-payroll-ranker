## 1. Spec-Aligned Runtime Foundations

- [x] 1.1 Extend `src/payroll_anomaly_ranking/scenarios.py` so the implemented catalog covers baseline operations, high timekeeping noise, high facility heterogeneity, heavy dollar tail, subtle residual issues, biased historical corrections, diversified severe issues, and temporal payroll drift with notebook-visible descriptions.
- [x] 1.2 Add or refine typed scenario controls in the employee-cycle synthetic generator so the new scenarios produce real DGP differences for timekeeping noise, facility heterogeneity, dollar tails, residual subtlety, bias strength, severe-issue diversification, and temporal drift.
- [x] 1.3 Update observed-correction simulation and related scenario plumbing so bias-strength scenarios change historical correction selection without leaking evaluation-only labels into scoring features.

## 2. Scenario Benchmark Aggregation

- [x] 2.1 Add a typed employee-cycle benchmark helper under `src/payroll_anomaly_ranking/` that runs scenario x seed employee-cycle scoring and evaluation and returns named dataclass outputs built from Polars DataFrames.
- [x] 2.2 Implement notebook-ready aggregation outputs for scenario catalog rows, scenario-seed design rows, winner frequency summaries, median metric tables with interval columns, and winner-map plot inputs.
- [x] 2.3 Ensure the benchmark helper is multi-seed capable while keeping notebook defaults configurable for a one-seed interim run.

## 3. Notebook Reframing

- [x] 3.1 Rewrite section `0. Executive Summary` in `notebooks/snf_payroll_ranker_report.py` so the main finding and interpretation are based on scenario-seed aggregation rather than a single-run baseline narrative.
- [x] 3.2 Rename section `2` to `Synthetic DGP Design and Scenario Suite`, retain the existing DGP diagram, and add the implemented scenario table plus the note that review capacity is a separate operating point.
- [x] 3.3 Update section `4` so it opens with a cross-scenario DGP summary table and keeps only clearly labeled baseline sanity plots as illustrative examples.
- [x] 3.4 Replace section `8` with `Main Study: DGP Scenario-Based Residual Ranking Benchmark` and render the scenario catalog, scenario-seed design, aggregate winner frequency, median metric table with intervals, winner map by objective and review budget, and the seed-versus-scenario interpretation note.

## 4. Supporting Contract And Research Updates

- [x] 4.1 Update any notebook appendix or runtime artifact summary content that still describes the old single-run framing so it stays consistent with the scenario-based benchmark contract.
- [x] 4.2 Add a concise entry to `RESEARCH_LOG.md` capturing the benchmark-framing decision, the interim one-seed default, and any interpretation caveats that affect implementation.

## 5. Verification

- [x] 5.1 Run `NOTEBOOK_VALIDATE=1 uv run jupytext --to ipynb --execute --run-path notebooks --output tmp/snf_payroll_ranker_report.validate.ipynb notebooks/snf_payroll_ranker_report.py`.
- [x] 5.2 Run `uv run prek run --all-files`.
- [x] 5.3 Run `uv run pytest tests/smoke` and `uv run pytest tests/integration/test_regression.py -k "notebook or plotting or evaluation"`.

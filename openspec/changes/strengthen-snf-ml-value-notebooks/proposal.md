## Why

The SNF payroll approval case-study notebook currently shows sparse tables but does not make the incremental value of automated ML-assisted anomaly ranking obvious against administrator-style manual threshold review. Strengthening the notebook sequence now will make the project persuasive to both SNF payroll operators and data scientists by separating business proof from technical validation while keeping both tied to the same leakage-safe evaluation story.

## What Changes

- Expand `notebooks/08_snf_payroll_approval_case_studies.py` into a business-facing SNF approval proof notebook with narrative throughout, case-study visuals, threshold-vs-hybrid lift scorecards, missed-by-threshold examples, false-positive avoidance summaries, facility approval views, and administrator-safe case cards.
- Add a new data-science-facing notebook, tentatively `notebooks/09_model_ablation_and_ml_value.py`, focused on method-complexity comparison, score-component ablation, temporal validation evidence, uncertainty/trust diagnostics, and robustness/stability summaries.
- Make the incremental value ladder explicit: manual thresholds, deterministic rules, robust statistical scoring, ML scoring, and hybrid ranking.
- Add plot-ready tables and Lets-Plot visuals where existing pipeline outputs support them; add small helper transformations in notebooks or reusable notebook/common helpers only when needed.
- Preserve analyst-safe boundaries: business-facing queues and case cards must not expose synthetic labels, anomaly categories, or injected anomaly dollars except in clearly evaluation-labeled technical sections.
- Update README notebook sequence documentation if the new notebook is added.
- No breaking changes are intended.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `snf-payroll-approval-workflow`: strengthen requirements for business-facing case-study evidence that compares automated ranking with administrator-style manual thresholds.
- `payroll-review-queue`: strengthen notebook requirements for administrator-safe narrative, case cards, facility summaries, and threshold-improvement visuals.
- `payroll-anomaly-evaluation`: strengthen requirements for approval-budget, exposure, false-positive, missed-risk, ablation, and temporal-validation evidence in the notebook sequence.
- `payroll-anomaly-scoring`: strengthen requirements for explaining the incremental contribution of rule, statistical, ML, exposure, and hybrid score components.
- `notebook-reproducibility`: extend notebook sequence expectations to include the new technical validation notebook if added.

## Impact

- Affected notebooks: `notebooks/08_snf_payroll_approval_case_studies.py` and new `notebooks/09_model_ablation_and_ml_value.py`.
- Potential supporting code: notebook-only plotting or table-shaping helpers under `notebooks/common/` if repeated transformations become unwieldy.
- Potential README update to document the expanded notebook sequence.
- No production API, model-training contract, persisted data, or dependency changes are expected.
- Verification should include `uv run prek run --all-files`, `uv run pytest tests/smoke`, targeted notebook/plotting regression tests if affected, and fast execution of changed Jupytext notebooks with `NOTEBOOK_FAST=1 uv run jupytext --to ipynb --execute --run-path notebooks --output /tmp/<notebook>.fast.ipynb <notebook>.py`.
